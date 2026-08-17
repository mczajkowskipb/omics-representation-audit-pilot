from __future__ import annotations

import os
from pathlib import Path

import pytest

from rep_audit.data.adapters.air import AIRRepositoryAdapter
from rep_audit.data.adapters.feasibility import FeasibilityRepositoryAdapter
from rep_audit.evaluation.repository_labels import RepositoryLabelLoader


ROOT = Path(__file__).parents[2]
FEASIBILITY_ROOT = os.environ.get("PILOT_FEASIBILITY_ROOT")
AIR_ROOT = os.environ.get("PILOT_AIR_ROOT")
ALLOW_REAL_LABEL_TEST = os.environ.get("PILOT_ALLOW_REAL_LABEL_TEST") == "1"


@pytest.mark.skipif(not FEASIBILITY_ROOT, reason="frozen feasibility repository not configured")
def test_feasibility_adapter_loads_three_label_free_bundles() -> None:
    adapter = FeasibilityRepositoryAdapter(
        FEASIBILITY_ROOT, ROOT / "data/manifests/feasibility_datasets.json"
    )
    expected = {"golub": (72, 7129), "colon": (62, 2000), "DLBCL": (194, 2294)}
    assert set(adapter.dataset_ids) == set(expected)
    for dataset_id, shape in expected.items():
        bundle = adapter.load(dataset_id)
        assert bundle.shape == shape
        assert bundle.metadata["labels_loaded"] == "false"
        assert not hasattr(bundle, "y")


@pytest.mark.skipif(not AIR_ROOT, reason="frozen AIR repository not configured")
def test_air_adapter_verifies_all_eight_matrices_and_loads_lung_pair() -> None:
    adapter = AIRRepositoryAdapter(AIR_ROOT, ROOT / "data/manifests/air_datasets.json")
    assert len(adapter.dataset_ids) == 8
    adapter.verify_all()
    source = adapter.load("GSE10072")
    target = adapter.load("GSE19804")
    assert source.shape == (107, 22283)
    assert target.shape == (120, 54675)
    assert len(set(source.feature_ids) & set(target.feature_ids)) == 22277
    assert source.metadata["labels_loaded"] == target.metadata["labels_loaded"] == "false"


@pytest.mark.skipif(
    not (FEASIBILITY_ROOT and AIR_ROOT and ALLOW_REAL_LABEL_TEST),
    reason="real labels remain sealed until an explicitly authorized evaluation phase",
)
def test_evaluation_loader_aligns_only_after_bundle_exists() -> None:
    air = AIRRepositoryAdapter(AIR_ROOT, ROOT / "data/manifests/air_datasets.json")
    bundle = air.load("GSE10072")
    loader = RepositoryLabelLoader(
        ROOT / "data/manifests/evaluation_labels.json",
        {"feasibility": FEASIBILITY_ROOT, "air": AIR_ROOT},
    )
    labels = loader.load("GSE10072", expected_sample_ids=bundle.sample_ids)
    assert labels.sample_ids == bundle.sample_ids
    assert set(labels.values) == {"normal", "tumor"}
