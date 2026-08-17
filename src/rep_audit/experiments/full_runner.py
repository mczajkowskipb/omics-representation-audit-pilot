"""Two-phase, resumable execution of the protocol's 630-pair Gate B grid."""

from __future__ import annotations

import json
import os
import resource
import shutil
import sys
import tempfile
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from threadpoolctl import threadpool_limits

from rep_audit.audit.diagnostics import fit_source_audit
from rep_audit.audit.distances import method_family
from rep_audit.audit.report import SourceAuditReport
from rep_audit.audit.selector import calibrate_null, select_representation
from rep_audit.experiments.grid import make_primary_grid
from rep_audit.experiments.job_spec import SimulationJobSpec
from rep_audit.io.canonical_json import (
    atomic_write_canonical_json,
    canonical_json_bytes,
    sha256_bytes,
)
from rep_audit.simulation.generators import generate_simulation
from rep_audit.transfer.artifact import freeze_transfer_set
from rep_audit.transfer.assign import TargetAssignmentSet, assign_target


PRELABEL_HASHED = (
    "config.json",
    "frozen_transfer.json",
    "target_assignments.json",
    "runtime.json",
)


def _peak_rss_bytes() -> int:
    maximum = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return maximum if sys.platform == "darwin" else maximum * 1024


def source_group_id(job: SimulationJobSpec) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {
                "schema": "PrimarySourceGroup/v1",
                "source_generation": job.simulation.source_generation_dict(),
                "audit": job.audit.to_dict(),
            }
        )
    )


def _validate_hashed_directory(
    path: Path,
    *,
    marker_name: str,
    marker_schema: str,
    expected_id: str,
    hashed_files: Sequence[str],
) -> None:
    marker_path = path / marker_name
    if not marker_path.is_file():
        raise ValueError(f"missing {marker_name}: {path}")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    if marker.get("schema") != marker_schema or marker.get("id") != expected_id:
        raise ValueError(f"invalid {marker_name}: {path}")
    checksums = marker.get("sha256")
    if not isinstance(checksums, dict) or set(checksums) != set(hashed_files):
        raise ValueError(f"invalid checksum inventory: {path}")
    for relative in hashed_files:
        payload = (path / relative).read_bytes()
        if sha256_bytes(payload) != checksums[relative]:
            raise ValueError(f"checksum mismatch: {path / relative}")


def _atomic_publish_directory(
    destination: Path,
    *,
    identifier: str,
    marker_name: str,
    marker_schema: str,
    files: Mapping[str, Any],
) -> str:
    if destination.exists():
        _validate_hashed_directory(
            destination,
            marker_name=marker_name,
            marker_schema=marker_schema,
            expected_id=identifier,
            hashed_files=tuple(files),
        )
        return "skipped_valid_existing"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{identifier[:12]}.tmp-", dir=destination.parent)
    )
    try:
        for relative, value in files.items():
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(value, bytes):
                target.write_bytes(value)
            else:
                target.write_bytes(canonical_json_bytes(value))
        checksums = {
            relative: sha256_bytes((temporary / relative).read_bytes())
            for relative in files
        }
        (temporary / marker_name).write_bytes(
            canonical_json_bytes(
                {"schema": marker_schema, "id": identifier, "sha256": checksums}
            )
        )
        _validate_hashed_directory(
            temporary,
            marker_name=marker_name,
            marker_schema=marker_schema,
            expected_id=identifier,
            hashed_files=tuple(files),
        )
        os.replace(temporary, destination)
        return "completed"
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _validate_source(path: Path, group_id: str) -> None:
    _validate_hashed_directory(
        path,
        marker_name="DONE",
        marker_schema="CompletedSourceAudit/v1",
        expected_id=group_id,
        hashed_files=("audit.json", "source.json", "runtime.json"),
    )


def _validate_prelabel_job(path: Path, job_id: str) -> None:
    _validate_hashed_directory(
        path,
        marker_name="PRELABEL_DONE",
        marker_schema="CompletedPrelabelJob/v1",
        expected_id=job_id,
        hashed_files=PRELABEL_HASHED,
    )
    frozen = json.loads((path / "frozen_transfer.json").read_text(encoding="utf-8"))
    assignments = json.loads(
        (path / "target_assignments.json").read_text(encoding="utf-8")
    )
    if frozen.get("schema") != "FrozenTransferSet/v1":
        raise ValueError(f"invalid frozen transfer schema: {path}")
    if assignments.get("schema") != "TargetAssignmentSet/v1" or not assignments.get(
        "label_free"
    ):
        raise ValueError(f"invalid label-free assignments: {path}")


