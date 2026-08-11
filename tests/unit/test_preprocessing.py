from __future__ import annotations

import numpy as np
import pytest

from rep_audit.data.schema import DatasetBundle
from rep_audit.preprocessing.artifact import SourcePreprocessingArtifact
from rep_audit.preprocessing.robust import fit_source_preprocessing


def source_bundle(*, permute_columns: bool = False) -> DatasetBundle:
    feature_ids = np.array(["z_high", "a_tie", "b_tie", "c_const", "d_missing"])
    matrix = np.array(
        [
            [0.0, 0.0, 0.0, 5.0, np.nan],
            [10.0, 0.0, 0.0, 5.0, 1.0],
            [20.0, 2.0, 2.0, 5.0, 1.0],
            [30.0, 2.0, 2.0, 5.0, 3.0],
        ]
    )
    if permute_columns:
        order = np.array([3, 2, 0, 4, 1])
        matrix = matrix[:, order]
        feature_ids = feature_ids[order]
    return DatasetBundle(
        X=matrix,
        sample_ids=("s1", "s2", "s3", "s4"),
        feature_ids=tuple(feature_ids),
        dataset_id="source-toy",
        platform_id="sim",
        cohort_id="source",
    )


def target_bundle(offset: float) -> DatasetBundle:
    return DatasetBundle(
        X=np.array(
            [
                [100.0 + offset, 0.0 + offset, 0.0, 7.0, 1.0],
                [200.0 + offset, 2.0 + offset, 2.0, 7.0, np.nan],
            ]
        ),
        sample_ids=("t1", "t2"),
        feature_ids=("z_high", "a_tie", "b_tie", "c_const", "d_missing"),
        dataset_id="target-toy",
        platform_id="sim2",
        cohort_id="target",
    )


def test_source_mad_selection_is_deterministic_and_tie_breaks_by_feature_id() -> None:
    artifact = fit_source_preprocessing(source_bundle(), feature_budget=3)
    assert artifact.selected_feature_ids == ("z_high", "a_tie", "b_tie")
    assert artifact.mad_scores == (10.0, 1.0, 1.0)
    assert artifact.source_medians == (15.0, 1.0, 1.0)
    assert artifact.source_iqrs == (15.0, 2.0, 2.0)
    assert artifact.iqr_fallback == (False, False, False)


def test_column_permutation_does_not_change_fitted_parameters() -> None:
    first = fit_source_preprocessing(source_bundle(), feature_budget=3)
    second = fit_source_preprocessing(
        source_bundle(permute_columns=True), feature_budget=3
    )
    assert first.selected_feature_ids == second.selected_feature_ids
    assert first.source_medians == second.source_medians
    assert first.source_iqrs == second.source_iqrs
    assert first.mad_scores == second.mad_scores


def test_target_values_cannot_change_source_artifact() -> None:
    source = source_bundle()
    target_a = target_bundle(0.0)
    target_b = target_bundle(9999.0)
    artifact_a = fit_source_preprocessing(
        source, feature_budget=3, allowed_feature_ids=target_a.feature_ids
    )
    artifact_b = fit_source_preprocessing(
        source, feature_budget=3, allowed_feature_ids=target_b.feature_ids
    )
    assert artifact_a.to_json_bytes() == artifact_b.to_json_bytes()


def test_transform_uses_frozen_source_parameters_and_median_imputation() -> None:
    artifact = fit_source_preprocessing(source_bundle(), feature_budget=3)
    before = artifact.to_json_bytes()
    transformed = artifact.transform(target_bundle(0.0))
    after = artifact.to_json_bytes()
    expected_first = np.array([(100.0 - 15.0) / 15.0, -0.5, -0.5])
    assert np.allclose(transformed.matrix[0], expected_first)
    assert transformed.feature_ids == artifact.selected_feature_ids
    assert before == after
    with pytest.raises(ValueError):
        transformed.matrix[0, 0] = 0.0


def test_zero_iqr_fallback_is_explicit() -> None:
    source = source_bundle()
    artifact = fit_source_preprocessing(
        source, feature_budget=1, allowed_feature_ids=("c_const",)
    )
    assert artifact.selected_feature_ids == ("c_const",)
    assert artifact.source_iqrs == (0.0,)
    assert artifact.scale_denominators == (1.0,)
    assert artifact.iqr_fallback == (True,)


def test_all_missing_features_are_ineligible() -> None:
    source = DatasetBundle(
        X=np.array([[np.nan], [np.nan]]),
        sample_ids=("s1", "s2"),
        feature_ids=("g_missing",),
        dataset_id="missing",
        platform_id="sim",
        cohort_id="source",
    )
    with pytest.raises(ValueError, match="eligible source features"):
        fit_source_preprocessing(source, feature_budget=1)


def test_mad_uses_observed_source_values_before_imputation() -> None:
    source = DatasetBundle(
        X=np.array([[0.0], [1.0], [2.0], [np.nan]]),
        sample_ids=("s1", "s2", "s3", "s4"),
        feature_ids=("g_partial",),
        dataset_id="partial",
        platform_id="sim",
        cohort_id="source",
    )
    artifact = fit_source_preprocessing(source, feature_budget=1)
    assert artifact.mad_scores == (1.0,)


def test_artifact_roundtrip_is_byte_identical(tmp_path) -> None:
    artifact = fit_source_preprocessing(source_bundle(), feature_budget=3)
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    artifact.save(first)
    loaded = SourcePreprocessingArtifact.load(first)
    loaded.save(second)
    assert first.read_bytes() == second.read_bytes() == artifact.to_json_bytes()
    assert loaded.sha256() == artifact.sha256()


def test_allowed_feature_universe_must_be_source_schema_only() -> None:
    with pytest.raises(ValueError, match="absent from source"):
        fit_source_preprocessing(
            source_bundle(), feature_budget=1, allowed_feature_ids=("unknown",)
        )
