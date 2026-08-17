from __future__ import annotations

import inspect

import numpy as np

from rep_audit.audit.config import AuditConfig
from rep_audit.audit.diagnostics import fit_source_audit
from rep_audit.data.schema import DatasetBundle
from rep_audit.simulation.generators import SimulationSpec, generate_simulation
from rep_audit.transfer.artifact import FrozenTransferSet, freeze_transfer_set
from rep_audit.transfer.assign import assign_target


def _fitted_source():
    generated = generate_simulation(
        SimulationSpec(
            regime="HYBRID",
            signal="strong",
            shift="moderate",
            replicate=0,
            seed=4102,
            n_source=60,
            n_target=60,
            p=30,
            k=3,
            informative_features=18,
        )
    )
    config = AuditConfig(
        k=3,
        feature_budget=30,
        relation_budget=100,
        resamples=2,
        seed=991,
        relation_screen_perturbations=1,
    )
    return generated, fit_source_audit(generated.source, config)


def test_source_self_transfer_reproduces_pam_forced_assignments() -> None:
    generated, fitted = _fitted_source()
    frozen = freeze_transfer_set(
        generated.source,
        generated.source.feature_ids,
        generated.source.dataset_id,
        fitted,
    )
    assigned = assign_target(generated.source, frozen)
    for method in fitted.report.methods:
        observed = assigned.method_by_id(method.method_id)
        assert tuple(row.forced_cluster for row in observed.rows) == method.assignments


def test_frozen_artifact_ignores_target_values_and_round_trips(tmp_path) -> None:
    generated, fitted = _fitted_source()
    first = freeze_transfer_set(
        generated.source,
        generated.target.feature_ids,
        generated.target.dataset_id,
        fitted,
    )
    changed_target = DatasetBundle(
        X=generated.target.X * 1000.0 + 77.0,
        sample_ids=generated.target.sample_ids,
        feature_ids=generated.target.feature_ids,
        dataset_id=generated.target.dataset_id,
        platform_id=generated.target.platform_id,
        cohort_id=generated.target.cohort_id,
    )
    second = freeze_transfer_set(
        generated.source,
        changed_target.feature_ids,
        changed_target.dataset_id,
        fitted,
    )
    assert first.sha256() == second.sha256()
    path = tmp_path / "frozen.json"
    first.save(path)
    assert FrozenTransferSet.load(path).sha256() == first.sha256()


def test_target_rows_are_assigned_independently() -> None:
    generated, fitted = _fitted_source()
    frozen = freeze_transfer_set(
        generated.source,
        generated.target.feature_ids,
        generated.target.dataset_id,
        fitted,
    )
    batch = assign_target(generated.target, frozen)
    selected_rows = (0, 7, 23)
    for row_index in selected_rows:
        one = DatasetBundle(
            X=generated.target.X[[row_index]],
            sample_ids=(generated.target.sample_ids[row_index],),
            feature_ids=generated.target.feature_ids,
            dataset_id=generated.target.dataset_id,
            platform_id=generated.target.platform_id,
            cohort_id=generated.target.cohort_id,
        )
        singleton = assign_target(one, frozen)
        for method in batch.methods:
            assert singleton.method_by_id(method.method_id).rows[0] == method.rows[row_index]


def test_transfer_fit_and_assignment_interfaces_accept_no_labels() -> None:
    assert "label" not in inspect.signature(freeze_transfer_set).parameters
    assert "label" not in inspect.signature(assign_target).parameters


def test_common_feature_selection_uses_ids_but_not_target_values() -> None:
    generated = generate_simulation(
        SimulationSpec(
            regime="VALUE",
            signal="moderate",
            shift="strong",
            replicate=0,
            seed=8801,
            n_source=30,
            n_target=30,
            p=20,
            k=3,
            informative_features=8,
        )
    )
    common = tuple(sorted(set(generated.source.feature_ids) & set(generated.target.feature_ids)))
    fitted = fit_source_audit(
        generated.source,
        AuditConfig(
            k=3,
            feature_budget=20,
            relation_budget=30,
            resamples=1,
            seed=8,
            relation_screen_perturbations=1,
        ),
        allowed_feature_ids=common,
    )
    assert fitted.representations.preprocessing.feature_budget == len(common) == 19
    assert set(fitted.representations.preprocessing.selected_feature_ids) <= set(common)
