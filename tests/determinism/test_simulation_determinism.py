from __future__ import annotations

import numpy as np

from rep_audit.simulation.generators import SimulationSpec, generate_simulation


def test_same_spec_produces_byte_identical_source_target_and_truth() -> None:
    specification = SimulationSpec(
        regime="HYBRID",
        signal="strong",
        shift="strong",
        replicate=2,
        seed=98765,
        n_source=24,
        n_target=27,
        p=30,
        k=3,
        informative_features=18,
    )
    first = generate_simulation(specification)
    second = generate_simulation(specification)
    assert first.source.fingerprint() == second.source.fingerprint()
    assert first.target.fingerprint() == second.target.fingerprint()
    assert first.source.X.tobytes() == second.source.X.tobytes()
    assert first.target.X.tobytes() == second.target.X.tobytes()
    assert first.truth.source_labels.values == second.truth.source_labels.values
    assert first.truth.target_labels.values == second.truth.target_labels.values


def test_different_seed_changes_both_independent_cohorts() -> None:
    common = dict(
        regime="VALUE",
        signal="moderate",
        shift="none",
        replicate=0,
        n_source=18,
        n_target=18,
        p=18,
        k=3,
        informative_features=9,
    )
    first = generate_simulation(SimulationSpec(seed=1, **common))
    second = generate_simulation(SimulationSpec(seed=2, **common))
    assert not np.array_equal(first.source.X, second.source.X)
    assert not np.array_equal(first.target.X, second.target.X)
