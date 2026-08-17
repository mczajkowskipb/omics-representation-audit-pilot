"""Source-only prediction strength, stability, invariance, and Q diagnostics."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import adjusted_rand_score

from rep_audit.audit.config import AuditConfig, stable_seed
from rep_audit.audit.distances import (
    FrozenDistanceSet,
    build_frozen_perturbation_distances,
    build_source_representations,
    method_family,
)
from rep_audit.audit.report import MethodAuditResult, SourceAuditReport
from rep_audit.clustering.pam import PAMResult, deterministic_pam
from rep_audit.data.schema import DatasetBundle
from rep_audit.distances.validation import DistanceMatrix
from rep_audit.simulation.perturbations import (
    apply_perturbation,
    audit_perturbation_suite,
)


def _submatrix(distance: DistanceMatrix, indices: Sequence[int], suffix: str) -> DistanceMatrix:
    index = np.asarray(indices, dtype=int)
    return DistanceMatrix(
        values=distance.values[np.ix_(index, index)],
        sample_ids=tuple(distance.sample_ids[item] for item in index),
        metric_id=f"{distance.metric_id}_{suffix}",
    )


def _canonical_indices(distance: DistanceMatrix) -> np.ndarray:
    return np.asarray(
        sorted(range(len(distance.sample_ids)), key=lambda index: distance.sample_ids[index]),
        dtype=int,
    )


def _assign_rows(
    distance: DistanceMatrix,
    row_indices: Sequence[int],
    medoid_ids: Sequence[str],
) -> tuple[int, ...]:
    medoid_ids = tuple(sorted(str(item) for item in medoid_ids))
    id_to_index = {sample_id: index for index, sample_id in enumerate(distance.sample_ids)}
    medoid_indices = np.asarray([id_to_index[item] for item in medoid_ids], dtype=int)
    medoid_to_label = {sample_id: label for label, sample_id in enumerate(medoid_ids)}
    labels: list[int] = []
    for row_index in row_indices:
        sample_id = distance.sample_ids[row_index]
        if sample_id in medoid_to_label:
            labels.append(medoid_to_label[sample_id])
            continue
        row = distance.values[row_index, medoid_indices]
        minimum = float(row.min())
        tied = np.flatnonzero(np.abs(row - minimum) <= 1.0e-12)
        labels.append(int(tied[0]))
    return tuple(labels)


def _prediction_strength_once(
    distance: DistanceMatrix,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    k: int,
) -> float:
    train = deterministic_pam(_submatrix(distance, train_indices, "ps_train"), k=k)
    held_out = deterministic_pam(_submatrix(distance, test_indices, "ps_test"), k=k)
    predicted = np.asarray(_assign_rows(distance, test_indices, train.medoid_ids), dtype=int)
    observed = np.asarray(held_out.labels, dtype=int)
    cluster_scores: list[float] = []
    for cluster in range(k):
        members = np.flatnonzero(predicted == cluster)
        if members.size < 2:
            cluster_scores.append(0.0)
            continue
        left, right = np.triu_indices(members.size, k=1)
        agreement = observed[members[left]] == observed[members[right]]
        cluster_scores.append(float(np.mean(agreement)))
    return min(cluster_scores)


def prediction_strength(
    distance: DistanceMatrix,
    *,
    k: int,
    resamples: int,
    seed: int,
) -> float:
    n = len(distance.sample_ids)
    if n // 2 < k:
        raise ValueError("prediction strength requires at least 2*k samples")
    ordered = _canonical_indices(distance)
    rng = np.random.default_rng(seed)
    scores: list[float] = []
    for _ in range(resamples):
        permutation = rng.permutation(n)
        split = n // 2
        train = ordered[permutation[:split]]
        test = ordered[permutation[split:]]
        scores.append(_prediction_strength_once(distance, train, test, k))
    return float(np.median(scores))


def cluster_stability(
    distance: DistanceMatrix,
    baseline: PAMResult,
    *,
    k: int,
    resamples: int,
    seed: int,
) -> float:
    n = len(distance.sample_ids)
    subset_size = max(k, int(np.ceil(0.80 * n)))
    ordered = _canonical_indices(distance)
    rng = np.random.default_rng(seed)
    scores: list[float] = []
    for replicate in range(resamples):
        chosen_positions = rng.choice(n, size=subset_size, replace=False)
        chosen = ordered[np.sort(chosen_positions)]
        fitted = deterministic_pam(
            _submatrix(distance, chosen, f"stability_{replicate}"), k=k
        )
        assigned = _assign_rows(distance, range(n), fitted.medoid_ids)
        score = float(adjusted_rand_score(baseline.labels, assigned))
        scores.append(max(0.0, min(1.0, score)))
    return float(np.median(scores))


def nondegeneracy(
    labels: Sequence[int], *, k: int, min_cluster_fraction: float
) -> tuple[float, bool, float, float]:
    labels_array = np.asarray(labels, dtype=int)
    counts = np.bincount(labels_array, minlength=k).astype(np.float64)
    proportions = counts / float(len(labels_array))
    minimum = float(proportions.min())
    positive = proportions > 0.0
    entropy = float(-np.sum(proportions[positive] * np.log(proportions[positive])) / np.log(k))
    size_score = min(1.0, minimum / min_cluster_fraction) if min_cluster_fraction > 0 else 1.0
    score = float(min(size_score, entropy))
    passes = bool(np.all(counts > 0) and minimum >= min_cluster_fraction)
    return score, passes, minimum, entropy


def _distance_order_stability(first: DistanceMatrix, second: DistanceMatrix) -> float:
    if first.sample_ids != second.sample_ids:
        raise ValueError("distance stability requires aligned samples")
    indices = np.triu_indices(len(first.sample_ids), k=1)
    left = first.values[indices]
    right = second.values[indices]
    if np.array_equal(left, right):
        return 1.0
    if np.all(left == left[0]) or np.all(right == right[0]):
        return 0.0
    correlation = float(spearmanr(left, right).statistic)
    if not np.isfinite(correlation):
        return 0.0
    return max(0.0, min(1.0, correlation))


def perturbation_scores(
    method_id: str,
    baseline_distance: DistanceMatrix,
    baseline: PAMResult,
    perturbations: Sequence[FrozenDistanceSet],
    *,
    k: int,
) -> tuple[float, float, int]:
    assignment_scores: list[float] = []
    distance_scores: list[float] = []
    failures = 0
    for perturbation in perturbations:
        distance = perturbation.distances.get(method_id)
        if distance is None:
            failures += 1
            assignment_scores.append(0.0)
            distance_scores.append(0.0)
            continue
        fitted = deterministic_pam(distance, k=k)
        ari = float(adjusted_rand_score(baseline.labels, fitted.labels))
        assignment_scores.append(max(0.0, min(1.0, ari)))
        distance_scores.append(_distance_order_stability(baseline_distance, distance))
    return (
        float(np.median(assignment_scores)),
        float(np.median(distance_scores)),
        failures,
    )


def run_source_audit(source: DatasetBundle, config: AuditConfig) -> SourceAuditReport:
    """Run the complete audit without accepting a target or label object."""

    representations = build_source_representations(source, config)
    perturbation_specs = audit_perturbation_suite(
        count=config.resamples,
        seed=stable_seed(config.seed, "audit_perturbations"),
        level=config.perturbation_level,
    )
    perturbed_distances = tuple(
        build_frozen_perturbation_distances(
            apply_perturbation(source, specification), representations, config
        )
        for specification in perturbation_specs
    )

    methods: list[MethodAuditResult] = []
    failures = dict(representations.failures)
    for method_id, distance in representations.distances.items():
        try:
            baseline = deterministic_pam(distance, k=config.k)
            ps = prediction_strength(
                distance,
                k=config.k,
                resamples=config.resamples,
                seed=stable_seed(config.seed, method_id, "prediction_strength"),
            )
            stability = cluster_stability(
                distance,
                baseline,
                k=config.k,
                resamples=config.resamples,
                seed=stable_seed(config.seed, method_id, "cluster_stability"),
            )
            invariance, representation_stability, perturbation_failures = perturbation_scores(
                method_id,
                distance,
                baseline,
                perturbed_distances,
                k=config.k,
            )
            nd_score, nd_pass, minimum, entropy = nondegeneracy(
                baseline.labels,
                k=config.k,
                min_cluster_fraction=config.min_cluster_fraction,
            )
            q_score = min(ps, stability, invariance)
            methods.append(
                MethodAuditResult(
                    method_id=method_id,
                    family=method_family(method_id),
                    prediction_strength=ps,
                    cluster_stability=stability,
                    perturbation_invariance=invariance,
                    representation_stability=representation_stability,
                    nondegeneracy_score=nd_score,
                    nondegenerate=nd_pass,
                    min_cluster_fraction=minimum,
                    cluster_entropy=entropy,
                    q_score=q_score,
                    medoid_ids=baseline.medoid_ids,
                    sample_ids=baseline.sample_ids,
                    assignments=baseline.labels,
                    complexity=representations.complexities[method_id],
                    perturbation_failures=perturbation_failures,
                )
            )
        except (ValueError, RuntimeError, FloatingPointError) as error:
            failures[method_id] = f"{type(error).__name__}: {error}"

    return SourceAuditReport(
        source_dataset_id=source.dataset_id,
        source_fingerprint=source.fingerprint(),
        config_sha256=config.sha256(),
        config=config.to_dict(),
        representation_manifest=representations.manifest(),
        methods=tuple(sorted(methods, key=lambda item: item.method_id)),
        failures=failures,
    )
