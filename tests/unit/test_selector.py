from __future__ import annotations

from dataclasses import replace

import pytest

from rep_audit.audit.report import MethodAuditResult, SourceAuditReport
from rep_audit.audit.selector import (
    NullCalibrationArtifact,
    calibrate_null,
    select_representation,
)


def method(
    method_id: str,
    family: str,
    q: float,
    *,
    complexity: int = 10,
    nondegenerate: bool = True,
) -> MethodAuditResult:
    return MethodAuditResult(
        method_id=method_id,
        family=family,
        prediction_strength=q,
        cluster_stability=q,
        perturbation_invariance=q,
        representation_stability=q,
        nondegeneracy_score=1.0 if nondegenerate else 0.2,
        nondegenerate=nondegenerate,
        min_cluster_fraction=0.30 if nondegenerate else 0.02,
        cluster_entropy=1.0 if nondegenerate else 0.4,
        q_score=q,
        medoid_ids=("s1", "s2", "s3"),
        sample_ids=("s1", "s2", "s3", "s4", "s5", "s6"),
        assignments=(0, 0, 1, 1, 2, 2),
        complexity=complexity,
        perturbation_failures=0,
    )


def report(*methods: MethodAuditResult, suffix: str = "x") -> SourceAuditReport:
    return SourceAuditReport(
        source_dataset_id=f"source-{suffix}",
        source_fingerprint=(suffix * 64)[:64],
        config_sha256=("c" * 64),
        config={"k": 3},
        representation_manifest={},
        methods=tuple(sorted(methods, key=lambda item: item.method_id)),
        failures={},
    )


def calibration(**thresholds: float) -> NullCalibrationArtifact:
    return NullCalibrationArtifact(
        k=3,
        quantile=0.90,
        method_thresholds=thresholds,
        method_counts={key: 10 for key in thresholds},
        delta_hybrid=0.05,
        null_report_sha256=("n" * 64,),
    )


def test_no_method_above_null_returns_explicit_abstention() -> None:
    audit = report(
        method("V_EUC_PAM", "VALUE", 0.40),
        method("R_PAIR_PAM", "RELATIONAL", 0.45),
    )
    selected = select_representation(
        [audit], calibration(V_EUC_PAM=0.50, R_PAIR_PAM=0.50)
    )
    assert selected.decision == "NO_STABLE_STRUCTURE"
    assert selected.selected_method is None


def test_best_eligible_pure_family_is_selected() -> None:
    audit = report(
        method("V_EUC_PAM", "VALUE", 0.70, complexity=20),
        method("R_PAIR_PAM", "RELATIONAL", 0.82, complexity=100),
    )
    selected = select_representation(
        [audit], calibration(V_EUC_PAM=0.50, R_PAIR_PAM=0.50)
    )
    assert selected.decision == "RELATIONAL"
    assert selected.selected_method == "R_PAIR_PAM"


def test_equivalent_pure_families_choose_simpler_method() -> None:
    audit = report(
        method("V_EUC_PAM", "VALUE", 0.80, complexity=20),
        method("R_PAIR_PAM", "RELATIONAL", 0.81, complexity=100),
    )
    selected = select_representation(
        [audit],
        calibration(V_EUC_PAM=0.50, R_PAIR_PAM=0.50),
        equivalence_margin=0.02,
    )
    assert selected.decision == "VALUE"


def test_hybrid_requires_gain_over_both_pure_endpoints() -> None:
    base = (
        method("V_EUC_PAM", "VALUE", 0.70),
        method("R_PAIR_PAM", "RELATIONAL", 0.72),
    )
    thresholds = calibration(
        V_EUC_PAM=0.50,
        R_PAIR_PAM=0.50,
        H_EUC_PAIR_A050_PAM=0.50,
    )
    insufficient = select_representation(
        [report(*base, method("H_EUC_PAIR_A050_PAM", "HYBRID", 0.76))],
        thresholds,
    )
    sufficient = select_representation(
        [report(*base, method("H_EUC_PAIR_A050_PAM", "HYBRID", 0.80))],
        thresholds,
    )
    assert insufficient.decision == "RELATIONAL"
    assert sufficient.decision == "HYBRID"
    assert sufficient.selected_alpha == 0.50


def test_outer_vote_marks_low_frequency_as_uncertain() -> None:
    thresholds = calibration(V_EUC_PAM=0.5, R_PAIR_PAM=0.5)
    value = report(method("V_EUC_PAM", "VALUE", 0.8), suffix="a")
    relational = report(method("R_PAIR_PAM", "RELATIONAL", 0.8), suffix="b")
    selected = select_representation(
        [value, relational], thresholds, minimum_decision_frequency=0.60
    )
    assert selected.decision == "VALUE"
    assert selected.decision_confidence == 0.5
    assert selected.uncertain


def test_null_calibration_uses_conservative_higher_quantile() -> None:
    reports = [
        report(method("V_EUC_PAM", "VALUE", value), suffix=str(index))
        for index, value in enumerate((0.1, 0.2, 0.3, 0.4))
    ]
    artifact = calibrate_null(reports, quantile=0.75)
    assert artifact.method_thresholds["V_EUC_PAM"] == 0.4
    assert artifact.method_counts["V_EUC_PAM"] == 4
    assert artifact.multiple_testing_margin == pytest.approx(0.1)
    assert artifact.delta_hybrid == 0.02


def test_multiple_testing_margin_uses_method_specific_excess_not_raw_q() -> None:
    reports = [
        report(
            method("V_EUC_PAM", "VALUE", value_q),
            method("R_PAIR_PAM", "RELATIONAL", relation_q),
            suffix=str(index),
        )
        for index, (value_q, relation_q) in enumerate(
            ((0.80, 0.10), (0.81, 0.11), (0.82, 0.12), (0.83, 0.13))
        )
    ]
    artifact = calibrate_null(reports, quantile=0.75)
    assert artifact.method_thresholds["V_EUC_PAM"] == 0.83
    assert artifact.method_thresholds["R_PAIR_PAM"] == 0.13
    assert artifact.multiple_testing_margin == pytest.approx(0.01)


def test_selection_adds_multiple_testing_margin_to_each_method_threshold() -> None:
    artifact = NullCalibrationArtifact(
        k=3,
        quantile=0.90,
        method_thresholds={"V_EUC_PAM": 0.50, "R_PAIR_PAM": 0.20},
        method_counts={"V_EUC_PAM": 10, "R_PAIR_PAM": 10},
        delta_hybrid=0.05,
        null_report_sha256=("n" * 64,),
        multiple_testing_margin=0.10,
    )
    audit = report(
        method("V_EUC_PAM", "VALUE", 0.59),
        method("R_PAIR_PAM", "RELATIONAL", 0.31),
    )
    selected = select_representation([audit], artifact)
    assert selected.decision == "RELATIONAL"
    assert selected.null_threshold == pytest.approx(0.30)


def test_degenerate_method_is_rejected_even_above_null() -> None:
    audit = report(method("V_EUC_PAM", "VALUE", 0.95, nondegenerate=False))
    selected = select_representation([audit], calibration(V_EUC_PAM=0.50))
    assert selected.decision == "NO_STABLE_STRUCTURE"
    assert selected.rejection_reasons["V_EUC_PAM"] == "degenerate"


@pytest.mark.parametrize("reports", [[], tuple()])
def test_selector_requires_reports(reports) -> None:
    with pytest.raises(ValueError):
        select_representation(reports, calibration(V_EUC_PAM=0.5))
