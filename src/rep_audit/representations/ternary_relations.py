"""Ternary relative-order states with explicit missingness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from rep_audit.representations.ranks import RankRepresentation


RelationPair = tuple[str, str]


@dataclass(frozen=True, slots=True)
class TernaryRelationRepresentation:
    states: np.ndarray
    observed: np.ndarray
    sample_ids: tuple[str, ...]
    relation_pairs: tuple[RelationPair, ...]
    margin: float

    def __post_init__(self) -> None:
        states = np.array(self.states, dtype=np.int8, order="C", copy=True)
        observed = np.array(self.observed, dtype=bool, order="C", copy=True)
        expected = (len(self.sample_ids), len(self.relation_pairs))
        if states.shape != expected or observed.shape != expected:
            raise ValueError("relation arrays must match sample and relation IDs")
        if not np.isin(states[observed], (-1, 0, 1)).all():
            raise ValueError("observed relation states must be -1, 0, or +1")
        if not 0.0 <= float(self.margin) <= 1.0:
            raise ValueError("margin must be in [0, 1]")
        states[~observed] = 0
        states.flags.writeable = False
        observed.flags.writeable = False
        object.__setattr__(self, "states", states)
        object.__setattr__(self, "observed", observed)
        object.__setattr__(self, "sample_ids", tuple(self.sample_ids))
        object.__setattr__(self, "relation_pairs", tuple(self.relation_pairs))
        object.__setattr__(self, "margin", float(self.margin))

    @property
    def relation_ids(self) -> tuple[str, ...]:
        return tuple(f"{left}>{right}" for left, right in self.relation_pairs)


def encode_ternary_relations(
    ranks: RankRepresentation,
    relation_pairs: Sequence[tuple[object, object]],
    *,
    margin: float,
) -> TernaryRelationRepresentation:
    """Encode ordered pairs as ``-1``, ``0``, or ``+1``.

    The ordered pair ``(left, right)`` receives ``+1`` only when
    ``q_left - q_right > margin`` and ``-1`` only below ``-margin``.
    Equality to the margin is the zero state.
    """

    margin = float(margin)
    if not np.isfinite(margin) or not 0.0 <= margin <= 1.0:
        raise ValueError("margin must be finite and in [0, 1]")
    pairs = tuple((str(left), str(right)) for left, right in relation_pairs)
    if len(pairs) == 0:
        raise ValueError("at least one relation pair is required")
    if len(pairs) != len(set(pairs)):
        raise ValueError("relation pairs must be unique")
    if any(left == right for left, right in pairs):
        raise ValueError("self-relations are not allowed")

    feature_index = {
        feature_id: index for index, feature_id in enumerate(ranks.feature_ids)
    }
    unknown = sorted(
        {
            feature_id
            for pair in pairs
            for feature_id in pair
            if feature_id not in feature_index
        }
    )
    if unknown:
        raise ValueError("unknown relation features: " + ", ".join(unknown[:10]))

    states = np.zeros((len(ranks.sample_ids), len(pairs)), dtype=np.int8)
    observed = np.zeros_like(states, dtype=bool)
    for relation_index, (left, right) in enumerate(pairs):
        left_index = feature_index[left]
        right_index = feature_index[right]
        pair_observed = ranks.observed[:, left_index] & ranks.observed[:, right_index]
        difference = ranks.q[:, left_index] - ranks.q[:, right_index]
        states[pair_observed & (difference > margin), relation_index] = 1
        states[pair_observed & (difference < -margin), relation_index] = -1
        observed[:, relation_index] = pair_observed

    return TernaryRelationRepresentation(
        states=states,
        observed=observed,
        sample_ids=ranks.sample_ids,
        relation_pairs=pairs,
        margin=margin,
    )