def _prelabel_group(
    jobs: tuple[SimulationJobSpec, ...],
    output_root_text: str,
    transfer_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Worker entry point: fit one source and freeze its three target views."""

    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    output_root = Path(output_root_text)
    group_id = source_group_id(jobs[0])
    if any(source_group_id(job) != group_id for job in jobs) or len(jobs) != 3:
        raise ValueError("a primary source group must contain exactly three paired shifts")
    source_path = output_root / "prelabel" / "sources" / group_id
    job_paths = {
        job.job_id: output_root / "prelabel" / "jobs" / job.job_id for job in jobs
    }
    try:
        _validate_source(source_path, group_id)
        for job in jobs:
            _validate_prelabel_job(job_paths[job.job_id], job.job_id)
        return {"group_id": group_id, "status": "skipped_valid_existing"}
    except (FileNotFoundError, ValueError):
        pass

    started = time.perf_counter()
    with threadpool_limits(limits=1):
        generated_first = generate_simulation(jobs[0].simulation)
        fitted = fit_source_audit(generated_first.source, jobs[0].audit)
        audit_seconds = time.perf_counter() - started
        _atomic_publish_directory(
            source_path,
            identifier=group_id,
            marker_name="DONE",
            marker_schema="CompletedSourceAudit/v1",
            files={
                "audit.json": fitted.report.to_json_bytes(),
                "source.json": {
                    "schema": "PrimarySourceRecord/v1",
                    "group_id": group_id,
                    "source_generation": jobs[0].simulation.source_generation_dict(),
                    "source_fingerprint": generated_first.source.fingerprint(),
                    "paired_shifts": tuple(sorted(job.simulation.shift for job in jobs)),
                },
                "runtime.json": {
                    "schema": "RuntimeRecord/v1",
                    "wall_seconds": audit_seconds,
                    "peak_rss_bytes": _peak_rss_bytes(),
                    "threads_per_job": 1,
                },
            },
        )
        completed_jobs = 0
        for job in sorted(jobs, key=lambda item: item.simulation.shift):
            job_started = time.perf_counter()
            generated = generate_simulation(job.simulation)
            if generated.source.fingerprint() != generated_first.source.fingerprint():
                raise RuntimeError("paired shifts unexpectedly changed the source cohort")
            frozen = freeze_transfer_set(
                generated.source,
                generated.target.feature_ids,
                generated.target.dataset_id,
                fitted,
                minimum_feature_coverage=float(
                    transfer_config["minimum_feature_coverage"]
                ),
                minimum_relation_coverage=float(
                    transfer_config["minimum_relation_coverage"]
                ),
            )
            assignments = assign_target(generated.target, frozen)
            status = _atomic_publish_directory(
                job_paths[job.job_id],
                identifier=job.job_id,
                marker_name="PRELABEL_DONE",
                marker_schema="CompletedPrelabelJob/v1",
                files={
                    "config.json": {
                        "schema": "PrimaryPrelabelJob/v1",
                        "job": job.to_dict(),
                        "source_group_id": group_id,
                        "labels_loaded": False,
                    },
                    "frozen_transfer.json": frozen.to_json_bytes(),
                    "target_assignments.json": assignments.to_json_bytes(),
                    "runtime.json": {
                        "schema": "RuntimeRecord/v1",
                        "wall_seconds": time.perf_counter() - job_started,
                        "peak_rss_bytes": _peak_rss_bytes(),
                        "threads_per_job": 1,
                        "shared_source_audit_seconds": audit_seconds,
                    },
                },
            )
            completed_jobs += status == "completed"
    return {
        "group_id": group_id,
        "status": "completed",
        "completed_jobs": completed_jobs,
        "wall_seconds": time.perf_counter() - started,
    }


def _group_jobs(
    jobs: Sequence[SimulationJobSpec],
) -> tuple[tuple[SimulationJobSpec, ...], ...]:
    grouped: dict[str, list[SimulationJobSpec]] = {}
    for job in jobs:
        grouped.setdefault(source_group_id(job), []).append(job)
    result = tuple(
        tuple(sorted(items, key=lambda item: item.simulation.shift))
        for _, items in sorted(grouped.items())
    )
    if len(result) != 210 or any(len(items) != 3 for items in result):
        raise RuntimeError("630 jobs must form 210 paired source groups")
    return result


def run_prelabel_phase(
    config: Mapping[str, Any],
    *,
    output_root: str | Path,
    max_workers: int,
) -> dict[str, Any]:
    """Complete every label-free audit/assignment before returning."""

    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    jobs = make_primary_grid(config)
    groups = _group_jobs(jobs)
    workers = max(1, min(int(max_workers), len(groups)))
    started = time.perf_counter()
    status_counts: Counter[str] = Counter()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _prelabel_group,
                group,
                str(output_root),
                dict(config["transfer"]),
            ): group
            for group in groups
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            status_counts[str(result["status"])] += 1
            print(
                f"PRELABEL {completed:03d}/210 {result['status']} "
                f"{result['group_id'][:12]}",
                flush=True,
            )

    for group in groups:
        group_id = source_group_id(group[0])
        _validate_source(output_root / "prelabel" / "sources" / group_id, group_id)
    for job in jobs:
        _validate_prelabel_job(output_root / "prelabel" / "jobs" / job.job_id, job.job_id)
    config_sha = sha256_bytes(canonical_json_bytes(dict(config)))
    completion = {
        "schema": "PrelabelGridComplete/v1",
        "labels_loaded": False,
        "config_sha256": config_sha,
        "job_count": len(jobs),
        "source_group_count": len(groups),
        "job_ids_sha256": sha256_bytes(
            canonical_json_bytes(tuple(sorted(job.job_id for job in jobs)))
        ),
    }
    atomic_write_canonical_json(output_root / "PRELABEL_COMPLETE.json", completion)
    atomic_write_canonical_json(
        output_root / "prelabel_runtime.json",
        {
            "schema": "GridRuntimeRecord/v1",
            "wall_seconds": time.perf_counter() - started,
            "workers": workers,
            "status_counts": dict(sorted(status_counts.items())),
        },
    )
    return completion


def _require_complete_prelabel(
    config: Mapping[str, Any], output_root: Path, jobs: Sequence[SimulationJobSpec]
) -> str:
    path = output_root / "PRELABEL_COMPLETE.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    config_sha = sha256_bytes(canonical_json_bytes(dict(config)))
    if (
        value.get("schema") != "PrelabelGridComplete/v1"
        or value.get("labels_loaded") is not False
        or value.get("config_sha256") != config_sha
        or value.get("job_count") != 630
    ):
        raise ValueError("evaluation refused: invalid prelabel completion marker")
    for job in jobs:
        _validate_prelabel_job(output_root / "prelabel" / "jobs" / job.job_id, job.job_id)
    return sha256_bytes(path.read_bytes())


def _method_metrics(
    report: SourceAuditReport,
    assignments: TargetAssignmentSet,
    truth_values: Mapping[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method in report.methods:
        target_method = assignments.method_by_id(method.method_id)
        truth = [truth_values[row.sample_id] for row in target_method.rows]
        forced = [row.forced_cluster for row in target_method.rows]
        accepted_rows = [row for row in target_method.rows if row.accepted_cluster is not None]
        accepted_truth = [truth_values[row.sample_id] for row in accepted_rows]
        accepted_clusters = [int(row.accepted_cluster) for row in accepted_rows]
        rows.append(
            {
                "method_id": method.method_id,
                "family": method.family,
                "source_q": method.q_score,
                "target_ari_forced": float(adjusted_rand_score(truth, forced)),
                "target_nmi_forced": float(normalized_mutual_info_score(truth, forced)),
                "assignment_coverage": target_method.coverage,
                "target_ari_accepted": (
                    None
                    if len(accepted_rows) < 2
                    else float(adjusted_rand_score(accepted_truth, accepted_clusters))
                ),
            }
        )
    return rows


def _evaluate_one(
    job: SimulationJobSpec,
    report: SourceAuditReport,
    assignments: TargetAssignmentSet,
    selection,
    prelabel_marker_sha256: str,
) -> dict[str, Any]:
    # This is the first point at which the truth object is accessed.
    generated = generate_simulation(job.simulation)
    if assignments.target_fingerprint != generated.target.fingerprint():
        raise ValueError("frozen assignments do not match regenerated target")
    truth_map = generated.truth.target_labels.as_mapping()
    methods = _method_metrics(report, assignments, truth_map)
    oracle = sorted(methods, key=lambda item: (-item["target_ari_forced"], item["method_id"]))[0]
    selected = (
        None
        if selection.selected_method is None
        else next(item for item in methods if item["method_id"] == selection.selected_method)
    )
    selected_ari = 0.0 if selected is None else float(selected["target_ari_forced"])
    family_q: dict[str, float | None] = {}
    family_target: dict[str, float | None] = {}
    for family in ("VALUE", "RELATIONAL", "HYBRID"):
        available = [item for item in methods if item["family"] == family]
        family_q[family] = (
            None if not available else max(float(item["source_q"]) for item in available)
        )
        family_target[family] = (
            None
            if not available
            else max(float(item["target_ari_forced"]) for item in available)
        )
    return {
        "schema": "PrimarySimulationMetrics/v1",
        "evaluation_only": True,
        "prelabel_complete_sha256": prelabel_marker_sha256,
        "target_assignments_sha256": assignments.sha256(),
        "source_group_id": source_group_id(job),
        "job_id": job.job_id,
        "regime": job.simulation.regime,
        "signal": job.simulation.signal,
        "shift": job.simulation.shift,
        "replicate": job.simulation.replicate,
        "expected_decision": generated.truth.expected_decision,
        "selected_decision": selection.decision,
        "selected_method": selection.selected_method,
        "decision_correct": selection.decision == generated.truth.expected_decision,
        "selected_target_ari_forced": selected_ari,
        "selected_target_nmi_forced": (
            None if selected is None else selected["target_nmi_forced"]
        ),
        "selected_assignment_coverage": 0.0 if selected is None else selected["assignment_coverage"],
        "oracle_method": oracle["method_id"],
        "oracle_family": oracle["family"],
        "oracle_target_ari_forced": oracle["target_ari_forced"],
        "target_ari_regret": max(0.0, oracle["target_ari_forced"] - selected_ari),
        "source_family_q": family_q,
        "target_family_ari": family_target,
        "methods": methods,
        "gate_b_assignment_policy": "forced_all_samples",
    }


def _collect_gate_b(metrics: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    signal = [item for item in metrics if item["regime"] != "NULL"]
    null = [item for item in metrics if item["regime"] == "NULL"]
    pure = [item for item in signal if item["regime"] in {"VALUE", "RELATIONAL"}]
    exact = float(np.mean([bool(item["decision_correct"]) for item in signal]))
    regret = float(np.median([float(item["target_ari_regret"]) for item in signal]))
    null_false = float(
        np.mean([item["selected_decision"] != "NO_STABLE_STRUCTURE" for item in null])
    )
    hybrid_pure = float(
        np.mean([item["selected_decision"] == "HYBRID" for item in pure])
    )
    q_differences: list[float] = []
    performance_differences: list[float] = []
    pairs = (("VALUE", "RELATIONAL"), ("HYBRID", "VALUE"), ("HYBRID", "RELATIONAL"))
    for item in signal:
        for left, right in pairs:
            if (
                item["source_family_q"][left] is None
                or item["source_family_q"][right] is None
                or item["target_family_ari"][left] is None
                or item["target_family_ari"][right] is None
            ):
                continue
            q_differences.append(
                float(item["source_family_q"][left] - item["source_family_q"][right])
            )
            performance_differences.append(
                float(item["target_family_ari"][left] - item["target_family_ari"][right])
            )
    statistic = float(spearmanr(q_differences, performance_differences).statistic)
    correlation = statistic if np.isfinite(statistic) else 0.0
    checks = {
        "all_630_pairs_complete": len(metrics) == 630,
        "exact_family_identification_at_least_0_70": exact >= 0.70,
        "median_target_ari_regret_at_most_0_05": regret <= 0.05,
        "null_false_structure_rate_at_most_0_10": null_false <= 0.10,
        "hybrid_selection_on_pure_at_most_0_20": hybrid_pure <= 0.20,
        "source_audit_target_performance_spearman_at_least_0_40": correlation >= 0.40,
    }
    by_cell: dict[str, Any] = {}
    for regime in ("VALUE", "RELATIONAL", "HYBRID", "NULL"):
        signals = ("moderate", "strong") if regime != "NULL" else ("none",)
        for signal_level in signals:
            for shift in ("none", "moderate", "strong"):
                cell = [
                    item
                    for item in metrics
                    if item["regime"] == regime
                    and item["signal"] == signal_level
                    and item["shift"] == shift
                ]
                key = f"{regime}/{signal_level}/{shift}"
                by_cell[key] = {
                    "n": len(cell),
                    "decision_accuracy": float(
                        np.mean([bool(item["decision_correct"]) for item in cell])
                    ),
                    "median_target_ari_regret": float(
                        np.median([float(item["target_ari_regret"]) for item in cell])
                    ),
                    "decision_counts": dict(
                        sorted(Counter(item["selected_decision"] for item in cell).items())
                    ),
                }
    return {
        "schema": "GateBSummary/v1",
        "job_count": len(metrics),
        "signal_job_count": len(signal),
        "null_job_count": len(null),
        "exact_family_identification_rate": exact,
        "median_target_ari_regret": regret,
        "null_false_structure_rate": null_false,
        "hybrid_selection_on_pure_rate": hybrid_pure,
        "source_audit_target_performance_spearman": correlation,
        "spearman_definition": "three signed family-pair contrasts per signal pair; family maxima",
        "assignment_policy": "forced_all_samples; rejection coverage reported separately",
        "gate_checks": checks,
        "gate_b_go": all(checks.values()),
        "by_cell": by_cell,
    }


def run_evaluation_phase(
    config: Mapping[str, Any], *, output_root: str | Path
) -> dict[str, Any]:
    """Unblind synthetic truth only after all 630 prelabel jobs validate."""

    output_root = Path(output_root).resolve()
    jobs = make_primary_grid(config)
    marker_sha = _require_complete_prelabel(config, output_root, jobs)
    reports: dict[str, SourceAuditReport] = {}
    for job in jobs:
        group_id = source_group_id(job)
        if group_id not in reports:
            reports[group_id] = SourceAuditReport.load(
                output_root / "prelabel" / "sources" / group_id / "audit.json"
            )
    null_group_ids = sorted(
        {source_group_id(job) for job in jobs if job.simulation.regime == "NULL"}
    )
    null_reports = [reports[group_id] for group_id in null_group_ids]
    selector = config["selector"]
    calibration = calibrate_null(
        null_reports,
        quantile=float(selector["null_quantile"]),
        minimum_hybrid_gain=float(selector["minimum_hybrid_gain"]),
    )
    calibration.save(output_root / "null_calibration.json")
    null_loo = {
        group_id: calibrate_null(
            [report for other, report in zip(null_group_ids, null_reports, strict=True) if other != group_id],
            quantile=float(selector["null_quantile"]),
            minimum_hybrid_gain=float(selector["minimum_hybrid_gain"]),
        )
        for group_id in null_group_ids
    }
    metrics: list[dict[str, Any]] = []
    evaluation_root = output_root / "evaluation" / "jobs"
    for index, job in enumerate(jobs, start=1):
        group_id = source_group_id(job)
        report = reports[group_id]
        job_calibration = null_loo[group_id] if job.simulation.regime == "NULL" else calibration
        selection = select_representation(
            [report],
            job_calibration,
            equivalence_margin=float(selector["equivalence_margin"]),
            minimum_decision_frequency=float(selector["minimum_decision_frequency"]),
        )
        assignments = TargetAssignmentSet.load(
            output_root / "prelabel" / "jobs" / job.job_id / "target_assignments.json"
        )
        item = _evaluate_one(job, report, assignments, selection, marker_sha)
        metrics.append(item)
        _atomic_publish_directory(
            evaluation_root / job.job_id,
            identifier=job.job_id,
            marker_name="EVALUATED",
            marker_schema="CompletedEvaluationJob/v1",
            files={
                "metrics.json": item,
                "selection.json": selection.to_json_bytes(),
            },
        )
        if index % 30 == 0:
            print(f"EVALUATE {index:03d}/630", flush=True)
    summary = _collect_gate_b(metrics)
    atomic_write_canonical_json(output_root / "gate_b_summary.json", summary)
    return summary


def run_full_grid(
    config: Mapping[str, Any],
    *,
    output_root: str | Path,
    max_workers: int,
) -> dict[str, Any]:
    run_prelabel_phase(config, output_root=output_root, max_workers=max_workers)
    return run_evaluation_phase(config, output_root=output_root)
