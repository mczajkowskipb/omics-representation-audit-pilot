# Pilot v2.1 — identifiability diagnostic addendum

## Status

Pilot v2 remains **STOP** under its prospective gate. This addendum does not relax, replace, or retrospectively rescue that decision.

## Why the addendum is needed

The original v2 REL generator assigned the same class-dependent shift to all six left-hand signal genes and the opposite shift to all six right-hand signal genes. Therefore, not only the six designated pairs but many left-vs-right cross-pairs became equally class-discriminative. Exact recovery of the six designated pairs was consequently non-identifiable even when clustering itself was perfect.

The observed v2 pattern is consistent with that failure mode: synthetic RR_DIRECT ARI was 1.0 while median designated-pair recovery was 1/6.

## Diagnostic design

The v2.1 generator keeps the RR_DIRECT hyperparameters unchanged but makes the rule-recovery endpoint identifiable. Six signal pairs occupy separated order blocks. Within each block, the designated pair reverses direction between the two groups. Cross-block relations remain class-independent. Positive sample-wise affine transformations retain the intended within-sample invariance.

The addendum records source ARI, exact designated-pair recovery, frozen-target ARI, target coverage, prototype size, convergence, and margins across the same three noise levels and 40 replicates per level.

## Interpretation

A positive diagnostic result supports the claim that the v2 rule-recovery failure arose from the synthetic endpoint design rather than from inability of RR_DIRECT to recover uniquely identifiable relations. It must not be presented as a retrospective PASS of the original prospective v2 gate.
