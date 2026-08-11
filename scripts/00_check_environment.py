#!/usr/bin/env python3
"""Strict, machine-readable environment check for PILOT-001."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import tempfile
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PROTOCOL_SHA256 = (
    "5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704"
)
THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "NUMBA_NUM_THREADS",
)
REQUIRED_DISTRIBUTIONS = (
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "numba",
    "PyYAML",
    "pytest",
    "psutil",
)
FORBIDDEN_DEPENDENCY_TOKENS = (
    "torch",
    "tensorflow",
    "cupy",
    "jax",
    "cuda",
    "fuzzy",
    "deap",
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    payload = (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = [
        str(item).lower() for item in pyproject["project"].get("dependencies", [])
    ]
    test_declared = [
        str(item).lower()
        for item in pyproject["project"].get("optional-dependencies", {}).get("test", [])
    ]
    all_declared = declared + test_declared

    package_versions: dict[str, str | None] = {}
    for distribution in REQUIRED_DISTRIBUTIONS:
        try:
            package_versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            package_versions[distribution] = None

    thread_values = {name: os.environ.get(name) for name in THREAD_VARIABLES}
    protocol_path = ROOT / "docs" / "SONATA_BIS_PILOT_PROTOCOL_v1.md"
    protocol_sha = file_sha256(protocol_path) if protocol_path.exists() else None
    config_sha = file_sha256(ROOT / "configs" / "pilot.yml")

    checks = {
        "python_at_least_3_11": sys.version_info >= (3, 11),
        "required_packages_present": all(
            value is not None for value in package_versions.values()
        ),
        "single_thread_environment": all(
            value == "1" for value in thread_values.values()
        ),
        "protocol_sha256_matches": protocol_sha == EXPECTED_PROTOCOL_SHA256,
        "forbidden_dependencies_absent": not any(
            token in dependency
            for token in FORBIDDEN_DEPENDENCY_TOKENS
            for dependency in all_declared
        ),
    }

    try:
        import psutil

        logical_cpu_count = psutil.cpu_count(logical=True)
        physical_cpu_count = psutil.cpu_count(logical=False)
    except Exception:
        logical_cpu_count = os.cpu_count()
        physical_cpu_count = None

    report = {
        "schema_version": 1,
        "checks": checks,
        "ok": all(checks.values()),
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "platform": platform.platform(),
        "cpu": {
            "logical_count": logical_cpu_count,
            "physical_count": physical_cpu_count,
            "execution_mode": "deterministic_cpu",
        },
        "thread_environment": thread_values,
        "packages": package_versions,
        "protocol_sha256": protocol_sha,
        "config_sha256": config_sha,
    }

    if args.output is not None:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        atomic_json(output, report)

    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if args.strict and not report["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
