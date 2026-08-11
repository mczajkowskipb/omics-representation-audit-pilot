# PILOT-001--006 acceptance report

Date: 2026-08-11

Protocol: `SONATA BIS PILOT PROTOCOL v1.0`

Protocol SHA-256: `5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704`

## Plain-language status

This block builds the measuring and clustering foundation. A patient can now
be represented by robust values, within-patient ranks/relations, or a hybrid
distance, and every such distance is passed to the same deterministic PAM
engine. The block does **not** yet decide which representation is appropriate
for a dataset. That source-only Representation Audit begins with PILOT-007--010.
Sparse relation regions that describe a cluster by rules such as `gene_A >
gene_B` are later work (PILOT-016--017).

## Repository structure

```text
omics-representation-audit-pilot/
  configs/pilot.yml
  data/{README.md,manifests/}
  docs/{SONATA_BIS_PILOT_PROTOCOL_v1.md,DECISION_LOG.md,REUSE_AUDIT.md,
        PILOT_REPORT.md}
  results/README.md
  scripts/{00_check_environment.py,01_verify_core.sh}
  src/rep_audit/
    clustering/pam.py
    data/schema.py
    distances/{validation,value,footrule,relation_hamming,hybrid}.py
    evaluation/external_labels.py
    io/canonical_json.py
    preprocessing/{artifact,robust}.py
    representations/{ranks,ternary_relations}.py
  tests/{unit,integration,determinism,golden}/
  .gitignore
  LICENSE
  pyproject.toml
  requirements.lock
  README.md
```

## Stage reports

### PILOT-001 — repository and environment

Changes:

- created an independent Python package and repository skeleton;
- stored the protocol byte-for-byte and pinned its checksum;
- froze deterministic one-thread CPU settings and prohibited dependency
  families;
- recorded exact direct dependency versions used for acceptance.

Principal files:

- `pyproject.toml`, `requirements.lock`, `.gitignore`, `LICENSE`, `README.md`;
- `configs/pilot.yml`;
- `scripts/00_check_environment.py`, `scripts/01_verify_core.sh`;
- `tests/unit/test_environment_contract.py`.

Acceptance: 3 environment-contract tests passed; the strict environment report
returned all checks `true`.

Risks: this validates the current 9-CPU container, not the approximately
30-core target server. The same strict command must be run on that server
before experiments.

Deviation: none.

### PILOT-002 — label-free data contract

Changes:

- added immutable `DatasetBundle` with defensive matrix copying, stable IDs,
  explicit NaN support, and deterministic fingerprinting;
- placed `EvaluationLabels` only under `rep_audit.evaluation`;
- added an AST import firewall so fitting/clustering code cannot import the
  evaluation namespace.

Principal files:

- `src/rep_audit/data/schema.py`;
- `src/rep_audit/evaluation/external_labels.py`;
- `tests/unit/test_data_schema.py`;
- `tests/unit/test_label_import_firewall.py`.

Acceptance: 11 schema and label-firewall tests passed. Three additional
cross-stage leakage tests passed after the complete pipeline was available.

Risks: the firewall protects project interfaces and imports; raw user-written
code could still violate the protocol, so later job runners must expose only
the frozen label-free interfaces.

Deviation: none.

### PILOT-003 — source-only preprocessing artifact

Changes:

- implemented source-only MAD feature selection with stable `feature_id` tie
  resolution;
- computed MAD on observed source values before imputation;
- froze source medians, median imputation, linear source IQRs, and explicit
  zero-IQR fallback;
- made artifacts canonical, hashed, atomic, reloadable, and byte-stable;
- allowed a target to contribute only a label-free feature-ID intersection.

Principal files:

- `src/rep_audit/preprocessing/artifact.py`;
- `src/rep_audit/preprocessing/robust.py`;
- `src/rep_audit/io/canonical_json.py`;
- `tests/unit/test_preprocessing.py`;
- `tests/determinism/test_preprocessing_subprocess.py`;
- `tests/integration/test_no_leakage.py`.

Acceptance: 10 dedicated preprocessing/determinism tests and 3 cross-stage
leakage tests passed. Changing target values did not change the source
artifact; changing evaluation labels changed neither artifacts nor PAM
assignments.

Risks: all-missing source features are deliberately ineligible; a requested
budget larger than the eligible common universe stops with an error.

Deviation: none. The treatment of missing values in MAD was made explicit in
the decision log without changing the source-only MAD criterion.

### PILOT-004 — ranks, ties, and ternary relations

Changes:

- implemented per-sample normalized average ranks;
- represented missingness by a separate observation mask;
- implemented `-1/0/+1` ordered relations with strict margin boundaries;
- made tie behavior independent of feature-column order.

