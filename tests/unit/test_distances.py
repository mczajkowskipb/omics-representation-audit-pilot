from __future__ import annotations

import numpy as np
import pytest

from rep_audit.distances.footrule import footrule_distance_matrix
from rep_audit.distances.hybrid import (
    fit_hybrid_scales,
    fit_source_distance_scale,
    hybrid_distance_matrix,
    normalize_distance,
)
from rep_audit.distances.relation_hamming import relation_hamming_distance_matrix
from rep_audit.distances.validation import DistanceMatrix
from rep_audit.distances.value import (
    correlation_distance_matrix,
    euclidean_distance_matrix,
)
from rep_audit.preprocessing.artifact import PreprocessedValues
from rep_audit.representations.ranks import RankRepresentation
from rep_audit.representations.ternary_relations import (
    TernaryRelationRepresentation,
)


def values(matrix, ids=("s1", "s2", "s3")) -> PreprocessedValues:
    matrix = np.asarray(matrix, dtype=float)
    return PreprocessedValues(
        matrix=matrix,
        sample_ids=ids,
        feature_ids=tuple(f"g{i + 1}" for i in range(matrix.shape[1])),
        artifact_sha256="0" * 64,
    )


def test_euclidean_golden_triangle() -> None:
    distance = euclidean_distance_matrix(
        values([[0.0, 0.0], [3.0, 4.0], [0.0, 4.0]])
    )
    assert np.array_equal(
        distance.values,
        np.array([[0.0, 5.0, 4.0], [5.0, 0.0, 3.0], [4.0, 3.0, 0.0]]),
    )


def test_correlation_golden_identical_and_reverse_profiles() -> None:
    distance = correlation_distance_matrix(
        values([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [3.0, 2.0, 1.0]])
    )
    assert np.allclose(
        distance.values,
        np.array([[0.0, 0.0, 2.0], [0.0, 0.0, 2.0], [2.0, 2.0, 0.0]]),
        atol=1.0e-12,
    )


def test_correlation_rejects_constant_sample_profile() -> None:
    with pytest.raises(ValueError, match="constant sample"):
        correlation_distance_matrix(values([[1.0, 1.0], [1.0, 2.0]], ids=("c", "x")))


def test_footrule_zero_for_identical_and_one_for_reverse_ranking() -> None:
    ranks = RankRepresentation(
        q=np.array([[0.0, 0.5, 1.0], [0.0, 0.5, 1.0], [1.0, 0.5, 0.0]]),
        observed=np.ones((3, 3), dtype=bool),
        sample_ids=("same1", "same2", "reverse"),
        feature_ids=("a", "b", "c"),
    )
    distance = footrule_distance_matrix(ranks)
    assert distance.values[0, 1] == 0.0
    assert distance.values[0, 2] == 1.0
    assert distance.values[1, 2] == 1.0


def test_footrule_rejects_missing_rank_positions() -> None:
    ranks = RankRepresentation(
        q=np.array([[0.0, 1.0], [0.0, 0.0]]),
        observed=np.array([[True, True], [True, False]]),
        sample_ids=("s1", "s2"),
        feature_ids=("a", "b"),
    )
    with pytest.raises(ValueError, match="complete frozen"):
        footrule_distance_matrix(ranks)


def test_relation_hamming_masks_missing_instead_of_counting_disagreement() -> None:
    relations = TernaryRelationRepresentation(
        states=np.array([[1, 0, -1], [1, 1, 1], [-1, 0, -1]], dtype=np.int8),
        observed=np.array(
            [[True, True, True], [True, True, False], [True, True, True]]
        ),
        sample_ids=("s1", "s2", "s3"),
        relation_pairs=(("a", "b"), ("a", "c"), ("b", "c")),
        margin=0.0,
    )
    distance = relation_hamming_distance_matrix(relations)
    assert distance.values[0, 1] == 0.5
    assert distance.values[0, 2] == pytest.approx(1.0 / 3.0)
    assert distance.values[1, 2] == 1.0


def test_relation_hamming_respects_frozen_weights() -> None:
    relations = TernaryRelationRepresentation(
        states=np.array([[1, 0], [-1, 0]], dtype=np.int8),
        observed=np.ones((2, 2), dtype=bool),
        sample_ids=("s1", "s2"),
        relation_pairs=(("a", "b"), ("a", "c")),
        margin=0.0,
    )
    distance = relation_hamming_distance_matrix(relations, weights=(3.0, 1.0))
    assert distance.values[0, 1] == 0.75


