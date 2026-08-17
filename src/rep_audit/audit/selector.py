"""Null-calibrated conservative representation selector."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from rep_audit.audit.report import MethodAuditResult, SourceAuditReport
from rep_audit.io.canonical_json import (
    atomic_write_bytes,
    canonical_json_bytes,
    sha256_bytes,
)


DECISIONS = ("VALUE", "RELATIONAL", "HYBRID", "NO_STABLE_STRUCTURE")
_CONSERVATIVE_TIE_ORDER = {
    "NO_STABLE_STRUCTURE": 0,
    "VALUE": 1,
    "RELATIONAL": 2,
    "HYBRID": 3,
}


@dataclass(frozen=True, slots=True)
class NullCalibrationArtifact:
    k: int
    quantile: float
    method_thresholds: Mapping[str, float]
    method_counts: Mapping[str, int]
    delta_hybrid: float
    null_report_sha256: tuple[str, ...]
    multiple_testing_margin: float = 0.0

    def __post_init__(self) -> None:
        if self.k < 2:
            raise ValueError("k must be at least two")
        if not 0.0 < self.quantile < 1.0:
            raise ValueError("quantile must be strictly between zero and one")
        thresholds = dict(sorted((str(k), float(v)) for k, v in self.method_thresholds.items()))
        counts = dict(sorted((str(k), int(v)) for k, v in self.method_counts.items()))
        if thresholds.keys() != counts.keys() or not thresholds:
            raise ValueError("calibration thresholds and counts must be aligned")
        if any(not np.isfinite(value) or not 0.0 <= value <= 1.0 for value in thresholds.values()):
            raise ValueError("null thresholds must be finite and in [0, 1]")
        if any(value <= 0 for value in counts.values()):
            raise ValueError("every calibrated method needs null observations")
        if not np.isfinite(self.delta_hybrid) or self.delta_hybrid < 0.0:
            raise ValueError("delta_hybrid must be finite and non-negative")
        if not np.isfinite(
            self.multiple_testing_margin
        ) or not 0.0 <= self.multiple_testing_margin <= 1.0:
            raise ValueError("multiple_testing_margin must be in [0, 1]")
        object.__setattr__(self, "method_thresholds", MappingProxyType(thresholds))
        object.__setattr__(self, "method_counts", MappingProxyType(counts))
        object.__setattr__(self, "null_report_sha256", tuple(sorted(self.null_report_sha256)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "NullCalibrationArtifact/v1",
            "source_only": True,
            "k": self.k,
            "quantile": self.quantile,
            "quantile_method": "higher",
            "method_thresholds": dict(self.method_thresholds),
            "method_counts": dict(self.method_counts),
            "multiple_testing_margin": self.multiple_testing_margin,
            "multiple_testing_calibration": "cross_fitted_max_method_excess",
            "delta_hybrid": self.delta_hybrid,
            "null_report_sha256": self.null_report_sha256,
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def sha256(self) -> str:
        return sha256_bytes(self.to_json_bytes())

    def save(self, path: str | Path) -> None:
        atomic_write_bytes(path, self.to_json_bytes())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "NullCalibrationArtifact":
        if value.get("schema") != "NullCalibrationArtifact/v1":
            raise ValueError("not a NullCalibrationArtifact/v1")
        return cls(
            k=int(value["k"]),
            quantile=float(value["quantile"]),
            method_thresholds={
                str(key): float(item) for key, item in value["method_thresholds"].items()
            },
            method_counts={
                str(key): int(item) for key, item in value["method_counts"].items()
            },
            delta_hybrid=float(value["delta_hybrid"]),
            null_report_sha256=tuple(str(item) for item in value["null_report_sha256"]),
            multiple_testing_margin=float(value["multiple_testing_margin"]),
        )

    @classmethod
    def load(cls, path: str | Path) -> "NullCalibrationArtifact":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


@dataclass(frozen=True, slots=True)
class RepresentationSelection:
    decision: str
    uncertain: bool
    decision_confidence: float
    selected_method: str | None
    selected_k: int
    selected_alpha: float | None
    q_score: float | None
    null_threshold: float | None
    eligible_alternatives: tuple[str, ...]
    rejection_reasons: Mapping[str, str]
    vote_counts: Mapping[str, int]
    audit_report_sha256: tuple[str, ...]
    calibration_sha256: str

    def __post_init__(self) -> None:
        if self.decision not in DECISIONS:
            raise ValueError("unsupported representation decision")
        if not np.isfinite(self.decision_confidence) or not 0.0 <= self.decision_confidence <= 1.0:
            raise ValueError("decision_confidence must be in [0, 1]")
        if self.decision == "NO_STABLE_STRUCTURE" and self.selected_method is not None:
            raise ValueError("abstention cannot have a selected method")
        if self.decision != "NO_STABLE_STRUCTURE" and self.selected_method is None:
            raise ValueError("a selected family requires selected_method")
        if self.q_score is not None and not 0.0 <= self.q_score <= 1.0:
            raise ValueError("q_score must be in [0, 1]")
        if self.null_threshold is not None and not 0.0 <= self.null_threshold <= 1.0:
            raise ValueError("null_threshold must be in [0, 1]")
        object.__setattr__(
            self, "eligible_alternatives", tuple(sorted(self.eligible_alternatives))
        )
        object.__setattr__(
            self,
            "rejection_reasons",
            MappingProxyType(dict(sorted(self.rejection_reasons.items()))),
        )
        object.__setattr__(
            self,
            "vote_counts",
            MappingProxyType(dict(sorted(self.vote_counts.items()))),
        )
        object.__setattr__(self, "audit_report_sha256", tuple(sorted(self.audit_report_sha256)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "RepresentationSelection/v1",
            "source_only": True,
            "decision": self.decision,
            "uncertain": self.uncertain,
            "decision_confidence": self.decision_confidence,
            "selected_method": self.selected_method,
            "selected_k": self.selected_k,
            "selected_alpha": self.selected_alpha,
            "q_score": self.q_score,
            "null_threshold": self.null_threshold,
            "eligible_alternatives": self.eligible_alternatives,
            "rejection_reasons": dict(self.rejection_reasons),
            "vote_counts": dict(self.vote_counts),
            "audit_report_sha256": self.audit_report_sha256,
            "calibration_sha256": self.calibration_sha256,
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def sha256(self) -> str:
        return sha256_bytes(self.to_json_bytes())

    def save(self, path: str | Path) -> None:
        atomic_write_bytes(path, self.to_json_bytes())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RepresentationSelection":
        if value.get("schema") != "RepresentationSelection/v1":
            raise ValueError("not a RepresentationSelection/v1")
        return cls(
            decision=str(value["decision"]),
            uncertain=bool(value["uncertain"]),
            decision_confidence=float(value["decision_confidence"]),
            selected_method=(
                None if value["selected_method"] is None else str(value["selected_method"])
            ),
            selected_k=int(value["selected_k"]),
            selected_alpha=(
                None if value["selected_alpha"] is None else float(value["selected_alpha"])
            ),
            q_score=None if value["q_score"] is None else float(value["q_score"]),
            null_threshold=(
                None if value["null_threshold"] is None else float(value["null_threshold"])
            ),
            eligible_alternatives=tuple(str(item) for item in value["eligible_alternatives"]),
            rejection_reasons={
                str(key): str(item) for key, item in value["rejection_reasons"].items()
            },
            vote_counts={str(key): int(item) for key, item in value["vote_counts"].items()},
            audit_report_sha256=tuple(str(item) for item in value["audit_report_sha256"]),
            calibration_sha256=str(value["calibration_sha256"]),
        )

    @classmethod
    def load(cls, path: str | Path) -> "RepresentationSelection":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _higher_quantile(values: Sequence[float], quantile: float) -> float:
    return float(np.quantile(np.asarray(values, dtype=float), quantile, method="higher"))


def calibrate_null(
    null_reports: Sequence[SourceAuditReport],
    *,
    quantile: float = 0.90,
    minimum_hybrid_gain: float = 0.02,
) -> NullCalibrationArtifact:
    """Fit method-specific Q thresholds from source-only NULL reports."""

    reports = tuple(null_reports)
    if len(reports) < 3:
        raise ValueError("at least three NULL audit reports are required")
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must be strictly between zero and one")
    if minimum_hybrid_gain < 0.0:
        raise ValueError("minimum_hybrid_gain must be non-negative")
    k_values = {int(report.config["k"]) for report in reports}
    if len(k_values) != 1:
        raise ValueError("all NULL reports must use the same k")
    method_values: dict[str, list[float]] = defaultdict(list)
    hybrid_gains: list[float] = []
    for report in reports:
        by_family: dict[str, list[MethodAuditResult]] = defaultdict(list)
        for method in report.methods:
            method_values[method.method_id].append(method.q_score)
            by_family[method.family].append(method)
        pure_values = by_family.get("VALUE", []) + by_family.get("RELATIONAL", [])
        hybrids = by_family.get("HYBRID", [])
        if pure_values and hybrids:
            best_pure = max(item.q_score for item in pure_values)
            best_hybrid = max(item.q_score for item in hybrids)
            hybrid_gains.append(best_hybrid - best_pure)
    thresholds = {
        method: _higher_quantile(values, quantile)
        for method, values in sorted(method_values.items())
    }
    if not thresholds:
        raise ValueError("NULL reports contain no auditable methods")
    empirical_gain = (
        _higher_quantile(hybrid_gains, quantile) if hybrid_gains else 0.0
    )

    # Raw Q values from distinct representations need not share the same NULL
    # distribution.  Control the opportunity to select any of several methods
    # on the comparable scale "Q minus its own NULL threshold".  Each NULL
    # report is held out while its method thresholds are estimated, preventing
    # the report from calibrating its own excess.
    cross_fitted_max_excess: list[float] = []
    for held_out_index, held_out in enumerate(reports):
        training = reports[:held_out_index] + reports[held_out_index + 1 :]
        training_values: dict[str, list[float]] = defaultdict(list)
        for training_report in training:
            for method in training_report.methods:
                training_values[method.method_id].append(method.q_score)
        excesses = [
            method.q_score
            - _higher_quantile(training_values[method.method_id], quantile)
            for method in held_out.methods
            if method.nondegenerate and training_values.get(method.method_id)
        ]
        cross_fitted_max_excess.append(max(excesses, default=0.0))
    multiple_testing_margin = max(
        0.0, _higher_quantile(cross_fitted_max_excess, quantile)
    )
    return NullCalibrationArtifact(
        k=next(iter(k_values)),
        quantile=float(quantile),
        method_thresholds=thresholds,
        method_counts={method: len(values) for method, values in method_values.items()},
        delta_hybrid=float(max(minimum_hybrid_gain, empirical_gain)),
        null_report_sha256=tuple(report.sha256() for report in reports),
        multiple_testing_margin=float(multiple_testing_margin),
    )


@dataclass(frozen=True, slots=True)
class _SingleDecision:
    decision: str
    method: MethodAuditResult | None
    eligible_methods: tuple[str, ...]
    rejection_reasons: Mapping[str, str]


def _best(methods: Sequence[MethodAuditResult]) -> MethodAuditResult | None:
    if not methods:
        return None
    return sorted(
        methods,
        key=lambda item: (-item.q_score, item.complexity, item.method_id),
    )[0]


def _single_decision(
    report: SourceAuditReport,
    calibration: NullCalibrationArtifact,
    *,
    equivalence_margin: float,
) -> _SingleDecision:
    eligible: list[MethodAuditResult] = []
    rejection_reasons: dict[str, str] = {}
    for method in report.methods:
        method_threshold = calibration.method_thresholds.get(method.method_id)
        if method_threshold is None:
            rejection_reasons[method.method_id] = "no_null_threshold"
        elif not method.nondegenerate:
            rejection_reasons[method.method_id] = "degenerate"
        elif method.q_score <= min(
            1.0, method_threshold + calibration.multiple_testing_margin
        ):
            rejection_reasons[method.method_id] = "not_above_null_threshold"
        else:
            eligible.append(method)
    if not eligible:
        return _SingleDecision(
            decision="NO_STABLE_STRUCTURE",
            method=None,
            eligible_methods=(),
            rejection_reasons=rejection_reasons,
        )

    eligible_value = _best([item for item in eligible if item.family == "VALUE"])
    eligible_relational = _best(
        [item for item in eligible if item.family == "RELATIONAL"]
    )
    eligible_hybrid = _best([item for item in eligible if item.family == "HYBRID"])
    best_all_value = _best([item for item in report.methods if item.family == "VALUE"])
    best_all_relational = _best(
        [item for item in report.methods if item.family == "RELATIONAL"]
    )

    pure_candidates = [
        item for item in (eligible_value, eligible_relational) if item is not None
    ]
    selected_pure = _best(pure_candidates)
    if eligible_value is not None and eligible_relational is not None:
        if abs(eligible_value.q_score - eligible_relational.q_score) <= equivalence_margin:
            selected_pure = sorted(
                (eligible_value, eligible_relational),
                key=lambda item: (item.complexity, item.family != "VALUE", item.method_id),
            )[0]

    if eligible_hybrid is not None:
        pure_endpoints = [
            item
            for item in (best_all_value, best_all_relational)
            if item is not None
        ]
        if len(pure_endpoints) == 2:
            required = max(item.q_score for item in pure_endpoints) + calibration.delta_hybrid
            if eligible_hybrid.q_score > required:
                return _SingleDecision(
                    decision="HYBRID",
                    method=eligible_hybrid,
                    eligible_methods=tuple(item.method_id for item in eligible),
                    rejection_reasons=rejection_reasons,
                )
            rejection_reasons[eligible_hybrid.method_id] = (
                "insufficient_gain_over_both_pure_endpoints"
            )

    if selected_pure is None:
        return _SingleDecision(
            decision="NO_STABLE_STRUCTURE",
            method=None,
            eligible_methods=tuple(item.method_id for item in eligible),
            rejection_reasons=rejection_reasons,
        )
    return _SingleDecision(
        decision=selected_pure.family,
        method=selected_pure,
        eligible_methods=tuple(item.method_id for item in eligible),
        rejection_reasons=rejection_reasons,
    )


def _alpha_from_method(method_id: str | None) -> float | None:
    if method_id is None or not method_id.startswith("H_EUC_PAIR_A"):
        return None
    encoded = method_id.split("_A", 1)[1].split("_", 1)[0]
    return int(encoded) / 100.0


def select_representation(
    audit_reports: Sequence[SourceAuditReport],
    calibration: NullCalibrationArtifact,
    *,
    equivalence_margin: float = 0.02,
    minimum_decision_frequency: float = 0.60,
) -> RepresentationSelection:
    """Select a family from one or more outer source-only audit reports."""

    reports = tuple(audit_reports)
    if len(reports) == 0:
        raise ValueError("at least one audit report is required")
    if not 0.0 <= equivalence_margin <= 1.0:
        raise ValueError("equivalence_margin must be in [0, 1]")
    if not 0.0 < minimum_decision_frequency <= 1.0:
        raise ValueError("minimum_decision_frequency must be in (0, 1]")
    if any(int(report.config["k"]) != calibration.k for report in reports):
        raise ValueError("audit k does not match null calibration")

    decisions = tuple(
        _single_decision(
            report, calibration, equivalence_margin=equivalence_margin
        )
        for report in reports
    )
    vote_counts = Counter(item.decision for item in decisions)
    winning_decision = sorted(
        vote_counts,
        key=lambda decision: (
            -vote_counts[decision],
            _CONSERVATIVE_TIE_ORDER[decision],
        ),
    )[0]
    confidence = vote_counts[winning_decision] / len(decisions)
    winning_items = [item for item in decisions if item.decision == winning_decision]
    winning_methods = [item.method for item in winning_items if item.method is not None]
    selected_method = _best(winning_methods)
    method_id = None if selected_method is None else selected_method.method_id
    threshold = (
        None
        if method_id is None
        else min(
            1.0,
            calibration.method_thresholds.get(method_id, 0.0)
            + calibration.multiple_testing_margin,
        )
    )
    all_eligible = sorted(
        {
            method
            for decision in decisions
            for method in decision.eligible_methods
            if method != method_id
        }
    )
    rejection_reasons: dict[str, str] = {}
    for decision in decisions:
        for method, reason in decision.rejection_reasons.items():
            rejection_reasons.setdefault(method, reason)
    return RepresentationSelection(
        decision=winning_decision,
        uncertain=confidence < minimum_decision_frequency,
        decision_confidence=float(confidence),
        selected_method=method_id,
        selected_k=calibration.k,
        selected_alpha=_alpha_from_method(method_id),
        q_score=None if selected_method is None else selected_method.q_score,
        null_threshold=threshold,
        eligible_alternatives=tuple(all_eligible),
        rejection_reasons=rejection_reasons,
        vote_counts=dict(vote_counts),
        audit_report_sha256=tuple(report.sha256() for report in reports),
        calibration_sha256=calibration.sha256(),
    )
