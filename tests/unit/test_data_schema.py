from __future__ import annotations

import re
from dataclasses import fields

import numpy as np
import pytest

from rep_audit.data.schema import DatasetBundle
from rep_audit.evaluation.external_labels import EvaluationLabels


def make_bundle() -> DatasetBundle:
    original = np.array([[1.0, np.nan], [2.0, 3.0]])
    return DatasetBundle(
        X=original,
        sample_ids=("s1", "s2"),
        feature_ids=("g1", "g2"),
        dataset_id="toy",
        platform_id="sim",
        cohort_id="source",
        metadata={"input_scale": "log2"},
    )


def test_bundle_is_defensively_copied_and_read_only() -> None:
    original = np.array([[1.0, 2.0], [3.0, 4.0]])
    bundle = DatasetBundle(
        X=original,
        sample_ids=("s1", "s2"),
        feature_ids=("g1", "g2"),
        dataset_id="toy",
        platform_id="sim",
        cohort_id="source",
    )
    original[0, 0] = 99.0
    assert bundle.X[0, 0] == 1.0
    with pytest.raises(ValueError):
        bundle.X[0, 0] = 7.0
    with pytest.raises(TypeError):
        bundle.metadata["new"] = "value"


def test_bundle_contract_has_no_label_channel() -> None:
    field_names = {field.name for field in fields(DatasetBundle)}
    assert field_names == {
        "X",
        "sample_ids",
        "feature_ids",
        "dataset_id",
        "platform_id",
        "cohort_id",
        "metadata",
    }
    with pytest.raises(TypeError):
        DatasetBundle(  # type: ignore[call-arg]
            X=np.ones((2, 2)),
            sample_ids=("s1", "s2"),
            feature_ids=("g1", "g2"),
            dataset_id="toy",
            platform_id="sim",
            cohort_id="source",
            labels=(0, 1),
        )


def test_evaluation_labels_are_a_separate_type() -> None:
    bundle = make_bundle()
    labels = EvaluationLabels(
        dataset_id="toy",
        sample_ids=("s1", "s2"),
        values=("case", "control"),
    )
    assert "labels" not in dir(bundle)
    assert labels.as_mapping() == {"s1": "case", "s2": "control"}


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"sample_ids": ("s1", "s1")}, "sample IDs must be unique"),
        ({"feature_ids": ("g1", "g1")}, "feature IDs must be unique"),
        ({"sample_ids": ("s1",)}, "len(sample_ids)"),
        ({"feature_ids": ("g1",)}, "len(feature_ids)"),
    ],
)
def test_bundle_rejects_identifier_contract_violations(kwargs, message) -> None:
    base = {
        "X": np.ones((2, 2)),
        "sample_ids": ("s1", "s2"),
        "feature_ids": ("g1", "g2"),
        "dataset_id": "toy",
        "platform_id": "sim",
        "cohort_id": "source",
    }
    base.update(kwargs)
    with pytest.raises(ValueError, match=re.escape(message)):
        DatasetBundle(**base)


def test_bundle_allows_nan_but_rejects_infinity() -> None:
    assert np.isnan(make_bundle().X[0, 1])
    with pytest.raises(ValueError, match="infinity"):
        DatasetBundle(
            X=np.array([[1.0, np.inf]]),
            sample_ids=("s1",),
            feature_ids=("g1", "g2"),
            dataset_id="toy",
            platform_id="sim",
            cohort_id="source",
        )


def test_fingerprint_is_stable_and_value_sensitive() -> None:
    first = make_bundle()
    second = make_bundle()
    assert first.fingerprint() == second.fingerprint()
    changed = DatasetBundle(
        X=np.array([[1.0, np.nan], [2.0, 4.0]]),
        sample_ids=first.sample_ids,
        feature_ids=first.feature_ids,
        dataset_id=first.dataset_id,
        platform_id=first.platform_id,
        cohort_id=first.cohort_id,
        metadata=first.metadata,
    )
    assert first.fingerprint() != changed.fingerprint()
