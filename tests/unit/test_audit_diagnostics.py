from __future__ import annotations

import inspect

import numpy as np

from rep_audit.audit.config import AuditConfig
from rep_audit.audit.diagnostics import (
    cluster_stability,
    nondegeneracy,
    prediction_strength,
    run_source_audit,
)
from rep_audit.clustering.pam import deterministic_pam
from rep_audit.distances.validation import DistanceMatrix
from rep_audit.simulation.generators import SimulationSpec, generate_simulation


def clear_block_distance() -> DistanceMatrix:
    n_per_cluster = 10
    labels = np.repeat([0, 1], n_per_cluster)
    values = np.where(labels[:, None] == labels[None, :], 0.1, 10.0)
    np.fill_diagonal(values, 0.0)
    return DistanceMatrix(
        values=values,
        sample_ids=tuple(f"s{index:02d}" for index in range(len(labels))),
        metric_id="clear_blocks",
    )


def test_clear_distance_has_high_prediction_strength_and_stability() -> None:
    distance = clear_block_distance()
    baseline = deterministic_pam(distance, k=2)
    ps = prediction_strength(distance, k=2, resamples=5, seed=11)
    stability = cluster_stability(
        distance, baseline, k=2, resamples=5, seed=12
    )
    assert ps == 1.0
    assert stability == 1.0


def test_nondegeneracy_rejects_tiny_cluster() -> None:
    score, passes, minimum, entropy = nondegeneracy(
        [0] * 19 + [1], k=2, min_cluster_fraction=0.10
    )
    assert not passes
    assert minimum == 0.05
    assert 0.0 < score < 1.0
    assert 0.0 < entropy < 1.0


def test_small_source_audit_is_canonical_and_deterministic() -> None:
    generated = generate_simulation(
        SimulationSpec(
            regime="VALUE",
            signal="strong",
            shift="moderate",
            replicate=0,
            seed=41,
            n_source=30,
            n_target=30,
            p=24,
            k=3,
            informative_features=12,
        )
    )
    config = AuditConfig(
        k=3,
        feature_budget=24,
        relation_budget=20,
        resamples=2,
        seed=99,
        relation_screen_perturbations=1,
        relation_stability_threshold=0.50,
    )
    first = run_source_audit(generated.source, config)
    second = run_source_audit(generated.source, config)
    assert first.to_json_bytes() == second.to_json_bytes()
    assert first.to_dict()["source_only"] is True
    assert first.source_fingerprint == generated.source.fingerprint()
    assert {method.family for method in first.methods} <= {
        "VALUE",
        "RELATIONAL",
        "HYBRID",
    }
    assert all(
        method.q_score
        == min(
            method.prediction_strength,
            method.cluster_stability,
            method.perturbation_invariance,
        )
        for method in first.methods
    )


def test_source_audit_interface_cannot_accept_target_or_labels() -> None:
    parameters = inspect.signature(run_source_audit).parameters
    assert set(parameters) == {"source", "config"}
    assert "target" not in parameters
    assert "labels" not in parameters
    assert "y" not in parameters
