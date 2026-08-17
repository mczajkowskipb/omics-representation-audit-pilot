"""Two-phase smoke-grid audit, null calibration, and atomic job publication."""

from __future__ import annotations

import csv
import gzip
import io
import json
import os
import resource
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from rep_audit.audit.diagnostics import run_source_audit
from rep_audit.audit.report import SourceAuditReport
from rep_audit.audit.selector import (
    NullCalibrationArtifact,
    RepresentationSelection,
    calibrate_null,
    select_representation,
)
from rep_audit.evaluation.simulation_metrics import evaluate_simulation_selection
from rep_audit.experiments.grid import make_smoke_grid
from rep_audit.experiments.job_spec import SimulationJobSpec
from rep_audit.io.canonical_json import (
    atomic_write_bytes,
    atomic_write_canonical_json,
    canonical_json_bytes,
    sha256_bytes,
)
from rep_audit.simulation.generators import generate_simulation


REQUIRED_JOB_FILES = (
    "config.json",
    "metrics.json",
    "assignments.csv.gz",
    "runtime.json",
    "artifact/audit.json",
    "artifact/selection.json",
    "DONE",
)
HASHED_JOB_FILES = (
    "config.json",
    "metrics.json",
    "assignments.csv.gz",
    "artifact/audit.json",
    "artifact/selection.json",
)
EXPECTED_JSON_SCHEMAS = {
    "config.json": "SimulationJobSpec/v1",
    "metrics.json": "SimulationMetrics/v1",
    "runtime.json": "RuntimeRecord/v1",
    "artifact/audit.json": "SourceAuditReport/v1",
    "artifact/selection.json": "RepresentationSelection/v1",
}


def _process_peak_rss_bytes() -> int:
    """Return the process high-water RSS with platform-correct units."""

    maximum = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Linux/BSD report KiB; macOS reports bytes.
    return maximum if sys.platform == "darwin" else maximum * 1024


def _assignment_bytes(
    report: SourceAuditReport,
    selection: RepresentationSelection,
) -> bytes:
    rows: list[tuple[str, str]] = []
    if selection.selected_method is None:
        sample_ids = tuple(report.representation_manifest["sample_ids"])
        rows = [(sample_id, "UNASSIGNED") for sample_id in sorted(sample_ids)]
    else:
        method = report.method_by_id(selection.selected_method)
        rows = [
            (sample_id, str(cluster))
            for sample_id, cluster in sorted(
                zip(method.sample_ids, method.assignments, strict=True),
                key=lambda item: item[0],
            )
        ]
    plain = io.StringIO(newline="")
    writer = csv.writer(plain, lineterminator="\n")
    writer.writerow(("sample_id", "cluster"))
    writer.writerows(rows)
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", filename="", mtime=0) as handle:
        handle.write(plain.getvalue().encode("utf-8"))
    return compressed.getvalue()


def _validate_job_directory(path: Path, *, expected_job_id: str | None = None) -> None:
    missing = [relative for relative in REQUIRED_JOB_FILES if not (path / relative).is_file()]
    if missing:
        raise ValueError(f"incomplete job {path.name}; missing: {', '.join(missing)}")
    done = json.loads((path / "DONE").read_text(encoding="utf-8"))
    job_id = path.name if expected_job_id is None else expected_job_id
    if done.get("schema") != "CompletedJob/v1" or done.get("job_id") != job_id:
        raise ValueError(f"invalid DONE marker for job {path.name}")
    expected = done.get("sha256", {})
    if not isinstance(expected, dict) or set(expected) != set(HASHED_JOB_FILES):
        raise ValueError(f"invalid checksum manifest for job {path.name}")
    for relative, checksum in expected.items():
        payload = (path / relative).read_bytes()
        if sha256_bytes(payload) != checksum:
            raise ValueError(f"checksum mismatch in {path.name}/{relative}")
    for relative, schema in EXPECTED_JSON_SCHEMAS.items():
        try:
            value = json.loads((path / relative).read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid JSON in {path.name}/{relative}") from error
        if not isinstance(value, dict) or value.get("schema") != schema:
            raise ValueError(f"invalid schema in {path.name}/{relative}")
    runtime = json.loads((path / "runtime.json").read_text(encoding="utf-8"))
    if (
        not isinstance(runtime.get("wall_seconds"), (int, float))
        or float(runtime["wall_seconds"]) < 0.0
        or not isinstance(runtime.get("peak_rss_bytes"), int)
        or runtime["peak_rss_bytes"] <= 0
        or runtime.get("threads_per_job") != 1
    ):
        raise ValueError(f"invalid runtime record for job {path.name}")
    try:
        with gzip.open(path / "assignments.csv.gz", mode="rt", newline="") as handle:
            header = next(csv.reader(handle), None)
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"invalid assignments archive for job {path.name}") from error
    if header != ["sample_id", "cluster"]:
        raise ValueError(f"invalid assignments schema for job {path.name}")


