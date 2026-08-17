from __future__ import annotations

import json

import pytest

from rep_audit.audit.config import AuditConfig
from rep_audit.audit.report import MethodAuditResult, SourceAuditReport
from rep_audit.audit.selector import RepresentationSelection
from rep_audit.evaluation.external_labels import EvaluationLabels
from rep_audit.experiments.real_lung import _validate_null_report
from rep_audit.experiments.real_within import (
    PROTOCOL_DATASETS,
    _assignment_payload,
    _collect_within,
    _dataset_specs,
    _evaluate_dataset,
)


def _method(method_id: str, family: str, assignments: tuple[int, ...], q: float):
    return MethodAuditResult(
        method_id=method_id,
        family=family,
        prediction_strength=q,
        cluster_stability=min(1.0, q + 0.1),
        perturbation_invariance=min(1.0, q + 0.2),
        representation_stability=0.8,
        nondegeneracy_score=1.0,
        nondegenerate=True,
        min_cluster_fraction=0.5,
        cluster_entropy=1.0,
        q_score=q,
        medoid_ids=("s0", "s2"),
        sample_ids=("s0", "s1", "s2", "s3"),
        assignments=assignments,
        complexity=4,
        perturbation_failures=0,
    )


def _report(config: AuditConfig | None = None) -> SourceAuditReport:
    config = config or AuditConfig(
        k=2, feature_budget=4, relation_budget=4, resamples=1, seed=7
    )
    return SourceAuditReport(
        source_dataset_id="toy",
        source_fingerprint="source-sha",
        config_sha256=config.sha256(),
        config=config.to_dict(),
        representation_manifest={"schema": "SourceRepresentationSet/v1"},
        methods=(
            _method("R_FOOT_PAM", "RELATIONAL", (0, 1, 0, 1), 0.7),
            _method("V_EUC_PAM", "VALUE", (0, 0, 1, 1), 0.8),
        ),
        failures={},
    )


def _selection(report: SourceAuditReport) -> RepresentationSelection:
    return RepresentationSelection(
        decision="VALUE",
        uncertain=False,
        decision_confidence=1.0,
        selected_method="V_EUC_PAM",
        selected_k=2,
        selected_alpha=None,
        q_score=0.8,
        null_threshold=0.5,
        eligible_alternatives=("R_FOOT_PAM",),
        rejection_reasons={},
        vote_counts={"VALUE": 1},
        audit_report_sha256=(report.sha256(),),
        calibration_sha256="calibration-sha",
    )


def test_dataset_config_is_exact_and_k_is_frozen() -> None:
    config = {
        "audit": {"k": 2},
        "datasets": [
            {
                "dataset_id": dataset_id,
                "repository": "feasibility" if index < 3 else "air",
                "display_id": dataset_id,
                "k": 2,
            }
            for index, dataset_id in enumerate(PROTOCOL_DATASETS)
        ],
    }
    assert len(_dataset_specs(config)) == 11
    config["datasets"][0]["k"] = 3
    with pytest.raises(ValueError, match="K=2"):
        _dataset_specs(config)


def test_frozen_assignment_payload_contains_all_methods_without_truth() -> None:
    report = _report()
    value = _assignment_payload(report, _selection(report))
    rendered = json.dumps(value).lower()
    assert value["label_free"] is True
    assert value["selected_method"] == "V_EUC_PAM"
    assert [item["method_id"] for item in value["methods"]] == [
        "R_FOOT_PAM",
        "V_EUC_PAM",
    ]
    assert "truth" not in rendered
    assert "class_label" not in rendered


def test_evaluation_scores_only_already_frozen_assignments() -> None:
    report = _report()
    labels = EvaluationLabels(
        dataset_id="toy",
        sample_ids=("s0", "s1", "s2", "s3"),
        values=("A", "A", "B", "B"),
        label_name="evaluation_only",
    )
    value = _evaluate_dataset(
        dataset_id="toy",
        display_id="Toy",
        report=report,
        selection=_selection(report),
        labels=labels,
        marker_sha="marker-sha",
    )
    assert value["selected_ari"] == pytest.approx(1.0)
    assert value["oracle_method"] == "V_EUC_PAM"
    assert value["ari_regret"] == pytest.approx(0.0)
    assert value["not_external_validation"] is True
    assert value["labels_unblinded_after_all_prelabel_validation"] is True


def test_collection_is_descriptive_and_not_a_new_gate() -> None:
    report = _report()
    labels = EvaluationLabels(
        dataset_id="toy",
        sample_ids=("s0", "s1", "s2", "s3"),
        values=("A", "A", "B", "B"),
        label_name="evaluation_only",
    )
    row = _evaluate_dataset(
        dataset_id="toy",
        display_id="Toy",
        report=report,
        selection=_selection(report),
        labels=labels,
        marker_sha="marker-sha",
    )
    summary = _collect_within([row])
    assert summary["descriptive_not_a_gate"] is True
    assert "go" not in json.dumps(summary).lower()


def test_cached_null_report_rejects_wrong_sample_size_or_config() -> None:
    config = AuditConfig(
        k=2, feature_budget=4, relation_budget=4, resamples=1, seed=7
    )
    report = _report(config)
    _validate_null_report(report, n_samples=4, expected_config=config)
    round_tripped = SourceAuditReport.from_dict(
        json.loads(report.to_json_bytes().decode("utf-8"))
    )
    _validate_null_report(round_tripped, n_samples=4, expected_config=config)
    with pytest.raises(ValueError, match="sample size"):
        _validate_null_report(report, n_samples=5, expected_config=config)
    with pytest.raises(ValueError, match="configuration"):
        _validate_null_report(
            report,
            n_samples=4,
            expected_config=AuditConfig(
                k=2, feature_budget=4, relation_budget=4, resamples=1, seed=99
            ),
        )
