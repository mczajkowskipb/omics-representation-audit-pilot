# Omics Representation Audit Pilot

Deterministic Python reference implementation for the source-only
representation audit in the SONATA BIS pilot. The repository implements the
approved scope **PILOT-001--011**.

## The idea in plain language

The same patient can be compared in several ways:

- **VALUE**: compare absolute, source-scaled measurements;
- **RELATIONAL**: compare which features rank above or below other features;
- **HYBRID**: combine both distances;
- **NO_STABLE_STRUCTURE**: abstain when no representation supports stable groups.

The implemented Representation Audit compares those views using only the
source cohort. It measures split prediction strength, cluster stability and
perturbation invariance, rejects degenerate or NULL-like structure, and then
selects VALUE, RELATIONAL, HYBRID, or `NO_STABLE_STRUCTURE`. Every candidate
uses the same deterministic PAM implementation.

PAM represents each cluster by a **medoid**, meaning one actual source sample
that is most central under the selected distance. A later post-hoc region step
(PILOT-016) may summarize a relational cluster by sparse rules such as
`gene_A > gene_B` and `gene_C < gene_D`. That rule set is the planned
interpretable analogue of a centroid.

Regions, real-data adapters, frozen target transfer and anchors are
intentionally not implemented yet. Fuzzy methods, evolutionary algorithms,
deep learning, federated learning, CUDA and a portal remain outside scope.

## Setup and verification

```bash
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
PYTHON_BIN=.venv/bin/python bash scripts/01_verify_core.sh
```

The extended command additionally runs the frozen 40-dataset smoke grid and
refuses to overwrite an existing result directory:

```bash
PYTHON_BIN=.venv/bin/python \
SMOKE_OUTPUT=results/smoke40_verify \
bash scripts/03_verify_pilot_007_011.sh
```

Two independent smoke runs can be compared while deliberately excluding
non-deterministic runtime measurements:

```bash
.venv/bin/python scripts/04_compare_smoke_artifacts.py \
  results/smoke40_run_a results/smoke40_run_b
```

The accepted smoke result and limitations are documented in
`docs/PILOT_007_011_REPORT.md`. Passing this smoke grid is not the full Gate B:
target ARI regret, score/performance correlation, the 630-pair primary grid and
real external transfer remain untested.

## Leakage boundary

`DatasetBundle` deliberately has no label field. Evaluation labels live in the
separate `rep_audit.evaluation` namespace. Core fitting, representation,
clustering and audit modules cannot import that namespace. A fixed
experimental `K` is supplied by frozen configuration and is never inferred
from class labels. Target values and target labels are not accepted by the
source-audit or selector interfaces.
