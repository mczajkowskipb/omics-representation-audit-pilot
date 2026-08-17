"""Build matched source representations and frozen perturbation distances."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np

from rep_audit.audit.config import AuditConfig, stable_seed
from rep_audit.data.schema import DatasetBundle
from rep_audit.distances.footrule import footrule_distance_matrix
from rep_audit.distances.hybrid import HybridScaleArtifact, fit_hybrid_scales
from rep_audit.distances.relation_hamming import relation_hamming_distance_matrix
from rep_audit.distances.validation import DistanceMatrix
from rep_audit.distances.value import (
    correlation_distance_matrix,
    euclidean_distance_matrix,
)
from rep_audit.preprocessing.artifact import SourcePreprocessingArtifact
from rep_audit.preprocessing.robust import fit_source_preprocessing
from rep_audit.representations.ranks import average_rank_encode
from rep_audit.representations.relation_screen import (
    NoEligibleRelationsError,
    RelationScreenArtifact,
    screen_source_relations,
)
from rep_audit.representations.ternary_relations import encode_ternary_relations


VALUE_METHODS = ("V_EUC_PAM", "V_COR_PAM")
RELATIONAL_METHODS = ("R_FOOT_PAM", "R_PAIR_PAM")


def hybrid_method_id(alpha: float) -> str:
    return f"H_EUC_PAIR_A{int(round(alpha * 100)):03d}_PAM"


def method_family(method_id: str) -> str:
    if method_id in VALUE_METHODS:
        return "VALUE"
    if method_id in RELATIONAL_METHODS:
        return "RELATIONAL"
    if method_id.startswith("H_EUC_PAIR_A"):
        return "HYBRID"
    raise ValueError(f"unknown method_id: {method_id}")


@dataclass(frozen=True, slots=True)
class FrozenDistanceSet:
    distances: Mapping[str, DistanceMatrix]
    failures: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "distances", MappingProxyType(dict(sorted(self.distances.items())))
        )
        object.__setattr__(
            self, "failures", MappingProxyType(dict(sorted(self.failures.items())))
        )


@dataclass(frozen=True, slots=True)
class SourceRepresentationSet:
    source_fingerprint: str
    sample_ids: tuple[str, ...]
    preprocessing: SourcePreprocessingArtifact
    relation_screen: RelationScreenArtifact | None
    hybrid_scales: HybridScaleArtifact | None
    distances: Mapping[str, DistanceMatrix]
    complexities: Mapping[str, int]
    failures: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "sample_ids", tuple(self.sample_ids))
        object.__setattr__(
            self, "distances", MappingProxyType(dict(sorted(self.distances.items())))
        )
        object.__setattr__(
            self, "complexities", MappingProxyType(dict(sorted(self.complexities.items())))
        )
        object.__setattr__(
            self, "failures", MappingProxyType(dict(sorted(self.failures.items())))
        )
        if any(matrix.sample_ids != self.sample_ids for matrix in self.distances.values()):
            raise ValueError("all source distances must align with sample_ids")

    def manifest(self) -> dict[str, object]:
        return {
            "schema": "SourceRepresentationSet/v1",
            "source_only": True,
            "source_fingerprint": self.source_fingerprint,
            "sample_ids": self.sample_ids,
            "preprocessing_sha256": self.preprocessing.sha256(),
            "preprocessing": self.preprocessing.to_dict(),
            "relation_screen_sha256": (
                None if self.relation_screen is None else self.relation_screen.sha256()
            ),
            "relation_screen": (
                None if self.relation_screen is None else self.relation_screen.to_dict()
            ),
            "hybrid_scale_sha256": (
                None if self.hybrid_scales is None else self.hybrid_scales.sha256()
            ),
            "hybrid_scales": (
                None if self.hybrid_scales is None else self.hybrid_scales.to_dict()
            ),
            "distance_sha256": {
                method: distance.fingerprint()
                for method, distance in self.distances.items()
            },
            "complexities": dict(self.complexities),
            "failures": dict(self.failures),
        }


def _safe_add(
    target: dict[str, DistanceMatrix],
    failures: dict[str, str],
    method_id: str,
    factory,
) -> None:
    try:
        target[method_id] = factory()
    except (ValueError, FloatingPointError) as error:
        failures[method_id] = f"{type(error).__name__}: {error}"


def build_source_representations(
    source: DatasetBundle,
    config: AuditConfig,
) -> SourceRepresentationSet:
    """Fit all representation artifacts using only the complete source cohort."""

    preprocessing = fit_source_preprocessing(
        source,
        feature_budget=config.feature_budget,
        protocol_version=config.protocol_version,
    )
    selected = preprocessing.selected_feature_ids
    values = preprocessing.transform(source)
    distances: dict[str, DistanceMatrix] = {}
    failures: dict[str, str] = {}
    complexities: dict[str, int] = {}

    _safe_add(distances, failures, "V_EUC_PAM", lambda: euclidean_distance_matrix(values))
    _safe_add(
        distances,
        failures,
        "V_COR_PAM",
        lambda: correlation_distance_matrix(values),
    )
    for method in VALUE_METHODS:
        if method in distances:
            complexities[method] = len(selected)

    ranks = average_rank_encode(source, feature_ids=selected)
    _safe_add(distances, failures, "R_FOOT_PAM", lambda: footrule_distance_matrix(ranks))
    if "R_FOOT_PAM" in distances:
        complexities["R_FOOT_PAM"] = len(selected)

    relation_screen: RelationScreenArtifact | None = None
    try:
        relation_screen = screen_source_relations(
            source,
            feature_ids=selected,
            margin=config.margin,
            relation_budget=config.relation_budget,
            coverage_threshold=config.relation_coverage_threshold,
            entropy_threshold=config.relation_entropy_threshold,
            stability_threshold=config.relation_stability_threshold,
            perturbation_count=config.relation_screen_perturbations,
            perturbation_seed=stable_seed(config.seed, "relation_screen"),
        )
        relations = encode_ternary_relations(
            ranks, relation_screen.relation_pairs, margin=config.margin
        )
        distances["R_PAIR_PAM"] = relation_hamming_distance_matrix(
            relations, weights=relation_screen.weights
        )
        complexities["R_PAIR_PAM"] = len(relation_screen.relation_pairs)
    except (NoEligibleRelationsError, ValueError, FloatingPointError) as error:
        failures["R_PAIR_PAM"] = f"{type(error).__name__}: {error}"

    hybrid_scales: HybridScaleArtifact | None = None
    if "V_EUC_PAM" in distances and "R_PAIR_PAM" in distances:
        hybrid_scales = fit_hybrid_scales(
            distances["V_EUC_PAM"], distances["R_PAIR_PAM"]
        )
        for alpha in config.alphas:
            method = hybrid_method_id(alpha)
            hybrid_values = (
                (1.0 - alpha)
                * distances["V_EUC_PAM"].values
                / hybrid_scales.value_scale
                + alpha
                * distances["R_PAIR_PAM"].values
                / hybrid_scales.relational_scale
            )
            distances[method] = DistanceMatrix(
                values=hybrid_values,
                sample_ids=source.sample_ids,
                metric_id=f"hybrid_value_relation_alpha_{alpha:.2f}",
            )
            complexities[method] = len(selected) + len(relation_screen.relation_pairs)
    else:
        reason = "hybrid endpoints unavailable"
        for alpha in config.alphas:
            failures[hybrid_method_id(alpha)] = reason

    return SourceRepresentationSet(
        source_fingerprint=source.fingerprint(),
        sample_ids=source.sample_ids,
        preprocessing=preprocessing,
        relation_screen=relation_screen,
        hybrid_scales=hybrid_scales,
        distances=distances,
        complexities=complexities,
        failures=failures,
    )


def build_frozen_perturbation_distances(
    perturbed_source: DatasetBundle,
    fitted: SourceRepresentationSet,
    config: AuditConfig,
) -> FrozenDistanceSet:
    """Apply frozen source artifacts to a perturbed view without refitting."""

    if perturbed_source.sample_ids != fitted.sample_ids:
        raise ValueError("perturbed source must preserve ordered sample IDs")
    distances: dict[str, DistanceMatrix] = {}
    failures: dict[str, str] = {}
    values = fitted.preprocessing.transform(perturbed_source)
    _safe_add(distances, failures, "V_EUC_PAM", lambda: euclidean_distance_matrix(values))
    _safe_add(
        distances,
        failures,
        "V_COR_PAM",
        lambda: correlation_distance_matrix(values),
    )
    ranks = average_rank_encode(
        perturbed_source, feature_ids=fitted.preprocessing.selected_feature_ids
    )
    _safe_add(distances, failures, "R_FOOT_PAM", lambda: footrule_distance_matrix(ranks))
    if fitted.relation_screen is not None:
        try:
            relations = encode_ternary_relations(
                ranks,
                fitted.relation_screen.relation_pairs,
                margin=fitted.relation_screen.margin,
            )
            distances["R_PAIR_PAM"] = relation_hamming_distance_matrix(
                relations, weights=fitted.relation_screen.weights
            )
        except (ValueError, FloatingPointError) as error:
            failures["R_PAIR_PAM"] = f"{type(error).__name__}: {error}"
    else:
        failures["R_PAIR_PAM"] = "no frozen relation screen artifact"

    if fitted.hybrid_scales is not None:
        for alpha in config.alphas:
            method = hybrid_method_id(alpha)
            if "V_EUC_PAM" not in distances or "R_PAIR_PAM" not in distances:
                failures[method] = "hybrid perturbation endpoint unavailable"
                continue
            hybrid_values = (
                (1.0 - alpha)
                * distances["V_EUC_PAM"].values
                / fitted.hybrid_scales.value_scale
                + alpha
                * distances["R_PAIR_PAM"].values
                / fitted.hybrid_scales.relational_scale
            )
            distances[method] = DistanceMatrix(
                values=hybrid_values,
                sample_ids=perturbed_source.sample_ids,
                metric_id=f"frozen_hybrid_alpha_{alpha:.2f}",
            )
    return FrozenDistanceSet(distances=distances, failures=failures)
