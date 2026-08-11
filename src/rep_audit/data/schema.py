"""Strict label-free dataset contract."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np

from rep_audit.io.canonical_json import canonical_json_bytes


def _normalize_ids(values: Sequence[object], *, kind: str) -> tuple[str, ...]:
    normalized = tuple(str(value) for value in values)
    if any(not value or value.strip() != value for value in normalized):
        raise ValueError(f"{kind} IDs must be non-empty and have no edge whitespace")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{kind} IDs must be unique")
    return normalized


def _nonempty_identifier(value: object, *, name: str) -> str:
    normalized = str(value)
    if not normalized or normalized.strip() != normalized:
        raise ValueError(f"{name} must be a non-empty stable identifier")
    return normalized


@dataclass(frozen=True, slots=True)
class DatasetBundle:
    """An immutable samples-by-features matrix with no evaluation labels.

    NaN values are allowed as explicit missing measurements. Positive and
    negative infinity are rejected rather than silently converted or imputed.
    """

    X: np.ndarray
    sample_ids: tuple[str, ...]
    feature_ids: tuple[str, ...]
    dataset_id: str
    platform_id: str
    cohort_id: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        raw = np.asarray(self.X)
        if raw.ndim != 2:
            raise ValueError("X must be a two-dimensional samples-by-features matrix")
        if raw.dtype == np.bool_ or not np.issubdtype(raw.dtype, np.number):
            raise TypeError("X must contain numeric, non-boolean values")
        if raw.shape[0] == 0 or raw.shape[1] == 0:
            raise ValueError("X must contain at least one sample and one feature")

        matrix = np.array(raw, dtype=np.dtype("<f8"), order="C", copy=True)
        if np.isinf(matrix).any():
            raise ValueError("X must not contain positive or negative infinity")
        matrix[np.isnan(matrix)] = np.nan

        sample_ids = _normalize_ids(self.sample_ids, kind="sample")
        feature_ids = _normalize_ids(self.feature_ids, kind="feature")
        if len(sample_ids) != matrix.shape[0]:
            raise ValueError("len(sample_ids) must equal the number of X rows")
        if len(feature_ids) != matrix.shape[1]:
            raise ValueError("len(feature_ids) must equal the number of X columns")

        normalized_metadata: dict[str, str] = {}
        for key, value in dict(self.metadata).items():
            key_text = _nonempty_identifier(key, name="metadata key")
            normalized_metadata[key_text] = str(value)

        matrix.flags.writeable = False
        object.__setattr__(self, "X", matrix)
        object.__setattr__(self, "sample_ids", sample_ids)
        object.__setattr__(self, "feature_ids", feature_ids)
        object.__setattr__(
            self, "dataset_id", _nonempty_identifier(self.dataset_id, name="dataset_id")
        )
        object.__setattr__(
            self, "platform_id", _nonempty_identifier(self.platform_id, name="platform_id")
        )
        object.__setattr__(
            self, "cohort_id", _nonempty_identifier(self.cohort_id, name="cohort_id")
        )
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(sorted(normalized_metadata.items()))),
        )

    @property
    def shape(self) -> tuple[int, int]:
        return self.X.shape

    def fingerprint(self) -> str:
        """Hash identifiers, metadata, shape, dtype, and canonical matrix bytes."""

        header = {
            "schema": "DatasetBundle/v1",
            "dataset_id": self.dataset_id,
            "platform_id": self.platform_id,
            "cohort_id": self.cohort_id,
            "sample_ids": self.sample_ids,
            "feature_ids": self.feature_ids,
            "metadata": dict(self.metadata),
            "shape": self.X.shape,
            "dtype": self.X.dtype.str,
        }
        digest = hashlib.sha256(canonical_json_bytes(header))
        digest.update(self.X.tobytes(order="C"))
        return digest.hexdigest()
