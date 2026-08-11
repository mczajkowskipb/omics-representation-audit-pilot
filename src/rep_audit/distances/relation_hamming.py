"""Masked weighted Hamming distance on ternary relation states."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from rep_audit.distances.validation import DistanceMatrix
from rep_audit.representations.ternary_relations import (
    TernaryRelationRepresentation,
)


def relation_hamming_distance_matrix(
    relations: TernaryRelationRepresentation,
    *,
    weights: Sequence[float] | None = None,
) -> DistanceMatrix:
    n, m = relations.states.shape
    if weights is None:
        weight_array = np.ones(m, dtype=np.float64)
    else:
        weight_array = np.asarray(weights, dtype=np.float64)
        if weight_array.shape != (m,):
            raise ValueError("weights must have one value per relation")
    if not np.isfinite(weight_array).all() or np.any(weight_array < 0.0):
        raise ValueError("weights must be finite and non-negative")
    if not np.any(weight_array > 0.0):
        raise ValueError("at least one relation weight must be positive")

    positive = weight_array > 0.0
    for sample_index in range(n):
        if not np.any(relations.observed[sample_index] & positive):
            raise ValueError(
                "sample has no observed positive-weight relations: "
                + relations.sample_ids[sample_index]
            )

    distance = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            jointly_observed = (
                relations.observed[i] & relations.observed[j] & positive
            )
            denominator = float(weight_array[jointly_observed].sum())
            if denominator <= 0.0:
                raise ValueError(
                    "samples have no jointly observed positive-weight relations: "
                    f"{relations.sample_ids[i]}, {relations.sample_ids[j]}"
                )
            disagreements = relations.states[i] != relations.states[j]
            numerator = float(
                weight_array[jointly_observed & disagreements].sum()
            )
            value = numerator / denominator
            distance[i, j] = value
            distance[j, i] = value

    return DistanceMatrix(
        values=distance,
        sample_ids=relations.sample_ids,
        metric_id="ternary_relation_hamming_masked_weighted",
    )
