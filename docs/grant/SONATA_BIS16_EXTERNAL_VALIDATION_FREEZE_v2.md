# SONATA BIS 16 — prospective external-cohort freeze v2

**Freeze timestamp:** 2026-08-25 19:50 CEST  
**Status:** metadata-only cohort selection; no confirmatory RR_DIRECT outcome analysis has been run on the frozen targets.

## Primary confirmatory module — lung adenocarcinoma

### Source: GSE19804
Previously used in the pilot; therefore it is not an untouched target. It is the frozen discovery/source cohort for the future confirmatory transfer.

### Untouched target 1: GSE27262
- 25 stage-I lung adenocarcinoma tumour/adjacent-normal pairs (50 samples);
- Affymetrix HG-U133 Plus 2.0 (GPL570);
- same-platform confirmatory target;
- absent from the frozen 11-dataset pilot;
- no RR_DIRECT transfer result inspected before this freeze.

### Untouched target 2: GSE32863
- 58 lung adenocarcinoma and 58 matched adjacent non-tumour tissues;
- Illumina HumanWG-6 v3.0 (GPL6884);
- deliberate cross-platform confirmatory target;
- metadata had previously been listed in the proposal-stage dataset audit, but no RR_DIRECT confirmatory outcome evaluation or target-guided tuning was run.

## Frozen G5 criterion

A **single source artifact fitted on GSE19804** must be applied unchanged to both targets.

For **each** target:
1. executable coverage must be **>= 0.70**;
2. forced all-sample ARI from frozen prototype scores must be **>= 0.50**;
3. assigned-sample ARI/NMI, rejection rate, score, margin and executable-rule coverage are secondary diagnostics;
4. every target sample and failed direction is reported.

**G5 PASS:** both targets satisfy criteria 1–2.  
**G5 FAIL:** either target fails. A failed target cannot be replaced after evaluation labels are opened.

Forced all-sample ARI is used as the primary quality criterion so that selective rejection cannot artificially improve the quality score; coverage is evaluated separately.

## Mapping freeze

To preserve one source prototype across both targets:
- the eligible common gene universe is defined before source fitting from platform annotation only;
- target expression values and labels cannot determine the universe;
- the identifier namespace, annotation release, multi-probe aggregation rule and mapping hashes are frozen before source fitting;
- a practical default is within-sample median aggregation when multiple platform features map to one gene;
- low target coverage causes `UNASSIGNED`/FAIL rather than target-guided replacement of genes.

## Secondary colorectal module

Accession-level freeze:
- **source:** GSE39582;
- **target 1:** GSE14333;
- **target 2:** GSE33113.

This secondary module **cannot rescue** a failed primary lung G5. Its exact subtype/phenotype endpoint is finalized only after a sample-level metadata audit, before labels are opened.

## Label firewall

For every confirmatory target:
1. create a sample/feature manifest;
2. keep evaluation labels outside the fit/assignment namespace;
3. fit the source artifact and write target assignments, scores, coverage and hashes;
4. seal the prelabel artifact;
5. only then open phenotype/subtype labels in the evaluation process;
6. no rerun may modify the source artifact after unsealing.

## Prohibited
- joint source-target normalization;
- target-dependent batch correction;
- target-performance-guided mapping, feature or relation selection;
- target-driven K or threshold tuning;
- target reclustering;
- replacing a failed target after unsealing;
- reporting only favourable transfer directions.

## Interpretation boundary

“Untouched target” means unused for RR_DIRECT fitting, model selection, threshold tuning or target-performance-guided feature/relation selection. Public metadata may be inspected for platform, sample type, histology and technical eligibility.

