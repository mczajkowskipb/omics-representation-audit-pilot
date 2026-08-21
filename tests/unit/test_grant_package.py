from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from rep_audit.io.canonical_json import canonical_json_bytes
from rep_audit.reporting.grant_package import (
    find_forbidden_claims,
    validate_claim_values,
    validate_grant_package,
)


ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_grant_package_matches_frozen_evidence() -> None:
    result = validate_grant_package(ROOT)
    assert result["validated"] is True
    assert result["gate_b"] == "GO"
    assert result["gate_c"] == "STOP"
    assert result["direct_regions"] == "NOT_TESTED"
    assert result["anchors"] == "NOT_TESTED"
    assert result["forbidden_claim_count"] == 0
    assert result["document_count"] == 12


def test_strategic_modify_is_narrow_and_preserves_frozen_boundaries() -> None:
    strategy = (
        ROOT / "docs/grant/SONATA_BIS16_STRATEGIC_DECISION_MODIFY_PL.md"
    ).read_text(encoding="utf-8")
    assert "Decyzja: **MODIFY**" in strategy
    assert "Omika jest częścią problemu badawczego" in strategy
    assert "Gate B: **GO**" in strategy
    assert "Gate C: **STOP**" in strategy
    assert "direct regions: **NOT TESTED**" in strategy
    assert "anchors: **NOT TESTED**" in strategy
    assert "defence/PYTHIA" in strategy
    assert "ogólny meta-learner" in strategy


def test_grant_package_validation_is_byte_deterministic() -> None:
    first = canonical_json_bytes(validate_grant_package(ROOT))
    second = canonical_json_bytes(validate_grant_package(ROOT))
    assert first == second


def test_claim_validator_rejects_retrospective_gate_c_relaxation() -> None:
    manifest = _load("docs/grant/CLAIMS_EVIDENCE.json")
    evidence = _load("docs/evidence/PILOT_019_VALIDATION.json")
    altered = copy.deepcopy(manifest)
    altered["metrics"]["gate_c"]["formal_decision"] = "GO"
    with pytest.raises(ValueError, match="Gate C decision"):
        validate_claim_values(altered, evidence)


def test_forbidden_overclaims_are_detected_case_insensitively() -> None:
    found = find_forbidden_claims(
        "The EXTERNAL VALIDATION PASSED and direct regions were validated.",
        ["external validation passed", "direct regions were validated"],
    )
    assert found == ["external validation passed", "direct regions were validated"]
