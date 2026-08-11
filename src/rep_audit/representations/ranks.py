"""Per-sample average ranks with explicit missingness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.stats import rankdata

from rep_audit.data.schema import DatasetBundle


@dataclass(frozen=True, slots=True)
class RankRepresentation:
    """Normalized average ranks and a separate observation mask.

    Values at unobserved positions are fixed to zero but carry no meaning; all
    consumers must use ``observed``.
    """

    q: np.ndarray
    observed: np.ndarray
    sample_ids: tuple[str, ...]
    feature_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        q = np.array(self.q, dtype=np.dtype("<f8"), order="C", copy=True)
        observed = np.array(self.observed, dtype=bool, order="C", copy=True)
        expected = (len(self.sample_ids), len(self.feature_ids))
        if q.shape != expected or observed.shape != expected:
            raise ValueError("rank arrays must match sample and feature IDs")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("sample IDs must be unique")
        if len(set(self.feature_ids)) != len(self.feature_ids):
            raise ValueError("feature IDs must be unique")
        if not np.isfinite(q).all():
            raise ValueError("rank storage must be finite; use the observation mask")
        if np.any((q[observed] < 0.0) | (q[observed] > 1.0)):
            raise ValueError("observed normalized ranks must be in [0, 1]")
        q[~observed] = 0.0
        q.flags.writeable = False
        observed.flags.writeable = False
        object.__setattr__(self, "q", q)
        object.__setattr__(self, "observed", observed)
        object.__setattr__(self, "sample_ids", tuple(self.sample_ids))
        object.__setattr__(self, "feature_ids", tuple(self.feature_ids))


def average_rank_encode(
    bundle: DatasetBundle,
    *,
    feature_ids: Sequence[object] | None = None,
) -> RankRepresentation:
    """Encode each sample independently using average ranks for exact ties."""

    selected = (
        bundle.feature_ids
        if feature_ids is None
        else tuple(str(feature_id) for feature_id in feature_ids)
    )
    if len(selected) == 0:
        raise ValueError("at least one feature is required")
    if len(selected) != len(set(selected)):
        raise ValueError("feature_ids must be unique")
    index = {feature_id: i for i, feature_id in enumerate(bundle.feature_ids)}
    missing = [feature_id for feature_id in selected if feature_id not in index]
    if missing:
        raise ValueError("unknown features: " + ", ".join(missing[:10]))
    matrix = bundle.X[:, [index[feature_id] for feature_id in selected]]
    observed = ~np.isnan(matrix)
    q = np.zeros(matrix.shape, dtype=np.float64)

    for row_index in range(matrix.shape[0]):
        mask = observed[row_index]
        count = int(mask.sum())
        if count == 0:
            continue
        ranks = rankdata(matrix[row_index, mask], method="average")
        if count == 1:
            normalized = np.zeros(1, dtype=np.float64)
        else:
            normalized = (ranks - 1.0) / float(count - 1)
        q[row_index, mask] = normalized

    return RankRepresentation(
        q=q,
        observed=observed,
        sample_ids=bundle.sample_ids,
        feature_ids=selected,
    )
