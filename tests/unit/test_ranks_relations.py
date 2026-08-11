from __future__ import annotations

import numpy as np
import pytest

from rep_audit.data.schema import DatasetBundle
from rep_audit.representations.ranks import average_rank_encode
from rep_audit.representations.ternary_relations import encode_ternary_relations


def bundle(X, feature_ids=("a", "b", "c", "d")) -> DatasetBundle:
    X = np.asarray(X, dtype=float)
    return DatasetBundle(
        X=X,
        sample_ids=tuple(f"s{i + 1}" for i in range(X.shape[0])),
        feature_ids=feature_ids,
        dataset_id="toy",
        platform_id="sim",
        cohort_id="source",
    )


def test_average_ranks_preserve_ties() -> None:
    ranks = average_rank_encode(bundle([[1.0, 1.0, 3.0, 2.0]]))
    expected = np.array([[1.0 / 6.0, 1.0 / 6.0, 1.0, 2.0 / 3.0]])
    assert np.allclose(ranks.q, expected)
    assert ranks.q[0, 0] == ranks.q[0, 1]


def test_tie_behavior_is_invariant_to_feature_column_permutation() -> None:
    original = bundle([[1.0, 1.0, 3.0, 2.0]])
    order = np.array([1, 3, 0, 2])
    permuted = bundle(
        original.X[:, order],
        feature_ids=tuple(np.asarray(original.feature_ids)[order]),
    )
    first = average_rank_encode(original)
    second = average_rank_encode(permuted)
    aligned = np.array(
        [second.q[0, second.feature_ids.index(feature)] for feature in first.feature_ids]
    )
    assert np.allclose(first.q[0], aligned)


def test_strictly_monotone_transformation_leaves_ranks_unchanged() -> None:
    source = bundle([[0.0, 0.5, 2.0, 5.0], [4.0, 2.0, 2.0, -1.0]])
    transformed = bundle(np.exp(source.X), feature_ids=source.feature_ids)
    assert np.array_equal(
        average_rank_encode(source).q,
        average_rank_encode(transformed).q,
    )


def test_rank_missingness_is_explicit_and_not_a_tie() -> None:
    ranks = average_rank_encode(bundle([[1.0, np.nan, 3.0, 2.0]]))
    assert not ranks.observed[0, 1]
    assert ranks.q[0, 1] == 0.0
    assert np.allclose(ranks.q[0, [0, 2, 3]], [0.0, 1.0, 0.5])


def test_ternary_states_margin_and_reverse_pair() -> None:
    ranks = average_rank_encode(
        bundle([[1.0, 2.0, 2.0, 4.0], [3.0, 2.0, 1.0, 4.0]])
    )
    relations = encode_ternary_relations(
        ranks,
        (("a", "b"), ("b", "a"), ("b", "c")),
        margin=0.0,
    )
    assert relations.states.tolist() == [[-1, 1, 0], [1, -1, 1]]
    assert relations.observed.all()
    assert relations.relation_ids == ("a>b", "b>a", "b>c")


def test_difference_equal_to_margin_is_zero() -> None:
    ranks = average_rank_encode(
        bundle([[1.0, 2.0, 3.0]], feature_ids=("a", "b", "c"))
    )
    relations = encode_ternary_relations(ranks, (("b", "a"),), margin=0.5)
    assert relations.states[0, 0] == 0


def test_relation_missingness_is_masked() -> None:
    ranks = average_rank_encode(
        bundle([[1.0, 2.0, np.nan, 4.0], [3.0, 2.0, 1.0, 4.0]])
    )
    relations = encode_ternary_relations(
        ranks, (("a", "c"), ("a", "b")), margin=0.0
    )
    assert relations.observed.tolist() == [[False, True], [True, True]]
    assert relations.states[0, 0] == 0


@pytest.mark.parametrize("margin", [-0.1, 1.1, np.nan])
def test_invalid_margin_is_rejected(margin) -> None:
    ranks = average_rank_encode(bundle([[1.0, 2.0, 3.0, 4.0]]))
    with pytest.raises(ValueError, match="margin"):
        encode_ternary_relations(ranks, (("a", "b"),), margin=margin)


def test_unknown_duplicate_and_self_relations_are_rejected() -> None:
    ranks = average_rank_encode(bundle([[1.0, 2.0, 3.0, 4.0]]))
    with pytest.raises(ValueError, match="unknown"):
        encode_ternary_relations(ranks, (("a", "x"),), margin=0.0)
    with pytest.raises(ValueError, match="unique"):
        encode_ternary_relations(
            ranks, (("a", "b"), ("a", "b")), margin=0.0
        )
    with pytest.raises(ValueError, match="self"):
        encode_ternary_relations(ranks, (("a", "a"),), margin=0.0)
