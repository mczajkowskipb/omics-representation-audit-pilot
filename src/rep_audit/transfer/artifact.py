"""Serializable source-fitted transfer artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from rep_audit.audit.diagnostics import FittedSourceAudit
from rep_audit.audit.distances import method_family
from rep_audit.data.schema import DatasetBundle
from rep_audit.io.canonical_json import (
    atomic_write_bytes,
    canonical_json_bytes,
    sha256_bytes,
)
from rep_audit.representations.ranks import average_rank_encode
from rep_audit.representations.ternary_relations import encode_ternary_relations


def feature_schema_sha256(feature_ids: tuple[str, ...]) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {"schema": "FeatureSchema/v1", "feature_ids": tuple(feature_ids)}
        )
    )


def _alpha(method_id: str) -> float | None:
    if not method_id.startswith("H_EUC_PAIR_A"):
        return None
    return int(method_id.split("_A", 1)[1].split("_", 1)[0]) / 100.0


@dataclass(frozen=True, slots=True)
class FrozenMethodArtifact:
    method_id: str
    family: str
    medoid_ids: tuple[str, ...]
    selected_feature_ids: tuple[str, ...]
    source_medians: tuple[float, ...]
    scale_denominators: tuple[float, ...]
    medoid_value_profiles: tuple[tuple[float, ...], ...]
    medoid_rank_profiles: tuple[tuple[float, ...], ...]
    relation_pairs: tuple[tuple[str, str], ...]
    relation_weights: tuple[float, ...]
    medoid_relation_states: tuple[tuple[int, ...], ...]
    relation_margin: float
    value_scale: float | None
    relational_scale: float | None
    alpha: float | None
    cluster_radius_q95: tuple[float, ...]
    confidence_q05: float
    minimum_feature_coverage: float = 0.80
    minimum_relation_coverage: float = 0.80

    def __post_init__(self) -> None:
        if self.family != method_family(self.method_id):
            raise ValueError("method family mismatch")
        k = len(self.medoid_ids)
        p = len(self.selected_feature_ids)
        if k < 2 or len(set(self.medoid_ids)) != k:
            raise ValueError("transfer requires unique medoids and k >= 2")
        if p < 2 or len(set(self.selected_feature_ids)) != p:
            raise ValueError("transfer requires at least two unique features")
        if len(self.source_medians) != p or len(self.scale_denominators) != p:
            raise ValueError("preprocessing vectors must align with selected features")
        if len(self.medoid_value_profiles) != k or len(self.medoid_rank_profiles) != k:
            raise ValueError("medoid profiles must align with medoids")
        if any(len(row) != p for row in self.medoid_value_profiles):
            raise ValueError("medoid value profile width mismatch")
        if any(len(row) != p for row in self.medoid_rank_profiles):
            raise ValueError("medoid rank profile width mismatch")
        m = len(self.relation_pairs)
        if len(self.relation_weights) != m:
            raise ValueError("relation weights must align with relation pairs")
        if len(self.medoid_relation_states) not in {0, k}:
            raise ValueError("medoid relation states must be absent or align with medoids")
        if any(len(row) != m for row in self.medoid_relation_states):
            raise ValueError("medoid relation-state width mismatch")
        if len(self.cluster_radius_q95) != k:
            raise ValueError("one source radius is required per cluster")
        numeric = (
            *self.source_medians,
            *self.scale_denominators,
            *self.cluster_radius_q95,
            self.confidence_q05,
            self.minimum_feature_coverage,
            self.minimum_relation_coverage,
        )
        if not np.isfinite(numeric).all():
            raise ValueError("frozen transfer values must be finite")
        if any(value <= 0.0 for value in self.scale_denominators):
            raise ValueError("source scale denominators must be positive")
        if not 0.0 <= self.confidence_q05 <= 1.0:
            raise ValueError("confidence threshold must be in [0,1]")
        if self.family == "HYBRID" and (
            self.alpha is None
            or self.value_scale is None
            or self.relational_scale is None
        ):
            raise ValueError("hybrid transfer is missing frozen endpoint scales")

    @property
    def k(self) -> int:
        return len(self.medoid_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "FrozenMethodArtifact/v1",
            "method_id": self.method_id,
            "family": self.family,
            "medoid_ids": self.medoid_ids,
            "selected_feature_ids": self.selected_feature_ids,
            "source_medians": self.source_medians,
            "scale_denominators": self.scale_denominators,
            "medoid_value_profiles": self.medoid_value_profiles,
            "medoid_rank_profiles": self.medoid_rank_profiles,
            "relation_pairs": self.relation_pairs,
            "relation_weights": self.relation_weights,
            "medoid_relation_states": self.medoid_relation_states,
            "relation_margin": self.relation_margin,
            "value_scale": self.value_scale,
            "relational_scale": self.relational_scale,
            "alpha": self.alpha,
            "rejection": {
                "cluster_radius": "source_cluster_distance_q95",
                "cluster_radius_q95": self.cluster_radius_q95,
                "confidence": "source_normalized_nearest_gap_q05",
                "confidence_q05": self.confidence_q05,
                "minimum_feature_coverage": self.minimum_feature_coverage,
                "minimum_relation_coverage": self.minimum_relation_coverage,
            },
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "FrozenMethodArtifact":
        if value.get("schema") != "FrozenMethodArtifact/v1":
            raise ValueError("not a FrozenMethodArtifact/v1")
        rejection = value["rejection"]
        return cls(
            method_id=str(value["method_id"]),
            family=str(value["family"]),
            medoid_ids=tuple(str(item) for item in value["medoid_ids"]),
            selected_feature_ids=tuple(str(item) for item in value["selected_feature_ids"]),
            source_medians=tuple(float(item) for item in value["source_medians"]),
            scale_denominators=tuple(float(item) for item in value["scale_denominators"]),
            medoid_value_profiles=tuple(
                tuple(float(item) for item in row) for row in value["medoid_value_profiles"]
            ),
            medoid_rank_profiles=tuple(
                tuple(float(item) for item in row) for row in value["medoid_rank_profiles"]
            ),
            relation_pairs=tuple(
                (str(row[0]), str(row[1])) for row in value["relation_pairs"]
            ),
            relation_weights=tuple(float(item) for item in value["relation_weights"]),
            medoid_relation_states=tuple(
                tuple(int(item) for item in row)
                for row in value["medoid_relation_states"]
            ),
            relation_margin=float(value["relation_margin"]),
            value_scale=(None if value["value_scale"] is None else float(value["value_scale"])),
            relational_scale=(
                None
                if value["relational_scale"] is None
                else float(value["relational_scale"])
            ),
            alpha=None if value["alpha"] is None else float(value["alpha"]),
            cluster_radius_q95=tuple(float(item) for item in rejection["cluster_radius_q95"]),
            confidence_q05=float(rejection["confidence_q05"]),
            minimum_feature_coverage=float(rejection["minimum_feature_coverage"]),
            minimum_relation_coverage=float(rejection["minimum_relation_coverage"]),
        )


@dataclass(frozen=True, slots=True)
class FrozenTransferSet:
    source_dataset_id: str
    source_fingerprint: str
    target_dataset_id: str
    target_feature_schema_sha256: str
    common_feature_count: int
    source_audit_sha256: str
    preprocessing_sha256: str
    methods: tuple[FrozenMethodArtifact, ...]

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.methods, key=lambda item: item.method_id))
        if ordered != self.methods or len({item.method_id for item in ordered}) != len(ordered):
            raise ValueError("frozen methods must be unique and sorted")
        if self.common_feature_count < 2:
            raise ValueError("transfer requires at least two common features")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "FrozenTransferSet/v1",
            "fitted_values": "source_only",
            "target_contribution": "feature_ids_only",
            "source_dataset_id": self.source_dataset_id,
            "source_fingerprint": self.source_fingerprint,
            "target_dataset_id": self.target_dataset_id,
            "target_feature_schema_sha256": self.target_feature_schema_sha256,
            "common_feature_count": self.common_feature_count,
            "source_audit_sha256": self.source_audit_sha256,
            "preprocessing_sha256": self.preprocessing_sha256,
            "methods": [item.to_dict() for item in self.methods],
            "assignment_engine": "nearest_frozen_source_medoid",
            "tie_break": "sorted_source_medoid_id",
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def sha256(self) -> str:
        return sha256_bytes(self.to_json_bytes())

    def save(self, path: str | Path) -> None:
        atomic_write_bytes(path, self.to_json_bytes())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "FrozenTransferSet":
        if value.get("schema") != "FrozenTransferSet/v1":
            raise ValueError("not a FrozenTransferSet/v1")
        return cls(
            source_dataset_id=str(value["source_dataset_id"]),
            source_fingerprint=str(value["source_fingerprint"]),
            target_dataset_id=str(value["target_dataset_id"]),
            target_feature_schema_sha256=str(value["target_feature_schema_sha256"]),
            common_feature_count=int(value["common_feature_count"]),
            source_audit_sha256=str(value["source_audit_sha256"]),
            preprocessing_sha256=str(value["preprocessing_sha256"]),
            methods=tuple(FrozenMethodArtifact.from_dict(item) for item in value["methods"]),
        )

    @classmethod
    def load(cls, path: str | Path) -> "FrozenTransferSet":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def method_by_id(self, method_id: str) -> FrozenMethodArtifact:
        for method in self.methods:
            if method.method_id == method_id:
                return method
        raise KeyError(method_id)


def _source_thresholds(
    distance: np.ndarray,
    sample_ids: tuple[str, ...],
    medoid_ids: tuple[str, ...],
    assignments: tuple[int, ...],
) -> tuple[tuple[float, ...], float]:
    index = {sample_id: position for position, sample_id in enumerate(sample_ids)}
    medoid_indices = np.asarray([index[item] for item in medoid_ids], dtype=int)
    nearest_matrix = distance[:, medoid_indices]
    radii: list[float] = []
    for cluster in range(len(medoid_ids)):
        rows = np.flatnonzero(np.asarray(assignments) == cluster)
        radii.append(
            float(np.quantile(nearest_matrix[rows, cluster], 0.95, method="linear"))
        )
    ordered = np.sort(nearest_matrix, axis=1)
    confidence = (ordered[:, 1] - ordered[:, 0]) / np.maximum(ordered[:, 1], 1.0e-15)
    return tuple(radii), float(np.quantile(confidence, 0.05, method="linear"))


def freeze_transfer_set(
    source: DatasetBundle,
    target_feature_ids: tuple[str, ...],
    target_dataset_id: str,
    fitted: FittedSourceAudit,
    *,
    minimum_feature_coverage: float = 0.80,
    minimum_relation_coverage: float = 0.80,
) -> FrozenTransferSet:
    """Freeze all candidate methods before any target labels are available."""

    report = fitted.report
    representations = fitted.representations
    if source.fingerprint() != report.source_fingerprint:
        raise ValueError("source does not match the fitted audit")
    selected = representations.preprocessing.selected_feature_ids
    target_set = set(str(item) for item in target_feature_ids)
    # Features absent from the target platform remain explicit missing values.
    # Cross-platform real transfers normally predeclare a common universe;
    # simulated strong shift deliberately tests the frozen missing-data policy.
    values = representations.preprocessing.transform(source).matrix
    ranks = average_rank_encode(source, feature_ids=selected)

    relation_states: np.ndarray | None = None
    relation_pairs: tuple[tuple[str, str], ...] = ()
    relation_weights: tuple[float, ...] = ()
    relation_margin = 0.0
    if representations.relation_screen is not None:
        screen = representations.relation_screen
        relation_pairs = screen.relation_pairs
        relation_weights = screen.weights
        relation_margin = screen.margin
        relation_states = encode_ternary_relations(
            ranks, relation_pairs, margin=relation_margin
        ).states

    source_id_index = {sample_id: index for index, sample_id in enumerate(source.sample_ids)}
    methods: list[FrozenMethodArtifact] = []
    for method_result in report.methods:
        medoid_indices = [source_id_index[item] for item in method_result.medoid_ids]
        radii, confidence = _source_thresholds(
            representations.distances[method_result.method_id].values,
            source.sample_ids,
            method_result.medoid_ids,
            method_result.assignments,
        )
        uses_pairs = method_result.method_id == "R_PAIR_PAM" or method_result.family == "HYBRID"
        hybrid = representations.hybrid_scales
        methods.append(
            FrozenMethodArtifact(
                method_id=method_result.method_id,
                family=method_result.family,
                medoid_ids=method_result.medoid_ids,
                selected_feature_ids=selected,
                source_medians=representations.preprocessing.source_medians,
                scale_denominators=representations.preprocessing.scale_denominators,
                medoid_value_profiles=tuple(
                    tuple(float(item) for item in values[index]) for index in medoid_indices
                ),
                medoid_rank_profiles=tuple(
                    tuple(float(item) for item in ranks.q[index]) for index in medoid_indices
                ),
                relation_pairs=relation_pairs if uses_pairs else (),
                relation_weights=relation_weights if uses_pairs else (),
                medoid_relation_states=(
                    ()
                    if not uses_pairs or relation_states is None
                    else tuple(
                        tuple(int(item) for item in relation_states[index])
                        for index in medoid_indices
                    )
                ),
                relation_margin=relation_margin,
                value_scale=(
                    hybrid.value_scale
                    if method_result.family == "HYBRID" and hybrid is not None
                    else None
                ),
                relational_scale=(
                    hybrid.relational_scale
                    if method_result.family == "HYBRID" and hybrid is not None
                    else None
                ),
                alpha=_alpha(method_result.method_id),
                cluster_radius_q95=radii,
                confidence_q05=confidence,
                minimum_feature_coverage=float(minimum_feature_coverage),
                minimum_relation_coverage=float(minimum_relation_coverage),
            )
        )
    common = set(source.feature_ids) & target_set
    return FrozenTransferSet(
        source_dataset_id=source.dataset_id,
        source_fingerprint=source.fingerprint(),
        target_dataset_id=str(target_dataset_id),
        target_feature_schema_sha256=feature_schema_sha256(tuple(target_feature_ids)),
        common_feature_count=len(common),
        source_audit_sha256=report.sha256(),
        preprocessing_sha256=representations.preprocessing.sha256(),
        methods=tuple(sorted(methods, key=lambda item: item.method_id)),
    )
