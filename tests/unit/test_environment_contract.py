from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_frozen_protocol_checksum() -> None:
    payload = (ROOT / "docs" / "SONATA_BIS_PILOT_PROTOCOL_v1.md").read_bytes()
    assert hashlib.sha256(payload).hexdigest() == (
        "5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704"
    )


def test_project_dependencies_exclude_forbidden_families() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = "\n".join(project["project"]["dependencies"]).lower()
    for forbidden in ("torch", "tensorflow", "cupy", "jax", "cuda", "fuzzy", "deap"):
        assert forbidden not in dependencies


def test_protocol_scope_does_not_have_future_modules() -> None:
    package = ROOT / "src" / "rep_audit"
    assert not (package / "anchors.py").exists()
    assert not (package / "clustering" / "direct_regions.py").exists()
    assert not (package / "simulation").exists()
    assert not (package / "audit").exists()
