from __future__ import annotations

import inspect

from rep_audit.preprocessing.robust import fit_source_preprocessing
from rep_audit.simulation.generators import SimulationSpec, generate_simulation
from rep_audit.simulation.perturbations import apply_perturbation


def _spec(shift: str) -> SimulationSpec:
    return SimulationSpec(
        regime="RELATIONAL",
        signal="strong",
        shift=shift,
        replicate=4,
        seed=20260817,
        n_source=30,
        n_target=30,
        p=24,
        k=3,
        informative_features=12,
    )


def test_changing_only_target_shift_leaves_source_and_artifact_byte_identical() -> None:
    none = generate_simulation(_spec("none"))
    strong = generate_simulation(_spec("strong"))
    assert none.source.fingerprint() == strong.source.fingerprint()
    assert none.source.X.tobytes() == strong.source.X.tobytes()
    assert none.target.fingerprint() != strong.target.fingerprint()
    artifact_none = fit_source_preprocessing(none.source, feature_budget=24)
    artifact_strong = fit_source_preprocessing(strong.source, feature_budget=24)
    assert artifact_none.to_json_bytes() == artifact_strong.to_json_bytes()


def test_perturbation_interface_cannot_accept_target_or_labels() -> None:
    parameters = inspect.signature(apply_perturbation).parameters
    assert set(parameters) == {"source", "specification"}
    assert "target" not in parameters
    assert "labels" not in parameters
    assert "y" not in parameters
