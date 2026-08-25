#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
"$PYTHON_BIN" -m pytest -q tests/unit/test_rr_direct.py
"$PYTHON_BIN" scripts/22_collect_pilot_v2_evidence.py
"$PYTHON_BIN" -m compileall -q src scripts tests
git status --short
