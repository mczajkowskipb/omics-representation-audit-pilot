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

## Frozen for PILOT-012--015

20. Reference adapters accept only an exact upstream commit and exact file
    size/SHA-256. Their fitting manifests contain X paths only; y paths exist
    solely in an evaluation-owned manifest.
21. The primary grid is exactly 630 pairs: 18 signal cells and 3 NULL cells,
    each with 30 replicates. The three shift levels are paired views of one
    source cohort, so 210 source audits feed 630 independently frozen target
    assignments.
22. The count of 630 in the protocol does not contain a margin axis. Primary
    execution therefore freezes margin `0.00`; margin `0.02` is not selected
    retrospectively after target evaluation.
23. Gate B target ARI/regret uses a forced nearest-medoid assignment for all
    target samples, isolating representation quality. Rejection coverage is
    reported separately and cannot improve the ARI used by the gate.
24. Target rejection is source-fitted: cluster radius is the source
    within-cluster distance 95th percentile, confidence is the source 5th
    percentile of the normalized nearest/second-medoid gap, and minimum
    feature/relation coverage is `0.80`.
25. Real transfer uses the 22,277 probe IDs common to GSE10072 and GSE19804.
    MAD selection of 200 probes, preprocessing, relation screening, hybrid
    scales, method selection and medoids use source values only.
26. K=2 for both lung directions is the predeclared binary benchmark control,
    not a value inferred from evaluation labels. NULL calibration is separately
    matched to K=2 and source sample sizes 107 and 120 with 30 replicates each.
27. Gate B is GO. Gate C is STOP because forward regret is
    `0.10528419284859625`, above the frozen reverse-direction allowance of
    `0.10`; no post-label retuning or threshold relaxation is permitted.
28. PILOT-016, direct regions and anchors remain blocked pending an explicit
    decision on the Gate C STOP. The current result must not be presented as a
    passed external-transfer gate.

## Frozen for the closeout block

29. The protocol-required within-dataset analysis covers exactly Golub, Colon,
    DLBCL and the eight AIR datasets. K=2 is the predeclared binary benchmark
    control for every dataset; membership labels remain unavailable until all
    eleven audit decisions and assignments have immutable markers.
30. Real within-dataset NULL calibration is K- and exact-sample-size-aware,
    using 30 NULL reports for each of the eleven distinct sample sizes. Cached
    reports must match the complete audit-configuration hash and sample count.
31. Within-dataset ARI/NMI is descriptive, not external validation and not a
    new GO/STOP gate. Stable unsupervised structure may be unrelated to the
    available clinical label. These results cannot rescue or modify Gate C.
32. Gate C remains STOP without threshold relaxation or target retuning.
    PILOT-016--018 are closed as `NOT_RUN_BLOCKED_BY_GATE_C_STOP`; PILOT-019
    validates and collects the completed evidence, and PILOT-020 reports the
    mixed result without claiming that direct regions or anchors were tested.

## Deferred scientific risk

A stable technical nuisance can be statistically indistinguishable from a
stable biological cluster when only `X` is available. NULL/nuisance simulation
reduces the false-positive risk but cannot prove that a stable real-data group
is biological. No batch-aware diagnostic has been introduced.

The GSE10072/GSE19804 transfer is also a combined biological and technical
stress test, because their normal-tissue definitions differ and GSE19804 has a
paired tumour/adjacent-normal design. This must be reflected in the later Gate C
interpretation.

The working AIR checkout discovered during adapter validation contained
pre-existing truncated copies of GSE17920 and GSE27272. All accepted adapter
checks used a separate clean detached snapshot at commit
`2dee739f6ee5e001ef1be76df2eb753ca389adb3`; neither reference repository was
modified.

At closeout, that detached AIR snapshot also contained one untracked temporary
partial file, `data/final/GSE19804/.X_features_x_samples.csv.Bceve0`, timestamped
before the closeout run. It was preserved rather than deleted. Git reported no
tracked changes, and the adapter accepted only the tracked GSE19804 matrix with
the manifest-pinned size and SHA-256; the untracked file was not read.

## Post-pilot grant-writing block

33. The scientific pilot remains closed at commit `9adae88`; the grant-writing
    block does not reopen Gate C, run PILOT-016--018 or create a new scientific
    result.
34. Grant-facing numerical claims are machine-checked against
    `docs/evidence/PILOT_019_VALIDATION.json`. Gate B remains GO, Gate C remains
    STOP and real within-dataset results remain descriptive.
35. The proposed SONATA BIS centre of gravity is TRPP: source-only
    representation adequacy followed by prospective direct sparse relational
    regions and frozen multi-cohort transfer. Automatic representation
    selection is not presented as already validated across cohorts.
36. Anchor restriction is conditional and anchor sets are excluded from the
    core proposal. No target-driven rescue, threshold relaxation or additional
    post-label model selection is authorised by this writing block.
