#!/usr/bin/env python3
"""Validate every scientific artifact and emit PILOT-019 evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

from rep_audit.experiments.closeout_validation import validate_closeout
from rep_audit.io.canonical_json import atomic_write_canonical_json


ROOT = Path(__file__).resolve().parents[1]


def _run_acceptance_tests() -> dict[str, object]:
    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONHASHSEED": "0",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "NUMBA_NUM_THREADS": "1",
            "PILOT_ALLOW_REAL_LABEL_TEST": "1",
            "PYTHONPATH": str(ROOT / "src"),
        }
    )
    dataset_config = yaml.safe_load(
        (ROOT / "configs/datasets.local.yml").read_text(encoding="utf-8")
    )
    environment["PILOT_FEASIBILITY_ROOT"] = str(
        dataset_config["reference_roots"]["feasibility"]
    )
    environment["PILOT_AIR_ROOT"] = str(dataset_config["reference_roots"]["air"])
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT,
        env=environment,
        check=True,
        text=True,
        capture_output=True,
    )
    match = re.search(r"(\d+) passed", completed.stdout)
    if match is None:
        raise ValueError("could not parse pytest acceptance result")
    subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "src", "tests", "scripts"],
        cwd=ROOT,
        env=environment,
        check=True,
    )
    pip_check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        cwd=ROOT,
        env=environment,
        check=True,
        text=True,
        capture_output=True,
    )
    return {
        "command": f"{sys.executable} -m pytest -q",
        "passed": int(match.group(1)),
        "failed": 0,
        "pytest_summary": completed.stdout.strip().splitlines()[-1],
        "compileall": "passed",
        "pip_check": pip_check.stdout.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", default="configs/datasets.local.yml")
    parser.add_argument("--full-config", default="configs/full630.yml")
    parser.add_argument("--real-config", default="configs/real_lung.yml")
    parser.add_argument("--within-config", default="configs/real_within.yml")
    parser.add_argument("--full-output", default="results/full630_primary")
    parser.add_argument("--real-output", default="results/real_lung_primary")
    parser.add_argument("--within-output", default="results/real_within_primary")
    parser.add_argument(
        "--output", default="docs/evidence/PILOT_019_VALIDATION.json"
    )
    parser.add_argument("--run-tests", action="store_true")
    args = parser.parse_args()
    load_yaml = lambda path: yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    report = validate_closeout(
        repository_root=ROOT,
        dataset_config=load_yaml(args.datasets),
        full_config=load_yaml(args.full_config),
        real_config=load_yaml(args.real_config),
        within_config=load_yaml(args.within_config),
        full_output=ROOT / args.full_output,
        real_output=ROOT / args.real_output,
        within_output=ROOT / args.within_output,
    )
    if args.run_tests:
        report["tests"] = _run_acceptance_tests()
    output = ROOT / args.output
    atomic_write_canonical_json(output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
