"""Validated immutable precomputed-distance contract."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

from rep_audit.io.canonical_json import canonical_json_bytes


DISTANCE_TOLERANCE = 1.0e-12


@dataclass(frozen=True, slots=True)
class DistanceMatrix:
    values: np.ndarray
    sample_ids: tuple[str, ...]
    metric_id: str

    def __post_init__(self) -> None:
        values = np.array(self.values, dtype=np.dtype("<f8"), order="C", copy=True)
        sample_ids = tuple(str(item) for item in self.sample_ids)
        n = len(sample_ids)
        if values.shape != (n, n):
            raise ValueError("distance matrix must be square and match sample_ids")
        if n == 0:
            raise ValueError("distance matrix must contain at least one sample")
        if len(sample_ids) != len(set(sample_ids)):
            raise ValueError("sample_ids must be unique")
        if not np.isfinite(values).all():
            raise ValueError("distance matrix must be finite")
        if np.any(values < -DISTANCE_TOLERANCE):
            raise ValueError("distance matrix must be non-negative")
        if not np.allclose(values, values.T, rtol=0.0, atol=DISTANCE_TOLERANCE):
            raise ValueError("distance matrix must be symmetric")
        if not np.allclose(
            np.diag(values), 0.0, rtol=0.0, atol=DISTANCE_TOLERANCE
        ):
            raise ValueError("distance matrix diagonal must be zero")
        metric_id = str(self.metric_id)
        if not metric_id or metric_id.strip() != metric_id:
            raise ValueError("metric_id must be non-empty")
        values[values < 0.0] = 0.0
        np.fill_diagonal(values, 0.0)
        values.flags.writeable = False
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "sample_ids", sample_ids)
        object.__setattr__(self, "metric_id", metric_id)

    def fingerprint(self) -> str:
        header = canonical_json_bytes(
            {
                "schema": "DistanceMatrix/v1",
                "metric_id": self.metric_id,
                "sample_ids": self.sample_ids,
                "shape": self.values.shape,
                "dtype": self.values.dtype.str,
            }
        )
        digest = hashlib.sha256(header)
        digest.update(self.values.tobytes(order="C"))
        return digest.hexdigest()


def require_same_samples(first: DistanceMatrix, second: DistanceMatrix) -> None:
    if first.sample_ids != second.sample_ids:
        raise ValueError("distance matrices must have identical ordered sample_ids")
