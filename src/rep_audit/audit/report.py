"""Canonical source-only Representation Audit artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from rep_audit.io.canonical_json import (
    atomic_write_bytes,
    canonical_json_bytes,
    sha256_bytes,
)


@dataclass(frozen=True, slots=True)
class MethodAuditResult:
    method_id: str
    family: str
    prediction_strength: float
    cluster_stability: float
    perturbation_invariance: float
    representation_stability: float
    nondegeneracy_score: float
    nondegenerate: bool
    min_cluster_fraction: float
    cluster_entropy: float
    q_score: float
    medoid_ids: tuple[str, ...]
    sample_ids: tuple[str, ...]
    assignments: tuple[int, ...]
    complexity: int
    perturbation_failures: int

    def __post_init__(self) -> None:
        if self.family not in {"VALUE", "RELATIONAL", "HYBRID"}:
            raise ValueError("unsupported representation family")
        metrics = (
            self.prediction_strength,
            self.cluster_stability,
            self.perturbation_invariance,
            self.representation_stability,
            self.nondegeneracy_score,
            self.min_cluster_fraction,
            self.cluster_entropy,
            self.q_score,
        )
        if any(not np.isfinite(value) or not 0.0 <= value <= 1.0 for value in metrics):
            raise ValueError("audit metrics must be finite and in [0, 1]")
        expected_q = min(
            self.prediction_strength,
            self.cluster_stability,
            self.perturbation_invariance,
        )
        if abs(self.q_score - expected_q) > 1.0e-12:
            raise ValueError("q_score must be min(PS, STAB, INV)")
        if len(self.sample_ids) != len(self.assignments):
            raise ValueError("assignments must align with sample_ids")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("sample_ids must be unique")
        if self.complexity <= 0 or self.perturbation_failures < 0:
            raise ValueError("invalid method complexity or failure count")
        object.__setattr__(self, "medoid_ids", tuple(self.medoid_ids))
        object.__setattr__(self, "sample_ids", tuple(self.sample_ids))
        object.__setattr__(self, "assignments", tuple(self.assignments))

    def to_dict(self) -> dict[str, Any]:
        assignment_rows = [
            {"sample_id": sample_id, "cluster": cluster}
            for sample_id, cluster in sorted(
                zip(self.sample_ids, self.assignments, strict=True),
                key=lambda item: item[0],
            )
        ]
        return {
            "method_id": self.method_id,
            "family": self.family,
            "prediction_strength": self.prediction_strength,
            "cluster_stability": self.cluster_stability,
            "perturbation_invariance": self.perturbation_invariance,
            "representation_stability": self.representation_stability,
            "nondegeneracy_score": self.nondegeneracy_score,
            "nondegenerate": self.nondegenerate,
            "min_cluster_fraction": self.min_cluster_fraction,
            "cluster_entropy": self.cluster_entropy,
            "q_score": self.q_score,
            "medoid_ids": self.medoid_ids,
            "assignments": assignment_rows,
            "complexity": self.complexity,
            "perturbation_failures": self.perturbation_failures,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MethodAuditResult":
        rows = tuple(value["assignments"])
        return cls(
            method_id=str(value["method_id"]),
            family=str(value["family"]),
            prediction_strength=float(value["prediction_strength"]),
            cluster_stability=float(value["cluster_stability"]),
            perturbation_invariance=float(value["perturbation_invariance"]),
            representation_stability=float(value["representation_stability"]),
            nondegeneracy_score=float(value["nondegeneracy_score"]),
            nondegenerate=bool(value["nondegenerate"]),
            min_cluster_fraction=float(value["min_cluster_fraction"]),
            cluster_entropy=float(value["cluster_entropy"]),
            q_score=float(value["q_score"]),
            medoid_ids=tuple(str(item) for item in value["medoid_ids"]),
            sample_ids=tuple(str(row["sample_id"]) for row in rows),
            assignments=tuple(int(row["cluster"]) for row in rows),
            complexity=int(value["complexity"]),
            perturbation_failures=int(value["perturbation_failures"]),
        )


@dataclass(frozen=True, slots=True)
class SourceAuditReport:
    source_dataset_id: str
    source_fingerprint: str
    config_sha256: str
    config: Mapping[str, Any]
    representation_manifest: Mapping[str, Any]
    methods: tuple[MethodAuditResult, ...]
    failures: Mapping[str, str]

    def __post_init__(self) -> None:
        method_ids = tuple(item.method_id for item in self.methods)
        if method_ids != tuple(sorted(method_ids)) or len(set(method_ids)) != len(method_ids):
            raise ValueError("audit methods must be unique and sorted by method_id")
        object.__setattr__(self, "config", MappingProxyType(dict(self.config)))
        object.__setattr__(
            self, "representation_manifest", MappingProxyType(dict(self.representation_manifest))
        )
        object.__setattr__(self, "failures", MappingProxyType(dict(sorted(self.failures.items()))))

    def method_by_id(self, method_id: str) -> MethodAuditResult:
        for method in self.methods:
            if method.method_id == method_id:
                return method
        raise KeyError(method_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "SourceAuditReport/v1",
            "source_only": True,
            "source_dataset_id": self.source_dataset_id,
            "source_fingerprint": self.source_fingerprint,
            "config_sha256": self.config_sha256,
            "config": dict(self.config),
            "representation_manifest": dict(self.representation_manifest),
            "methods": [method.to_dict() for method in self.methods],
            "failures": dict(self.failures),
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def sha256(self) -> str:
        return sha256_bytes(self.to_json_bytes())

    def save(self, path: str | Path) -> None:
        atomic_write_bytes(path, self.to_json_bytes())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SourceAuditReport":
        if value.get("schema") != "SourceAuditReport/v1":
            raise ValueError("not a SourceAuditReport/v1 object")
        return cls(
            source_dataset_id=str(value["source_dataset_id"]),
            source_fingerprint=str(value["source_fingerprint"]),
            config_sha256=str(value["config_sha256"]),
            config=dict(value["config"]),
            representation_manifest=dict(value["representation_manifest"]),
            methods=tuple(
                sorted(
                    (MethodAuditResult.from_dict(item) for item in value["methods"]),
                    key=lambda item: item.method_id,
                )
            ),
            failures=dict(value["failures"]),
        )

    @classmethod
    def load(cls, path: str | Path) -> "SourceAuditReport":
        import json

        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
