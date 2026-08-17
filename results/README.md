# Results

Generated verification and experiment outputs are intentionally ignored by
Git. Each experiment job writes to its own atomically published and validated
directory. A run must use a new output root; completed jobs are never
overwritten.

Compact accepted evidence is versioned under `docs/evidence/`. The full
PILOT-011 result tree may be generated with
`scripts/03_verify_pilot_007_011.sh`.
