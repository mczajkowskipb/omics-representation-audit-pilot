"""Deterministic source-only perturbations used by the Representation Audit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from rep_audit.data.schema import DatasetBundle
from rep_audit.io.canonical_json import canonical_json_bytes, sha256_bytes


PERTURBATION_KINDS = (
    "sample_monotone",
    "gene_offset",
    "additive_noise",
    "feature_dropout",
    "quantization",
)
PERTURBATION_LEVELS = ("small", "moderate", "strong")


@dataclass(frozen=True, slots=True)
class PerturbationSpec:
    kind: str
    level: str
    replicate: int
    seed: int

    def __post_init__(self) -> None:
        kind = str(self.kind).lower()
        level = str(self.level).lower()
        if kind not in PERTURBATION_KINDS:
            raise ValueError(f"kind must be one of {PERTURBATION_KINDS}")
        if level not in PERTURBATION_LEVELS:
            raise ValueError(f"level must be one of {PERTURBATION_LEVELS}")
        if (
            not isinstance(self.replicate, int)
            or isinstance(self.replicate, bool)
            or self.replicate < 0
        ):
            raise ValueError("replicate must be a non-negative integer")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "level", level)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "PerturbationSpec/v1",
            "kind": self.kind,
            "level": self.level,
            "replicate": self.replicate,
            "seed": self.seed,
        }

    def sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.to_dict()))


def _feature_scales(matrix: np.ndarray) -> np.ndarray:
    scales = np.empty(matrix.shape[1], dtype=np.float64)
    for index in range(matrix.shape[1]):
        observed = matrix[:, index][~np.isnan(matrix[:, index])]
        if observed.size < 2:
            scales[index] = 1.0
            continue
        q25, q75 = np.quantile(observed, [0.25, 0.75], method="linear")
        value = float(q75 - q25)
        scales[index] = value if np.isfinite(value) and value > 0.0 else 1.0
    return scales


def _level_value(level: str, small: float, moderate: float, strong: float) -> float:
    return {"small": small, "moderate": moderate, "strong": strong}[level]


def apply_perturbation(
    source: DatasetBundle,
    specification: PerturbationSpec,
) -> DatasetBundle:
    """Perturb only ``X`` while preserving the source schema and ID order."""

    rng = np.random.default_rng(specification.seed)
    sample_order = np.asarray(
        sorted(range(len(source.sample_ids)), key=lambda index: source.sample_ids[index]),
        dtype=int,
    )
    feature_order = np.asarray(
        sorted(range(len(source.feature_ids)), key=lambda index: source.feature_ids[index]),
        dtype=int,
    )
    matrix = np.array(
        source.X[np.ix_(sample_order, feature_order)], dtype=np.float64, copy=True
    )
    scales = _feature_scales(matrix)

    if specification.kind == "sample_monotone":
        gamma_sd = _level_value(specification.level, 0.01, 0.03, 0.08)
        gamma = np.clip(
            rng.normal(1.0, gamma_sd, size=(len(source.sample_ids), 1)),
            0.75,
            1.25,
        )
        matrix = np.sign(matrix) * np.power(np.abs(matrix), gamma)
    elif specification.kind == "gene_offset":
        multiplier = _level_value(specification.level, 0.05, 0.20, 0.55)
        matrix += rng.normal(0.0, multiplier * scales, size=(1, matrix.shape[1]))
    elif specification.kind == "additive_noise":
        multiplier = _level_value(specification.level, 0.03, 0.10, 0.30)
        matrix += rng.normal(
            0.0, multiplier * scales, size=matrix.shape
        )
    elif specification.kind == "feature_dropout":
        rate = _level_value(specification.level, 0.01, 0.04, 0.12)
        missing = rng.random(matrix.shape) < rate
        matrix[missing] = np.nan
    elif specification.kind == "quantization":
        multiplier = _level_value(specification.level, 0.02, 0.08, 0.20)
        quantum = np.maximum(multiplier * scales, np.finfo(float).eps)
        matrix = np.round(matrix / quantum) * quantum

    restored = np.empty_like(matrix)
    restored[np.ix_(sample_order, feature_order)] = matrix
    metadata = dict(source.metadata)
    metadata.update(
        {
            "perturbation_sha256": specification.sha256(),
            "perturbation_kind": specification.kind,
            "perturbation_level": specification.level,
        }
    )
    return DatasetBundle(
        X=restored,
        sample_ids=source.sample_ids,
        feature_ids=source.feature_ids,
        dataset_id=source.dataset_id,
        platform_id=source.platform_id,
        cohort_id=source.cohort_id,
        metadata=metadata,
    )


def audit_perturbation_suite(
    *,
    count: int,
    seed: int,
    level: str = "moderate",
) -> tuple[PerturbationSpec, ...]:
    """Return a deterministic balanced cycle over all protocol perturbations."""

    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise ValueError("count must be a positive integer")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if level not in PERTURBATION_LEVELS:
        raise ValueError(f"level must be one of {PERTURBATION_LEVELS}")
    child_seeds = np.random.SeedSequence(seed).spawn(count)
    return tuple(
        PerturbationSpec(
            kind=PERTURBATION_KINDS[index % len(PERTURBATION_KINDS)],
            level=level,
            replicate=index,
            seed=int(child_seeds[index].generate_state(1, dtype=np.uint32)[0]),
        )
        for index in range(count)
    )
