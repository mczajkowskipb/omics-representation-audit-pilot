"""Integrity-checked, label-blind repository adapter utilities."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping


class ReferenceIntegrityError(ValueError):
    """Raised when a reference repository is not the frozen input."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: str | Path, *, expected_schema: str) -> Mapping[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != expected_schema:
        raise ReferenceIntegrityError(f"expected {expected_schema}: {path}")
    return value


def safe_relative_file(root: Path, relative: object) -> Path:
    root = root.resolve()
    candidate = (root / str(relative)).resolve()
    if candidate == root or root not in candidate.parents:
        raise ReferenceIntegrityError("manifest path escapes the reference root")
    if not candidate.is_file():
        raise ReferenceIntegrityError(f"missing reference file: {candidate}")
    return candidate


def verify_git_revision(root: Path, expected: object) -> str:
    try:
        completed = subprocess.run(
            ("git", "-C", str(root), "rev-parse", "HEAD"),
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ReferenceIntegrityError(f"cannot verify git revision: {root}") from error
    observed = completed.stdout.strip()
    if observed != str(expected):
        raise ReferenceIntegrityError(
            f"reference revision mismatch: expected {expected}, observed {observed}"
        )
    return observed


def verify_file(path: Path, *, expected_size: object, expected_sha256: object) -> None:
    size = path.stat().st_size
    if size != int(expected_size):
        raise ReferenceIntegrityError(
            f"reference size mismatch for {path}: expected {expected_size}, observed {size}"
        )
    observed = sha256_file(path)
    if observed != str(expected_sha256):
        raise ReferenceIntegrityError(
            f"reference SHA-256 mismatch for {path}: expected {expected_sha256}, observed {observed}"
        )
