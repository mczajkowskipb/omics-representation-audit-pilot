"""Fit robust preprocessing exclusively on a source ``DatasetBundle``."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from rep_audit.data.schema import DatasetBundle
from rep_audit.io.canonical_json import canonical_json_bytes, sha256_bytes
from rep_audit.preprocessing.artifact import SourcePreprocessingArtifact


def _selection_universe(
    source: DatasetBundle, allowed_feature_ids: Iterable[object] | None
) -> tuple[str, ...]:
    if allowed_feature_ids is None:
        return tuple(sorted(source.feature_ids))
    normalized = tuple(str(item) for item in allowed_feature_ids)
    if len(normalized) != len(set(normalized)):
        raise ValueError("allowed_feature_ids must be unique")
    unknown = sorted(set(normalized).difference(source.feature_ids))
    if unknown:
        raise ValueError(
            "allowed_feature_ids contains features absent from source: "
            + ", ".join(unknown[:10])
        )
    return tuple(sorted(normalized))


def fit_source_preprocessing(
    source: DatasetBundle,
    *,
    feature_budget: int,
    allowed_feature_ids: Iterable[object] | None = None,
    protocol_version: str = "1.0",
) -> SourcePreprocessingArtifact:
    """Fit source MAD selection, median imputation, and median/IQR scaling.

    No target matrix or label object is accepted by this interface. A target
    may contribute only a label-free feature-ID intersection prepared outside
    this function and passed through ``allowed_feature_ids``.
    """

    if feature_budget <= 0:
        raise ValueError("feature_budget must be positive")
    universe = _selection_universe(source, allowed_feature_ids)
    feature_to_index = {
        feature_id: index for index, feature_id in enumerate(source.feature_ids)
    }

    candidates: list[dict[str, object]] = []
    for feature_id in universe:
        values = np.asarray(source.X[:, feature_to_index[feature_id]], dtype=float)
        observed = values[~np.isnan(values)]
        if observed.size == 0:
            continue
        median = float(np.median(observed))
        mad = float(np.median(np.abs(observed - median)))
        imputed = np.where(np.isnan(values), median, values)
        q25, q75 = np.quantile(imputed, [0.25, 0.75], method="linear")
        iqr = float(q75 - q25)
        fallback = not np.isfinite(iqr) or iqr <= 0.0
        scale = 1.0 if fallback else iqr
        candidates.append(
            {
                "feature_id": feature_id,
                "median": median,
                "mad": mad,
                "iqr": 0.0 if fallback and not np.isfinite(iqr) else iqr,
                "fallback": fallback,
                "scale": scale,
            }
        )

    if len(candidates) < feature_budget:
        raise ValueError(
            f"only {len(candidates)} eligible source features for budget {feature_budget}"
        )
    selected = sorted(
        candidates,
        key=lambda item: (-float(item["mad"]), str(item["feature_id"])),
    )[:feature_budget]

    universe_sha = sha256_bytes(
        canonical_json_bytes({"feature_ids": universe, "schema": "FeatureUniverse/v1"})
    )
    return SourcePreprocessingArtifact(
        schema_version=1,
        protocol_version=str(protocol_version),
        source_dataset_id=source.dataset_id,
        source_cohort_id=source.cohort_id,
        source_fingerprint=source.fingerprint(),
        selection_universe_sha256=universe_sha,
        selection_universe_size=len(universe),
        feature_budget=feature_budget,
        selected_feature_ids=tuple(str(item["feature_id"]) for item in selected),
        source_medians=tuple(float(item["median"]) for item in selected),
        source_iqrs=tuple(float(item["iqr"]) for item in selected),
        scale_denominators=tuple(float(item["scale"]) for item in selected),
        iqr_fallback=tuple(bool(item["fallback"]) for item in selected),
        mad_scores=tuple(float(item["mad"]) for item in selected),
        quantile_method="linear",
    )
