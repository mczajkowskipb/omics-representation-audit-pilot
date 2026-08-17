"""Evaluation-only loaders for labels stored outside adapter manifests."""

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
from rep_audit.evaluation.external_labels import EvaluationLabels


class RepositoryLabelLoader:
    """Read labels only in an explicitly evaluation-owned process."""

    def __init__(self, manifest_path: str | Path, roots: dict[str, str | Path]) -> None:
        self.manifest = load_manifest(
            manifest_path, expected_schema="EvaluationLabelManifest/v1"
        )
        self.roots = {name: Path(path).resolve() for name, path in roots.items()}
        for name, revision in self.manifest["repositories"].items():
            if name not in self.roots:
                raise ReferenceIntegrityError(f"missing root for label repository: {name}")
            verify_git_revision(self.roots[name], revision["git_commit"])

    def load(self, dataset_id: str, *, expected_sample_ids: tuple[str, ...]) -> EvaluationLabels:
        try:
            entry = self.manifest["datasets"][str(dataset_id)]
        except KeyError as error:
            raise KeyError(f"unknown evaluation label dataset: {dataset_id}") from error
        path = safe_relative_file(self.roots[entry["repository"]], entry["y_path"])
        verify_file(
            path,
            expected_size=entry["y_size_bytes"],
            expected_sha256=entry["y_sha256"],
        )
        frame = pd.read_csv(path)
        if entry["alignment"] == "sample_id":
            if set(frame["sample_id"].astype(str)) != set(expected_sample_ids):
                raise ReferenceIntegrityError(f"label/sample ID mismatch for {dataset_id}")
            indexed = frame.assign(sample_id=frame["sample_id"].astype(str)).set_index("sample_id")
            values = tuple(str(indexed.loc[item, entry["label_column"]]) for item in expected_sample_ids)
        elif entry["alignment"] == "row_order":
            if len(frame) != len(expected_sample_ids):
                raise ReferenceIntegrityError(f"label row count mismatch for {dataset_id}")
            values = tuple(str(value) for value in frame[entry["label_column"]])
        else:
            raise ReferenceIntegrityError("unsupported evaluation-label alignment")
        return EvaluationLabels(
            dataset_id=str(dataset_id),
            sample_ids=expected_sample_ids,
            values=values,
            label_name=str(entry["label_column"]),
        )
