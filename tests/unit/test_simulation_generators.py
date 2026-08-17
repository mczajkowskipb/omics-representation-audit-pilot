from __future__ import annotations

import numpy as np
import pytest

from rep_audit.data.schema import DatasetBundle
from rep_audit.simulation.generators import SimulationSpec, generate_simulation


def spec(regime: str, signal: str, shift: str = "moderate") -> SimulationSpec:
    return SimulationSpec(
        regime=regime,
        signal=signal,
        shift=shift,
        replicate=0,
        seed=1234,
        n_source=30,
        n_target=33,
        p=24,
        k=3,
        informative_features=12,
    )


@pytest.mark.parametrize(
    ("regime", "signal", "expected"),
    [
        ("VALUE", "moderate", "VALUE"),
        ("RELATIONAL", "strong", "RELATIONAL"),
        ("HYBRID", "moderate", "HYBRID"),
        ("NULL", "none", "NO_STABLE_STRUCTURE"),
    ],
)
def test_all_frozen_regimes_emit_separate_data_and_truth(
    regime: str, signal: str, expected: str
) -> None:
    generated = generate_simulation(spec(regime, signal))
    assert isinstance(generated.source, DatasetBundle)
    assert isinstance(generated.target, DatasetBundle)
    assert not hasattr(generated.source, "labels")
    assert not hasattr(generated.target, "labels")
    assert generated.truth.expected_decision == expected
    assert generated.truth.source_labels.sample_ids == generated.source.sample_ids
    assert generated.truth.target_labels.sample_ids == generated.target.sample_ids
    assert generated.source.X.shape == (30, 24)


def test_source_and_target_are_independent_cohorts() -> None:
    generated = generate_simulation(spec("VALUE", "strong", "none"))
    assert generated.source.sample_ids != generated.target.sample_ids
    assert not np.array_equal(generated.source.X[:30], generated.target.X[:30])


def test_strong_target_shift_can_remove_features_without_touching_source() -> None:
    generated = generate_simulation(spec("RELATIONAL", "strong", "strong"))
    assert generated.source.shape[1] == 24
    assert generated.target.shape[1] == 23
    assert set(generated.target.feature_ids) < set(generated.source.feature_ids)
    assert np.isnan(generated.target.X).any()
    assert not np.isnan(generated.source.X).any()


def test_value_signal_preserves_almost_all_source_rank_order() -> None:
    generated = generate_simulation(spec("VALUE", "strong", "none"))
    order = np.argsort(generated.source.X, axis=1)
    reference = order[0]
    agreement = np.mean(np.all(order == reference, axis=1))
    assert agreement >= 0.90


def test_value_source_has_no_sample_wide_multiplicative_batch_factor() -> None:
    generated = generate_simulation(spec("VALUE", "strong", "none"))
    centered = generated.source.X - np.arange(24, dtype=float)[None, :] * 6.0
    per_sample_slopes = np.polyfit(
        np.arange(24, dtype=float), generated.source.X.T, deg=1
    )[0]
    assert np.std(per_sample_slopes) < 0.03
    assert np.isfinite(centered).all()
    assert np.all(np.ptp(generated.source.X[:, 12:], axis=0) == 0.0)


def test_relational_signal_has_stable_class_specific_pair_states() -> None:
    generated = generate_simulation(spec("RELATIONAL", "strong", "none"))
    labels = np.asarray(
        [int(value[1:]) for value in generated.truth.source_labels.values]
    )
    state = generated.source.X[:, 0] > generated.source.X[:, 1]
    class_rates = [float(state[labels == label].mean()) for label in range(3)]
    assert max(class_rates) >= 0.9
    assert min(class_rates) <= 0.1


def test_null_has_variable_relations_but_no_class_conditioned_generator_signal() -> None:
    generated = generate_simulation(spec("NULL", "none", "none"))
    state = generated.source.X[:, 0] > generated.source.X[:, 1]
    assert 0.20 < float(state.mean()) < 0.80
    labels = np.asarray(
        [int(value[1:]) for value in generated.truth.source_labels.values]
    )
    rates = [float(state[labels == label].mean()) for label in range(3)]
    assert max(rates) - min(rates) < 0.60


@pytest.mark.parametrize(
    "kwargs",
    [
        {"regime": "BAD", "signal": "moderate"},
        {"regime": "NULL", "signal": "strong"},
        {"regime": "VALUE", "signal": "none"},
    ],
)
def test_invalid_regime_signal_combinations_are_rejected(kwargs) -> None:
    with pytest.raises(ValueError):
        SimulationSpec(
            shift="none",
            replicate=0,
            seed=1,
            n_source=12,
            n_target=12,
            p=12,
            k=3,
            informative_features=6,
            **kwargs,
        )