def test_relation_hamming_rejects_zero_joint_coverage() -> None:
    relations = TernaryRelationRepresentation(
        states=np.zeros((2, 2), dtype=np.int8),
        observed=np.array([[True, False], [False, True]]),
        sample_ids=("s1", "s2"),
        relation_pairs=(("a", "b"), ("c", "d")),
        margin=0.0,
    )
    with pytest.raises(ValueError, match="no jointly observed"):
        relation_hamming_distance_matrix(relations)


def test_source_scale_uses_only_nonzero_strict_upper_triangle() -> None:
    distance = DistanceMatrix(
        values=np.array([[0.0, 0.0, 2.0], [0.0, 0.0, 4.0], [2.0, 4.0, 0.0]]),
        sample_ids=("s1", "s2", "s3"),
        metric_id="toy",
    )
    assert fit_source_distance_scale(distance) == 3.0


def test_hybrid_endpoints_exactly_reproduce_normalized_pure_distances() -> None:
    value_distance = DistanceMatrix(
        values=np.array([[0.0, 2.0, 4.0], [2.0, 0.0, 6.0], [4.0, 6.0, 0.0]]),
        sample_ids=("s1", "s2", "s3"),
        metric_id="value",
    )
    relation_distance = DistanceMatrix(
        values=np.array([[0.0, 1.0, 2.0], [1.0, 0.0, 3.0], [2.0, 3.0, 0.0]]),
        sample_ids=value_distance.sample_ids,
        metric_id="relation",
    )
    scales = fit_hybrid_scales(value_distance, relation_distance)
    value_endpoint = normalize_distance(
        value_distance, scale=scales.value_scale, endpoint_name="value"
    )
    relation_endpoint = normalize_distance(
        relation_distance, scale=scales.relational_scale, endpoint_name="relation"
    )
    alpha_zero = hybrid_distance_matrix(
        value_distance, relation_distance, scales, alpha=0.0
    )
    alpha_one = hybrid_distance_matrix(
        value_distance, relation_distance, scales, alpha=1.0
    )
    midpoint = hybrid_distance_matrix(
        value_distance, relation_distance, scales, alpha=0.5
    )
    assert np.array_equal(alpha_zero.values, value_endpoint.values)
    assert np.array_equal(alpha_one.values, relation_endpoint.values)
    assert np.array_equal(
        midpoint.values, (value_endpoint.values + relation_endpoint.values) / 2.0
    )
    assert scales.value_scale == 4.0
    assert scales.relational_scale == 2.0


def test_hybrid_rejects_degenerate_source_scale_and_matrix_mutation() -> None:
    zero = DistanceMatrix(
        values=np.zeros((2, 2)), sample_ids=("s1", "s2"), metric_id="zero"
    )
    nonzero = DistanceMatrix(
        values=np.array([[0.0, 1.0], [1.0, 0.0]]),
        sample_ids=("s1", "s2"),
        metric_id="nonzero",
    )
    with pytest.raises(ValueError, match="positive source scale"):
        fit_hybrid_scales(zero, nonzero)

    scales = fit_hybrid_scales(nonzero, nonzero)
    changed = DistanceMatrix(
        values=np.array([[0.0, 2.0], [2.0, 0.0]]),
        sample_ids=nonzero.sample_ids,
        metric_id=nonzero.metric_id,
    )
    with pytest.raises(ValueError, match="differs"):
        hybrid_distance_matrix(changed, nonzero, scales, alpha=0.5)


@pytest.mark.parametrize(
    "matrix, message",
    [
        (np.array([[0.0, 1.0], [2.0, 0.0]]), "symmetric"),
        (np.array([[1.0, 0.0], [0.0, 0.0]]), "diagonal"),
        (np.array([[0.0, -1.0], [-1.0, 0.0]]), "non-negative"),
        (np.array([[0.0, np.nan], [np.nan, 0.0]]), "finite"),
    ],
)
def test_distance_contract_rejects_invalid_matrices(matrix, message) -> None:
    with pytest.raises(ValueError, match=message):
        DistanceMatrix(values=matrix, sample_ids=("s1", "s2"), metric_id="bad")
