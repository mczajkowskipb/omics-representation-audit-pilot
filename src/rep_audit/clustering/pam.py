"""Deterministic PAM using BUILD followed by exhaustive best SWAP updates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

import numpy as np

from rep_audit.distances.validation import DistanceMatrix
from rep_audit.io.canonical_json import (
    atomic_write_bytes,
    canonical_json_bytes,
    sha256_bytes,
)


DEFAULT_IMPROVEMENT_TOLERANCE = 1.0e-12


def _objective(values: np.ndarray, medoids: tuple[int, ...]) -> float:
    return float(np.min(values[:, medoids], axis=1).sum())


def _medoid_id_key(
    medoids: tuple[int, ...], sample_ids: tuple[str, ...]
) -> tuple[str, ...]:
    return tuple(sorted(sample_ids[index] for index in medoids))


def _is_strictly_better(candidate: float, current: float, tolerance: float) -> bool:
    return candidate < current - tolerance


def _is_tied(first: float, second: float, tolerance: float) -> bool:
    return abs(first - second) <= tolerance


def _build(
    distance: DistanceMatrix,
    k: int,
    tolerance: float,
) -> tuple[int, ...]:
    values = distance.values
    ids = distance.sample_ids
    n = len(ids)
    ordered_indices = sorted(range(n), key=lambda index: ids[index])
    medoids: tuple[int, ...] = ()

    for _ in range(k):
        best_candidate: int | None = None
        best_cost = np.inf
        best_key: tuple[str, ...] | None = None
        for candidate in ordered_indices:
            if candidate in medoids:
                continue
            proposed = medoids + (candidate,)
            cost = _objective(values, proposed)
            key = _medoid_id_key(proposed, ids)
            if _is_strictly_better(cost, best_cost, tolerance) or (
                _is_tied(cost, best_cost, tolerance)
                and (best_key is None or key < best_key)
            ):
                best_candidate = candidate
                best_cost = cost
                best_key = key
        if best_candidate is None:
            raise RuntimeError("deterministic BUILD could not select a medoid")
        medoids = medoids + (best_candidate,)
    return medoids


def _best_improving_swap(
    distance: DistanceMatrix,
    medoids: tuple[int, ...],
    current_cost: float,
    tolerance: float,
) -> tuple[tuple[int, ...], float] | None:
    values = distance.values
    ids = distance.sample_ids
    medoid_set = set(medoids)
    outside = sorted(
        (index for index in range(len(ids)) if index not in medoid_set),
        key=lambda index: ids[index],
    )
    ordered_medoids = sorted(medoids, key=lambda index: ids[index])
    best_set: tuple[int, ...] | None = None
    best_cost = current_cost
    best_key: tuple[str, ...] | None = None

    for outgoing in ordered_medoids:
        for incoming in outside:
            proposed = tuple(
                incoming if index == outgoing else index for index in medoids
            )
            cost = _objective(values, proposed)
            if not _is_strictly_better(cost, current_cost, tolerance):
                continue
            key = _medoid_id_key(proposed, ids)
            if best_set is None or _is_strictly_better(
                cost, best_cost, tolerance
            ) or (_is_tied(cost, best_cost, tolerance) and key < best_key):
                best_set = proposed
                best_cost = cost
                best_key = key

    if best_set is None:
        return None
    return best_set, best_cost


def _assign(
    distance: DistanceMatrix,
    medoids: tuple[int, ...],
    tolerance: float,
) -> tuple[tuple[str, ...], tuple[int, ...]]:
    ids = distance.sample_ids
    sorted_medoids = tuple(sorted(medoids, key=lambda index: ids[index]))
    medoid_ids = tuple(ids[index] for index in sorted_medoids)
    own_cluster = {sample_index: label for label, sample_index in enumerate(sorted_medoids)}
    labels: list[int] = []

    for sample_index in range(len(ids)):
        if sample_index in own_cluster:
            labels.append(own_cluster[sample_index])
            continue
        distances = distance.values[sample_index, sorted_medoids]
        minimum = float(distances.min())
        tied = np.flatnonzero(np.abs(distances - minimum) <= tolerance)
        labels.append(int(tied[0]))
    return medoid_ids, tuple(labels)


@dataclass(frozen=True, slots=True)
class PAMResult:
    sample_ids: tuple[str, ...]
    labels: tuple[int, ...]
    medoid_ids: tuple[str, ...]
    objective: float
    objective_trace: tuple[float, ...]
    n_swaps: int
    distance_metric_id: str
    distance_sha256: str
    improvement_tolerance: float

    def __post_init__(self) -> None:
        if len(self.sample_ids) != len(self.labels):
            raise ValueError("labels must align with sample_ids")
        if len(self.medoid_ids) == 0 or len(set(self.medoid_ids)) != len(
            self.medoid_ids
        ):
            raise ValueError("medoid_ids must be non-empty and unique")
        expected_labels = set(range(len(self.medoid_ids)))
        if set(self.labels) != expected_labels:
            raise ValueError("PAM output must contain every cluster label")
        if len(self.objective_trace) == 0:
            raise ValueError("objective_trace must contain the BUILD objective")
        if any(
            later > earlier + self.improvement_tolerance
            for earlier, later in zip(
                self.objective_trace, self.objective_trace[1:], strict=False
            )
        ):
            raise ValueError("objective_trace must be non-increasing")
        if abs(self.objective_trace[-1] - self.objective) > self.improvement_tolerance:
            raise ValueError("final objective must equal the trace endpoint")

    @property
    def assignments_by_sample(self) -> Mapping[str, int]:
        return MappingProxyType(
            dict(zip(self.sample_ids, self.labels, strict=True))
        )

    def to_dict(self) -> dict[str, object]:
        assignments = [
            {"sample_id": sample_id, "cluster": label}
            for sample_id, label in sorted(
                zip(self.sample_ids, self.labels, strict=True), key=lambda item: item[0]
            )
        ]
        return {
            "schema": "PAMResult/v1",
            "algorithm": "deterministic_pam_build_swap",
            "converged": True,
            "distance_metric_id": self.distance_metric_id,
            "distance_sha256": self.distance_sha256,
            "k": len(self.medoid_ids),
            "medoid_ids": self.medoid_ids,
            "assignments": assignments,
            "objective": self.objective,
            "objective_trace": self.objective_trace,
            "n_swaps": self.n_swaps,
            "improvement_tolerance": self.improvement_tolerance,
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def sha256(self) -> str:
        return sha256_bytes(self.to_json_bytes())

    def save(self, path: str | Path) -> None:
        atomic_write_bytes(path, self.to_json_bytes())


def deterministic_pam(
    distance: DistanceMatrix,
    *,
    k: int,
    max_swaps: int = 100,
    improvement_tolerance: float = DEFAULT_IMPROVEMENT_TOLERANCE,
) -> PAMResult:
    """Cluster a validated distance matrix with deterministic BUILD+SWAP PAM."""

    n = len(distance.sample_ids)
    if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= n:
        raise ValueError("k must be an integer in [1, n_samples]")
    if not isinstance(max_swaps, int) or isinstance(max_swaps, bool) or max_swaps < 0:
        raise ValueError("max_swaps must be a non-negative integer")
    tolerance = float(improvement_tolerance)
    if not np.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("improvement_tolerance must be finite and non-negative")

    medoids = _build(distance, k, tolerance)
    current_cost = _objective(distance.values, medoids)
    trace = [current_cost]
    n_swaps = 0

    while True:
        improvement = _best_improving_swap(
            distance, medoids, current_cost, tolerance
        )
        if improvement is None:
            break
        if n_swaps >= max_swaps:
            raise RuntimeError(
                "PAM reached max_swaps while an improving swap still exists"
            )
        medoids, current_cost = improvement
        n_swaps += 1
        trace.append(current_cost)

    medoid_ids, labels = _assign(distance, medoids, tolerance)
    return PAMResult(
        sample_ids=distance.sample_ids,
        labels=labels,
        medoid_ids=medoid_ids,
        objective=current_cost,
        objective_trace=tuple(trace),
        n_swaps=n_swaps,
        distance_metric_id=distance.metric_id,
        distance_sha256=distance.fingerprint(),
        improvement_tolerance=tolerance,
    )
