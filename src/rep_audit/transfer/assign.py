"""Independent target assignment to frozen source medoids."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import rankdata

from rep_audit.data.schema import DatasetBundle
from rep_audit.io.canonical_json import atomic_write_bytes, canonical_json_bytes, sha256_bytes
from rep_audit.transfer.artifact import (
    FrozenMethodArtifact,
    FrozenTransferSet,
    feature_schema_sha256,
)


@dataclass(frozen=True, slots=True)
class TargetAssignment:
    sample_id: str
    forced_cluster: int
    accepted_cluster: int | None
    nearest_distance: float
    second_distance: float
    confidence: float
    feature_coverage: float
    relation_coverage: float | None
    rejection_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "forced_cluster": self.forced_cluster,
            "accepted_cluster": (
                "UNASSIGNED" if self.accepted_cluster is None else self.accepted_cluster
            ),
            "nearest_distance": self.nearest_distance,
            "second_distance": self.second_distance,
            "confidence": self.confidence,
            "feature_coverage": self.feature_coverage,
            "relation_coverage": self.relation_coverage,
            "rejection_reasons": self.rejection_reasons,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TargetAssignment":
        accepted = value["accepted_cluster"]
        return cls(
            sample_id=str(value["sample_id"]),
            forced_cluster=int(value["forced_cluster"]),
            accepted_cluster=None if accepted == "UNASSIGNED" else int(accepted),
            nearest_distance=float(value["nearest_distance"]),
            second_distance=float(value["second_distance"]),
            confidence=float(value["confidence"]),
            feature_coverage=float(value["feature_coverage"]),
            relation_coverage=(
                None
                if value["relation_coverage"] is None
                else float(value["relation_coverage"])
            ),
            rejection_reasons=tuple(str(item) for item in value["rejection_reasons"]),
        )


@dataclass(frozen=True, slots=True)
class MethodTargetAssignments:
    method_id: str
    rows: tuple[TargetAssignment, ...]

    @property
    def coverage(self) -> float:
        return sum(row.accepted_cluster is not None for row in self.rows) / len(self.rows)

    def to_dict(self) -> dict[str, Any]:
        return {
            "method_id": self.method_id,
            "coverage": self.coverage,
            "rows": [row.to_dict() for row in self.rows],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "MethodTargetAssignments":
        return cls(
            method_id=str(value["method_id"]),
            rows=tuple(TargetAssignment.from_dict(row) for row in value["rows"]),
        )


@dataclass(frozen=True, slots=True)
class TargetAssignmentSet:
    target_dataset_id: str
    target_fingerprint: str
    frozen_transfer_sha256: str
    methods: tuple[MethodTargetAssignments, ...]

    def __post_init__(self) -> None:
        if self.methods != tuple(sorted(self.methods, key=lambda item: item.method_id)):
            raise ValueError("target assignment methods must be sorted")

    def method_by_id(self, method_id: str) -> MethodTargetAssignments:
        for method in self.methods:
            if method.method_id == method_id:
                return method
        raise KeyError(method_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "TargetAssignmentSet/v1",
            "label_free": True,
            "target_dataset_id": self.target_dataset_id,
            "target_fingerprint": self.target_fingerprint,
            "frozen_transfer_sha256": self.frozen_transfer_sha256,
            "methods": [item.to_dict() for item in self.methods],
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def sha256(self) -> str:
        return sha256_bytes(self.to_json_bytes())

    def save(self, path: str | Path) -> None:
        atomic_write_bytes(path, self.to_json_bytes())

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TargetAssignmentSet":
        if value.get("schema") != "TargetAssignmentSet/v1":
            raise ValueError("not a TargetAssignmentSet/v1")
        return cls(
            target_dataset_id=str(value["target_dataset_id"]),
            target_fingerprint=str(value["target_fingerprint"]),
            frozen_transfer_sha256=str(value["frozen_transfer_sha256"]),
            methods=tuple(
                sorted(
                    (MethodTargetAssignments.from_dict(item) for item in value["methods"]),
                    key=lambda item: item.method_id,
                )
            ),
        )

    @classmethod
    def load(cls, path: str | Path) -> "TargetAssignmentSet":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _aligned_raw(target: DatasetBundle, selected: tuple[str, ...]) -> np.ndarray:
    index = {feature_id: position for position, feature_id in enumerate(target.feature_ids)}
    matrix = np.full((target.shape[0], len(selected)), np.nan, dtype=np.float64)
    present = [(column, index[item]) for column, item in enumerate(selected) if item in index]
    if present:
        output_columns, input_columns = zip(*present, strict=True)
        matrix[:, output_columns] = target.X[:, input_columns]
    return matrix


def _rank_row(raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    observed = ~np.isnan(raw)
    q = np.zeros(len(raw), dtype=np.float64)
    count = int(observed.sum())
    if count == 1:
        q[observed] = 0.0
    elif count > 1:
        q[observed] = (rankdata(raw[observed], method="average") - 1.0) / (count - 1.0)
    return q, observed


def _euclidean(value: np.ndarray, medoids: np.ndarray) -> np.ndarray:
    return np.linalg.norm(medoids - value[None, :], axis=1)


def _correlation(value: np.ndarray, medoids: np.ndarray) -> np.ndarray:
    left = value - value.mean()
    right = medoids - medoids.mean(axis=1, keepdims=True)
    left_norm = float(np.linalg.norm(left))
    right_norm = np.linalg.norm(right, axis=1)
    valid = (left_norm > 0.0) & (right_norm > 0.0)
    result = np.full(len(medoids), 2.0, dtype=np.float64)
    if np.any(valid):
        similarity = (right[valid] @ left) / (right_norm[valid] * left_norm)
        result[valid] = 1.0 - np.clip(similarity, -1.0, 1.0)
    return result


def _footrule(
    q: np.ndarray, observed: np.ndarray, medoid_ranks: np.ndarray
) -> np.ndarray:
    p = len(q)
    count = int(observed.sum())
    if count < 2:
        return np.ones(len(medoid_ranks), dtype=np.float64)
    denominator = float((p * p) // 2)
    correction = p / count
    values = (
        np.abs(medoid_ranks[:, observed] - q[None, observed]).sum(axis=1)
        * (p - 1.0)
        / denominator
        * correction
    )
    return np.clip(values, 0.0, 1.0)


def _relations(
    q: np.ndarray,
    observed: np.ndarray,
    artifact: FrozenMethodArtifact,
) -> tuple[np.ndarray, np.ndarray, float]:
    feature_index = {
        feature_id: index for index, feature_id in enumerate(artifact.selected_feature_ids)
    }
    states = np.zeros(len(artifact.relation_pairs), dtype=np.int8)
    mask = np.zeros(len(artifact.relation_pairs), dtype=bool)
    for pair_index, (left, right) in enumerate(artifact.relation_pairs):
        li, ri = feature_index[left], feature_index[right]
        if not (observed[li] and observed[ri]):
            continue
        difference = q[li] - q[ri]
        states[pair_index] = (
            1 if difference > artifact.relation_margin else -1 if difference < -artifact.relation_margin else 0
        )
        mask[pair_index] = True
    weights = np.asarray(artifact.relation_weights, dtype=np.float64)
    positive_total = float(weights.sum())
    coverage = 0.0 if positive_total <= 0.0 else float(weights[mask].sum() / positive_total)
    return states, mask, coverage


def _pair_distance(
    states: np.ndarray,
    mask: np.ndarray,
    artifact: FrozenMethodArtifact,
) -> np.ndarray:
    weights = np.asarray(artifact.relation_weights, dtype=np.float64)
    denominator = float(weights[mask].sum())
    if denominator <= 0.0:
        return np.ones(artifact.k, dtype=np.float64)
    medoids = np.asarray(artifact.medoid_relation_states, dtype=np.int8)
    return np.sum(weights[None, :] * mask[None, :] * (medoids != states[None, :]), axis=1) / denominator


def _assign_method(
    target: DatasetBundle,
    raw: np.ndarray,
    artifact: FrozenMethodArtifact,
) -> MethodTargetAssignments:
    medoid_values = np.asarray(artifact.medoid_value_profiles, dtype=np.float64)
    medoid_ranks = np.asarray(artifact.medoid_rank_profiles, dtype=np.float64)
    medians = np.asarray(artifact.source_medians, dtype=np.float64)
    scales = np.asarray(artifact.scale_denominators, dtype=np.float64)
    rows: list[TargetAssignment] = []
    for row_index, sample_id in enumerate(target.sample_ids):
        q, observed = _rank_row(raw[row_index])
        feature_coverage = float(observed.mean())
        imputed = np.where(observed, raw[row_index], medians)
        value = (imputed - medians) / scales
        relation_coverage: float | None = None
        pair: np.ndarray | None = None
        if artifact.relation_pairs:
            states, relation_mask, relation_coverage = _relations(q, observed, artifact)
            pair = _pair_distance(states, relation_mask, artifact)
        if artifact.method_id == "V_EUC_PAM":
            distances = _euclidean(value, medoid_values)
        elif artifact.method_id == "V_COR_PAM":
            distances = _correlation(value, medoid_values)
        elif artifact.method_id == "R_FOOT_PAM":
            distances = _footrule(q, observed, medoid_ranks)
        elif artifact.method_id == "R_PAIR_PAM":
            if pair is None:
                raise ValueError("pair artifact is incomplete")
            distances = pair
        elif artifact.family == "HYBRID":
            if pair is None:
                raise ValueError("hybrid pair artifact is incomplete")
            value_distance = _euclidean(value, medoid_values)
            distances = (
                (1.0 - float(artifact.alpha)) * value_distance / float(artifact.value_scale)
                + float(artifact.alpha) * pair / float(artifact.relational_scale)
            )
        else:
            raise ValueError(f"unsupported frozen method: {artifact.method_id}")
        order = np.argsort(distances, kind="stable")
        forced = int(order[0])
        nearest = float(distances[order[0]])
        second = float(distances[order[1]])
        confidence = max(0.0, min(1.0, (second - nearest) / max(second, 1.0e-15)))
        reasons: list[str] = []
        if feature_coverage < artifact.minimum_feature_coverage:
            reasons.append("feature_coverage")
        if artifact.relation_pairs and float(relation_coverage) < artifact.minimum_relation_coverage:
            reasons.append("relation_coverage")
        if nearest > artifact.cluster_radius_q95[forced] + 1.0e-12:
            reasons.append("source_radius")
        if confidence + 1.0e-12 < artifact.confidence_q05:
            reasons.append("confidence")
        rows.append(
            TargetAssignment(
                sample_id=sample_id,
                forced_cluster=forced,
                accepted_cluster=None if reasons else forced,
                nearest_distance=nearest,
                second_distance=second,
                confidence=confidence,
                feature_coverage=feature_coverage,
                relation_coverage=relation_coverage,
                rejection_reasons=tuple(reasons),
            )
        )
    return MethodTargetAssignments(method_id=artifact.method_id, rows=tuple(rows))


def assign_target(target: DatasetBundle, frozen: FrozenTransferSet) -> TargetAssignmentSet:
    """Assign rows independently; neither labels nor target fitting are accepted."""

    if target.dataset_id != frozen.target_dataset_id:
        raise ValueError("target dataset ID does not match frozen transfer direction")
    if feature_schema_sha256(target.feature_ids) != frozen.target_feature_schema_sha256:
        raise ValueError("target feature schema does not match frozen transfer direction")
    methods: list[MethodTargetAssignments] = []
    for artifact in frozen.methods:
        raw = _aligned_raw(target, artifact.selected_feature_ids)
        methods.append(_assign_method(target, raw, artifact))
    return TargetAssignmentSet(
        target_dataset_id=target.dataset_id,
        target_fingerprint=target.fingerprint(),
        frozen_transfer_sha256=frozen.sha256(),
        methods=tuple(sorted(methods, key=lambda item: item.method_id)),
    )
