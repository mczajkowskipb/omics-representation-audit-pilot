"""Frozen source-fitted robust preprocessing artifact."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from rep_audit.data.schema import DatasetBundle
from rep_audit.io.canonical_json import (
    atomic_write_bytes,
    canonical_json_bytes,
    sha256_bytes,
)


@dataclass(frozen=True, slots=True)
class PreprocessedValues:
    """Read-only source-parameterized value representation."""

    matrix: np.ndarray
    sample_ids: tuple[str, ...]
    feature_ids: tuple[str, ...]
    artifact_sha256: str

    def __post_init__(self) -> None:
        matrix = np.array(self.matrix, dtype=np.dtype("<f8"), order="C", copy=True)
        if matrix.ndim != 2 or matrix.shape != (
            len(self.sample_ids),
            len(self.feature_ids),
        ):
            raise ValueError("preprocessed matrix dimensions do not match IDs")
        if not np.isfinite(matrix).all():
            raise ValueError("preprocessed values must be finite")
        matrix.flags.writeable = False
        object.__setattr__(self, "matrix", matrix)
        object.__setattr__(self, "sample_ids", tuple(self.sample_ids))
        object.__setattr__(self, "feature_ids", tuple(self.feature_ids))


@dataclass(frozen=True, slots=True)
class SourcePreprocessingArtifact:
    schema_version: int
    protocol_version: str
    source_dataset_id: str
    source_cohort_id: str
    source_fingerprint: str
    selection_universe_sha256: str
    selection_universe_size: int
    feature_budget: int
    selected_feature_ids: tuple[str, ...]
    source_medians: tuple[float, ...]
    source_iqrs: tuple[float, ...]
    scale_denominators: tuple[float, ...]
    iqr_fallback: tuple[bool, ...]
    mad_scores: tuple[float, ...]
    quantile_method: str = "linear"

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported preprocessing artifact schema")
        if self.feature_budget <= 0:
            raise ValueError("feature_budget must be positive")
        if len(self.selected_feature_ids) != self.feature_budget:
            raise ValueError("selected feature count must equal feature_budget")
        if len(set(self.selected_feature_ids)) != len(self.selected_feature_ids):
            raise ValueError("selected_feature_ids must be unique")
        expected = len(self.selected_feature_ids)
        aligned = (
            self.source_medians,
            self.source_iqrs,
            self.scale_denominators,
            self.iqr_fallback,
            self.mad_scores,
        )
        if any(len(values) != expected for values in aligned):
            raise ValueError("all per-feature parameters must be aligned")
        if not all(np.isfinite(self.source_medians)):
            raise ValueError("source medians must be finite")
        if not all(np.isfinite(self.source_iqrs)):
            raise ValueError("source IQRs must be finite")
        if not all(np.isfinite(self.scale_denominators)) or not all(
            value > 0 for value in self.scale_denominators
        ):
            raise ValueError("scale denominators must be positive and finite")
        if not all(np.isfinite(self.mad_scores)):
            raise ValueError("MAD scores must be finite")
        if self.quantile_method != "linear":
            raise ValueError("PILOT-003 freezes quantile_method='linear'")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "SourcePreprocessingArtifact/v1",
            "schema_version": self.schema_version,
            "protocol_version": self.protocol_version,
            "source": {
                "dataset_id": self.source_dataset_id,
                "cohort_id": self.source_cohort_id,
                "fingerprint": self.source_fingerprint,
            },
            "selection_universe": {
                "sha256": self.selection_universe_sha256,
                "size": self.selection_universe_size,
            },
            "feature_budget": self.feature_budget,
            "selected_feature_ids": self.selected_feature_ids,
            "source_medians": self.source_medians,
            "source_iqrs": self.source_iqrs,
            "scale_denominators": self.scale_denominators,
            "iqr_fallback": self.iqr_fallback,
            "mad_scores": self.mad_scores,
            "quantile_method": self.quantile_method,
            "imputation": "source_median",
            "scaling": "source_median_iqr",
            "feature_tie_break": "feature_id",
            "source_only": True,
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def sha256(self) -> str:
        return sha256_bytes(self.to_json_bytes())

    def save(self, path: str | Path) -> None:
        atomic_write_bytes(path, self.to_json_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SourcePreprocessingArtifact":
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if value.get("schema") != "SourcePreprocessingArtifact/v1":
            raise ValueError("not a SourcePreprocessingArtifact/v1 file")
        source = value["source"]
        universe = value["selection_universe"]
        return cls(
            schema_version=int(value["schema_version"]),
            protocol_version=str(value["protocol_version"]),
            source_dataset_id=str(source["dataset_id"]),
            source_cohort_id=str(source["cohort_id"]),
            source_fingerprint=str(source["fingerprint"]),
            selection_universe_sha256=str(universe["sha256"]),
            selection_universe_size=int(universe["size"]),
            feature_budget=int(value["feature_budget"]),
            selected_feature_ids=tuple(value["selected_feature_ids"]),
            source_medians=tuple(float(item) for item in value["source_medians"]),
            source_iqrs=tuple(float(item) for item in value["source_iqrs"]),
            scale_denominators=tuple(
                float(item) for item in value["scale_denominators"]
            ),
            iqr_fallback=tuple(bool(item) for item in value["iqr_fallback"]),
            mad_scores=tuple(float(item) for item in value["mad_scores"]),
            quantile_method=str(value["quantile_method"]),
        )

    def transform(self, bundle: DatasetBundle) -> PreprocessedValues:
        feature_to_index = {
            feature_id: index for index, feature_id in enumerate(bundle.feature_ids)
        }
        missing = [
            feature_id
            for feature_id in self.selected_feature_ids
            if feature_id not in feature_to_index
        ]
        if missing:
            raise ValueError(
                "bundle is missing frozen selected features: " + ", ".join(missing[:10])
            )

        indices = [feature_to_index[item] for item in self.selected_feature_ids]
        matrix = np.array(bundle.X[:, indices], dtype=np.float64, copy=True)
        medians = np.asarray(self.source_medians, dtype=np.float64)
        scales = np.asarray(self.scale_denominators, dtype=np.float64)
        missing_values = np.isnan(matrix)
        if missing_values.any():
            matrix[missing_values] = np.broadcast_to(medians, matrix.shape)[
                missing_values
            ]
        matrix = (matrix - medians) / scales
        return PreprocessedValues(
            matrix=matrix,
            sample_ids=bundle.sample_ids,
            feature_ids=self.selected_feature_ids,
            artifact_sha256=self.sha256(),
        )
