from __future__ import annotations

import numpy as np
import pytest

from rep_audit.data.schema import DatasetBundle
from rep_audit.representations.ranks import average_rank_encode
from rep_audit.simulation.perturbations import (
    PERTURBATION_KINDS,
    PerturbationSpec,
    apply_perturbation,
    audit_perturbation_suite,
)


def source_bundle() -> DatasetBundle:
    return DatasetBundle(
        X=np.array(
            [
                [1.0, 3.0, 7.0, 12.0],
                [2.0, 4.0, 8.0, 13.0],
                [0.5, 2.5, 6.0, 11.0],
                [1.5, 3.5, 9.0, 14.0],
            ]
        ),
        sample_ids=("s1", "s2", "s3", "s4"),
        feature_ids=("g1", "g2", "g3", "g4"),
        dataset_id="toy",
        platform_id="sim",
        cohort_id="source",
    )


def test_sample_monotone_perturbation_preserves_exact_rank_order() -> None:
    source = source_bundle()
    specification = PerturbationSpec(
        kind="sample_monotone", level="strong", replicate=0, seed=17
    )
    perturbed = apply_perturbation(source, specification)
    assert np.array_equal(
        average_rank_encode(source).q,
        average_rank_encode(perturbed).q,
    )


@pytest.mark.parametrize("kind", PERTURBATION_KINDS)
def test_every_perturbation_is_deterministic_and_preserves_schema(kind: str) -> None:
    specification = PerturbationSpec(
        kind=kind, level="moderate", replicate=1, seed=991
    )
    first = apply_perturbation(source_bundle(), specification)
    second = apply_perturbation(source_bundle(), specification)
    assert first.fingerprint() == second.fingerprint()
    assert first.X.tobytes() == second.X.tobytes()
    assert first.sample_ids == source_bundle().sample_ids
    assert first.feature_ids == source_bundle().feature_ids


def test_dropout_is_explicit_nan_not_zero_or_removed_column() -> None:
    source = DatasetBundle(
        X=np.arange(600, dtype=float).reshape(100, 6),
        sample_ids=tuple(f"s{i}" for i in range(100)),
        feature_ids=tuple(f"g{i}" for i in range(6)),
        dataset_id="dropout",
        platform_id="sim",
        cohort_id="source",
    )
    perturbed = apply_perturbation(
        source,
        PerturbationSpec(
            kind="feature_dropout", level="strong", replicate=0, seed=7
        ),
    )
    assert perturbed.shape == source.shape
    assert np.isnan(perturbed.X).any()
    assert perturbed.feature_ids == source.feature_ids


def test_audit_suite_cycles_all_kinds_with_stable_seeds() -> None:
    first = audit_perturbation_suite(count=7, seed=123, level="small")
    second = audit_perturbation_suite(count=7, seed=123, level="small")
    assert first == second
    assert tuple(item.kind for item in first[:5]) == PERTURBATION_KINDS
    assert len({item.seed for item in first}) == 7


def test_random_perturbation_is_invariant_to_row_and_column_order() -> None:
    source = source_bundle()
    row_order = np.array([2, 0, 3, 1])
    column_order = np.array([3, 1, 0, 2])
    permuted = DatasetBundle(
        X=source.X[np.ix_(row_order, column_order)],
        sample_ids=tuple(np.asarray(source.sample_ids)[row_order]),
        feature_ids=tuple(np.asarray(source.feature_ids)[column_order]),
        dataset_id=source.dataset_id,
        platform_id=source.platform_id,
        cohort_id=source.cohort_id,
    )
    specification = PerturbationSpec(
        kind="additive_noise", level="moderate", replicate=0, seed=12345
    )
    first = apply_perturbation(source, specification)
    second = apply_perturbation(permuted, specification)
    aligned = np.empty_like(second.X)
    inverse_rows = np.argsort(row_order)
    inverse_columns = np.argsort(column_order)
    aligned = second.X[np.ix_(inverse_rows, inverse_columns)]
    assert np.allclose(first.X, aligned)
