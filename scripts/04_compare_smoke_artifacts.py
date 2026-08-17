#!/usr/bin/env python3
"""Compare deterministic scientific artifacts from two complete smoke runs."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


JOB_ARTIFACTS = (
    "config.json",
    "metrics.json",
    "assignments.csv.gz",
    "artifact/audit.json",
    "artifact/selection.json",
    "DONE",
)


def artifact_paths(root: Path) -> tuple[Path, ...]:
    paths = [Path("summary.json"), Path("null_calibration.json")]
    jobs_root = root / "jobs"
    if not jobs_root.is_dir():
        raise ValueError(f"missing jobs directory: {jobs_root}")
    jobs = sorted(path for path in jobs_root.iterdir() if path.is_dir())
    if len(jobs) != 40:
        raise ValueError(f"expected 40 jobs in {root}, found {len(jobs)}")
    for job in jobs:
        paths.extend(Path("jobs") / job.name / name for name in JOB_ARTIFACTS)
    return tuple(sorted(paths, key=lambda path: path.as_posix()))


def tree_sha256(root: Path, paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        payload = (root / relative).read_bytes()
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    args = parser.parse_args()
    first_paths = artifact_paths(args.first)
    second_paths = artifact_paths(args.second)
    if first_paths != second_paths:
        raise ValueError("smoke runs do not contain the same artifact paths")
    mismatches = [
        path
        for path in first_paths
        if (args.first / path).read_bytes() != (args.second / path).read_bytes()
    ]
    first_hash = tree_sha256(args.first, first_paths)
    second_hash = tree_sha256(args.second, second_paths)
    print(f"compared={len(first_paths)}")
    print(f"mismatches={len(mismatches)}")
    print(f"first_tree_sha256={first_hash}")
    print(f"second_tree_sha256={second_hash}")
    for path in mismatches[:20]:
        print(f"MISMATCH {path}")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
