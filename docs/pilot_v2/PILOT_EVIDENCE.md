# Pilot v2 / v2.1 evidence snapshot

This directory contains compact, tracked evidence copied from the reproducible run directories under `results/`. The original result directories remain ignored by Git; this snapshot is intended for repository review and grant-facing traceability.

## Scientific status

**Pilot v2 prospective gate: STOP.** Four of five preregistered criteria passed; exact designated-pair recovery failed. Thresholds were not relaxed after observing the result.

- `null_control`: PASS
- `real_noninferiority`: PASS
- `rule_recovery`: FAIL
- `synthetic_ari`: PASS
- `transfer`: PASS

Pilot v2.1 is a diagnostic identifiability addendum only. It does not convert Pilot v2 to GO and must not be reported as a retrospective gate rescue.

## Pilot v2 key metrics

- synthetic RR_DIRECT median ARI: **1.0000**
- synthetic designated-pair recovery: **0.1667**
- NULL high-confidence false-structure rate: **0.0000**
- real RR_DIRECT median ARI: **0.0332**
- real RELATION/PAM median ARI: **0.0223**
- median real RR_DIRECT − RELATION/PAM ARI: **0.0116**
- best frozen transfer ARI: **0.9596**
- coverage at best transfer ARI: **0.9252**

The low median ARI on the eleven real within-dataset tasks is evidence against claiming broad real-data superiority at this stage. The strong frozen transfer result is promising but should be presented as a pilot observation, not definitive external validation of the full future framework.

## Eleven real omics datasets

| dataset | RELATION_PAM | RELATION_PAM_POSTHOC | RR_DIRECT | VALUE_PAM |
| --- | --- | --- | --- | --- |
| DLBCL | 0.022 | 0.000 | 0.329 | 0.018 |
| GDS2771 | 0.006 | -0.004 | 0.008 | -0.002 |
| GSE10072 | 0.087 | 0.000 | 0.926 | 0.598 |
| GSE17920 | 0.027 | 0.003 | -0.000 | 0.041 |
| GSE19804 | 0.063 | 0.094 | 0.839 | -0.001 |
| GSE25837 | 0.011 | -0.027 | 0.033 | 0.016 |
| GSE27272 | -0.010 | 0.000 | 0.002 | 0.002 |
| GSE3365 | 0.068 | 0.000 | 0.055 | -0.015 |
| GSE6613 | 0.006 | 0.000 | -0.001 | -0.002 |
| colon | 0.002 | 0.008 | 0.446 | -0.042 |
| golub | 0.050 | 0.000 | -0.008 | -0.013 |

## Frozen transfer

| source | target | method | ari | coverage | mean_score | mean_margin |
| --- | --- | --- | --- | --- | --- | --- |
| GSE10072 | GSE19804 | RR_DIRECT_FROZEN | 0.771 | 0.967 | 0.930 | 0.860 |
| GSE19804 | GSE10072 | RR_DIRECT_FROZEN | 0.960 | 0.925 | 0.910 | 0.816 |

## Pilot v2.1 identifiability diagnostic

- median source ARI: **1.0000**
- median exact-pair recovery: **1.0000**
- median frozen-target ARI: **1.0000**
- median target coverage: **1.0000**
- all replicates exact-pair recovery: **True**
- all replicates source ARI ≥ 0.75: **True**

The v2.1 result supports the diagnosis that the original exact-recovery endpoint was non-identifiable because many cross-pair relations were equally discriminative. RR_DIRECT hyperparameters were unchanged.

## Reproduction

```bash
PYTHON_BIN=.venv/bin/python bash scripts/20_run_pilot_v2.sh
PYTHON_BIN=.venv/bin/python bash scripts/21_run_pilot_v2_1.sh
.venv/bin/python scripts/22_collect_pilot_v2_evidence.py
```

Real-data inputs are not duplicated here. They are loaded through the repository's integrity-checked reference adapters and manifests, preserving the existing source-only / evaluation-label separation.
