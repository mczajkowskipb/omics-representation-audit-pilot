"""Leakage-safe bidirectional GSE10072/GSE19804 transfer and Gate C."""

from __future__ import annotations

import json
import os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from threadpoolctl import threadpool_limits

from rep_audit.audit.config import AuditConfig, stable_seed
from rep_audit.audit.diagnostics import fit_source_audit, run_source_audit
from rep_audit.audit.report import SourceAuditReport
from rep_audit.audit.selector import (
    NullCalibrationArtifact,
    RepresentationSelection,
    calibrate_null,
    select_representation,
)
from rep_audit.data.adapters.air import AIRRepositoryAdapter
from rep_audit.experiments.full_runner import (
    _atomic_publish_directory,
    _validate_hashed_directory,
)
from rep_audit.io.canonical_json import (
    atomic_write_canonical_json,
    canonical_json_bytes,
    sha256_bytes,
)
from rep_audit.simulation.generators import SimulationSpec, generate_simulation
from rep_audit.transfer.artifact import freeze_transfer_set
from rep_audit.transfer.assign import TargetAssignmentSet, assign_target


DIRECTIONS = (
    ("GSE10072", "GSE19804"),
    ("GSE19804", "GSE10072"),
)
REAL_PRELABEL_FILES = (
    "manifest.json",
    "common_feature_ids.json",
    "null_calibration.json",
    "source_audit.json",
    "selection.json",
    "frozen_transfer.json",
    "target_assignments.json",
)


def _audit_config(config: Mapping[str, Any], *, seed: int) -> AuditConfig:
    audit = config["audit"]
    return AuditConfig(
        k=int(audit["k"]),
        feature_budget=int(audit["feature_budget"]),
        relation_budget=int(audit["relation_budget"]),
        resamples=int(audit["resamples"]),
        seed=int(seed),
        margin=float(audit["margin"]),
        alphas=tuple(float(item) for item in audit["alphas"]),
        perturbation_level=str(audit["perturbation_level"]),
        min_cluster_fraction=float(audit["min_cluster_fraction"]),
        relation_coverage_threshold=float(audit["relation_coverage_threshold"]),
        relation_entropy_threshold=float(audit["relation_entropy_threshold"]),
        relation_stability_threshold=float(audit["relation_stability_threshold"]),
        relation_screen_perturbations=int(audit["relation_screen_perturbations"]),
        protocol_version=str(config["protocol_version"]),
    )


def _null_report_worker(
    n_samples: int,
    replicate: int,
    config: Mapping[str, Any],
    output_path_text: str,
) -> str:
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    output_path = Path(output_path_text)
    if output_path.is_file():
        return str(output_path)
    calibration = config["null_calibration"]
    simulation_seed = stable_seed(
        int(config["base_seed"]), "real_null_calibration", n_samples, replicate
    )
    specification = SimulationSpec(
        regime="NULL",
        signal="none",
        shift="none",
        replicate=replicate,
        seed=simulation_seed,
        n_source=n_samples,
        n_target=n_samples,
        p=int(calibration["p"]),
        k=int(config["audit"]["k"]),
        informative_features=int(calibration["informative_features"]),
        protocol_version=str(config["protocol_version"]),
    )
    with threadpool_limits(limits=1):
        generated = generate_simulation(specification)
        report = run_source_audit(
            generated.source,
            _audit_config(config, seed=stable_seed(simulation_seed, "audit")),
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.save(output_path)
    return str(output_path)


def _ensure_calibrations(
    config: Mapping[str, Any],
    output_root: Path,
    sample_sizes: tuple[int, ...],
    *,
    max_workers: int,
) -> dict[int, NullCalibrationArtifact]:
    replicates = int(config["null_calibration"]["replicates"])
    tasks = [
        (
            n_samples,
            replicate,
            output_root
            / "calibration"
            / f"n{n_samples}_k{int(config['audit']['k'])}"
            / "reports"
            / f"null_{replicate:03d}.json",
        )
        for n_samples in sample_sizes
        for replicate in range(replicates)
    ]
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _null_report_worker, n_samples, replicate, dict(config), str(path)
            ): (n_samples, replicate)
            for n_samples, replicate, path in tasks
        }
        for index, future in enumerate(as_completed(futures), start=1):
            future.result()
            if index % 10 == 0:
                print(f"REAL NULL {index:02d}/{len(tasks)}", flush=True)
    artifacts: dict[int, NullCalibrationArtifact] = {}
    for n_samples in sample_sizes:
        directory = output_root / "calibration" / f"n{n_samples}_k{int(config['audit']['k'])}"
        reports = [
            SourceAuditReport.load(directory / "reports" / f"null_{replicate:03d}.json")
            for replicate in range(replicates)
        ]
        artifact = calibrate_null(
            reports,
            quantile=float(config["null_calibration"]["quantile"]),
            minimum_hybrid_gain=float(
                config["null_calibration"]["minimum_hybrid_gain"]
            ),
        )
        artifact.save(directory / "null_calibration.json")
        atomic_write_canonical_json(
            directory / "DONE",
            {
                "schema": "RealNullCalibrationComplete/v1",
                "n_samples": n_samples,
                "k": int(config["audit"]["k"]),
                "replicates": replicates,
                "artifact_sha256": artifact.sha256(),
            },
        )
        artifacts[n_samples] = artifact
    return artifacts


