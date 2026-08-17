"""Label-blind adapter for AIR-relational-benchmark."""

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


class AIRRepositoryAdapter:
    """Load feature-by-sample AIR matrices as sample-by-feature bundles."""

    def __init__(self, root: str | Path, manifest_path: str | Path) -> None:
        self.root = Path(root).resolve()
        self.manifest = load_manifest(manifest_path, expected_schema="AIRDataManifest/v1")
        verify_git_revision(self.root, self.manifest["git_commit"])

    @property
    def dataset_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.manifest["datasets"]))

    def verify_all(self) -> None:
        for dataset_id in self.dataset_ids:
            entry = self.manifest["datasets"][dataset_id]
            path = safe_relative_file(self.root, entry["x_path"])
            verify_file(
                path,
                expected_size=entry["x_size_bytes"],
                expected_sha256=entry["x_sha256"],
            )

    def load(self, dataset_id: str) -> DatasetBundle:
        try:
            entry = self.manifest["datasets"][str(dataset_id)]
        except KeyError as error:
            raise KeyError(f"unknown AIR dataset: {dataset_id}") from error
        path = safe_relative_file(self.root, entry["x_path"])
        verify_file(
            path,
            expected_size=entry["x_size_bytes"],
            expected_sha256=entry["x_sha256"],
        )
        frame = pd.read_csv(path, index_col=0)
        expected_feature_sample_shape = (
            int(entry["n_features"]),
            int(entry["n_samples"]),
        )
        if frame.shape != expected_feature_sample_shape:
            raise ReferenceIntegrityError(
                f"matrix shape mismatch for {dataset_id}: "
                f"{frame.shape} != {expected_feature_sample_shape}"
            )
        if frame.index.has_duplicates or frame.columns.has_duplicates:
            raise ReferenceIntegrityError(f"duplicate matrix IDs in {dataset_id}")
        return DatasetBundle(
            X=frame.to_numpy(dtype=float, copy=True).T,
            sample_ids=tuple(str(value) for value in frame.columns),
            feature_ids=tuple(str(value) for value in frame.index),
            dataset_id=str(dataset_id),
            platform_id=str(entry["platform_id"]),
            cohort_id="complete",
            metadata={
                "adapter": "AIRRepositoryAdapter/v1",
                "orientation_on_disk": "features_x_samples",
                "reference_commit": str(self.manifest["git_commit"]),
                "x_sha256": str(entry["x_sha256"]),
                "labels_loaded": "false",
            },
        )
