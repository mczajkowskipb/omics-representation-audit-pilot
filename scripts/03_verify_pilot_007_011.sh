#!/usr/bin/env bash
set -euo pipefail

export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export NUMBA_NUM_THREADS=1

PYTHON_BIN="${PYTHON_BIN:-python}"
SMOKE_OUTPUT="${SMOKE_OUTPUT:-results/smoke40_verify}"

if [[ -e "${SMOKE_OUTPUT}" ]]; then
  echo "Refusing to reuse existing smoke output: ${SMOKE_OUTPUT}" >&2
  echo "Set SMOKE_OUTPUT to a new path; completed jobs are never overwritten." >&2
  exit 2
fi

"${PYTHON_BIN}" scripts/00_check_environment.py \
  --strict \
  --output results/environment.json
"${PYTHON_BIN}" -m pytest -q
"${PYTHON_BIN}" scripts/02_run_smoke_grid.py \
  --config configs/smoke.yml \
  --output "${SMOKE_OUTPUT}"
