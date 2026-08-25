"""Deterministic direct clustering by sparse within-sample relational prototypes.

Each cluster is represented by a small executable set of relations x_i > x_j.
The same prototype both defines membership and can be frozen for assignment of
unseen samples. No evaluation labels are accepted by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import numpy as np


@dataclass(frozen=True, slots=True)
class SparseRelationalPrototype:
    cluster: int
    rules: tuple[tuple[str, str, int, float, float], ...]
    # (feature_a, feature_b, direction, within_support, contrast)

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster": self.cluster,
            "rules": [
                {
                    "feature_a": a,
                    "feature_b": b,
                    "direction": ">" if d == 1 else "<",
                    "within_support": s,
                    "contrast": c,
                }
                for a, b, d, s, c in self.rules
            ],
        }


@dataclass(frozen=True, slots=True)
class RRDirectResult:
    labels: tuple[int, ...]
    prototypes: tuple[SparseRelationalPrototype, ...]
    selected_feature_ids: tuple[str, ...]
    n_candidate_pairs: int
    n_iterations: int
    converged: bool
    score_margin: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "RRDirectResult/v1",
            "algorithm": "deterministic_sparse_relational_prototype_clustering",
            "labels": self.labels,
            "selected_feature_ids": self.selected_feature_ids,
            "n_candidate_pairs": self.n_candidate_pairs,
            "n_iterations": self.n_iterations,
            "converged": self.converged,
            "score_margin": self.score_margin,
            "prototypes": [p.to_dict() for p in self.prototypes],
        }


def _median_impute(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    med = np.nanmedian(X, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    return np.where(np.isnan(X), med[None, :], X)


def _feature_subset(X: np.ndarray, feature_ids: Sequence[str], budget: int) -> tuple[np.ndarray, tuple[str, ...]]:
    raw = np.asarray(X, dtype=float)
    feature_ids = tuple(str(x) for x in feature_ids)
    if raw.ndim != 2 or raw.shape[1] != len(feature_ids):
        raise ValueError("feature_ids must match X columns")
    observed = np.sum(np.isfinite(raw), axis=0) > 0
    if not np.any(observed):
        raise ValueError("no observed features available for RR_DIRECT")
    raw = raw[:, observed]
    fids = tuple(feature_ids[j] for j in np.flatnonzero(observed))
    Ximp = _median_impute(raw)
    scale = np.median(np.abs(Ximp - np.median(Ximp, axis=0)), axis=0)
    order = sorted(range(Ximp.shape[1]), key=lambda j: (-float(scale[j]), fids[j]))
    keep = tuple(order[: min(int(budget), Ximp.shape[1])])
    if len(keep) < 2:
        raise ValueError("RR_DIRECT requires at least two observed features")
    return Ximp[:, keep], tuple(fids[j] for j in keep)


def _pairs(p: int, max_pairs: int) -> tuple[tuple[int, int], ...]:
    all_pairs = [(i, j) for i in range(p) for j in range(i + 1, p)]
    return tuple(all_pairs[: min(int(max_pairs), len(all_pairs))])


def _binary_relations(X: np.ndarray, pairs: Sequence[tuple[int, int]]) -> np.ndarray:
    if not pairs:
        raise ValueError("no candidate relations")
    return np.column_stack([(X[:, i] > X[:, j]).astype(np.uint8) for i, j in pairs])


def _initial_labels(B: np.ndarray, k: int) -> np.ndarray:
    # Deterministic farthest-first seeds in binary relation space.
    n = B.shape[0]
    if not 2 <= k <= n:
        raise ValueError("k must be in [2, n_samples]")
    prevalence = B.mean(axis=0)
    central_cost = np.mean(np.abs(B - prevalence), axis=1)
    seeds = [int(np.argmax(central_cost))]
    while len(seeds) < k:
        dmin = np.min([np.mean(B != B[s], axis=1) for s in seeds], axis=0)
        dmin[seeds] = -1.0
        seeds.append(int(np.argmax(dmin)))
    D = np.column_stack([np.mean(B != B[s], axis=1) for s in seeds])
    return np.argmin(D, axis=1).astype(int)


def _build_prototypes(
    B: np.ndarray,
    labels: np.ndarray,
    pairs: Sequence[tuple[int, int]],
    feature_ids: Sequence[str],
    k: int,
    max_rules: int,
    min_support: float,
    min_contrast: float,
) -> tuple[SparseRelationalPrototype, ...]:
    global_prev = B.mean(axis=0)
    result = []
    for c in range(k):
        mask = labels == c
        if mask.sum() == 0:
            raise RuntimeError("empty cluster during prototype update")
        prev = B[mask].mean(axis=0)
        direction = (prev >= 0.5).astype(np.uint8)
        support = np.where(direction == 1, prev, 1.0 - prev)
        other = np.where(direction == 1, global_prev, 1.0 - global_prev)
        contrast = support - other
        candidates = [
            j for j in range(B.shape[1])
            if support[j] >= min_support and contrast[j] >= min_contrast
        ]
        if not candidates:
            # deterministic fallback: strongest stable/contrasting relations
            candidates = list(range(B.shape[1]))
        candidates.sort(key=lambda j: (-float(contrast[j]), -float(support[j]), j))
        chosen = candidates[: max(1, min(int(max_rules), len(candidates)))]
        rules = []
        for j in chosen:
            a, b = pairs[j]
            rules.append((
                str(feature_ids[a]), str(feature_ids[b]), int(direction[j]),
                float(support[j]), float(contrast[j])
            ))
        result.append(SparseRelationalPrototype(cluster=c, rules=tuple(rules)))
    return tuple(result)


def _score_from_prototypes(
    X: np.ndarray,
    feature_ids: Sequence[str],
    prototypes: Sequence[SparseRelationalPrototype],
) -> np.ndarray:
    """Score executable rules without target-cohort imputation.

    Missing target measurements simply make the affected rule unavailable for
    that sample. This keeps frozen assignment independent of target-distribution
    statistics.
    """
    X = np.asarray(X, dtype=float)
    index = {str(f): j for j, f in enumerate(feature_ids)}
    scores = np.full((X.shape[0], len(prototypes)), -np.inf, dtype=float)
    for ci, proto in enumerate(prototypes):
        numerator = np.zeros(X.shape[0], dtype=float)
        denominator = np.zeros(X.shape[0], dtype=float)
        for a, b, direction, support, contrast in proto.rules:
            if a not in index or b not in index:
                continue
            xa = X[:, index[a]]
            xb = X[:, index[b]]
            available = np.isfinite(xa) & np.isfinite(xb)
            if not np.any(available):
                continue
            obs = xa[available] > xb[available]
            weight = max(1e-12, support * max(contrast, 1e-6))
            numerator[available] += weight * (obs == bool(direction))
            denominator[available] += weight
        valid = denominator > 0.0
        scores[valid, ci] = numerator[valid] / denominator[valid]
    return scores


def _repair_empty(labels: np.ndarray, scores: np.ndarray, k: int) -> np.ndarray:
    labels = labels.copy()
    for c in range(k):
        if np.any(labels == c):
            continue
        counts = np.bincount(labels, minlength=k)
        donor = int(np.argmax(counts))
        donor_idx = np.flatnonzero(labels == donor)
        # move donor sample least securely assigned to donor
        margins = scores[donor_idx, donor] - np.max(np.delete(scores[donor_idx], donor, axis=1), axis=1)
        labels[donor_idx[int(np.argmin(margins))]] = c
    return labels


def fit_rr_direct(
    X: np.ndarray,
    feature_ids: Sequence[str],
    *,
    k: int = 2,
    feature_budget: int = 60,
    max_pairs: int = 1500,
    max_rules: int = 25,
    min_support: float = 0.80,
    min_contrast: float = 0.10,
    max_iter: int = 50,
) -> RRDirectResult:
    """Fit direct sparse relational prototypes without labels."""
    Xs, fids = _feature_subset(X, feature_ids, feature_budget)
    pairs = _pairs(Xs.shape[1], max_pairs)
    B = _binary_relations(Xs, pairs)
    labels = _initial_labels(B, k)
    converged = False
    prototypes = ()
    scores = np.zeros((Xs.shape[0], k), dtype=float)
    for it in range(1, max_iter + 1):
        prototypes = _build_prototypes(
            B, labels, pairs, fids, k, max_rules, min_support, min_contrast
        )
        scores = _score_from_prototypes(Xs, fids, prototypes)
        if not np.isfinite(scores).any(axis=1).all():
            raise RuntimeError("prototype scoring failed for at least one sample")
        new_labels = np.argmax(scores, axis=1).astype(int)
        new_labels = _repair_empty(new_labels, scores, k)
        if np.array_equal(new_labels, labels):
            converged = True
            labels = new_labels
            break
        labels = new_labels
    # Rebuild the executable prototypes from the final partition.  This is
    # essential when max_iter is reached without an exact fixed point: the
    # returned labels and returned prototypes must always describe the same
    # final state.
    prototypes = _build_prototypes(
        B, labels, pairs, fids, k, max_rules, min_support, min_contrast
    )
    scores = _score_from_prototypes(Xs, fids, prototypes)
    if not np.isfinite(scores).any(axis=1).all():
        raise RuntimeError("final prototype scoring failed for at least one sample")
    order = np.sort(scores, axis=1)
    margin = order[:, -1] - order[:, -2] if k > 1 else order[:, -1]
    return RRDirectResult(
        labels=tuple(int(x) for x in labels),
        prototypes=tuple(prototypes),
        selected_feature_ids=fids,
        n_candidate_pairs=len(pairs),
        n_iterations=it,
        converged=converged,
        score_margin=tuple(float(x) for x in margin),
    )


def assign_frozen_prototypes(
    X: np.ndarray,
    feature_ids: Sequence[str],
    prototypes: Sequence[SparseRelationalPrototype],
    *,
    min_score: float = 0.60,
    min_margin: float = 0.05,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Assign unseen samples to frozen prototypes; -1 denotes UNASSIGNED."""
    scores = _score_from_prototypes(X, feature_ids, prototypes)
    n = scores.shape[0]
    assigned = np.full(n, -1, dtype=int)
    best_score = np.full(n, np.nan, dtype=float)
    margin = np.full(n, np.nan, dtype=float)
    finite_count = np.sum(np.isfinite(scores), axis=1)
    valid_rows = finite_count >= min(2, scores.shape[1])
    for i in np.flatnonzero(valid_rows):
        row = scores[i]
        order = np.argsort(row)
        best = int(order[-1])
        second = int(order[-2]) if scores.shape[1] > 1 else best
        best_score[i] = float(row[best])
        margin[i] = float(row[best] - row[second]) if scores.shape[1] > 1 else float(row[best])
        if best_score[i] >= min_score and margin[i] >= min_margin:
            assigned[i] = best
    return assigned, best_score, margin

