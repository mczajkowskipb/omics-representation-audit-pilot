"""Frozen source-audit configuration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import numpy as np

from rep_audit.io.canonical_json import canonical_json_bytes, sha256_bytes
from rep_audit.simulation.perturbations import PERTURBATION_LEVELS


@dataclass(frozen=True, slots=True)
class AuditConfig:
    k: int
    feature_budget: int
    relation_budget: int
    resamples: int
    seed: int
    margin: float = 0.0
    alphas: tuple[float, ...] = (0.25, 0.50, 0.75)
    perturbation_level: str = "moderate"
    min_cluster_fraction: float = 0.10
    relation_coverage_threshold: float = 0.90
    relation_entropy_threshold: float = 0.05
    relation_stability_threshold: float = 0.80
    relation_screen_perturbations: int = 3
    protocol_version: str = "1.0"

    def __post_init__(self) -> None:
        integer_values = (
            self.k,
            self.feature_budget,
            self.relation_budget,
            self.resamples,
            self.seed,
            self.relation_screen_perturbations,
        )
        if any(not isinstance(value, int) or isinstance(value, bool) for value in integer_values):
            raise TypeError("audit counts and seed must be integers")
        if self.k < 2:
            raise ValueError("k must be at least two")
        if self.feature_budget < 2 or self.relation_budget <= 0:
            raise ValueError("feature and relation budgets must be positive")
        if self.resamples <= 0 or self.relation_screen_perturbations <= 0:
            raise ValueError("resample counts must be positive")
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        if not np.isfinite(self.margin) or not 0.0 <= self.margin <= 1.0:
            raise ValueError("margin must be finite and in [0, 1]")
        alphas = tuple(float(value) for value in self.alphas)
        if len(alphas) == 0 or len(alphas) != len(set(alphas)):
            raise ValueError("alphas must be non-empty and unique")
        if any(not np.isfinite(value) or not 0.0 < value < 1.0 for value in alphas):
            raise ValueError("hybrid alphas must be finite and strictly between 0 and 1")
        if self.perturbation_level not in PERTURBATION_LEVELS:
            raise ValueError("unsupported perturbation_level")
        probabilities = (
            self.min_cluster_fraction,
            self.relation_coverage_threshold,
            self.relation_entropy_threshold,
            self.relation_stability_threshold,
        )
        if any(not np.isfinite(value) or not 0.0 <= value <= 1.0 for value in probabilities):
            raise ValueError("audit thresholds must be finite and in [0, 1]")
        object.__setattr__(self, "alphas", alphas)
        object.__setattr__(self, "perturbation_level", str(self.perturbation_level))
        object.__setattr__(self, "protocol_version", str(self.protocol_version))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "AuditConfig/v1",
            "source_only": True,
            "protocol_version": self.protocol_version,
            "k": self.k,
            "feature_budget": self.feature_budget,
            "relation_budget": self.relation_budget,
            "resamples": self.resamples,
            "seed": self.seed,
            "margin": self.margin,
            "alphas": self.alphas,
            "perturbation_level": self.perturbation_level,
            "min_cluster_fraction": self.min_cluster_fraction,
            "relation_screen": {
                "coverage_threshold": self.relation_coverage_threshold,
                "entropy_threshold": self.relation_entropy_threshold,
                "stability_threshold": self.relation_stability_threshold,
                "perturbations": self.relation_screen_perturbations,
            },
            "q_definition": "min(prediction_strength,cluster_stability,perturbation_invariance)",
        }

    def sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.to_dict()))


def stable_seed(seed: int, *parts: object) -> int:
    payload = canonical_json_bytes({"seed": seed, "parts": tuple(str(item) for item in parts)})
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")
