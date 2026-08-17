"""PILOT-019 integrity validation and collection across all experiment levels."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from rep_audit.audit.config import stable_seed
from rep_audit.audit.report import SourceAuditReport
from rep_audit.experiments.full_runner import (
    _collect_gate_b,
    _require_complete_prelabel,
    _validate_hashed_directory,
    _validate_source,
    source_group_id,
)
from rep_audit.experiments.grid import make_primary_grid
from rep_audit.experiments.real_lung import (
    DIRECTIONS,
    _audit_config,
    _direction_id,
    _validate_null_report,
    _validate_real_prelabel,
)
from rep_audit.experiments.real_within import (
    _collect_within,
    _dataset_specs,
    _require_complete_within_prelabel,
    scientific_tree_sha256,
)
from rep_audit.io.canonical_json import canonical_json_bytes, sha256_bytes


EXPECTED_PROTOCOL_SHA256 = (
    "5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704"
)
EXPECTED_REFERENCES = {
    "feasibility": "dc97680a1e944e74924b5e7b151e0c27d5655f22",
    "air": "2dee739f6ee5e001ef1be76df2eb753ca389adb3",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _tree_sha256(root: Path, relative_paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(relative_paths, key=lambda item: item.as_posix()):
        payload = (root / relative).read_bytes()
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def gate_c_checks(evaluations: Mapping[str, Mapping[str, Any]]) -> dict[str, bool]:
    regrets = sorted(float(item["target_ari_regret"]) for item in evaluations.values())
    return {
        "one_direction_regret_at_most_0_05_and_reverse_at_most_0_10": (
            regrets[0] <= 0.05 and regrets[1] <= 0.10
        ),
        "both_decisions_frozen_before_label_evaluation": all(
            bool(item["labels_unblinded_after_prelabel_validation"])
            for item in evaluations.values()
        ),
        "both_target_assignment_coverages_at_least_0_80": all(
            float(item["selected_assignment_coverage"]) >= 0.80
            for item in evaluations.values()
        ),
        "every_assigned_target_cluster_at_least_0_10": all(
            float(item["selected_min_assigned_cluster_fraction_of_target"]) >= 0.10
            for item in evaluations.values()
        ),
    }


def _validate_reference(root: Path, expected_commit: str) -> dict[str, Any]:
    revision = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    tracked_status = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "status",
            "--porcelain",
            "--untracked-files=no",
        ],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    untracked = tuple(
        line
        for line in subprocess.run(
            ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.splitlines()
        if line
    )
    if revision != expected_commit or tracked_status:
        raise ValueError(f"reference repository integrity failure: {root}")
    return {
        "root": str(root),
        "commit": revision,
        "tracked_worktree_clean": True,
        "untracked_files_excluded_from_adapters": untracked,
    }


def _validate_gate_b(
    config: Mapping[str, Any], output_root: Path
) -> dict[str, Any]:
    jobs = make_primary_grid(config)
    prelabel_marker_sha = _require_complete_prelabel(config, output_root, jobs)
    groups = {source_group_id(job) for job in jobs}
    for group_id in groups:
        _validate_source(output_root / "prelabel" / "sources" / group_id, group_id)
    metrics = []
    evaluation_paths: list[Path] = [Path("null_calibration.json")]
    scientific_prelabel_paths: list[Path] = [Path("PRELABEL_COMPLETE.json")]
    for group_id in groups:
        scientific_prelabel_paths.extend(
            (
                Path("prelabel/sources") / group_id / "audit.json",
                Path("prelabel/sources") / group_id / "source.json",
            )
        )
    for job in jobs:
        prelabel = Path("prelabel/jobs") / job.job_id
        scientific_prelabel_paths.extend(
            prelabel / name
            for name in (
                "config.json",
                "frozen_transfer.json",
                "target_assignments.json",
            )
        )
        evaluation = output_root / "evaluation" / "jobs" / job.job_id
        _validate_hashed_directory(
            evaluation,
            marker_name="EVALUATED",
            marker_schema="CompletedEvaluationJob/v1",
            expected_id=job.job_id,
            hashed_files=("metrics.json", "selection.json"),
        )
        item = _read_json(evaluation / "metrics.json")
        if item.get("job_id") != job.job_id or item.get("evaluation_only") is not True:
            raise ValueError(f"invalid Gate B evaluation job: {job.job_id}")
        metrics.append(item)
        evaluation_paths.extend(
            Path("evaluation/jobs") / job.job_id / name
            for name in ("metrics.json", "selection.json", "EVALUATED")
        )
    summary = _read_json(output_root / "gate_b_summary.json")
    recomputed = _collect_gate_b(metrics)
    if canonical_json_bytes(summary) != canonical_json_bytes(recomputed):
        raise ValueError("stored Gate B summary does not match its 630 job metrics")
    evaluation_paths.append(Path("gate_b_summary.json"))
    return {
        "validated": True,
        "go": bool(summary["gate_b_go"]),
        "job_count": len(jobs),
        "source_group_count": len(groups),
        "prelabel_complete_sha256": prelabel_marker_sha,
        "summary_sha256": sha256_bytes((output_root / "gate_b_summary.json").read_bytes()),
        "prelabel_scientific_tree_sha256": _tree_sha256(
            output_root, scientific_prelabel_paths
        ),
        "evaluation_tree_sha256": _tree_sha256(output_root, evaluation_paths),
        "metrics": {
            "exact_family_identification_rate": summary[
                "exact_family_identification_rate"
            ],
            "median_target_ari_regret": summary["median_target_ari_regret"],
            "null_false_structure_rate": summary["null_false_structure_rate"],
            "hybrid_selection_on_pure_rate": summary[
                "hybrid_selection_on_pure_rate"
            ],
            "source_audit_target_performance_spearman": summary[
                "source_audit_target_performance_spearman"
            ],
        },
    }


def _validate_real_calibration(
    config: Mapping[str, Any], output_root: Path, sample_sizes: Sequence[int]
) -> int:
    replicates = int(config["null_calibration"]["replicates"])
    count = 0
    for n_samples in sample_sizes:
        for replicate in range(replicates):
            simulation_seed = stable_seed(
                int(config["base_seed"]),
                "real_null_calibration",
                n_samples,
                replicate,
            )
            report = SourceAuditReport.load(
                output_root
                / "calibration"
                / f"n{n_samples}_k2"
                / "reports"
                / f"null_{replicate:03d}.json"
            )
            _validate_null_report(
                report,
                n_samples=n_samples,
                expected_config=_audit_config(
                    config, seed=stable_seed(simulation_seed, "audit")
                ),
            )
            count += 1
    return count


def _validate_gate_c(
    config: Mapping[str, Any], output_root: Path
) -> dict[str, Any]:
    completion = _read_json(output_root / "REAL_PRELABEL_COMPLETE.json")
    if completion.get("schema") != "RealLungPrelabelSummary/v1" or completion.get(
        "labels_loaded"
    ) is not False:
        raise ValueError("invalid real-transfer global prelabel marker")
    marker_hashes = {}
    evaluations = {}
    for source_id, target_id in DIRECTIONS:
        direction_id = _direction_id(source_id, target_id)
        prelabel = output_root / "transfers" / direction_id / "prelabel"
        marker_hashes[direction_id] = _validate_real_prelabel(prelabel, direction_id)
        evaluation = _read_json(
            output_root / "transfers" / direction_id / "evaluation.json"
        )
        if (
            evaluation.get("evaluation_only") is not True
            or evaluation.get("prelabel_marker_sha256") != marker_hashes[direction_id]
        ):
            raise ValueError(f"invalid Gate C evaluation: {direction_id}")
        evaluations[direction_id] = evaluation
    summary = _read_json(output_root / "gate_c_summary.json")
    checks = gate_c_checks(evaluations)
    if (
        summary.get("directions") != evaluations
        or summary.get("gate_checks") != checks
        or summary.get("gate_c_go") is not all(checks.values())
    ):
        raise ValueError("stored Gate C summary is inconsistent")
    if summary["gate_c_go"] is not False:
        raise ValueError("closeout expects the frozen formal Gate C STOP")
    calibration_count = _validate_real_calibration(config, output_root, (107, 120))
    paths = sorted(path.relative_to(output_root) for path in output_root.rglob("*") if path.is_file())
    regrets = {
        key: float(value["target_ari_regret"]) for key, value in evaluations.items()
    }
    return {
        "validated": True,
        "go": False,
        "formal_decision": "STOP",
        "summary_sha256": sha256_bytes((output_root / "gate_c_summary.json").read_bytes()),
        "tree_sha256": _tree_sha256(output_root, paths),
        "null_report_count": calibration_count,
        "prelabel_marker_sha256": marker_hashes,
        "regret_by_direction": regrets,
        "failed_checks": tuple(key for key, passed in checks.items() if not passed),
    }


def _validate_within(
    config: Mapping[str, Any], output_root: Path
) -> dict[str, Any]:
    specs = _dataset_specs(config)
    ids = tuple(str(item["dataset_id"]) for item in specs)
    marker_hashes = _require_complete_within_prelabel(output_root, ids)
    evaluations = []
    sample_sizes = set()
    for dataset_id in ids:
        manifest = _read_json(
            output_root / "datasets" / dataset_id / "prelabel" / "manifest.json"
        )
        sample_sizes.add(int(manifest["n_samples"]))
        evaluation = output_root / "datasets" / dataset_id / "evaluation"
        _validate_hashed_directory(
            evaluation,
            marker_name="EVALUATED",
            marker_schema="CompletedWithinDatasetEvaluation/v1",
            expected_id=dataset_id,
            hashed_files=("metrics.json",),
        )
        metrics = _read_json(evaluation / "metrics.json")
        if (
            metrics.get("evaluation_only") is not True
            or metrics.get("labels_unblinded_after_all_prelabel_validation") is not True
            or metrics.get("prelabel_marker_sha256") != marker_hashes[dataset_id]
        ):
            raise ValueError(f"invalid within-dataset evaluation: {dataset_id}")
        evaluations.append(metrics)
    stored = _read_json(output_root / "within_summary.json")
    recomputed = _collect_within(evaluations)
    if canonical_json_bytes(stored) != canonical_json_bytes(recomputed):
        raise ValueError("stored within-dataset summary is inconsistent")
    calibration_count = _validate_real_calibration(
        config, output_root, tuple(sorted(sample_sizes))
    )
    return {
        "validated": True,
        "descriptive_not_a_gate": True,
        "dataset_count": len(evaluations),
        "null_report_count": calibration_count,
        "prelabel_marker_sha256": marker_hashes,
        "summary_sha256": sha256_bytes((output_root / "within_summary.json").read_bytes()),
        "tree_sha256": scientific_tree_sha256(output_root),
        "decision_counts": stored["decision_counts"],
        "median_selected_ari": stored["median_selected_ari"],
        "median_ari_regret": stored["median_ari_regret"],
        "selected_within_0_05_of_oracle_rate": stored[
            "selected_within_0_05_of_oracle_rate"
        ],
    }


def validate_closeout(
    *,
    repository_root: str | Path,
    dataset_config: Mapping[str, Any],
    full_config: Mapping[str, Any],
    real_config: Mapping[str, Any],
    within_config: Mapping[str, Any],
    full_output: str | Path,
    real_output: str | Path,
    within_output: str | Path,
) -> dict[str, Any]:
    repository_root = Path(repository_root).resolve()
    protocol = repository_root / "docs" / "SONATA_BIS_PILOT_PROTOCOL_v1.md"
    protocol_sha = sha256_bytes(protocol.read_bytes())
    if protocol_sha != EXPECTED_PROTOCOL_SHA256:
        raise ValueError("frozen protocol checksum mismatch")
    roots = dataset_config["reference_roots"]
    references = {
        name: _validate_reference(Path(roots[name]).resolve(), revision)
        for name, revision in EXPECTED_REFERENCES.items()
    }
    gate_b = _validate_gate_b(full_config, Path(full_output).resolve())
    if gate_b["go"] is not True:
        raise ValueError("PILOT-019 expected the frozen Gate B GO")
    gate_c = _validate_gate_c(real_config, Path(real_output).resolve())
    within = _validate_within(within_config, Path(within_output).resolve())
    commit = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    return {
        "schema": "Pilot019Validation/v1",
        "all_integrity_checks_passed": True,
        "protocol_sha256": protocol_sha,
        "validated_repository_commit": commit,
        "references": references,
        "gate_b": gate_b,
        "real_within": within,
        "gate_c": gate_c,
        "scope_decision": {
            "PILOT-016": "NOT_RUN_BLOCKED_BY_GATE_C_STOP",
            "PILOT-017": "NOT_RUN_BLOCKED_BY_GATE_C_STOP",
            "PILOT-018": "NOT_RUN_BLOCKED_BY_GATE_C_STOP",
            "PILOT-019": "VALIDATED",
            "PILOT-020": "PENDING_REPORT_GENERATION",
            "retrospective_gate_c_rescue": False,
        },
    }
