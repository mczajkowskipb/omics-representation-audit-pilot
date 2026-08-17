"""Leakage-safe within-dataset audits for the eleven protocol datasets."""

from __future__ import annotations

import gc
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from threadpoolctl import threadpool_limits

from rep_audit.audit.config import stable_seed
from rep_audit.audit.diagnostics import fit_source_audit
from rep_audit.audit.report import SourceAuditReport
from rep_audit.audit.selector import RepresentationSelection, select_representation
from rep_audit.data.adapters.air import AIRRepositoryAdapter
from rep_audit.data.adapters.feasibility import FeasibilityRepositoryAdapter
from rep_audit.experiments.full_runner import (
    _atomic_publish_directory,
    _validate_hashed_directory,
)
from rep_audit.experiments.real_lung import _audit_config, _ensure_calibrations
from rep_audit.io.canonical_json import (
    atomic_write_canonical_json,
    canonical_json_bytes,
    sha256_bytes,
)


PROTOCOL_DATASETS = (
    "golub",
    "colon",
    "DLBCL",
    "GDS2771",
    "GSE10072",
    "GSE17920",
    "GSE19804",
    "GSE25837",
    "GSE27272",
    "GSE3365",
    "GSE6613",
)
WITHIN_PRELABEL_FILES = (
    "manifest.json",
    "null_calibration.json",
    "source_audit.json",
    "selection.json",
    "source_assignments.json",
)


