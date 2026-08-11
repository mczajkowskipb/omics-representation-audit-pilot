from __future__ import annotations

import inspect

import numpy as np

from rep_audit.clustering.pam import deterministic_pam
from rep_audit.data.schema import DatasetBundle
from rep_audit.distances.value import euclidean_distance_matrix
from rep_audit.evaluation.external_labels import EvaluationLabels
from rep_audit.preprocessing.robust import fit_source_preprocessing


def test_fit_interface_has_no_target_or_label_parameter() -> None:
    parameters = inspect.signature(fit_source_preprocessing).parameters
    assert set(parameters) == {
        "source",
        "feature_budget",
        "allowed_feature_ids",
        "protocol_version",
    }
    assert "target" not in parameters
    assert "labels" not in parameters
    assert "y" not in parameters


def test_changing_evaluation_labels_cannot_change_fitted_artifact() -> None:
    source = DatasetBundle(
        X=np.array([[0.0, 5.0], [1.0, 5.0], [2.0, 5.0]]),
        sample_ids=("s1", "s2", "s3"),
        feature_ids=("g1", "g2"),
        dataset_id="toy",
        platform_id="sim",
        cohort_id="source",
    )
    labels_a = EvaluationLabels(
        dataset_id="toy",
        sample_ids=source.sample_ids,
        values=("A", "A", "B"),
    )
    labels_b = EvaluationLabels(
        dataset_id="toy",
        sample_ids=source.sample_ids,
        values=("X", "Y", "Z"),
    )
    before = fit_source_preprocessing(source, feature_budget=1).to_json_bytes()
    assert labels_a.values != labels_b.values
    after = fit_source_preprocessing(source, feature_budget=1).to_json_bytes()
    assert before == after


def test_changing_evaluation_labels_cannot_change_pam_assignments() -> None:
    source = DatasetBundle(
        X=np.array(
            [
                [0.0, 0.0],
                [0.5, 0.5],
                [9.5, 9.5],
                [10.0, 10.0],
            ]
        ),
        sample_ids=("s1", "s2", "s3", "s4"),
        feature_ids=("g1", "g2"),
        dataset_id="assignment-toy",
        platform_id="sim",
        cohort_id="source",
    )
    labels_a = EvaluationLabels(
        dataset_id=source.dataset_id,
        sample_ids=source.sample_ids,
        values=("A", "A", "B", "B"),
    )
    labels_b = EvaluationLabels(
        dataset_id=source.dataset_id,
        sample_ids=source.sample_ids,
        values=("W", "X", "Y", "Z"),
    )

    def frozen_assignments() -> bytes:
        artifact = fit_source_preprocessing(source, feature_budget=2)
        distance = euclidean_distance_matrix(artifact.transform(source))
        return deterministic_pam(distance, k=2).to_json_bytes()

    before = frozen_assignments()
    assert labels_a.values != labels_b.values
    after = frozen_assignments()
    assert before == after
