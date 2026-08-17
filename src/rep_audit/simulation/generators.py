"""VALUE, RELATIONAL, HYBRID, and NULL source-target generators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from rep_audit.data.schema import DatasetBundle
from rep_audit.evaluation.external_labels import EvaluationLabels
from rep_audit.evaluation.simulation_truth import SimulationTruth
from rep_audit.io.canonical_json import canonical_json_bytes, sha256_bytes


REGIMES = ("VALUE", "RELATIONAL", "HYBRID", "NULL")
SIGNAL_LEVELS = ("none", "moderate", "strong")
SHIFT_LEVELS = ("none", "moderate", "strong")


@dataclass(frozen=True, slots=True)
class SimulationSpec:
    regime: str
    signal: str
    shift: str
    replicate: int
    seed: int
    n_source: int = 180
    n_target: int = 180
    p: int = 200
    k: int = 3
    informative_features: int = 30
    protocol_version: str = "1.0"

    def __post_init__(self) -> None:
        regime = str(self.regime).upper()
        signal = str(self.signal).lower()
        shift = str(self.shift).lower()
        if regime not in REGIMES:
            raise ValueError(f"regime must be one of {REGIMES}")
        if signal not in SIGNAL_LEVELS:
            raise ValueError(f"signal must be one of {SIGNAL_LEVELS}")
        if shift not in SHIFT_LEVELS:
            raise ValueError(f"shift must be one of {SHIFT_LEVELS}")
        if regime == "NULL" and signal != "none":
            raise ValueError("NULL simulations require signal='none'")
        if regime != "NULL" and signal not in {"moderate", "strong"}:
            raise ValueError("signal regimes require moderate or strong signal")
        integer_fields = {
            "replicate": self.replicate,
            "seed": self.seed,
            "n_source": self.n_source,
            "n_target": self.n_target,
            "p": self.p,
            "k": self.k,
            "informative_features": self.informative_features,
        }
        if any(
            not isinstance(value, int) or isinstance(value, bool)
            for value in integer_fields.values()
        ):
            raise TypeError("simulation counts and seed must be integers")
        if self.replicate < 0 or self.seed < 0:
            raise ValueError("replicate and seed must be non-negative")
        if self.k < 2:
            raise ValueError("k must be at least two")
        if self.n_source < 2 * self.k or self.n_target < 2 * self.k:
            raise ValueError("each cohort must contain at least two samples per cluster")
        if self.p < 4 or not 2 <= self.informative_features <= self.p:
            raise ValueError("informative_features must be in [2, p]")
        if regime in {"RELATIONAL", "HYBRID"} and self.informative_features < 6:
            raise ValueError("relational regimes require at least six informative features")
        object.__setattr__(self, "regime", regime)
        object.__setattr__(self, "signal", signal)
        object.__setattr__(self, "shift", shift)
        object.__setattr__(self, "protocol_version", str(self.protocol_version))

    @property
    def dataset_id(self) -> str:
        return (
            f"sim-{self.regime.lower()}-{self.signal}"
            f"-r{self.replicate:03d}-s{self.seed}"
        )

    @property
    def pair_id(self) -> str:
        return f"{self.dataset_id}-shift-{self.shift}"

    def source_generation_dict(self) -> dict[str, Any]:
        """Return fields allowed to influence source generation and identity."""

        value = self.to_dict()
        value.pop("shift")
        value["schema"] = "SourceSimulationSpec/v1"
        return value

    def source_generation_sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.source_generation_dict()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "SimulationSpec/v1",
            "protocol_version": self.protocol_version,
            "regime": self.regime,
            "signal": self.signal,
            "shift": self.shift,
            "replicate": self.replicate,
            "seed": self.seed,
            "n_source": self.n_source,
            "n_target": self.n_target,
            "p": self.p,
            "k": self.k,
            "informative_features": self.informative_features,
        }

    def sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.to_dict()))


@dataclass(frozen=True, slots=True)
class GeneratedSimulation:
    """Label-free matrices plus a physically separate evaluation truth object."""

    source: DatasetBundle
    target: DatasetBundle
    truth: SimulationTruth
    spec: SimulationSpec

    def __post_init__(self) -> None:
        if self.source.dataset_id != self.spec.dataset_id:
            raise ValueError("source dataset_id does not match the simulation spec")
        if self.target.dataset_id != self.spec.dataset_id:
            raise ValueError("target dataset_id does not match the simulation spec")
        if self.truth.source_labels.sample_ids != self.source.sample_ids:
            raise ValueError("source truth IDs must align with the source bundle")
        if self.truth.target_labels.sample_ids != self.target.sample_ids:
            raise ValueError("target truth IDs must align with the target bundle")


def _balanced_labels(n: int, k: int, rng: np.random.Generator) -> np.ndarray:
    labels = np.arange(n, dtype=np.int64) % k
    rng.shuffle(labels)
    return labels


def _class_codes(k: int) -> np.ndarray:
    return np.linspace(-1.0, 1.0, num=k, dtype=np.float64)


def _base_centers(p: int) -> np.ndarray:
    return np.arange(p, dtype=np.float64) * 6.0


def _value_matrix(
    labels: np.ndarray,
    spec: SimulationSpec,
    rng: np.random.Generator,
) -> np.ndarray:
    centers = _base_centers(spec.p)
    matrix = np.broadcast_to(centers, (len(labels), spec.p)).copy()
    amplitude = 1.25 if spec.signal == "moderate" else 2.15
    codes = _class_codes(spec.k)
    informative = np.arange(spec.informative_features)
    matrix[:, informative] += rng.normal(
        0.0, 0.22, size=(len(labels), spec.informative_features)
    )
    feature_signs = np.where(informative % 2 == 0, 1.0, -1.0)
    matrix[:, informative] += (
        amplitude * codes[labels, None] * feature_signs[None, :]
    )
    return matrix


def _relation_patterns(k: int, pair_count: int) -> np.ndarray:
    patterns = np.empty((k, pair_count), dtype=np.float64)
    for pair_index in range(pair_count):
        singled_out = pair_index % k
        patterns[:, pair_index] = 1.0
        patterns[singled_out, pair_index] = -1.0
        patterns[:, pair_index] -= patterns[:, pair_index].mean()
    return patterns


def _relational_matrix(
    labels: np.ndarray,
    spec: SimulationSpec,
    rng: np.random.Generator,
) -> np.ndarray:
    matrix = _base_centers(spec.p) + rng.normal(
        0.0, 0.28, size=(len(labels), spec.p)
    )
    pair_count = spec.informative_features // 2
    amplitude = 1.15 if spec.signal == "moderate" else 2.0
    patterns = _relation_patterns(spec.k, pair_count)
    for pair_index in range(pair_count):
        left = 2 * pair_index
        right = left + 1
        center = 12.0 * pair_index
        common = rng.normal(0.0, 3.2, size=len(labels))
        effect = amplitude * patterns[labels, pair_index]
        matrix[:, left] = center + common + effect / 2.0 + rng.normal(
            0.0, 0.12, size=len(labels)
        )
        matrix[:, right] = center + common - effect / 2.0 + rng.normal(
            0.0, 0.12, size=len(labels)
        )
    if 2 * pair_count < spec.p:
        start = 2 * pair_count
        matrix[:, start:] += 12.0 * pair_count
    return matrix


def _hybrid_matrix(
    labels: np.ndarray,
    spec: SimulationSpec,
    rng: np.random.Generator,
) -> np.ndarray:
    centers = np.arange(spec.p, dtype=np.float64) * 20.0
    matrix = np.broadcast_to(centers, (len(labels), spec.p)).copy()
    value_count = max(3, spec.informative_features // 2)
    relation_start = value_count
    relation_count = spec.informative_features - value_count
    pair_count = relation_count // 2
    amplitude = 2.0 if spec.signal == "moderate" else 3.5

    value_codes = np.full(spec.k, -1.0, dtype=np.float64)
    value_codes[0] = 1.0
    value_codes -= value_codes.mean()
    value_signs = np.where(np.arange(value_count) % 2 == 0, 1.0, -1.0)
    matrix[:, :value_count] += (
        amplitude * value_codes[labels, None] * value_signs[None, :]
    )
    matrix[:, :value_count] += rng.normal(
        0.0, 0.10, size=(len(labels), value_count)
    )

    relation_codes = np.full(spec.k, 1.0, dtype=np.float64)
    relation_codes[-1] = -1.0
    relation_codes -= relation_codes.mean()
    for pair_index in range(pair_count):
        left = relation_start + 2 * pair_index
        right = left + 1
        center = 20.0 * (value_count + pair_index)
        common = rng.normal(0.0, 10.0, size=len(labels))
        effect = amplitude * relation_codes[labels]
        matrix[:, left] = center + common + effect / 2.0 + rng.normal(
            0.0, 0.05, size=len(labels)
        )
        matrix[:, right] = center + common - effect / 2.0 + rng.normal(
            0.0, 0.05, size=len(labels)
        )
    return matrix


def _null_matrix(
    n: int,
    spec: SimulationSpec,
    rng: np.random.Generator,
) -> np.ndarray:
    pair_centers = np.repeat(
        np.arange((spec.p + 1) // 2, dtype=np.float64) * 12.0, 2
    )[: spec.p]
    matrix = pair_centers + rng.normal(0.0, 2.5, size=(n, spec.p))
    continuous_nuisance = rng.normal(0.0, 0.12, size=(n, 1))
    return matrix + continuous_nuisance


def _generate_biology(
    labels: np.ndarray,
    spec: SimulationSpec,
    rng: np.random.Generator,
) -> np.ndarray:
    if spec.regime == "VALUE":
        return _value_matrix(labels, spec, rng)
    if spec.regime == "RELATIONAL":
        return _relational_matrix(labels, spec, rng)
    if spec.regime == "HYBRID":
        return _hybrid_matrix(labels, spec, rng)
    return _null_matrix(len(labels), spec, rng)


def _apply_source_nuisance(
    matrix: np.ndarray, rng: np.random.Generator, *, regime: str
) -> np.ndarray:
    if regime == "HYBRID":
        return np.array(matrix, dtype=np.float64, copy=True)
    if regime == "VALUE":
        # The VALUE control must express cluster-specific magnitudes rather than
        # clusters induced by a sample-wide multiplicative technical factor.
        # Target-side scaling remains part of the transfer stress test.
        return np.array(matrix, dtype=np.float64, copy=True)
    scales = rng.lognormal(mean=0.0, sigma=0.015, size=(len(matrix), 1))
    offsets = rng.normal(0.0, 0.08, size=(len(matrix), 1))
    return matrix * scales + offsets


def _strict_monotone_power(matrix: np.ndarray, gamma: np.ndarray) -> np.ndarray:
    return np.sign(matrix) * np.power(np.abs(matrix), gamma)


def _apply_target_shift(
    matrix: np.ndarray,
    feature_ids: tuple[str, ...],
    level: str,
    rng: np.random.Generator,
) -> tuple[np.ndarray, tuple[str, ...]]:
    shifted = np.array(matrix, dtype=np.float64, copy=True)
    if level == "none":
        return shifted, feature_ids

    if level == "moderate":
        scale_sigma = 0.06
        sample_offset_sd = 0.25
        gene_offset_sd = 0.12
        noise_sd = 0.18
        missing_entry_rate = 0.01
        missing_feature_rate = 0.0
        gamma_sd = 0.015
        quantum = 0.0
    else:
        scale_sigma = 0.14
        sample_offset_sd = 0.65
        gene_offset_sd = 0.45
        noise_sd = 0.42
        missing_entry_rate = 0.05
        missing_feature_rate = 0.05
        gamma_sd = 0.04
        quantum = 0.25

    scales = rng.lognormal(mean=0.0, sigma=scale_sigma, size=(len(shifted), 1))
    offsets = rng.normal(0.0, sample_offset_sd, size=(len(shifted), 1))
    shifted = shifted * scales + offsets
    gamma = rng.normal(1.0, gamma_sd, size=(len(shifted), 1))
    gamma = np.clip(gamma, 0.85, 1.15)
    shifted = _strict_monotone_power(shifted, gamma)
    shifted += rng.normal(0.0, gene_offset_sd, size=(1, shifted.shape[1]))
    shifted += rng.normal(0.0, noise_sd, size=shifted.shape)
    if quantum > 0.0:
        shifted = np.round(shifted / quantum) * quantum
    missing = rng.random(shifted.shape) < missing_entry_rate
    shifted[missing] = np.nan

    if missing_feature_rate > 0.0:
        drop_count = max(1, int(np.floor(len(feature_ids) * missing_feature_rate)))
        dropped = set(
            int(index)
            for index in rng.choice(len(feature_ids), size=drop_count, replace=False)
        )
        keep = [index for index in range(len(feature_ids)) if index not in dropped]
        shifted = shifted[:, keep]
        feature_ids = tuple(feature_ids[index] for index in keep)
    return shifted, feature_ids


def generate_simulation(spec: SimulationSpec) -> GeneratedSimulation:
    """Generate independent cohorts and separate their evaluation labels."""

    seed_sequence = np.random.SeedSequence(spec.seed)
    source_label_seed, target_label_seed, source_seed, target_seed, shift_seed = (
        seed_sequence.spawn(5)
    )
    source_labels = _balanced_labels(
        spec.n_source, spec.k, np.random.default_rng(source_label_seed)
    )
    target_labels = _balanced_labels(
        spec.n_target, spec.k, np.random.default_rng(target_label_seed)
    )
    source_matrix = _generate_biology(
        source_labels, spec, np.random.default_rng(source_seed)
    )
    target_matrix = _generate_biology(
        target_labels, spec, np.random.default_rng(target_seed)
    )
    source_matrix = _apply_source_nuisance(
        source_matrix,
        np.random.default_rng(source_seed.spawn(1)[0]),
        regime=spec.regime,
    )

    feature_ids = tuple(f"g{index:04d}" for index in range(spec.p))
    target_matrix, target_feature_ids = _apply_target_shift(
        target_matrix,
        feature_ids,
        spec.shift,
        np.random.default_rng(shift_seed),
    )
    source_ids = tuple(f"src_{index:04d}" for index in range(spec.n_source))
    target_ids = tuple(f"tgt_{index:04d}" for index in range(spec.n_target))
    source_metadata = {
        "generator": "representation_regimes_v1",
        "source_generation_sha256": spec.source_generation_sha256(),
        "regime_hidden_from_fit": "true",
    }
    target_metadata = {
        "generator": "representation_regimes_v1",
        "pair_spec_sha256": spec.sha256(),
        "target_shift": spec.shift,
        "regime_hidden_from_fit": "true",
    }
    source = DatasetBundle(
        X=source_matrix,
        sample_ids=source_ids,
        feature_ids=feature_ids,
        dataset_id=spec.dataset_id,
        platform_id="SIM_SOURCE_V1",
        cohort_id="source",
        metadata=source_metadata,
    )
    target = DatasetBundle(
        X=target_matrix,
        sample_ids=target_ids,
        feature_ids=target_feature_ids,
        dataset_id=spec.dataset_id,
        platform_id="SIM_TARGET_V1",
        cohort_id="target",
        metadata=target_metadata,
    )
    expected = "NO_STABLE_STRUCTURE" if spec.regime == "NULL" else spec.regime
    truth = SimulationTruth(
        regime=spec.regime,
        expected_decision=expected,
        source_labels=EvaluationLabels(
            dataset_id=spec.dataset_id,
            sample_ids=source_ids,
            values=tuple(f"C{label}" for label in source_labels),
            label_name="simulation_cluster",
        ),
        target_labels=EvaluationLabels(
            dataset_id=spec.dataset_id,
            sample_ids=target_ids,
            values=tuple(f"C{label}" for label in target_labels),
            label_name="simulation_cluster",
        ),
    )
    return GeneratedSimulation(source=source, target=target, truth=truth, spec=spec)