def _direction_id(source_id: str, target_id: str) -> str:
    return f"{source_id}_to_{target_id}"


def _validate_real_prelabel(path: Path, direction_id: str) -> str:
    _validate_hashed_directory(
        path,
        marker_name="PRELABEL_DONE",
        marker_schema="CompletedRealTransferPrelabel/v1",
        expected_id=direction_id,
        hashed_files=REAL_PRELABEL_FILES,
    )
    marker = path / "PRELABEL_DONE"
    return sha256_bytes(marker.read_bytes())


def run_real_prelabel(
    config: Mapping[str, Any],
    *,
    dataset_config: Mapping[str, Any],
    gate_b_summary_path: str | Path,
    output_root: str | Path,
    max_workers: int,
) -> dict[str, Any]:
    """Freeze both directions without importing or reading an evaluation label."""

    gate_path = Path(gate_b_summary_path)
    gate_b = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate_b.get("schema") != "GateBSummary/v1" or gate_b.get("gate_b_go") is not True:
        raise ValueError("real transfer is blocked until Gate B is GO")
    roots = dataset_config["reference_roots"]
    manifests = dataset_config["manifests"]
    adapter = AIRRepositoryAdapter(roots["air"], manifests["air"])
    bundles = {dataset_id: adapter.load(dataset_id) for dataset_id in ("GSE10072", "GSE19804")}
    common = tuple(sorted(set(bundles["GSE10072"].feature_ids) & set(bundles["GSE19804"].feature_ids)))
    if len(common) != 22277:
        raise ValueError(f"protocol expects exactly 22277 common probes, found {len(common)}")
    output_root = Path(output_root).resolve()
    calibrations = _ensure_calibrations(
        config,
        output_root,
        tuple(sorted({bundle.shape[0] for bundle in bundles.values()})),
        max_workers=max_workers,
    )
    summaries: dict[str, Any] = {}
    for source_id, target_id in DIRECTIONS:
        direction_id = _direction_id(source_id, target_id)
        destination = output_root / "transfers" / direction_id / "prelabel"
        try:
            marker_sha = _validate_real_prelabel(destination, direction_id)
            selection = RepresentationSelection.load(destination / "selection.json")
            assignments = TargetAssignmentSet.load(destination / "target_assignments.json")
            summaries[direction_id] = {
                "status": "complete",
                "prelabel_marker_sha256": marker_sha,
                "decision": selection.decision,
                "selected_method": selection.selected_method,
                "selected_coverage": (
                    0.0
                    if selection.selected_method is None
                    else assignments.method_by_id(selection.selected_method).coverage
                ),
            }
            continue
        except (FileNotFoundError, ValueError):
            pass
        source = bundles[source_id]
        target = bundles[target_id]
        audit_config = _audit_config(
            config,
            seed=stable_seed(int(config["base_seed"]), "real_source_audit", direction_id),
        )
        with threadpool_limits(limits=1):
            fitted = fit_source_audit(
                source, audit_config, allowed_feature_ids=common
            )
            calibration = calibrations[source.shape[0]]
            selection = select_representation(
                [fitted.report],
                calibration,
                equivalence_margin=float(config["selector"]["equivalence_margin"]),
                minimum_decision_frequency=float(
                    config["selector"]["minimum_decision_frequency"]
                ),
            )
            frozen = freeze_transfer_set(
                source,
                target.feature_ids,
                target.dataset_id,
                fitted,
                minimum_feature_coverage=float(
                    config["transfer"]["minimum_feature_coverage"]
                ),
                minimum_relation_coverage=float(
                    config["transfer"]["minimum_relation_coverage"]
                ),
            )
            assignments = assign_target(target, frozen)
        status = _atomic_publish_directory(
            destination,
            identifier=direction_id,
            marker_name="PRELABEL_DONE",
            marker_schema="CompletedRealTransferPrelabel/v1",
            files={
                "manifest.json": {
                    "schema": "RealTransferManifest/v1",
                    "labels_loaded": False,
                    "direction_id": direction_id,
                    "source_dataset_id": source_id,
                    "target_dataset_id": target_id,
                    "source_x_sha256": source.metadata["x_sha256"],
                    "target_x_sha256": target.metadata["x_sha256"],
                    "reference_commit": source.metadata["reference_commit"],
                    "gate_b_summary_sha256": sha256_bytes(gate_path.read_bytes()),
                    "k": 2,
                    "k_basis": "predeclared_binary_benchmark_task",
                    "common_feature_count": len(common),
                    "target_labels_read": False,
                },
                "common_feature_ids.json": {
                    "schema": "CommonFeatureUniverse/v1",
                    "source_dataset_id": source_id,
                    "target_dataset_id": target_id,
                    "feature_ids": common,
                },
                "null_calibration.json": calibration.to_json_bytes(),
                "source_audit.json": fitted.report.to_json_bytes(),
                "selection.json": selection.to_json_bytes(),
                "frozen_transfer.json": frozen.to_json_bytes(),
                "target_assignments.json": assignments.to_json_bytes(),
            },
        )
        marker_sha = _validate_real_prelabel(destination, direction_id)
        summaries[direction_id] = {
            "status": "complete",
            "prelabel_marker_sha256": marker_sha,
            "decision": selection.decision,
            "selected_method": selection.selected_method,
            "selected_coverage": (
                0.0
                if selection.selected_method is None
                else assignments.method_by_id(selection.selected_method).coverage
            ),
            "source_audit_sha256": fitted.report.sha256(),
            "target_assignments_sha256": assignments.sha256(),
        }
        print(f"REAL PRELABEL {direction_id} {selection.decision}", flush=True)
    result = {
        "schema": "RealLungPrelabelSummary/v1",
        "labels_loaded": False,
        "gate_b_go_required": True,
        "common_feature_count": len(common),
        "directions": summaries,
    }
    atomic_write_canonical_json(output_root / "REAL_PRELABEL_COMPLETE.json", result)
    return result


