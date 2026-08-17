"""Evaluation-only ground truth for deterministic simulations."""

from __future__ import annotations

from dataclasses import dataclass

from rep_audit.evaluation.external_labels import EvaluationLabels


@dataclass(frozen=True, slots=True)
class SimulationTruth:
    """Latent labels kept outside every fit and audit interface."""

    regime: str
    expected_decision: str
    source_labels: EvaluationLabels
    target_labels: EvaluationLabels

    def __post_init__(self) -> None:
        if self.regime not in {"VALUE", "RELATIONAL", "HYBRID", "NULL"}:
            raise ValueError("unsupported simulation regime")
        expected = (
            "NO_STABLE_STRUCTURE" if self.regime == "NULL" else self.regime
        )
        if self.expected_decision != expected:
            raise ValueError("expected_decision must follow the frozen regime map")
