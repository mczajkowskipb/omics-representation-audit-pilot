from __future__ import annotations

import itertools

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from rep_audit.clustering.pam import deterministic_pam
from rep_audit.distances.hybrid import (
    fit_hybrid_scales,
    hybrid_distance_matrix,
    normalize_distance,
)
from rep_audit.distances.validation import DistanceMatrix


def exhaustive_optimum(distance: DistanceMatrix, k: int) -> tuple[float, tuple[str, ...]]:
    best_cost = np.inf
    best_ids: tuple[str, ...] | None = None
    for indices in itertools.combinations(range(len(distance.sample_ids)), k):
        cost = float(np.min(distance.values[:, indices], axis=1).sum())
        ids = tuple(sorted(distance.sample_ids[index] for index in indices))
        if cost < best_cost - 1.0e-12 or (
            abs(cost - best_cost) <= 1.0e-12
            and (best_ids is None or ids < best_ids)
        ):
            best_cost = cost
            best_ids = ids
    assert best_ids is not None
    return best_cost, best_ids


def test_build_swap_matches_exhaustive_optimum_on_old_pam_counterexample() -> None:
    points = np.array(
        [[15, 8], [22, 8], [28, 23], [8, 10], [16, 15], [19, 17]],
        dtype=float,
    )
    distance = DistanceMatrix(
        values=cdist(points, points, metric="cityblock"),
        sample_ids=tuple(f"p{index}" for index in range(len(points))),
        metric_id="golden_cityblock",
    )
    optimum, _ = exhaustive_optimum(distance, 3)
    result = deterministic_pam(distance, k=3)
    assert optimum == 21.0
    assert result.objective == optimum


def test_tiny_line_matches_exhaustive_optimum() -> None:
    points = np.array([[0.0], [1.0], [9.0], [10.0]])
    distance = DistanceMatrix(
        values=cdist(points, points, metric="euclidean"),
        sample_ids=("a", "b", "c", "d"),
        metric_id="golden_line",
    )
    optimum, _ = exhaustive_optimum(distance, 2)
    result = deterministic_pam(distance, k=2)
    assert result.objective == optimum == 2.0
    assert set(result.labels) == {0, 1}


def test_duplicate_points_never_produce_an_empty_output_cluster() -> None:
    distance = DistanceMatrix(
        values=np.zeros((4, 4)),
        sample_ids=("z", "a", "m", "b"),
        metric_id="all_zero",
    )
    result = deterministic_pam(distance, k=2)
    assert result.medoid_ids == ("a", "b")
    assert set(result.labels) == {0, 1}
    assert result.objective == 0.0


def test_objective_trace_is_non_increasing() -> None:
    points = np.array([[0.0], [2.0], [3.0], [20.0], [21.0], [40.0]])
    distance = DistanceMatrix(
        values=cdist(points, points),
        sample_ids=tuple(f"s{index}" for index in range(len(points))),
        metric_id="trace",
    )
    result = deterministic_pam(distance, k=3)
    assert all(
        later <= earlier + 1.0e-12
        for earlier, later in zip(
            result.objective_trace, result.objective_trace[1:], strict=False
        )
    )
    assert result.objective_trace[-1] == result.objective


def test_row_permutation_preserves_medoid_ids_and_assignment_mapping() -> None:
    points = np.array([[0.0], [1.0], [9.0], [10.0], [30.0]])
    ids = ("s3", "s1", "s5", "s2", "s4")
    values = cdist(points, points)
    original = DistanceMatrix(values=values, sample_ids=ids, metric_id="line")
    permutation = np.array([3, 0, 4, 1, 2])
    permuted = DistanceMatrix(
        values=values[np.ix_(permutation, permutation)],
        sample_ids=tuple(np.asarray(ids)[permutation]),
        metric_id="line",
    )
    first = deterministic_pam(original, k=2)
    second = deterministic_pam(permuted, k=2)
    assert first.medoid_ids == second.medoid_ids
    assert dict(first.assignments_by_sample) == dict(second.assignments_by_sample)
    assert first.objective == second.objective


def test_hybrid_endpoints_and_pure_distances_produce_identical_pam_results() -> None:
    value = DistanceMatrix(
        values=np.array(
            [[0.0, 2.0, 8.0, 9.0], [2.0, 0.0, 7.0, 8.0], [8.0, 7.0, 0.0, 1.0], [9.0, 8.0, 1.0, 0.0]]
        ),
        sample_ids=("s1", "s2", "s3", "s4"),
        metric_id="value",
    )
    relation = DistanceMatrix(
        values=np.array(
            [[0.0, 1.0, 5.0, 6.0], [1.0, 0.0, 4.0, 5.0], [5.0, 4.0, 0.0, 1.0], [6.0, 5.0, 1.0, 0.0]]
        ),
        sample_ids=value.sample_ids,
        metric_id="relation",
    )
    scales = fit_hybrid_scales(value, relation)
    value_endpoint = normalize_distance(
        value, scale=scales.value_scale, endpoint_name="value"
    )
    relation_endpoint = normalize_distance(
        relation, scale=scales.relational_scale, endpoint_name="relation"
    )
    hybrid_zero = hybrid_distance_matrix(value, relation, scales, alpha=0.0)
    hybrid_one = hybrid_distance_matrix(value, relation, scales, alpha=1.0)

    pure_value = deterministic_pam(value_endpoint, k=2)
    endpoint_value = deterministic_pam(hybrid_zero, k=2)
    pure_relation = deterministic_pam(relation_endpoint, k=2)
    endpoint_relation = deterministic_pam(hybrid_one, k=2)
    assert pure_value.medoid_ids == endpoint_value.medoid_ids
    assert pure_value.labels == endpoint_value.labels
    assert pure_value.objective == endpoint_value.objective
    assert pure_relation.medoid_ids == endpoint_relation.medoid_ids
    assert pure_relation.labels == endpoint_relation.labels
    assert pure_relation.objective == endpoint_relation.objective


@pytest.mark.parametrize("k", [0, 5, 1.5, True])
def test_invalid_k_is_rejected(k) -> None:
    distance = DistanceMatrix(
        values=np.zeros((4, 4)),
        sample_ids=("a", "b", "c", "d"),
        metric_id="zero",
    )
    with pytest.raises(ValueError, match="k must"):
        deterministic_pam(distance, k=k)  # type: ignore[arg-type]
