#!/usr/bin/env python3
"""Run the frozen 40-dataset PILOT-011 smoke grid."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "NUMBA_NUM_THREADS",
):
    os.environ[variable] = "1"
os.environ["PYTHONHASHSEED"] = "0"

import yaml

from rep_audit.experiments.runner import run_smoke_grid


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/smoke.yml"))
    parser.add_argument("--output", type=Path, default=Path("results/smoke40"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    summary = run_smoke_grid(config, output_root=args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["smoke_gate_go"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
