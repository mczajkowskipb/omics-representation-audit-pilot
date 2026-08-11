#!/usr/bin/env bash
set -euo pipefail

export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export NUMBA_NUM_THREADS=1

PYTHON_BIN="${PYTHON_BIN:-python}"

"${PYTHON_BIN}" scripts/00_check_environment.py \
  --strict \
  --output results/environment.json
"${PYTHON_BIN}" -m pytest -q
