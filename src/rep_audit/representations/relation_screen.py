"""Source-only unsupervised screening of ternary relation candidates."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from rep_audit.data.schema import DatasetBundle
from rep_audit.io.canonical_json import (
    atomic_write_bytes,
    canonical_json_bytes,
    sha256_bytes,
)
from rep_audit.representations.ranks import average_rank_encode
from rep_audit.representations.ternary_relations import encode_ternary_relations
from rep_audit.simulation.perturbations import (
    apply_perturbation,
    audit_perturbation_suite,
)


class NoEligibleRelationsError(ValueError):
    """Raised when the frozen source screen retains no relation."""


@dataclass(frozen=True, slots=True)
class RelationScreenArtifact:
    source_fingerprint: str
    feature_ids: tuple[str, ...]
    relation_pairs: tuple[tuple[str, str], ...]
    weights: tuple[float, ...]
    scores: tuple[float, ...]
    coverage: tuple[float, ...]
    entropy: tuple[float, ...]
    stability: tuple[float, ...]
    margin: float
    relation_budget: int
    candidate_count: int
    eligible_count: int
    coverage_threshold: float
    entropy_threshold: float
    stability_threshold: float
    perturbation_count: int
    perturbation_seed: int

    def __post_init__(self) -> None:
        count = len(self.relation_pairs)
        if count == 0:
            raise ValueError("relation screen artifact must retain relations")
        if len(set(self.relation_pairs)) != count:
            raise ValueError("retained relation pairs must be unique")
        aligned = (
            self.weights,
            self.scores,
            self.coverage,
            self.entropy,
            self.stability,
        )
        if any(len(values) != count for values in aligned):
            raise ValueError("screen statistics must align with relation_pairs")
        arrays = [np.asarray(values, dtype=float) for values in aligned]
        if any(not np.isfinite(values).all() for values in arrays):
            raise ValueError("screen statistics must be finite")
        if not all(value > 0.0 for value in self.weights):
            raise ValueError("retained relation weights must be positive")
        if count > self.relation_budget or self.eligible_count < count:
            raise ValueError("retained relation count violates screen counts")
        if self.candidate_count < self.eligible_count:
            raise ValueError("eligible_count cannot exceed candidate_count")

    @property
    def relation_ids(self) -> tuple[str, ...]:
        return tuple(f"{left}>{right}" for left, right in self.relation_pairs)

    def to_dict(self) -> dict[str, Any]:
        rows = []
        for pair, weight, score, coverage, entropy, stability in zip(
            self.relation_pairs,
            self.weights,
            self.scores,
            self.coverage,
            self.entropy,
            self.stability,
            strict=True,
        ):
            rows.append(
                {
                    "left": pair[0],
                    "right": pair[1],
                    "weight": weight,
                    "score": score,
                    "coverage": coverage,
                    "entropy": entropy,
                    "stability": stability,
                }
            )
        return {
            "schema": "RelationScreenArtifact/v1",
            "source_only": True,
            "source_fingerprint": self.source_fingerprint,
            "feature_ids": self.feature_ids,
            "margin": self.margin,
            "relation_budget": self.relation_budget,
            "candidate_count": self.candidate_count,
            "eligible_count": self.eligible_count,
            "thresholds": {
                "coverage_strictly_above": self.coverage_threshold,
                "entropy_at_least": self.entropy_threshold,
                "stability_at_least": self.stability_threshold,
            },
            "perturbations": {
                "count": self.perturbation_count,
                "seed": self.perturbation_seed,
                "level": "small",
            },
            "relations": rows,
            "score_definition": "coverage_times_normalized_entropy_times_stability",
            "weight_definition": "score_normalized_to_mean_one",
            "tie_break": "relation_id",
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def sha256(self) -> str:
        return sha256_bytes(self.to_json_bytes())

    def save(self, path: str | Path) -> None:
        atomic_write_bytes(path, self.to_json_bytes())


def _normalized_entropy(states: np.ndarray, observed: np.ndarray) -> np.ndarray:
    result = np.zeros(states.shape[1], dtype=np.float64)
    for state in (-1, 0, 1):
        counts = np.sum(observed & (states == state), axis=0)
        totals = np.sum(observed, axis=0)
        probability = np.divide(
            counts,
            totals,
            out=np.zeros_like(counts, dtype=np.float64),
            where=totals > 0,
        )
        positive = probability > 0.0
        result[positive] -= probability[positive] * np.log(probability[positive])
    return result / np.log(3.0)


def _stability_against_perturbations(
    source: DatasetBundle,
    feature_ids: tuple[str, ...],
    pairs: tuple[tuple[str, str], ...],
    base_states: np.ndarray,
    base_observed: np.ndarray,
    *,
    margin: float,
    count: int,
    seed: int,
) -> np.ndarray:
    agreements: list[np.ndarray] = []
    for specification in audit_perturbation_suite(
        count=count, seed=seed, level="small"
    ):
        perturbed = apply_perturbation(source, specification)
        ranks = average_rank_encode(perturbed, feature_ids=feature_ids)
        relations = encode_ternary_relations(ranks, pairs, margin=margin)
        joint = base_observed & relations.observed
        denominator = joint.sum(axis=0)
        numerator = (joint & (base_states == relations.states)).sum(axis=0)
        agreement = np.divide(
            numerator,
            denominator,
            out=np.zeros_like(numerator, dtype=np.float64),
            where=denominator > 0,
        )
        agreements.append(agreement)
    return np.mean(np.stack(agreements, axis=0), axis=0)


def screen_source_relations(
    source: DatasetBundle,
    *,
    feature_ids: Sequence[object],
    margin: float,
    relation_budget: int,
    coverage_threshold: float = 0.90,
    entropy_threshold: float = 0.05,
    stability_threshold: float = 0.80,
    perturbation_count: int = 3,
    perturbation_seed: int = 0,
) -> RelationScreenArtifact:
    """Screen all canonical unordered pairs using source values only."""

    selected = tuple(str(item) for item in feature_ids)
    if len(selected) < 2 or len(selected) != len(set(selected)):
        raise ValueError("feature_ids must contain at least two unique IDs")
    if not isinstance(relation_budget, int) or relation_budget <= 0:
        raise ValueError("relation_budget must be a positive integer")
    if not isinstance(perturbation_count, int) or perturbation_count <= 0:
        raise ValueError("perturbation_count must be a positive integer")
    thresholds = (coverage_threshold, entropy_threshold, stability_threshold)
    if any(not np.isfinite(value) or not 0.0 <= value <= 1.0 for value in thresholds):
        raise ValueError("screen thresholds must be finite and in [0, 1]")
    pairs = tuple(itertools.combinations(sorted(selected), 2))
    ranks = average_rank_encode(source, feature_ids=selected)
    base = encode_ternary_relations(ranks, pairs, margin=margin)
    coverage = base.observed.mean(axis=0)
    entropy = _normalized_entropy(base.states, base.observed)
    stability = _stability_against_perturbations(
        source,
        selected,
        pairs,
        base.states,
        base.observed,
        margin=margin,
        count=perturbation_count,
        seed=perturbation_seed,
    )
    nonconstant = np.array(
        [
            len(np.unique(base.states[base.observed[:, index], index])) >= 2
            for index in range(len(pairs))
        ],
        dtype=bool,
    )
    score = coverage * entropy * stability
    eligible = (
        (coverage > coverage_threshold)
        & (entropy >= entropy_threshold)
        & (stability >= stability_threshold)
        & nonconstant
    )
    eligible_indices = np.flatnonzero(eligible)
    if eligible_indices.size == 0:
        raise NoEligibleRelationsError(
            "source-only screen retained no eligible ternary relations"
        )
    ordered = sorted(
        (int(index) for index in eligible_indices),
        key=lambda index: (-float(score[index]), f"{pairs[index][0]}>{pairs[index][1]}"),
    )
    retained = ordered[:relation_budget]
    raw_weights = score[retained]
    weights = raw_weights / float(raw_weights.mean())
    return RelationScreenArtifact(
        source_fingerprint=source.fingerprint(),
        feature_ids=selected,
        relation_pairs=tuple(pairs[index] for index in retained),
        weights=tuple(float(value) for value in weights),
        scores=tuple(float(score[index]) for index in retained),
        coverage=tuple(float(coverage[index]) for index in retained),
        entropy=tuple(float(entropy[index]) for index in retained),
        stability=tuple(float(stability[index]) for index in retained),
        margin=float(margin),
        relation_budget=relation_budget,
        candidate_count=len(pairs),
        eligible_count=len(ordered),
        coverage_threshold=float(coverage_threshold),
        entropy_threshold=float(entropy_threshold),
        stability_threshold=float(stability_threshold),
        perturbation_count=perturbation_count,
        perturbation_seed=perturbation_seed,
    )
