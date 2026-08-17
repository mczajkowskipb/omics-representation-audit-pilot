from __future__ import annotations

import json

from rep_audit.audit.config import AuditConfig
from rep_audit.experiments.full_runner import _prelabel_group, _validate_prelabel_job
from rep_audit.experiments.job_spec import SimulationJobSpec
from rep_audit.simulation.generators import SimulationSpec


def test_three_paired_shifts_freeze_without_labels(tmp_path) -> None:
    jobs = []
    for shift in ("none", "moderate", "strong"):
        spec = SimulationSpec(
            regime="RELATIONAL",
            signal="strong",
            shift=shift,
            replicate=0,
            seed=1818,
            n_source=36,
            n_target=36,
            p=24,
            k=3,
            informative_features=12,
        )
        jobs.append(
            SimulationJobSpec(
                simulation=spec,
                audit=AuditConfig(
                    k=3,
                    feature_budget=24,
                    relation_budget=50,
                    resamples=1,
                    seed=991,
                    relation_screen_perturbations=1,
                ),
            )
        )
    result = _prelabel_group(
        tuple(jobs),
        str(tmp_path),
        {"minimum_feature_coverage": 0.80, "minimum_relation_coverage": 0.80},
    )
    assert result["status"] == "completed"
    for job in jobs:
        path = tmp_path / "prelabel" / "jobs" / job.job_id
        _validate_prelabel_job(path, job.job_id)
        config = json.loads((path / "config.json").read_text())
        assignments = json.loads((path / "target_assignments.json").read_text())
        assert config["labels_loaded"] is False
        assert assignments["label_free"] is True
        assert "truth" not in json.dumps(assignments).lower()
        assert "class_label" not in json.dumps(assignments).lower()
