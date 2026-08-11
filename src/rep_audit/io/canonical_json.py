"""Canonical JSON serialization for deterministic key artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_ready(value.tolist())
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and value == 0.0:
        return 0.0
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Return UTF-8 canonical JSON with a final newline."""

    payload = json.dumps(
        _json_ready(value),
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def atomic_write_bytes(path: str | Path, payload: bytes) -> None:
    """Write bytes beside the destination and publish with ``os.replace``."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, destination)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def atomic_write_canonical_json(path: str | Path, value: Any) -> None:
    atomic_write_bytes(path, canonical_json_bytes(value))