def _publish_job(
    output_root: Path,
    job: SimulationJobSpec,
    report: SourceAuditReport,
    selection: RepresentationSelection,
    metrics: Mapping[str, Any],
    *,
    wall_seconds: float,
    peak_rss_bytes: int,
) -> str:
    jobs_root = output_root / "jobs"
    jobs_root.mkdir(parents=True, exist_ok=True)
    destination = jobs_root / job.job_id
    if destination.exists():
        _validate_job_directory(destination)
        existing = (destination / "config.json").read_bytes()
        if existing != canonical_json_bytes(job.to_dict()):
            raise ValueError(f"existing job ID collision: {job.job_id}")
        return "skipped_valid_existing"

    temporary = Path(tempfile.mkdtemp(prefix=f".{job.job_id}.tmp-", dir=jobs_root))
    try:
        (temporary / "artifact").mkdir()
        atomic_write_canonical_json(temporary / "config.json", job.to_dict())
        atomic_write_canonical_json(temporary / "metrics.json", dict(metrics))
        atomic_write_bytes(
            temporary / "assignments.csv.gz", _assignment_bytes(report, selection)
        )
        atomic_write_canonical_json(
            temporary / "runtime.json",
            {
                "schema": "RuntimeRecord/v1",
                "wall_seconds": float(wall_seconds),
                "peak_rss_bytes": int(peak_rss_bytes),
                "threads_per_job": 1,
            },
        )
        report.save(temporary / "artifact" / "audit.json")
        selection.save(temporary / "artifact" / "selection.json")
        checksums = {
            relative: sha256_bytes((temporary / relative).read_bytes())
            for relative in HASHED_JOB_FILES
        }
        atomic_write_canonical_json(
            temporary / "DONE",
            {
                "schema": "CompletedJob/v1",
                "job_id": job.job_id,
                "sha256": checksums,
            },
        )
        _validate_job_directory(temporary, expected_job_id=job.job_id)
        os.replace(temporary, destination)
        return "completed"
    except BaseException as error:
        try:
            (temporary / "BLOCKER.txt").write_text(
                f"{type(error).__name__}: {error}\n", encoding="utf-8"
            )
        finally:
            raise


