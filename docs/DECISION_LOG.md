# Decision log

## Frozen for PILOT-001--006

1. The protocol is authoritative and is stored byte-for-byte in this repository.
2. Feature selection is source-only MAD on observed source values, before
   imputation, with deterministic `feature_id` tie breaking.
3. Value preprocessing uses source medians and source IQRs; zero IQR uses a recorded `1.0` fallback.
4. Ties receive average ranks and missing states use an explicit mask.
5. Normalized Footrule uses the maximum Spearman Footrule `floor(p^2 / 2)`.
6. Relation Hamming is normalized over jointly observed, positive-weight relations only.
7. Hybrid scales are fitted only on source distance matrices.
8. Clustering uses one deterministic PAM BUILD+SWAP implementation for every representation.
9. `K` is an explicit experimental control and is never calculated from evaluation labels.

## Frozen after the PILOT-007--011 smoke gate

10. Simulation truth remains in `rep_audit.evaluation`; source and target
    `DatasetBundle` objects have no label field, and the source audit accepts
    neither a target object nor labels.
11. VALUE, RELATIONAL, HYBRID and NULL generators use independent source and
    target random streams. A target-shift change cannot alter source bytes or
    any source preprocessing/audit artifact.
12. The VALUE control contains magnitude shifts only in its informative block,
    keeps its non-informative source background fixed, and applies technical
    scaling/offset stress on target. This prevents a sample-wide source batch
    factor from becoming the intended VALUE clustering signal.
13. Relation candidates are all canonical unordered pairs in the shared
    source-selected feature universe. Screening is source-only and retains
    relations by coverage, normalized entropy/non-constancy and small-
    perturbation stability, with `relation_id` tie breaking.
14. The source audit quality is exactly `Q = min(PS, STAB, INV)`, subject to
    non-degeneracy. Representation stability is reported separately and
    complexity is only a tie-breaker.
15. NULL eligibility uses a method-specific upper quantile. Multiple-method
    opportunity is controlled by adding the upper quantile of cross-fitted
    maximum `(Q - method-specific threshold)` excesses. Raw Q thresholds from
    different representations are not pooled.
16. HYBRID must exceed both best pure endpoints by the larger of `0.02` and
    the NULL-calibrated upper hybrid-gain quantile. Pure solutions within the
    `0.02` equivalence margin prefer the simpler representation.
17. The smoke grid is frozen at eight cells, five replicates per cell,
    `n_source=n_target=90`, `p=200`, `K=3`, `B=5`, `M=500`, margin `0.00` and
    hybrid alphas `0.25/0.50/0.75`.
18. Scientific job artifacts are canonical and immutable. Runtime is recorded
    separately; deterministic comparisons cover 242 key files and exclude
    runtime measurements.
19. Smoke acceptance freezes the implementation and calibration formula, not
    a claim of full Gate B or external validity. Target regret, score/target
    correlation, the full 630-pair grid and real transfers remain required.

## Deferred scientific risk

A stable technical nuisance can be statistically indistinguishable from a
stable biological cluster when only `X` is available. NULL/nuisance simulation
reduces the false-positive risk but cannot prove that a stable real-data group
is biological. No batch-aware diagnostic has been introduced.

The GSE10072/GSE19804 transfer is also a combined biological and technical
stress test, because their normal-tissue definitions differ and GSE19804 has a
paired tumour/adjacent-normal design. This must be reflected in the later Gate C
interpretation.