def _evaluate_direction(
    direction_id: str,
    source_id: str,
    target_id: str,
    path: Path,
    labels,
    marker_sha: str,
) -> dict[str, Any]:
    selection = RepresentationSelection.load(path / "selection.json")
    assignments = TargetAssignmentSet.load(path / "target_assignments.json")
    truth_map = labels.as_mapping()
    methods: list[dict[str, Any]] = []
    for candidate in assignments.methods:
        truth = [truth_map[row.sample_id] for row in candidate.rows]
        forced = [row.forced_cluster for row in candidate.rows]
        accepted = [row for row in candidate.rows if row.accepted_cluster is not None]
        methods.append(
            {
                "method_id": candidate.method_id,
                "target_ari_forced": float(adjusted_rand_score(truth, forced)),
                "target_nmi_forced": float(normalized_mutual_info_score(truth, forced)),
                "assignment_coverage": candidate.coverage,
                "target_ari_accepted": (
                    None
                    if len(accepted) < 2
                    else float(
                        adjusted_rand_score(
                            [truth_map[row.sample_id] for row in accepted],
                            [int(row.accepted_cluster) for row in accepted],
                        )
                    )
                ),
            }
        )
    oracle = sorted(methods, key=lambda item: (-item["target_ari_forced"], item["method_id"]))[0]
    selected = (
        None
        if selection.selected_method is None
        else next(item for item in methods if item["method_id"] == selection.selected_method)
    )
    selected_assignments = (
        None
        if selection.selected_method is None
        else assignments.method_by_id(selection.selected_method)
    )
    n_target = len(labels.sample_ids)
    if selected_assignments is None:
        min_cluster_fraction = 0.0
    else:
        counts = Counter(
            row.accepted_cluster
            for row in selected_assignments.rows
            if row.accepted_cluster is not None
        )
        min_cluster_fraction = min(
            counts.get(cluster, 0) / n_target for cluster in range(2)
        )
    selected_ari = 0.0 if selected is None else float(selected["target_ari_forced"])
    return {
        "schema": "RealTransferEvaluation/v1",
        "evaluation_only": True,
        "direction_id": direction_id,
        "source_dataset_id": source_id,
        "target_dataset_id": target_id,
        "prelabel_marker_sha256": marker_sha,
        "labels_unblinded_after_prelabel_validation": True,
        "selected_decision": selection.decision,
        "selected_method": selection.selected_method,
        "selected_target_ari_forced": selected_ari,
        "selected_target_nmi_forced": None if selected is None else selected["target_nmi_forced"],
        "selected_assignment_coverage": 0.0 if selected is None else selected["assignment_coverage"],
        "selected_min_assigned_cluster_fraction_of_target": min_cluster_fraction,
        "oracle_method": oracle["method_id"],
        "oracle_target_ari_forced": oracle["target_ari_forced"],
        "target_ari_regret": max(0.0, float(oracle["target_ari_forced"]) - selected_ari),
        "methods": methods,
        "gate_c_assignment_policy": "forced_all_samples_for_ari; accepted_for_coverage",
    }


