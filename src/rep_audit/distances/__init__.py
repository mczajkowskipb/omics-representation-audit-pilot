"""Matched precomputed distances."""

from rep_audit.distances.footrule import footrule_distance_matrix
from rep_audit.distances.hybrid import (
    HybridScaleArtifact,
    fit_hybrid_scales,
    hybrid_distance_matrix,
    normalize_distance,
)
from rep_audit.distances.relation_hamming import relation_hamming_distance_matrix
from rep_audit.distances.validation import DistanceMatrix
from rep_audit.distances.value import (
    correlation_distance_matrix,
    euclidean_distance_matrix,
)

__all__ = [
    "DistanceMatrix",
    "HybridScaleArtifact",
    "correlation_distance_matrix",
    "euclidean_distance_matrix",
    "fit_hybrid_scales",
    "footrule_distance_matrix",
    "hybrid_distance_matrix",
    "normalize_distance",
    "relation_hamming_distance_matrix",
]
