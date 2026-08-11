"""Normalized Spearman Footrule distance on average ranks."""

from __future__ import annotations

import numpy as np

from rep_audit.distances.validation import DistanceMatrix
from rep_audit.representations.ranks import RankRepresentation


def footrule_distance_matrix(ranks: RankRepresentation) -> DistanceMatrix:
    if not ranks.observed.all():
        raise ValueError(
            "Footrule requires a complete frozen feature universe in PILOT-005"
        )
    n, p = ranks.q.shape
    if p < 2:
        raise ValueError("Footrule requires at least two features")
    raw_average_ranks = ranks.q * float(p - 1) + 1.0
    denominator = float((p * p) // 2)
    distance = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            value = float(
                np.abs(raw_average_ranks[i] - raw_average_ranks[j]).sum()
                / denominator
            )
            distance[i, j] = value
            distance[j, i] = value
    distance = np.clip(distance, 0.0, 1.0)
    return DistanceMatrix(
        values=distance,
        sample_ids=ranks.sample_ids,
        metric_id="rank_footrule_normalized",
    )