def run_real_evaluation(
    *,
    dataset_config: Mapping[str, Any],
    output_root: str | Path,
) -> dict[str, Any]:
    """Validate both freezes, then and only then load the real target labels."""

    output_root = Path(output_root).resolve()
    completion = json.loads(
        (output_root / "REAL_PRELABEL_COMPLETE.json").read_text(encoding="utf-8")
    )
    if completion.get("schema") != "RealLungPrelabelSummary/v1" or completion.get(
        "labels_loaded"
    ) is not False:
        raise ValueError("real evaluation refused: prelabel phase is incomplete")
    validated: dict[str, tuple[Path, str]] = {}
    for source_id, target_id in DIRECTIONS:
        direction_id = _direction_id(source_id, target_id)
        path = output_root / "transfers" / direction_id / "prelabel"
        validated[direction_id] = (path, _validate_real_prelabel(path, direction_id))

    # Evaluation namespace is imported above, but no label file is opened until
    # both immutable direction markers have passed validation.
    roots = dataset_config["reference_roots"]
    from rep_audit.evaluation.repository_labels import RepositoryLabelLoader

    loader = RepositoryLabelLoader(
        dataset_config["manifests"]["evaluation_labels"],
        {"air": roots["air"], "feasibility": roots["feasibility"]},
    )
    evaluations: dict[str, Any] = {}
    for source_id, target_id in DIRECTIONS:
        direction_id = _direction_id(source_id, target_id)
        path, marker_sha = validated[direction_id]
        assignments = TargetAssignmentSet.load(path / "target_assignments.json")
        sample_ids = tuple(
            row.sample_id for row in assignments.methods[0].rows
        )
        labels = loader.load(target_id, expected_sample_ids=sample_ids)
        result = _evaluate_direction(
            direction_id, source_id, target_id, path, labels, marker_sha
        )
        atomic_write_canonical_json(
            output_root / "transfers" / direction_id / "evaluation.json", result
        )
        evaluations[direction_id] = result

    regrets = sorted(float(item["target_ari_regret"]) for item in evaluations.values())
    checks = {
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
    summary = {
        "schema": "GateCSummary/v1",
        "directions": evaluations,
        "gate_checks": checks,
        "gate_c_go": all(checks.values()),
    }
    atomic_write_canonical_json(output_root / "gate_c_summary.json", summary)
    return summary
