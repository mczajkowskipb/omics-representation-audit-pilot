#!/usr/bin/env python3
"""Run the complete two-phase Gate B simulation grid."""

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

from rep_audit.experiments.full_runner import (
    run_evaluation_phase,
    run_full_grid,
    run_prelabel_phase,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/full630.yml")
    parser.add_argument("--output", default="results/full630_primary")
    parser.add_argument("--phase", choices=("prelabel", "evaluate", "all"), default="all")
    parser.add_argument("--max-workers", type=int)
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    workers = args.max_workers or int(config["runtime"]["max_workers"])
    if args.phase == "prelabel":
        result = run_prelabel_phase(config, output_root=args.output, max_workers=workers)
    elif args.phase == "evaluate":
        result = run_evaluation_phase(config, output_root=args.output)
    else:
        result = run_full_grid(config, output_root=args.output, max_workers=workers)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