def _dataset_specs(config: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    specs = tuple(dict(item) for item in config["datasets"])
    ids = tuple(str(item["dataset_id"]) for item in specs)
    if len(ids) != len(set(ids)) or set(ids) != set(PROTOCOL_DATASETS):
        raise ValueError("within-dataset config must contain exactly the 11 protocol datasets")
    if any(int(item["k"]) != 2 for item in specs) or int(config["audit"]["k"]) != 2:
        raise ValueError("the frozen within-dataset benchmark control is K=2")
    if any(item["repository"] not in {"feasibility", "air"} for item in specs):
        raise ValueError("unsupported reference repository in within-dataset config")
    return specs


def _adapters(dataset_config: Mapping[str, Any]):
    roots = dataset_config["reference_roots"]
    manifests = dataset_config["manifests"]
    return {
        "feasibility": FeasibilityRepositoryAdapter(
            roots["feasibility"], manifests["feasibility"]
        ),
        "air": AIRRepositoryAdapter(roots["air"], manifests["air"]),
    }


def _manifest_entry(adapters, spec: Mapping[str, Any]) -> Mapping[str, Any]:
    adapter = adapters[str(spec["repository"])]
    return adapter.manifest["datasets"][str(spec["dataset_id"])]


def _assignment_payload(
    report: SourceAuditReport, selection: RepresentationSelection
) -> dict[str, Any]:
    methods = []
    for method in report.methods:
        rows = method.to_dict()["assignments"]
        methods.append(
            {
                "method_id": method.method_id,
                "family": method.family,
                "assignments": rows,
            }
        )
    return {
        "schema": "WithinDatasetAssignments/v1",
        "label_free": True,
        "dataset_id": report.source_dataset_id,
        "source_audit_sha256": report.sha256(),
        "selected_method": selection.selected_method,
        "methods": methods,
    }


def _validate_within_prelabel(path: Path, dataset_id: str) -> str:
    _validate_hashed_directory(
        path,
        marker_name="PRELABEL_DONE",
        marker_schema="CompletedWithinDatasetPrelabel/v1",
        expected_id=dataset_id,
        hashed_files=WITHIN_PRELABEL_FILES,
    )
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    assignments = json.loads(
        (path / "source_assignments.json").read_text(encoding="utf-8")
    )
    report = SourceAuditReport.load(path / "source_audit.json")
    selection = RepresentationSelection.load(path / "selection.json")
    if (
        manifest.get("schema") != "WithinDatasetManifest/v1"
        or manifest.get("labels_loaded") is not False
        or manifest.get("evaluation_labels_read") is not False
        or manifest.get("dataset_id") != dataset_id
        or int(manifest.get("k", -1)) != 2
    ):
        raise ValueError(f"invalid label-free within-dataset manifest: {dataset_id}")
    if (
        assignments.get("schema") != "WithinDatasetAssignments/v1"
        or assignments.get("label_free") is not True
        or assignments.get("dataset_id") != dataset_id
        or assignments.get("source_audit_sha256") != report.sha256()
        or selection.audit_report_sha256 != (report.sha256(),)
    ):
        raise ValueError(f"invalid frozen within-dataset assignments: {dataset_id}")
    method_ids = tuple(item.method_id for item in report.methods)
    assignment_ids = tuple(item["method_id"] for item in assignments["methods"])
    if method_ids != assignment_ids:
        raise ValueError(f"within-dataset method inventory mismatch: {dataset_id}")
    if selection.selected_method is not None and selection.selected_method not in method_ids:
        raise ValueError(f"selected method is absent from frozen assignments: {dataset_id}")
    return sha256_bytes((path / "PRELABEL_DONE").read_bytes())


def _require_complete_within_prelabel(
    output_root: Path, dataset_ids: Sequence[str]
) -> dict[str, str]:
    completion_path = output_root / "WITHIN_PRELABEL_COMPLETE.json"
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    expected_ids = tuple(sorted(str(item) for item in dataset_ids))
    if (
        completion.get("schema") != "WithinDatasetPrelabelSummary/v1"
        or completion.get("labels_loaded") is not False
        or tuple(completion.get("dataset_ids", ())) != expected_ids
        or int(completion.get("dataset_count", -1)) != len(expected_ids)
    ):
        raise ValueError("within-dataset evaluation refused: incomplete prelabel boundary")
    validated = {
        dataset_id: _validate_within_prelabel(
            output_root / "datasets" / dataset_id / "prelabel", dataset_id
        )
        for dataset_id in expected_ids
    }
    if completion.get("prelabel_marker_sha256") != validated:
        raise ValueError("within-dataset completion marker inventory is inconsistent")
    return validated


def run_within_prelabel(
    config: Mapping[str, Any],
    *,
    dataset_config: Mapping[str, Any],
    gate_b_summary_path: str | Path,
    output_root: str | Path,
    max_workers: int,
) -> dict[str, Any]:
    """Freeze all eleven source-only audits without opening any label file."""

    specs = _dataset_specs(config)
    gate_path = Path(gate_b_summary_path)
    gate_b = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate_b.get("schema") != "GateBSummary/v1" or gate_b.get("gate_b_go") is not True:
        raise ValueError("real within-dataset audits are blocked until Gate B is GO")
    adapters = _adapters(dataset_config)
    sample_sizes = tuple(
        sorted(
            {
                int(_manifest_entry(adapters, spec)["n_samples"])
                for spec in specs
            }
        )
    )
    output_root = Path(output_root).resolve()
    calibrations = _ensure_calibrations(
        config, output_root, sample_sizes, max_workers=max_workers
    )
    summaries: dict[str, Any] = {}
    for index, spec in enumerate(specs, start=1):
        dataset_id = str(spec["dataset_id"])
        destination = output_root / "datasets" / dataset_id / "prelabel"
        try:
            marker_sha = _validate_within_prelabel(destination, dataset_id)
            selection = RepresentationSelection.load(destination / "selection.json")
            report = SourceAuditReport.load(destination / "source_audit.json")
            summaries[dataset_id] = {
                "status": "completed",
                "prelabel_marker_sha256": marker_sha,
                "decision": selection.decision,
                "selected_method": selection.selected_method,
                "source_audit_sha256": report.sha256(),
            }
            print(f"WITHIN PRELABEL {index:02d}/11 {dataset_id} validated", flush=True)
            continue
        except (FileNotFoundError, ValueError):
            pass

        bundle = adapters[str(spec["repository"])].load(dataset_id)
        expected_n = int(_manifest_entry(adapters, spec)["n_samples"])
        if bundle.shape[0] != expected_n:
            raise ValueError(f"manifest sample count mismatch for {dataset_id}")
        audit_config = _audit_config(
            config,
            seed=stable_seed(
                int(config["base_seed"]), "real_within_source_audit", dataset_id
            ),
        )
        with threadpool_limits(limits=1):
            fitted = fit_source_audit(bundle, audit_config)
            calibration = calibrations[bundle.shape[0]]
            selection = select_representation(
                [fitted.report],
                calibration,
                equivalence_margin=float(config["selector"]["equivalence_margin"]),
                minimum_decision_frequency=float(
                    config["selector"]["minimum_decision_frequency"]
                ),
            )
        assignment_payload = _assignment_payload(fitted.report, selection)
        _atomic_publish_directory(
            destination,
            identifier=dataset_id,
            marker_name="PRELABEL_DONE",
            marker_schema="CompletedWithinDatasetPrelabel/v1",
            files={
                "manifest.json": {
                    "schema": "WithinDatasetManifest/v1",
                    "labels_loaded": False,
                    "evaluation_labels_read": False,
                    "dataset_id": dataset_id,
                    "display_id": str(spec["display_id"]),
                    "repository": str(spec["repository"]),
                    "n_samples": bundle.shape[0],
                    "n_features": bundle.shape[1],
                    "x_sha256": bundle.metadata["x_sha256"],
                    "reference_commit": bundle.metadata["reference_commit"],
                    "gate_b_summary_sha256": sha256_bytes(gate_path.read_bytes()),
                    "k": 2,
                    "k_basis": "predeclared_binary_benchmark_control",
                    "null_calibration_sample_size": bundle.shape[0],
                },
                "null_calibration.json": calibration.to_json_bytes(),
                "source_audit.json": fitted.report.to_json_bytes(),
                "selection.json": selection.to_json_bytes(),
                "source_assignments.json": assignment_payload,
            },
        )
        marker_sha = _validate_within_prelabel(destination, dataset_id)
        summaries[dataset_id] = {
            "status": "completed",
            "prelabel_marker_sha256": marker_sha,
            "decision": selection.decision,
            "selected_method": selection.selected_method,
            "source_audit_sha256": fitted.report.sha256(),
        }
        print(
            f"WITHIN PRELABEL {index:02d}/11 {dataset_id} {selection.decision}",
            flush=True,
        )
        del bundle, fitted
        gc.collect()

    marker_hashes = {
        dataset_id: _validate_within_prelabel(
            output_root / "datasets" / dataset_id / "prelabel", dataset_id
        )
        for dataset_id in sorted(summaries)
    }
    result = {
        "schema": "WithinDatasetPrelabelSummary/v1",
        "labels_loaded": False,
        "dataset_count": len(summaries),
        "dataset_ids": tuple(sorted(summaries)),
        "prelabel_marker_sha256": marker_hashes,
        "decision_counts": dict(
            sorted(Counter(item["decision"] for item in summaries.values()).items())
        ),
        "datasets": dict(sorted(summaries.items())),
    }
    atomic_write_canonical_json(output_root / "WITHIN_PRELABEL_COMPLETE.json", result)
    return result


def _evaluate_dataset(
    *,
    dataset_id: str,
    display_id: str,
    report: SourceAuditReport,
    selection: RepresentationSelection,
    labels,
    marker_sha: str,
) -> dict[str, Any]:
    truth_map = labels.as_mapping()
    methods: list[dict[str, Any]] = []
    for method in report.methods:
        truth = [truth_map[sample_id] for sample_id in method.sample_ids]
        assignments = list(method.assignments)
        methods.append(
            {
                "method_id": method.method_id,
                "family": method.family,
                "source_q": method.q_score,
                "ari": float(adjusted_rand_score(truth, assignments)),
                "nmi": float(normalized_mutual_info_score(truth, assignments)),
                "min_cluster_fraction": method.min_cluster_fraction,
                "nondegenerate": method.nondegenerate,
            }
        )
    if not methods:
        raise ValueError(f"no auditable methods for {dataset_id}")
    oracle = sorted(methods, key=lambda item: (-item["ari"], item["method_id"]))[0]
    selected = (
        None
        if selection.selected_method is None
        else next(item for item in methods if item["method_id"] == selection.selected_method)
    )
    selected_ari = 0.0 if selected is None else float(selected["ari"])
    observed_class_count = len(set(labels.values))
    return {
        "schema": "WithinDatasetEvaluation/v1",
        "evaluation_only": True,
        "within_dataset_descriptive": True,
        "not_external_validation": True,
        "dataset_id": dataset_id,
        "display_id": display_id,
        "prelabel_marker_sha256": marker_sha,
        "labels_unblinded_after_all_prelabel_validation": True,
        "observed_evaluation_class_count": observed_class_count,
        "frozen_k": selection.selected_k,
        "frozen_k_matches_observed_class_count": selection.selected_k
        == observed_class_count,
        "selected_decision": selection.decision,
        "selected_method": selection.selected_method,
        "selected_ari": selected_ari,
        "selected_nmi": None if selected is None else float(selected["nmi"]),
        "selected_min_cluster_fraction": (
            0.0 if selected is None else float(selected["min_cluster_fraction"])
        ),
        "oracle_method": oracle["method_id"],
        "oracle_family": oracle["family"],
        "oracle_ari": float(oracle["ari"]),
        "ari_regret": max(0.0, float(oracle["ari"]) - selected_ari),
        "methods": methods,
    }


def _collect_within(evaluations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = tuple(evaluations)
    if not rows:
        raise ValueError("within-dataset collection requires evaluations")
    regrets = np.asarray([float(item["ari_regret"]) for item in rows], dtype=float)
    selected_aris = np.asarray([float(item["selected_ari"]) for item in rows], dtype=float)
    return {
        "schema": "WithinDatasetSummary/v1",
        "evaluation_only": True,
        "descriptive_not_a_gate": True,
        "dataset_count": len(rows),
        "all_frozen_k_match_observed_binary_tasks": all(
            bool(item["frozen_k_matches_observed_class_count"]) for item in rows
        ),
        "decision_counts": dict(
            sorted(Counter(str(item["selected_decision"]) for item in rows).items())
        ),
        "oracle_family_counts": dict(
            sorted(Counter(str(item["oracle_family"]) for item in rows).items())
        ),
        "median_selected_ari": float(np.median(selected_aris)),
        "median_ari_regret": float(np.median(regrets)),
        "selected_within_0_05_of_oracle_rate": float(np.mean(regrets <= 0.05)),
        "datasets": {
            str(item["dataset_id"]): dict(item)
            for item in sorted(rows, key=lambda value: str(value["dataset_id"]))
        },
    }


def run_within_evaluation(
    config: Mapping[str, Any],
    *,
    dataset_config: Mapping[str, Any],
    output_root: str | Path,
) -> dict[str, Any]:
    """Validate all eleven freezes before importing the evaluation label loader."""

    specs = _dataset_specs(config)
    output_root = Path(output_root).resolve()
    marker_hashes = _require_complete_within_prelabel(
        output_root, [str(item["dataset_id"]) for item in specs]
    )

    # Deliberately imported only after every prelabel marker validates.
    from rep_audit.evaluation.repository_labels import RepositoryLabelLoader

    roots = dataset_config["reference_roots"]
    loader = RepositoryLabelLoader(
        dataset_config["manifests"]["evaluation_labels"],
        {"air": roots["air"], "feasibility": roots["feasibility"]},
    )
    adapters = _adapters(dataset_config)
    evaluations: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, start=1):
        dataset_id = str(spec["dataset_id"])
        prelabel = output_root / "datasets" / dataset_id / "prelabel"
        report = SourceAuditReport.load(prelabel / "source_audit.json")
        selection = RepresentationSelection.load(prelabel / "selection.json")
        bundle = adapters[str(spec["repository"])].load(dataset_id)
        labels = loader.load(dataset_id, expected_sample_ids=bundle.sample_ids)
        result = _evaluate_dataset(
            dataset_id=dataset_id,
            display_id=str(spec["display_id"]),
            report=report,
            selection=selection,
            labels=labels,
            marker_sha=marker_hashes[dataset_id],
        )
        destination = output_root / "datasets" / dataset_id / "evaluation"
        _atomic_publish_directory(
            destination,
            identifier=dataset_id,
            marker_name="EVALUATED",
            marker_schema="CompletedWithinDatasetEvaluation/v1",
            files={"metrics.json": result},
        )
        evaluations.append(result)
        print(f"WITHIN EVALUATE {index:02d}/11 {dataset_id}", flush=True)
        del bundle, labels
        gc.collect()
    summary = _collect_within(evaluations)
    atomic_write_canonical_json(output_root / "within_summary.json", summary)
    return summary


def scientific_tree_sha256(output_root: str | Path) -> str:
    """Hash the complete deterministic within-dataset result tree."""

    root = Path(output_root).resolve()
    paths = sorted(path for path in root.rglob("*") if path.is_file())
    inventory = []
    for path in paths:
        digest = sha256_bytes(path.read_bytes())
        inventory.append((str(path.relative_to(root)), digest))
    return sha256_bytes(canonical_json_bytes(inventory))
