"""Evaluation-only metrics applied after source artifacts are frozen."""

from __future__ import annotations

from typing import Any

from sklearn.metrics import adjusted_rand_score

from rep_audit.audit.report import SourceAuditReport
from rep_audit.audit.selector import RepresentationSelection
from rep_audit.evaluation.simulation_truth import SimulationTruth


def evaluate_simulation_selection(
    selection: RepresentationSelection,
    audit: SourceAuditReport,
    truth: SimulationTruth,
) -> dict[str, Any]:
    """Unblind simulation truth only after audit and selection are frozen."""

    selected_ari: float | None = None
    if selection.selected_method is not None:
        method = audit.method_by_id(selection.selected_method)
        labels = truth.source_labels.as_mapping()
        true_values = [labels[sample_id] for sample_id in method.sample_ids]
        selected_ari = float(adjusted_rand_score(true_values, method.assignments))
    return {
        "schema": "SimulationMetrics/v1",
        "evaluation_only": True,
        "labels_unblinded_after_selection_sha256": selection.sha256(),
        "regime": truth.regime,
        "expected_decision": truth.expected_decision,
        "selected_decision": selection.decision,
        "decision_correct": selection.decision == truth.expected_decision,
        "uncertain": selection.uncertain,
        "selected_method": selection.selected_method,
        "selected_source_ari": selected_ari,
        "target_labels_used": False,
        "target_evaluation_deferred": True,
    }
