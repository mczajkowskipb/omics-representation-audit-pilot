# Pilot v2 results

**Prospective gate:** STOP

## Metrics

- **synthetic_rel_median_ari**: 1.0000
- **synthetic_rel_median_rule_recovery**: 0.1667
- **null_high_confidence_rate**: 0.0000
- **real_rr_median_ari**: 0.0332
- **real_relation_pam_median_ari**: 0.0223
- **real_median_difference_rr_minus_relation**: 0.0116
- **best_transfer_ari**: 0.9596
- **best_transfer_coverage_at_best_ari**: 0.9252

## Gate checks

- synthetic_ari: PASS
- rule_recovery: FAIL
- null_control: PASS
- real_noninferiority: PASS
- transfer: PASS

## Real datasets

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