Principal files:

- `src/rep_audit/representations/ranks.py`;
- `src/rep_audit/representations/ternary_relations.py`;
- `tests/unit/test_ranks_relations.py`.

Acceptance: 11 rank/relation tests passed, including monotone invariance,
column-permutation ties, reverse pairs, exact-margin zero states, and masked
missingness.

Risks: unsupervised relation screening and the frozen relation budget are not
part of PILOT-004 and remain unimplemented.

Deviation: none.

### PILOT-005 — matched distances

Changes:

- added validated immutable precomputed distance matrices;
- implemented Euclidean and correlation value distances;
- implemented normalized Spearman Footrule;
- implemented masked weighted ternary pair-Hamming;
- implemented hybrid scaling from the source-only median nonzero upper
  triangle and exact normalized endpoints.

Principal files:

- `src/rep_audit/distances/validation.py`;
- `src/rep_audit/distances/value.py`;
- `src/rep_audit/distances/footrule.py`;
- `src/rep_audit/distances/relation_hamming.py`;
- `src/rep_audit/distances/hybrid.py`;
- `tests/unit/test_distances.py`.

Acceptance: 15 distance tests passed. Footrule is zero for identical rankings,
missing relations are masked, invalid matrices are rejected, and hybrid
`alpha=0/1` exactly reproduces the normalized pure endpoints.

Risks: Footrule deliberately rejects incomplete rank vectors; pair-Hamming
deliberately rejects a sample pair with no jointly observed positive-weight
relation. Correlation distance rejects constant sample profiles rather than
inventing a value.

Deviation: none.

### PILOT-006 — deterministic PAM

Changes:

- implemented deterministic PAM BUILD followed by exhaustive best-improving
  SWAP iterations;
- resolved all ties by stable sample ID;
- protected empty output clusters by assigning each medoid to itself;
- returned medoid IDs, assignments, total objective, objective trace, hashes,
  and canonical atomic JSON artifacts;
- used the same `DistanceMatrix` input for value, relational, and hybrid cases.

Principal files:

- `src/rep_audit/clustering/pam.py`;
- `tests/golden/test_pam_golden.py`;
- `tests/determinism/test_pam_determinism.py`.

Acceptance: 12 PAM tests passed. Tiny cases match an independent exhaustive
medoid optimum, including a six-point counterexample where the old reference
updater had objective 27 and the accepted optimum is 21. Objective traces are
non-increasing, tied/duplicate data produce no empty output cluster, row order
does not alter the sample-ID result, and repeated JSON artifacts are
byte-identical.

Risks: this correctness-first PAM checks all candidate swaps and must be
benchmarked before the full grid; performance optimization must preserve the
golden outputs.

Deviation: none.

## Consolidated verification

Acceptance command:

```bash
PYTHON_BIN=.venv/bin/python bash scripts/01_verify_core.sh
```

Final result, run twice independently under one-thread settings:

```text
run 1: 65 passed in 0.87 s
run 2: 65 passed in 0.79 s
skipped/xfail: 0
```

Additional checks:

- `python -m pip check`: no broken requirements;
- `python -m compileall -q src tests scripts`: no errors;
- strict protocol checksum: matched;
- forbidden project dependencies: absent;
- key preprocessing and PAM JSON outputs: byte-identical across repeated or
  independent-process runs.

During development, two regular-expression assertions in the PILOT-002 tests
were corrected to escape literal parentheses, and one PILOT-004 fixture was
corrected because it supplied three matrix columns with four feature IDs.
Neither correction changed production code or an experimental criterion. The
MAD missing-value clarification did change production code before final
acceptance; its dedicated regression test and the full suite pass.

## Remaining experiment-level risks

1. A stable technical nuisance can look like stable biological structure when
   the audit sees only `X`; the NULL/nuisance simulations and Gate B claims
   need explicit review before PILOT-008--010.
2. No simulation has yet established whether VALUE, RELATIONAL, HYBRID, or
   NO_STABLE_STRUCTURE is selected correctly. PILOT-001--006 establish
   implementation correctness only.
3. No real dataset has been loaded and no target cohort has been used for
   tuning or evaluation.
4. Sparse post-hoc/direct regions and anchors are intentionally absent.

## Exact next task

Implement one larger simulation block covering PILOT-007 and PILOT-008:
VALUE/RELATIONAL/HYBRID/NULL source-target generators plus nuisance and
perturbation mechanisms, with fixed seeds, source/target independence,
directional golden tests, determinism tests, and leakage tests. Stop for review
before implementing the Representation Audit itself (PILOT-009--010).
