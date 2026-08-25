# Pilot v2 — Sparse Relational Prototypes

## Frozen question
Can clusters be learned directly as sparse within-sample relational prototypes that simultaneously define the group, explain membership, and assign unseen objects?

## Primary method
`RR_DIRECT`: each cluster prototype is a sparse set of executable relations `feature_a > feature_b` (or its reverse). The prototype is not fitted after clustering; partition and prototype are updated together until stable.

## Comparators
1. VALUE/PAM — Euclidean geometry after robust standardisation.
2. RELATION/PAM — Hamming geometry over pairwise within-sample relations.
3. RELATION/PAM + POSTHOC — relation-space partition followed by a sparse rule summary.
4. RR_DIRECT — direct sparse relational prototype clustering.

## Synthetic falsification block
Known relational clusters are generated under sample-wise positive affine magnitude distortions and three noise levels, alongside VALUE and NULL controls. The implemented v2 endpoints are ARI, designated-pair recovery, prototype size, frozen-target ARI, coverage, and score margins. Missing-value handling is exercised separately and is used for real-data execution; v2 does not contain a dedicated synthetic missingness sweep or a formal stability endpoint.

## Real-data block
Eleven frozen binary omics datasets already present in the repository are fitted label-blind. Predictions/prototypes are written before evaluation labels are opened. Evaluation then reports ARI/NMI only; labels never enter fitting.

A frozen source→target transfer block uses GSE10072/GSE19804 in both directions and reports target ARI plus rejection coverage.

## Gate v2
GO for continued SONATA development requires all of:
- synthetic median RR_DIRECT ARI >= 0.75 across non-NULL settings;
- median rule-recovery >= 0.60;
- the preregistered v2 NULL proxy — synthetic-null ARI > 0.50 together with mean source score margin > 0.15 — occurs in no more than 10% of replicates;
- RR_DIRECT median real-data ARI is not worse than RELATION/PAM by >0.05;
- at least one frozen lung transfer direction reaches ARI >= 0.70 with coverage >= 0.70.

Thresholds are prospective for Pilot v2 and must not be relaxed after looking at results.

**Interpretation of the NULL criterion.** The v2 NULL endpoint is a preregistered proxy, not a complete source-only no-structure detector. RR_DIRECT v2 always fits the frozen K=2 benchmark and does not yet implement source-side abstention. A confirmatory SONATA-stage method should add source-only null/stability calibration and explicit `NO_STABLE_STRUCTURE` / abstention.

## Missing-data handling (implementation clarification before successful v2 evaluation)
- Features with no observed source values are excluded before VALUE/RELATION screening and RR_DIRECT feature selection.
- Remaining source values use deterministic source-only median imputation where a finite matrix is required for fitting.
- Frozen RR_DIRECT target assignment does **not** estimate target-cohort medians: a rule is ignored for a sample when either participating feature is missing; samples without enough executable prototype information are `UNASSIGNED`.
- This clarification fixes an implementation failure observed before real-data evaluation completed. No prospective Gate v2 threshold is changed.


## Implementation clarification HOTFIX-2 (pre-evaluation runtime fix)

Before any real-data labels were opened, a strict distance validation failure
revealed machine-level floating-point asymmetry in a mathematically symmetric
pairwise Euclidean matrix.  All pairwise distance matrices are therefore
canonicalized as `(D + D.T) / 2` with an exact zero diagonal before the existing
strict `DistanceMatrix` validation.  No experimental threshold, dataset, method,
seed, gate criterion, or label-handling rule is changed.

The RR_DIRECT implementation also rebuilds its prototypes from the final
partition before returning, so labels and executable prototypes remain aligned
even if the iteration cap is reached.
