#!/usr/bin/env bash
set -euo pipefail
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
"$PYTHON_BIN" scripts/21_run_pilot_v2_1.py --config configs/pilot_v2_1.yml --output results/pilot_v2_1
