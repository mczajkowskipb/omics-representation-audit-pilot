"""Validate grant-facing claims against frozen pilot evidence.

This module does not perform scientific evaluation. It checks that prose prepared
after pilot closeout preserves the recorded numerical results, leakage boundary,
and GO/STOP decisions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


MANIFEST_SCHEMA = "GrantClaimsEvidence/v1"
VALIDATION_SCHEMA = "GrantPackageValidation/v1"
EVIDENCE_SCHEMA = "Pilot019Validation/v1"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise ValueError(f"grant claim mismatch for {label}: {actual!r} != {expected!r}")


def validate_claim_values(
    manifest: Mapping[str, Any], evidence: Mapping[str, Any]
) -> None:
    """Validate every numerical/status claim copied from PILOT-019 evidence."""

    _require_equal(manifest.get("schema"), MANIFEST_SCHEMA, "manifest schema")
    _require_equal(evidence.get("schema"), EVIDENCE_SCHEMA, "evidence schema")
    _require_equal(
        manifest.get("protocol_sha256"),
        evidence.get("protocol_sha256"),
        "protocol SHA-256",
    )

    claimed = manifest["metrics"]
    gate_b = evidence["gate_b"]
    _require_equal(claimed["gate_b"]["formal_decision"], "GO", "Gate B decision")
    _require_equal(gate_b["go"], True, "Gate B evidence decision")
    _require_equal(claimed["gate_b"]["job_count"], gate_b["job_count"], "Gate B job count")
    for key, value in claimed["gate_b"]["metrics"].items():
        _require_equal(value, gate_b["metrics"][key], f"Gate B {key}")

    gate_c = evidence["gate_c"]
    _require_equal(
        claimed["gate_c"]["formal_decision"],
        gate_c["formal_decision"],
        "Gate C decision",
    )
    _require_equal(gate_c["go"], False, "Gate C evidence decision")
    _require_equal(
        claimed["gate_c"]["regret_by_direction"],
        gate_c["regret_by_direction"],
        "Gate C directional regret",
    )

    within = evidence["real_within"]
    for key in (
        "dataset_count",
        "decision_counts",
        "median_ari_regret",
        "median_selected_ari",
        "selected_within_0_05_of_oracle_rate",
    ):
        _require_equal(claimed["real_within"][key], within[key], f"real-within {key}")
    _require_equal(
        claimed["real_within"]["interpretation"],
        "DESCRIPTIVE_NOT_EXTERNAL_VALIDATION",
        "real-within interpretation",
    )

    evidence_scope = evidence["scope_decision"]
    for issue in ("PILOT-016", "PILOT-017", "PILOT-018"):
        _require_equal(
            manifest["scope"][issue],
            evidence_scope[issue],
            f"{issue} scope status",
        )
    _require_equal(
        manifest["scope"]["retrospective_gate_c_rescue"],
        False,
        "retrospective Gate C rescue",
    )


def find_forbidden_claims(text: str, forbidden_literals: Sequence[str]) -> list[str]:
    """Return forbidden literal claims found case-insensitively in text."""

    folded = text.casefold()
    return [literal for literal in forbidden_literals if literal.casefold() in folded]


def validate_grant_package(repo_root: Path) -> dict[str, Any]:
    """Return a deterministic validation record for the grant-facing package."""

    root = repo_root.resolve()
    manifest_path = root / "docs/grant/CLAIMS_EVIDENCE.json"
    evidence_path = root / "docs/evidence/PILOT_019_VALIDATION.json"
    manifest = _read_json(manifest_path)
    evidence = _read_json(evidence_path)
    validate_claim_values(manifest, evidence)

    documents = [root / relative for relative in manifest["grant_documents"]]
    missing = [str(path.relative_to(root)) for path in documents if not path.is_file()]
    if missing:
        raise ValueError(f"missing grant documents: {missing}")

    combined_text = "\n".join(path.read_text(encoding="utf-8") for path in documents)
    forbidden = find_forbidden_claims(combined_text, manifest["forbidden_claim_literals"])
    if forbidden:
        raise ValueError(f"forbidden overclaims detected: {forbidden}")

    for literal in manifest["required_boundary_literals"]:
        if literal not in combined_text:
            raise ValueError(f"required claim boundary is missing: {literal!r}")

    document_hashes = {
        str(path.relative_to(root)): _sha256(path)
        for path in sorted(documents, key=lambda item: item.as_posix())
    }
    return {
        "schema": VALIDATION_SCHEMA,
        "validated": True,
        "protocol_sha256": evidence["protocol_sha256"],
        "pilot_commit": manifest["pilot_commit"],
        "gate_b": "GO",
        "gate_c": "STOP",
        "direct_regions": "NOT_TESTED",
        "anchors": "NOT_TESTED",
        "document_count": len(documents),
        "document_sha256": document_hashes,
        "forbidden_claim_count": 0,
    }
