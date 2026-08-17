#!/usr/bin/env python3
"""Run PILOT-014/015 in strict prelabel and evaluation phases."""

from __future__ import annotations

import os

for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[variable] = "1"

import argparse
import json
from pathlib import Path

import yaml

from rep_audit.experiments.real_lung import run_real_evaluation, run_real_prelabel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/real_lung.yml")
    parser.add_argument("--datasets", default="configs/datasets.local.yml")
    parser.add_argument("--gate-b", default="results/full630_primary/gate_b_summary.json")
    parser.add_argument("--output", default="results/real_lung_primary")
    parser.add_argument("--phase", choices=("prelabel", "evaluate", "all"), default="all")
    parser.add_argument("--max-workers", type=int)
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    datasets = yaml.safe_load(Path(args.datasets).read_text(encoding="utf-8"))
    workers = args.max_workers or int(config["runtime"]["max_workers"])
    if args.phase in {"prelabel", "all"}:
        result = run_real_prelabel(
            config,
            dataset_config=datasets,
            gate_b_summary_path=args.gate_b,
            output_root=args.output,
            max_workers=workers,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
    if args.phase in {"evaluate", "all"}:
        result = run_real_evaluation(dataset_config=datasets, output_root=args.output)
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
