from __future__ import annotations

import inspect

import numpy as np
import pytest

from rep_audit.data.schema import DatasetBundle
from rep_audit.representations.relation_screen import (
    NoEligibleRelationsError,
    screen_source_relations,
)


def relation_source(*, permute_columns: bool = False) -> DatasetBundle:
    matrix = np.array(
        [
            [3.0, 1.0, 10.0, 20.0],
            [4.0, 1.0, 11.0, 21.0],
            [1.0, 3.0, 12.0, 22.0],
            [1.0, 4.0, 13.0, 23.0],
            [3.5, 1.5, 14.0, 24.0],
            [1.5, 3.5, 15.0, 25.0],
        ]
    )
    feature_ids = np.array(["a", "b", "c", "d"])
    if permute_columns:
        order = np.array([2, 1, 3, 0])
        matrix = matrix[:, order]
        feature_ids = feature_ids[order]
    return DatasetBundle(
        X=matrix,
        sample_ids=tuple(f"s{i}" for i in range(len(matrix))),
        feature_ids=tuple(feature_ids),
        dataset_id="screen",
        platform_id="sim",
        cohort_id="source",
    )


def test_screen_retains_variable_stable_relation_and_freezes_weights() -> None:
    artifact = screen_source_relations(
        relation_source(),
        feature_ids=("a", "b", "c", "d"),
        margin=0.0,
        relation_budget=3,
        coverage_threshold=0.90,
        entropy_threshold=0.05,
        stability_threshold=0.50,
        perturbation_count=2,
        perturbation_seed=13,
    )
    assert ("a", "b") in artifact.relation_pairs
    assert artifact.candidate_count == 6
    assert len(artifact.relation_pairs) <= 3
    assert np.mean(artifact.weights) == pytest.approx(1.0)
    assert artifact.to_dict()["source_only"] is True


def test_screen_is_invariant_to_source_column_order() -> None:
    kwargs = dict(
        feature_ids=("a", "b", "c", "d"),
        margin=0.0,
        relation_budget=3,
        stability_threshold=0.50,
        perturbation_count=2,
        perturbation_seed=19,
    )
    first = screen_source_relations(relation_source(), **kwargs)
    second = screen_source_relations(relation_source(permute_columns=True), **kwargs)
    assert first.relation_pairs == second.relation_pairs
    assert np.allclose(first.scores, second.scores)
    assert np.allclose(first.weights, second.weights)


def test_constant_relation_universe_is_rejected() -> None:
    source = DatasetBundle(
        X=np.array([[0.0, 1.0, 2.0], [0.1, 1.1, 2.1], [0.2, 1.2, 2.2]]),
        sample_ids=("s1", "s2", "s3"),
        feature_ids=("a", "b", "c"),
        dataset_id="constant",
        platform_id="sim",
        cohort_id="source",
    )
    with pytest.raises(NoEligibleRelationsError):
        screen_source_relations(
            source,
            feature_ids=source.feature_ids,
            margin=0.0,
            relation_budget=2,
            perturbation_count=1,
        )


def test_screen_interface_has_no_target_or_label_argument() -> None:
    parameters = inspect.signature(screen_source_relations).parameters
    assert "target" not in parameters
    assert "labels" not in parameters
    assert "y" not in parameters
