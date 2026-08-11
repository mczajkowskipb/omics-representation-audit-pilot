# Omics Representation Audit Pilot

Deterministic Python reference implementation for the first correctness gate
of the SONATA BIS pilot.

## The idea in plain language

The same patient can be compared in several ways:

- **VALUE**: compare absolute, source-scaled measurements;
- **RELATIONAL**: compare which features rank above or below other features;
- **HYBRID**: combine both distances;
- **NO_STABLE_STRUCTURE**: abstain when no representation supports stable groups.

The later Representation Audit will decide, using the source cohort only,
which view is most credible before evaluating an independent target cohort.
Only after that gate may relational clusters be summarized by sparse rule
regions such as `gene_A > gene_B` and `gene_C < gene_D`. Such a region is an
interpretable group prototype: an analogue of a centroid, but made of stable
relations rather than arithmetic means.

This repository currently implements only **PILOT-001--006**: contracts,
source-only preprocessing, ranks and ternary relations, matched distances, and
deterministic PAM with golden tests. It does not yet implement the audit,
simulators, direct regions, anchors, fuzzy methods, evolutionary algorithms,
deep learning, federated learning, CUDA, or a portal.

## Setup and verification

```bash
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
PYTHON_BIN=.venv/bin/python bash scripts/01_verify_core.sh
```

The verification command runs the strict environment check and the complete
PILOT-001--006 test suite. A successful command establishes the core of Gate A
only; it does not establish that the future Representation Audit selects the
right family.

## Leakage boundary

`DatasetBundle` deliberately has no label field. Evaluation labels live in the
separate `rep_audit.evaluation` namespace. Core fitting and clustering modules
must not import that namespace. A fixed experimental `K` is supplied by frozen
configuration and is never inferred from class labels.
