"""Evaluation-only label contract.

This module is intentionally outside the data, preprocessing, representation,
distance, clustering, and future audit namespaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence


def _ids(values: Sequence[object]) -> tuple[str, ...]:
    normalized = tuple(str(value) for value in values)
    if any(not value or value.strip() != value for value in normalized):
        raise ValueError("sample IDs must be non-empty and have no edge whitespace")
    if len(normalized) != len(set(normalized)):
        raise ValueError("sample IDs in evaluation labels must be unique")
    return normalized


@dataclass(frozen=True, slots=True)
class EvaluationLabels:
    """Labels that may be consumed only after assignments are frozen."""

    dataset_id: str
    sample_ids: tuple[str, ...]
    values: tuple[str, ...]
    label_name: str = "class_label"

    def __post_init__(self) -> None:
        dataset_id = str(self.dataset_id)
        label_name = str(self.label_name)
        if not dataset_id or dataset_id.strip() != dataset_id:
            raise ValueError("dataset_id must be a non-empty stable identifier")
        if not label_name or label_name.strip() != label_name:
            raise ValueError("label_name must be non-empty")
        sample_ids = _ids(self.sample_ids)
        values = tuple(str(value) for value in self.values)
        if len(sample_ids) != len(values):
            raise ValueError("sample_ids and values must have equal length")
        object.__setattr__(self, "dataset_id", dataset_id)
        object.__setattr__(self, "sample_ids", sample_ids)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "label_name", label_name)

    def as_mapping(self) -> Mapping[str, str]:
        return MappingProxyType(dict(zip(self.sample_ids, self.values, strict=True)))
