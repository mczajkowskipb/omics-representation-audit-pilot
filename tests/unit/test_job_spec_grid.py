from __future__ import annotations

from pathlib import Path

import yaml

from rep_audit.experiments.grid import make_primary_grid, make_smoke_grid


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


def test_primary_grid_has_exact_protocol_cells_and_paired_sources() -> None:
    config = yaml.safe_load((ROOT / "configs" / "full630.yml").read_text())
    jobs = make_primary_grid(config)
    assert len(jobs) == len({job.job_id for job in jobs}) == 630
    counts: dict[tuple[str, str, str], int] = {}
    paired: dict[tuple[str, str, int], set[int]] = {}
    for job in jobs:
        spec = job.simulation
        cell = (spec.regime, spec.signal, spec.shift)
        counts[cell] = counts.get(cell, 0) + 1
        paired.setdefault((spec.regime, spec.signal, spec.replicate), set()).add(spec.seed)
    assert len(counts) == 21
    assert set(counts.values()) == {30}
    assert len(paired) == 210
    assert all(len(seeds) == 1 for seeds in paired.values())
