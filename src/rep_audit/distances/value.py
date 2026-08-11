"""Value-representation distances."""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import pdist, squareform

from rep_audit.distances.validation import DistanceMatrix
from rep_audit.preprocessing.artifact import PreprocessedValues


def euclidean_distance_matrix(values: PreprocessedValues) -> DistanceMatrix:
    matrix = squareform(pdist(values.matrix, metric="euclidean"))
    return DistanceMatrix(
        values=matrix,
        sample_ids=values.sample_ids,
        metric_id="value_euclidean",
    )


def correlation_distance_matrix(values: PreprocessedValues) -> DistanceMatrix:
    matrix = values.matrix
    centered = matrix - matrix.mean(axis=1, keepdims=True)
    norms = np.linalg.norm(centered, axis=1)
    constant = np.flatnonzero(norms <= 0.0)
    if constant.size:
        ids = [values.sample_ids[index] for index in constant]
        raise ValueError(
            "correlation distance is undefined for constant sample profiles: "
            + ", ".join(ids[:10])
        )
    similarity = (centered @ centered.T) / np.outer(norms, norms)
    similarity = np.clip(similarity, -1.0, 1.0)
    distance = 1.0 - similarity
    np.fill_diagonal(distance, 0.0)
    return DistanceMatrix(
        values=distance,
        sample_ids=values.sample_ids,
        metric_id="value_correlation",
    )