def _collect_summary(output_root: Path, expected_jobs: int) -> dict[str, Any]:
    jobs_root = output_root / "jobs"
    job_paths = sorted(
        path
        for path in jobs_root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )
    if len(job_paths) != expected_jobs:
        raise ValueError(f"expected {expected_jobs} completed jobs, found {len(job_paths)}")
    metrics: list[dict[str, Any]] = []
    for path in job_paths:
        _validate_job_directory(path)
        metrics.append(json.loads((path / "metrics.json").read_text(encoding="utf-8")))
    signal = [item for item in metrics if item["regime"] != "NULL"]
    null = [item for item in metrics if item["regime"] == "NULL"]
    pure = [item for item in signal if item["regime"] in {"VALUE", "RELATIONAL"}]
    signal_accuracy = sum(bool(item["decision_correct"]) for item in signal) / len(signal)
    null_false_structure_rate = sum(
        item["selected_decision"] != "NO_STABLE_STRUCTURE" for item in null
    ) / len(null)
    pure_hybrid_rate = sum(item["selected_decision"] == "HYBRID" for item in pure) / len(pure)
    by_regime: dict[str, dict[str, Any]] = {}
    for regime in ("VALUE", "RELATIONAL", "HYBRID", "NULL"):
        items = [item for item in metrics if item["regime"] == regime]
        by_regime[regime] = {
            "n": len(items),
            "decision_accuracy": sum(
                bool(item["decision_correct"]) for item in items
            )
            / len(items),
            "decision_counts": dict(
                sorted(Counter(item["selected_decision"] for item in items).items())
            ),
        }
    gate_checks = {
        "all_40_jobs_complete": len(metrics) == 40,
        "signal_decision_accuracy_at_least_0_70": signal_accuracy >= 0.70,
        "null_false_structure_rate_at_most_0_10": null_false_structure_rate <= 0.10,
        "pure_regime_hybrid_rate_at_most_0_20": pure_hybrid_rate <= 0.20,
    }
    summary = {
        "schema": "SmokeGridSummary/v1",
        "job_count": len(metrics),
        "signal_decision_accuracy": signal_accuracy,
        "null_false_structure_rate": null_false_structure_rate,
        "pure_regime_hybrid_selection_rate": pure_hybrid_rate,
        "by_regime": by_regime,
        "gate_checks": gate_checks,
        "smoke_gate_go": all(gate_checks.values()),
    }
    atomic_write_canonical_json(output_root / "summary.json", summary)
    return summary


def run_smoke_grid(
    config: Mapping[str, object],
    *,
    output_root: str | Path,
) -> dict[str, Any]:
    """Run all 40 audits, calibrate on NULL, then unblind evaluation truth."""

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    jobs = make_smoke_grid(config)
    reports: dict[str, SourceAuditReport] = {}
    elapsed: dict[str, float] = {}
    peak_rss: dict[str, int] = {}
    for index, job in enumerate(jobs, start=1):
        started = time.perf_counter()
        generated = generate_simulation(job.simulation)
        reports[job.job_id] = run_source_audit(generated.source, job.audit)
        elapsed[job.job_id] = time.perf_counter() - started
        peak_rss[job.job_id] = _process_peak_rss_bytes()
        print(
            f"AUDIT {index:02d}/40 {job.simulation.regime} "
            f"{job.simulation.signal} {job.simulation.shift} r{job.simulation.replicate}"
        )

    null_jobs = [job for job in jobs if job.simulation.regime == "NULL"]
    null_reports = [reports[job.job_id] for job in null_jobs]
    calibration = calibrate_null(
        null_reports,
        quantile=float(config["selector"]["null_quantile"]),  # type: ignore[index]
        minimum_hybrid_gain=float(
            config["selector"]["minimum_hybrid_gain"]  # type: ignore[index]
        ),
    )
    calibration.save(output_root / "null_calibration.json")

    for job in jobs:
        report = reports[job.job_id]
        if job.simulation.regime == "NULL":
            leave_one_out = [item for item in null_reports if item is not report]
            job_calibration = calibrate_null(
                leave_one_out,
                quantile=float(config["selector"]["null_quantile"]),  # type: ignore[index]
                minimum_hybrid_gain=float(
                    config["selector"]["minimum_hybrid_gain"]  # type: ignore[index]
                ),
            )
        else:
            job_calibration = calibration
        selection = select_representation(
            [report],
            job_calibration,
            equivalence_margin=float(
                config["selector"]["equivalence_margin"]  # type: ignore[index]
            ),
            minimum_decision_frequency=float(
                config["selector"]["minimum_decision_frequency"]  # type: ignore[index]
            ),
        )
        generated = generate_simulation(job.simulation)
        metrics = evaluate_simulation_selection(selection, report, generated.truth)
        _publish_job(
            output_root,
            job,
            report,
            selection,
            metrics,
            wall_seconds=elapsed[job.job_id],
            peak_rss_bytes=peak_rss[job.job_id],
        )
    return _collect_summary(output_root, expected_jobs=len(jobs))
