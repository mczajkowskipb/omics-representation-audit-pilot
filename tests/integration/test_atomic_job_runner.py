from __future__ import annotations

import json
from pathlib import Path

import pytest

from rep_audit.audit.config import AuditConfig
from rep_audit.audit.report import MethodAuditResult, SourceAuditReport
from rep_audit.audit.selector import RepresentationSelection
from rep_audit.experiments.job_spec import SimulationJobSpec
from rep_audit.experiments.runner import (
    _process_peak_rss_bytes,
    _publish_job,
    _validate_job_directory,
)
from rep_audit.simulation.generators import SimulationSpec


def job() -> SimulationJobSpec:
    simulation = SimulationSpec(
        regime="VALUE",
        signal="strong",
        shift="moderate",
        replicate=0,
        seed=4,
        n_source=12,
        n_target=12,
        p=8,
        k=2,
        informative_features=4,
    )
    audit = AuditConfig(
        k=2,
        feature_budget=8,
        relation_budget=5,
        resamples=1,
        seed=5,
        relation_screen_perturbations=1,
    )
    return SimulationJobSpec(simulation=simulation, audit=audit)


def report() -> SourceAuditReport:
    method = MethodAuditResult(
        method_id="V_EUC_PAM",
        family="VALUE",
        prediction_strength=0.8,
        cluster_stability=0.9,
        perturbation_invariance=0.85,
        representation_stability=0.9,
        nondegeneracy_score=1.0,
        nondegenerate=True,
        min_cluster_fraction=0.5,
        cluster_entropy=1.0,
        q_score=0.8,
        medoid_ids=("s1", "s3"),
        sample_ids=("s1", "s2", "s3", "s4"),
        assignments=(0, 0, 1, 1),
        complexity=8,
        perturbation_failures=0,
    )
    return SourceAuditReport(
        source_dataset_id="toy",
        source_fingerprint="f" * 64,
        config_sha256="c" * 64,
        config={"k": 2},
        representation_manifest={"sample_ids": method.sample_ids},
        methods=(method,),
        failures={},
    )


def selection(audit: SourceAuditReport) -> RepresentationSelection:
    return RepresentationSelection(
        decision="VALUE",
        uncertain=False,
        decision_confidence=1.0,
        selected_method="V_EUC_PAM",
        selected_k=2,
        selected_alpha=None,
        q_score=0.8,
        null_threshold=0.5,
        eligible_alternatives=(),
        rejection_reasons={},
        vote_counts={"VALUE": 1},
        audit_report_sha256=(audit.sha256(),),
        calibration_sha256="n" * 64,
    )


def test_job_is_published_atomically_and_valid_rerun_is_skipped(tmp_path: Path) -> None:
    specification = job()
    audit = report()
    selected = selection(audit)
    metrics = {
        "schema": "SimulationMetrics/v1",
        "regime": "VALUE",
        "expected_decision": "VALUE",
        "selected_decision": "VALUE",
        "decision_correct": True,
    }
    first = _publish_job(
        tmp_path,
        specification,
        audit,
        selected,
        metrics,
        wall_seconds=1.2,
        peak_rss_bytes=1024,
    )
    destination = tmp_path / "jobs" / specification.job_id
    _validate_job_directory(destination)
    key_before = {
        relative: (destination / relative).read_bytes()
        for relative in (
            "config.json",
            "metrics.json",
            "assignments.csv.gz",
            "artifact/audit.json",
            "artifact/selection.json",
        )
    }
    second = _publish_job(
        tmp_path,
        specification,
        audit,
        selected,
        metrics,
        wall_seconds=9.9,
        peak_rss_bytes=2048,
    )
    key_after = {relative: (destination / relative).read_bytes() for relative in key_before}
    assert first == "completed"
    assert second == "skipped_valid_existing"
    assert key_before == key_after
    assert not any(path.name.startswith(".") for path in (tmp_path / "jobs").iterdir())


def test_incomplete_existing_job_is_rejected_not_overwritten(tmp_path: Path) -> None:
    specification = job()
    destination = tmp_path / "jobs" / specification.job_id
    destination.mkdir(parents=True)
    (destination / "config.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete job"):
        _publish_job(
            tmp_path,
            specification,
            report(),
            selection(report()),
            {},
            wall_seconds=0.1,
            peak_rss_bytes=1,
        )
    assert (destination / "config.json").read_text(encoding="utf-8") == "{}\n"


def test_process_peak_rss_is_reported_as_positive_bytes() -> None:
    assert _process_peak_rss_bytes() > 1_000_000


def test_validator_rejects_schema_invalid_job_even_with_matching_checksum(
    tmp_path: Path,
) -> None:
    specification = job()
    audit = report()
    destination = tmp_path / "jobs" / specification.job_id
    _publish_job(
        tmp_path,
        specification,
        audit,
        selection(audit),
        {"schema": "SimulationMetrics/v1"},
        wall_seconds=0.1,
        peak_rss_bytes=1_000_001,
    )
    runtime_path = destination / "runtime.json"
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    runtime["schema"] = "WrongRuntime/v1"
    runtime_path.write_text(json.dumps(runtime), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid schema"):
        _validate_job_directory(destination)
