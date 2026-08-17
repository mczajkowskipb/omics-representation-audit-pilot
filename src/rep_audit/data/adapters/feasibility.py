"""Label-blind adapter for rank-relational-clustering-feasibility."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rep_audit.data.adapters.base import (
    ReferenceIntegrityError,
    load_manifest,
    safe_relative_file,
    verify_file,
    verify_git_revision,
)
from rep_audit.data.schema import DatasetBundle


class FeasibilityRepositoryAdapter:
    """Load only X from an exact, read-only upstream revision."""

    def __init__(self, root: str | Path, manifest_path: str | Path) -> None:
        self.root = Path(root).resolve()
        self.manifest = load_manifest(
            manifest_path, expected_schema="FeasibilityDataManifest/v1"
        )
        verify_git_revision(self.root, self.manifest["git_commit"])

    @property
    def dataset_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.manifest["datasets"]))

    def load(self, dataset_id: str) -> DatasetBundle:
        try:
            entry = self.manifest["datasets"][str(dataset_id)]
        except KeyError as error:
            raise KeyError(f"unknown feasibility dataset: {dataset_id}") from error
        path = safe_relative_file(self.root, entry["x_path"])
        verify_file(
            path,
            expected_size=entry["x_size_bytes"],
            expected_sha256=entry["x_sha256"],
        )
        frame = pd.read_csv(path)
        if bool(entry["first_column_is_sample_id"]):
            sample_ids = tuple(str(value) for value in frame.iloc[:, 0])
            frame = frame.iloc[:, 1:]
        else:
            sample_ids = tuple(
                f"{dataset_id}_row_{index:04d}" for index in range(len(frame))
            )
        expected_shape = (int(entry["n_samples"]), int(entry["n_features"]))
        if frame.shape != expected_shape:
            raise ReferenceIntegrityError(
                f"matrix shape mismatch for {dataset_id}: {frame.shape} != {expected_shape}"
            )
        return DatasetBundle(
            X=frame.to_numpy(dtype=float, copy=True),
            sample_ids=sample_ids,
            feature_ids=tuple(str(value) for value in frame.columns),
            dataset_id=str(dataset_id),
            platform_id=str(entry["platform_id"]),
            cohort_id="complete",
            metadata={
                "adapter": "FeasibilityRepositoryAdapter/v1",
                "reference_commit": str(self.manifest["git_commit"]),
                "x_sha256": str(entry["x_sha256"]),
                "labels_loaded": "false",
            },
        )
