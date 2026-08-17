"""Frozen 40-dataset smoke grid."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from rep_audit.audit.config import AuditConfig, stable_seed
from rep_audit.experiments.job_spec import SimulationJobSpec
from rep_audit.simulation.generators import SimulationSpec


def make_smoke_grid(config: Mapping[str, object]) -> tuple[SimulationJobSpec, ...]:
    """Create eight selected cells with five deterministic replicates each."""

    simulation = dict(config["simulation"])  # type: ignore[arg-type]
    audit = dict(config["audit"])  # type: ignore[arg-type]
    cells = tuple(config["cells"])  # type: ignore[arg-type]
    replicates = int(config["replicates_per_cell"])
    base_seed = int(config["base_seed"])
    if len(cells) != 8 or replicates != 5:
        raise ValueError("frozen smoke grid requires eight cells and five replicates")
    jobs: list[SimulationJobSpec] = []
    for cell_index, raw_cell in enumerate(cells):
        cell = dict(raw_cell)
        for replicate in range(replicates):
            seed = stable_seed(
                base_seed,
                "simulation",
                cell_index,
                cell["regime"],
                cell["signal"],
                cell["shift"],
                replicate,
            )
            sim_spec = SimulationSpec(
                regime=str(cell["regime"]),
                signal=str(cell["signal"]),
                shift=str(cell["shift"]),
                replicate=replicate,
                seed=seed,
                n_source=int(simulation["n_source"]),
                n_target=int(simulation["n_target"]),
                p=int(simulation["p"]),
                k=int(simulation["k"]),
                informative_features=int(simulation["informative_features"]),
                protocol_version=str(config["protocol_version"]),
            )
            audit_config = AuditConfig(
                k=sim_spec.k,
                feature_budget=int(audit["feature_budget"]),
                relation_budget=int(audit["relation_budget"]),
                resamples=int(audit["resamples"]),
                seed=stable_seed(seed, "audit"),
                margin=float(audit["margin"]),
                alphas=tuple(float(value) for value in audit["alphas"]),
                perturbation_level=str(audit["perturbation_level"]),
                min_cluster_fraction=float(audit["min_cluster_fraction"]),
                relation_coverage_threshold=float(audit["relation_coverage_threshold"]),
                relation_entropy_threshold=float(audit["relation_entropy_threshold"]),
                relation_stability_threshold=float(audit["relation_stability_threshold"]),
                relation_screen_perturbations=int(audit["relation_screen_perturbations"]),
                protocol_version=str(config["protocol_version"]),
            )
            jobs.append(SimulationJobSpec(simulation=sim_spec, audit=audit_config))
    ordered = tuple(
        sorted(
            jobs,
            key=lambda job: (
                job.simulation.regime,
                job.simulation.signal,
                job.simulation.shift,
                job.simulation.replicate,
                job.job_id,
            ),
        )
    )
    if len(ordered) != 40 or len({job.job_id for job in ordered}) != 40:
        raise RuntimeError("smoke grid must contain 40 unique deterministic jobs")
    return ordered


def make_primary_grid(config: Mapping[str, object]) -> tuple[SimulationJobSpec, ...]:
    """Create the protocol's paired 630 source-to-target simulation jobs."""

    simulation = dict(config["simulation"])  # type: ignore[arg-type]
    audit = dict(config["audit"])  # type: ignore[arg-type]
    base_seed = int(config["base_seed"])
    replicates = int(config["replicates_per_cell"])
    if replicates != 30:
        raise ValueError("primary grid requires 30 replicates per cell")
    signal_cells = tuple(
        (regime, signal, shift)
        for regime in ("VALUE", "RELATIONAL", "HYBRID")
        for signal in ("moderate", "strong")
        for shift in ("none", "moderate", "strong")
    )
    null_cells = tuple(
        ("NULL", "none", shift) for shift in ("none", "moderate", "strong")
    )
    jobs: list[SimulationJobSpec] = []
    for regime, signal, shift in signal_cells + null_cells:
        for replicate in range(replicates):
            # The three shift levels are paired: one source cohort/audit is
            # transferred to three independently shifted target views.
            seed = stable_seed(
                base_seed, "primary_simulation", regime, signal, replicate
            )
            sim_spec = SimulationSpec(
                regime=regime,
                signal=signal,
                shift=shift,
                replicate=replicate,
                seed=seed,
                n_source=int(simulation["n_source"]),
                n_target=int(simulation["n_target"]),
                p=int(simulation["p"]),
                k=int(simulation["k"]),
                informative_features=int(simulation["informative_features"]),
                protocol_version=str(config["protocol_version"]),
            )
            audit_config = AuditConfig(
                k=sim_spec.k,
                feature_budget=int(audit["feature_budget"]),
                relation_budget=int(audit["relation_budget"]),
                resamples=int(audit["resamples"]),
                seed=stable_seed(seed, "audit"),
                margin=float(audit["margin"]),
                alphas=tuple(float(value) for value in audit["alphas"]),
                perturbation_level=str(audit["perturbation_level"]),
                min_cluster_fraction=float(audit["min_cluster_fraction"]),
                relation_coverage_threshold=float(audit["relation_coverage_threshold"]),
                relation_entropy_threshold=float(audit["relation_entropy_threshold"]),
                relation_stability_threshold=float(audit["relation_stability_threshold"]),
                relation_screen_perturbations=int(audit["relation_screen_perturbations"]),
                protocol_version=str(config["protocol_version"]),
            )
            jobs.append(SimulationJobSpec(simulation=sim_spec, audit=audit_config))
    ordered = tuple(
        sorted(
            jobs,
            key=lambda job: (
                job.simulation.regime,
                job.simulation.signal,
                job.simulation.shift,
                job.simulation.replicate,
                job.job_id,
            ),
        )
    )
    if len(ordered) != 630 or len({job.job_id for job in ordered}) != 630:
        raise RuntimeError("primary grid must contain 630 unique deterministic jobs")
    return ordered
