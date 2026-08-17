from __future__ import annotations

from rep_audit.experiments.closeout_validation import gate_c_checks


def _direction(regret: float) -> dict[str, object]:
    return {
        "target_ari_regret": regret,
        "labels_unblinded_after_prelabel_validation": True,
        "selected_assignment_coverage": 0.90,
        "selected_min_assigned_cluster_fraction_of_target": 0.20,
    }


def test_gate_c_recomputation_preserves_frozen_asymmetric_limits() -> None:
    checks = gate_c_checks({"a": _direction(0.0), "b": _direction(0.105284)})
    assert checks[
        "one_direction_regret_at_most_0_05_and_reverse_at_most_0_10"
    ] is False
    assert sum(checks.values()) == 3


def test_gate_c_boundary_is_inclusive_without_relaxation() -> None:
    checks = gate_c_checks({"a": _direction(0.05), "b": _direction(0.10)})
    assert all(checks.values())
