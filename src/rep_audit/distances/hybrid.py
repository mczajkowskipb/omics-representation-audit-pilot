"""Source-fitted distance normalization and simple hybrid distance."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from rep_audit.distances.validation import DistanceMatrix, require_same_samples
from rep_audit.io.canonical_json import canonical_json_bytes, sha256_bytes


def fit_source_distance_scale(distance: DistanceMatrix) -> float:
    upper = distance.values[np.triu_indices(len(distance.sample_ids), k=1)]
    nonzero = upper[upper > 0.0]
    if nonzero.size == 0:
        raise ValueError(
            f"cannot fit a positive source scale for metric {distance.metric_id}"
        )
    scale = float(np.median(nonzero))
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError("source distance scale must be positive and finite")
    return scale


@dataclass(frozen=True, slots=True)
class HybridScaleArtifact:
    value_metric_id: str
    relational_metric_id: str
    value_distance_sha256: str
    relational_distance_sha256: str
    value_scale: float
    relational_scale: float
    sample_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not np.isfinite(self.value_scale) or self.value_scale <= 0.0:
            raise ValueError("value_scale must be positive and finite")
        if not np.isfinite(self.relational_scale) or self.relational_scale <= 0.0:
            raise ValueError("relational_scale must be positive and finite")
        object.__setattr__(self, "sample_ids", tuple(self.sample_ids))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "HybridScaleArtifact/v1",
            "source_only": True,
            "sample_ids": self.sample_ids,
            "value": {
                "metric_id": self.value_metric_id,
                "distance_sha256": self.value_distance_sha256,
                "scale": self.value_scale,
            },
            "relational": {
                "metric_id": self.relational_metric_id,
                "distance_sha256": self.relational_distance_sha256,
                "scale": self.relational_scale,
            },
            "scale_definition": "median_nonzero_strict_upper_triangle",
        }

    def sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.to_dict()))


def fit_hybrid_scales(
    value_source: DistanceMatrix,
    relational_source: DistanceMatrix,
) -> HybridScaleArtifact:
    require_same_samples(value_source, relational_source)
    return HybridScaleArtifact(
        value_metric_id=value_source.metric_id,
        relational_metric_id=relational_source.metric_id,
        value_distance_sha256=value_source.fingerprint(),
        relational_distance_sha256=relational_source.fingerprint(),
        value_scale=fit_source_distance_scale(value_source),
        relational_scale=fit_source_distance_scale(relational_source),
        sample_ids=value_source.sample_ids,
    )


def normalize_distance(
    distance: DistanceMatrix, *, scale: float, endpoint_name: str
) -> DistanceMatrix:
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError("distance scale must be positive and finite")
    return DistanceMatrix(
        values=distance.values / float(scale),
        sample_ids=distance.sample_ids,
        metric_id=f"normalized_{endpoint_name}",
    )


def hybrid_distance_matrix(
    value_source: DistanceMatrix,
    relational_source: DistanceMatrix,
    scales: HybridScaleArtifact,
    *,
    alpha: float,
) -> DistanceMatrix:
    require_same_samples(value_source, relational_source)
    if value_source.sample_ids != scales.sample_ids:
        raise ValueError("distance matrices do not match the source scale artifact")
    if value_source.fingerprint() != scales.value_distance_sha256:
        raise ValueError("value distance differs from the source-fitted artifact")
    if relational_source.fingerprint() != scales.relational_distance_sha256:
        raise ValueError("relational distance differs from the source-fitted artifact")
    alpha = float(alpha)
    if not np.isfinite(alpha) or not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be finite and in [0, 1]")
    value_normalized = value_source.values / scales.value_scale
    relational_normalized = relational_source.values / scales.relational_scale
    hybrid = (1.0 - alpha) * value_normalized + alpha * relational_normalized
    return DistanceMatrix(
        values=hybrid,
        sample_ids=value_source.sample_ids,
        metric_id=f"hybrid_value_relation_alpha_{alpha:.2f}",
    )
