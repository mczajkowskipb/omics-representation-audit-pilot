"""Canonical job specification and deterministic job ID."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rep_audit.audit.config import AuditConfig
from rep_audit.io.canonical_json import canonical_json_bytes, sha256_bytes
from rep_audit.simulation.generators import SimulationSpec


@dataclass(frozen=True, slots=True)
class SimulationJobSpec:
    simulation: SimulationSpec
    audit: AuditConfig
    source_target_direction: str = "source_to_target"

    def __post_init__(self) -> None:
        if self.source_target_direction != "source_to_target":
            raise ValueError("PILOT-011 supports only source_to_target simulation jobs")
        if self.audit.k != self.simulation.k:
            raise ValueError("simulation and audit k must match")
        if self.audit.feature_budget > self.simulation.p:
            raise ValueError("feature budget cannot exceed simulated p")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "SimulationJobSpec/v1",
            "protocol_version": self.simulation.protocol_version,
            "dataset_regime": self.simulation.regime,
            "source_target_direction": self.source_target_direction,
            "representation_method": "SOURCE_ONLY_AUDIT_ALL_MATCHED_PAM",
            "k": self.audit.k,
            "feature_budget": self.audit.feature_budget,
            "relation_budget": self.audit.relation_budget,
            "margin": self.audit.margin,
            "alphas": self.audit.alphas,
            "replicate": self.simulation.replicate,
            "seed": self.simulation.seed,
            "simulation": self.simulation.to_dict(),
            "audit": self.audit.to_dict(),
        }

    @property
    def job_id(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.to_dict()))
