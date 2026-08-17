from __future__ import annotations

from pathlib import Path

import yaml

from rep_audit.experiments.grid import make_smoke_grid


ROOT = Path(__file__).resolve().parents[2]


def test_frozen_smoke_grid_has_eight_cells_times_five_replicates() -> None:
    config = yaml.safe_load((ROOT / "configs" / "smoke.yml").read_text(encoding="utf-8"))
    first = make_smoke_grid(config)
    second = make_smoke_grid(config)
    assert len(first) == 40
    assert tuple(job.job_id for job in first) == tuple(job.job_id for job in second)
    assert len({job.job_id for job in first}) == 40
    cells = {
        (
            job.simulation.regime,
            job.simulation.signal,
            job.simulation.shift,
        )
        for job in first
    }
    assert len(cells) == 8
    assert all(job.audit.resamples == 5 for job in first)
    assert all(job.audit.feature_budget == 200 for job in first)
    assert all(job.audit.relation_budget == 500 for job in first)


def test_job_id_changes_when_any_experimental_axis_changes() -> None:
    config = yaml.safe_load((ROOT / "configs" / "smoke.yml").read_text(encoding="utf-8"))
    jobs = make_smoke_grid(config)
    ids = {job.job_id for job in jobs}
    assert len(ids) == len(jobs)
    assert all(len(job_id) == 64 for job_id in ids)
