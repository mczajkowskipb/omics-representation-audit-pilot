from __future__ import annotations

from rep_audit.audit.config import AuditConfig
from rep_audit.audit.diagnostics import run_source_audit
from rep_audit.simulation.generators import SimulationSpec, generate_simulation


def _spec(shift: str) -> SimulationSpec:
    return SimulationSpec(
        regime="RELATIONAL",
        signal="strong",
        shift=shift,
        replicate=1,
        seed=712,
        n_source=30,
        n_target=30,
        p=24,
        k=3,
        informative_features=12,
    )


def test_target_values_and_shift_cannot_change_source_audit_artifact() -> None:
    none = generate_simulation(_spec("none"))
    strong = generate_simulation(_spec("strong"))
    config = AuditConfig(
        k=3,
        feature_budget=24,
        relation_budget=20,
        resamples=2,
        seed=55,
        relation_screen_perturbations=1,
        relation_stability_threshold=0.50,
    )
    before = run_source_audit(none.source, config).to_json_bytes()
    assert none.target.fingerprint() != strong.target.fingerprint()
    after = run_source_audit(strong.source, config).to_json_bytes()
    assert before == after
