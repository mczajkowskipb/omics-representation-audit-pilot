# Pilot v2 — direct sparse relational prototypes

Pilot v2 extends the frozen representation-audit pilot with `RR_DIRECT`, where a cluster is represented directly by a sparse executable set of within-sample feature relations rather than by a post-hoc explanation alone.

## Run

```bash
PYTHON_BIN=.venv/bin/python bash scripts/20_run_pilot_v2.sh
PYTHON_BIN=.venv/bin/python bash scripts/21_run_pilot_v2_1.sh
PYTHON_BIN=.venv/bin/python bash scripts/22_finalize_pilot_v2.sh
```

Pilot v2 executes synthetic falsification, eleven real binary omics datasets, bidirectional frozen GSE10072/GSE19804 transfer, automatic figures and a prospective GO/STOP summary. The real-data fitting stage remains label-blind; labels are opened only by the evaluation-owned loader.

## Status boundary

The original Pilot v2 prospective gate remains **STOP** because the designated-pair rule-recovery criterion failed. Pilot v2.1 is an identifiability diagnostic: it makes the synthetic exact-recovery endpoint uniquely identifiable while leaving RR_DIRECT hyperparameters unchanged. It must not be interpreted as a retrospective PASS of Pilot v2.

Tracked compact evidence is generated under `docs/pilot_v2/evidence/` plus `docs/pilot_v2/PILOT_EVIDENCE.md`. Full temporary results remain under the Git-ignored `results/` tree.
