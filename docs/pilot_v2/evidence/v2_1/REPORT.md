# Pilot v2.1 — identifiability diagnostic addendum

**Pilot v2 prospective gate remains STOP. This addendum does not change or relax it.**

The original REL synthetic generator shifted all six left-hand genes together and all six right-hand genes together. Consequently, many cross-pair relations were equally class-discriminative, so exact recovery of only six designated pairs was not an identifiable endpoint.

This diagnostic generator separates the six signal pairs into distinct order blocks. Only the six within-block relations reverse between groups; cross-block relations are class-independent. RR_DIRECT parameters are unchanged.

## Diagnostic metrics

- **median_source_ari**: 1.0
- **median_exact_pair_recovery**: 1.0
- **median_target_ari**: 1.0
- **median_target_coverage**: 1.0
- **all_replicates_exact_pair_recovery**: True
- **all_replicates_source_ari_at_least_0_75**: True

## Interpretation boundary

These results may be used to diagnose the failed v2 rule-recovery endpoint, but must not be reported as a retrospective PASS of the original prospective v2 gate.
