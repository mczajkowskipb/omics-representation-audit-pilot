from __future__ import annotations

import numpy as np

from rep_audit.clustering.pam import deterministic_pam
from rep_audit.distances.validation import DistanceMatrix


def test_identical_configs_produce_byte_identical_pam_artifacts(tmp_path) -> None:
    distance = DistanceMatrix(
        values=np.array(
            [
                [0.0, 1.0, 8.0, 9.0],
                [1.0, 0.0, 7.0, 8.0],
                [8.0, 7.0, 0.0, 1.0],
                [9.0, 8.0, 1.0, 0.0],
            ]
        ),
        sample_ids=("s1", "s2", "s3", "s4"),
        metric_id="golden",
    )
    first = deterministic_pam(distance, k=2)
    second = deterministic_pam(distance, k=2)
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first.save(first_path)
    second.save(second_path)
    assert first.to_json_bytes() == second.to_json_bytes()
    assert first.sha256() == second.sha256()
    assert first_path.read_bytes() == second_path.read_bytes()


def test_stable_sample_id_breaks_distance_ties() -> None:
    distance = DistanceMatrix(
        values=np.zeros((3, 3)),
        sample_ids=("z", "a", "m"),
        metric_id="ties",
    )
    result = deterministic_pam(distance, k=1)
    assert result.medoid_ids == ("a",)
    assert result.labels == (0, 0, 0)
