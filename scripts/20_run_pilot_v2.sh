#!/usr/bin/env bash
set -euo pipefail
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
"$PYTHON_BIN" -m pytest -q tests/unit/test_rr_direct.py
"$PYTHON_BIN" scripts/20_run_pilot_v2.py --config configs/pilot_v2.yml --datasets configs/datasets.local.yml --output results/pilot_v2
