# Representation Adequacy and Transportable Relational Profiles in Omics Clustering

**Principal method family:** TRPP (Transportable Relational Patient Profiles)
**Scheme:** SONATA BIS 16  
**Duration:** 48 months  
**Primary panel:** ST6  
**Document status:** complete scientific draft; administrative, personnel, and
budget data must be supplied by the applicant before submission.

## 1. Scientific objective

Patient stratification from omics measurements depends on an early decision
that is usually implicit: what does it mean for two patients to be similar?
Distances between normalised expression values, distances between within-sample
ranks, and distances between pairwise ordering relations such as
`gene A > gene B` define different geometries and can yield different groups.
There is no reason to expect one geometry to be best for every disease,
platform, or cohort shift. Moreover, a stable partition of a discovery cohort
does not by itself imply biological relevance or transportability to new
patients.

The central question is when magnitude information should be retained,
replaced by within-sample relations, combined with them, or judged insufficient
for stable and transportable omics clustering. The project will develop a
leakage-controlled framework that audits this decision on the source cohort
only. Where relational structure is supported, it will learn Transportable
Relational Patient Profiles (TRPP) as short within-patient rule sets. A complete
source artifact - preprocessing, selected features and relations, distance
scales, representation decision, profiles, thresholds, and assignment rule -
will be frozen before it is applied to independent cohorts. Target samples will
be assigned without reclustering, joint normalisation, or target tuning; an
uncertain sample may remain `UNASSIGNED`.

The central hypothesis is that measurable signal and shift properties determine
whether transportable grouping should retain values, use within-sample
relations, combine both views, or abstain; within the relational domain,
biologically useful groups can be represented by sparse frozen rule sets. Four
objectives make this hypothesis falsifiable:

1. **Representation adequacy.** Establish when VALUE, RELATIONAL, HYBRID, or
   `NO_STABLE_STRUCTURE` is supported by source-only diagnostics.
2. **Direct relational regions.** Develop a deterministic algorithm that learns
   assignments and concise core/optional relational profiles jointly, and
   compare it with relational PAM followed by post-hoc rule extraction.
3. **Frozen transport.** Test whether source-learned profiles retain coverage,
   stability, interpretability, and external association in at least two target
   cohorts per disease module without target refitting.
4. **Applicability map.** Identify signal, noise, missing-feature, confounding,
   and platform-shift conditions under which relational information helps, is
   neutral, or fails.

The project does not assume that relational representations always win. A
valid outcome is a map showing that value geometry is preferable in some
regimes and that grouping should be withheld in others.

<!-- PAGE_BREAK -->

## 2. Significance and state of the art

High-dimensional omics studies commonly apply clustering after feature
filtering and normalisation. Yet algorithm choice is only part of the problem:
representation determines which variation is treated as signal. PAM provides a
useful controlled engine because it accepts arbitrary dissimilarities and uses
observed samples as medoids, but it still returns a partition for data with
little meaningful cluster structure. Stability resampling and prediction
strength address whether partitions persist under perturbation, while adjusted
Rand and mutual information quantify agreement after labels are revealed.
These tools do not, however, provide a general source-only decision among
candidate data geometries or a frozen rule system for assigning future samples.

Within-sample relative expression orderings have a complementary history in
supervised molecular classifiers. Top-scoring-pair methods showed that a few
comparisons can generate transparent decisions and reduce dependence on
absolute scale. Their success does not establish an unsupervised theory:
clustering lacks outcome labels during learning, pair spaces grow quadratically,
and technical shifts can alter gene-specific orderings. Conversely, conventional
batch correction can be effective for pooled analyses but is incompatible with
the primary frozen-transfer question when target distributional information is
used to refit the source representation.

Multi-view clustering already combines representations, interpretable
clustering already learns trees or rules, and transcriptomic single-sample
predictors already compare gene-pair rules with centroids. The project does not
claim any of those ingredients as new. It connects four elements that are
normally studied separately:

- an audit of representation adequacy before profile learning;
- explicit abstention when stability does not exceed a matched null process;
- direct learning of sparse regions made of within-sample relations rather than
  retrospective explanation of an arbitrary partition;
- application of a frozen patient-profile artifact to independent cohorts,
  including rejection when evidence is insufficient.

The project's novelty is therefore not the use of ranks, pair comparisons,
hybrid views, rules, PAM, or stability alone. It is the auditable architecture
and the direct optimisation of transportable within-sample relational regions
under a strict source/target boundary.
Each important claim has a negative counterpart: no stable structure, no
advantage over a post-hoc baseline, insufficient target feature coverage, or no
retained external association. These outcomes remain reportable rather than
being repaired after labels are inspected.

Preliminary work supports the question but does not settle it. A deterministic
Python pilot compared value, rank-relational, and hybrid representations using
one PAM implementation. In 630 controlled source-target pairs, the source-only
audit identified the generating family in 93.3% of signal replicates; median
target ARI regret was 0.000, the NULL false-structure rate was 6.7%, HYBRID was
never selected in pure regimes, and the source-audit/target-performance
Spearman association was 0.854. Gate B: GO.

The real-data evidence was deliberately more cautious. In eleven frozen
within-dataset audits, the selected representation was within 0.05 ARI of the
retrospective oracle in 9/11 cases, but median agreement with available labels
was only 0.065. In bidirectional GSE10072/GSE19804 transfer, one direction
matched the oracle (ARI 0.926; regret 0.000), whereas the reverse direction
obtained ARI 0.559 versus oracle 0.664 (regret 0.105284), exceeding the frozen
0.10 allowance. Gate C: STOP. Thresholds were not relaxed; direct regions:
NOT TESTED; anchors: NOT TESTED. The labels were used only after all source-only
decisions and assignments had been frozen. This mixed result identifies the
precise gap addressed by TRPP: within-cohort adequacy must be connected to an
explicit, multi-cohort model of transportability.

<!-- PAGE_BREAK -->

## 3. Concept and work plan

The 48-month project is organised into four overlapping work packages (WPs)
with preregistered transitions.

### WP1. Representation adequacy, invariance and abstention (months 1-12)

WP1 will formalise an operational invariance and information-loss taxonomy for
the finite VALUE, RELATIONAL, and HYBRID family, and turn it into controlled
predictions. Tests will include additive and multiplicative noise,
gene-specific offsets, monotone transformations, missing features, platform
mapping errors, nuisance structure, unequal groups, and unknown cluster
number. All views will use the same deterministic PAM in the matched primary
comparison. Source-only audit quality will combine perturbation stability,
prediction strength, non-degeneracy, and performance above matched NULL
distributions. Its output is an adequacy record or `NO_STABLE_STRUCTURE`, not a
promise that the chosen partition matches an unseen phenotype.

**WP1 gate:** profile learning proceeds only for non-degenerate solutions whose
source quality exceeds the frozen NULL eligibility rule. The controlled
benchmark must retain acceptable family discrimination, false-structure
control, and low target regret under held-out regimes. Failure narrows the audit
to descriptive diagnostics rather than triggering target-driven recalibration.

### WP2. Direct sparse relational regions (months 7-24)

WP2 will first implement `RR_POSTHOC`: deterministic relational PAM followed by
profile extraction. It will then develop `RR_DIRECT`, which alternates between
deterministic assignment and selection of relations that define compact regions.
A relation can be positive, tied, or negative; missingness is preserved rather
than silently converted to a tie. Profiles will distinguish core relations,
expected in most members, from optional relations that increase coverage
without dominating assignment. Candidate lengths of 10, 25, and 50 relations
will be declared in advance. Redundant inverse relations and excessive reuse of
a single gene will be controlled. All tie-breaking, empty-group handling, and
stopping conditions will be recorded in a trace.

**WP2 gate:** relative to `RR_POSTHOC`, `RR_DIRECT` must improve external
ARI/NMI by at least 0.05, improve bootstrap profile Jaccard by at least 0.10, or
remain within 0.03 while producing a materially shorter profile. Otherwise the
direct method stops and the post-hoc profile remains the supported result.

### WP3. Frozen multi-cohort transfer (months 18-38)

The lung module will use GSE10072 as the default source and GSE19804 and
GSE32863 as targets. It combines demographic/etiological and platform shifts;
GSE18842 is a preregistered broader-NSCLC sensitivity cohort. The colorectal
module will use tumour profiles from GSE39582 as source and GSE14333 and
GSE33113 as targets. CMS, stage, molecular markers, and outcomes are
evaluation-only; CMS is acknowledged as expression-derived rather than an
independent truth.

Each task will produce a hashed prelabel artifact. No target cohort will select
features, relations, cluster number, weights, or rejection thresholds.
Insufficient mapping produces an ineligible task or `UNASSIGNED`, not a new
target-optimised profile. Primary baselines are value PAM, relational PAM,
HYBRID PAM, and `RR_POSTHOC`; conventional cluster-then-classify procedures are
secondary comparators.

### WP4. Generalisation map and conditional efficiency (months 31-48)

WP4 will integrate controlled and real-cohort results into a domain-of-
applicability map. It will explicitly model negative cases: stable nuisance,
label-discordant structure, relation flips, low coverage, group collapse, and
poor assignment margins. Only after the WP2 gate passes will one restricted
single-anchor experiment test computational efficiency. Anchor sets are not in
the core scope. Release artifacts will include Python code, manifests, frozen
configurations, synthetic generators, and auditable result tables.

<!-- PAGE_BREAK -->

## 4. Methodology and evaluation

### Data boundary and reproducibility

Every dataset is represented by a `DatasetBundle` with measurements and sample
metadata separated from evaluation labels. Fit and audit packages cannot import
the label loader. Source preprocessing includes quality control, feature
mapping, transformation, robust scaling where required, and median absolute
deviation feature selection. The fitted artifact is serialised with ordered
feature identifiers, parameters, software versions, seeds, and hashes. Target
processing is a pure application of that artifact. A regression test will alter
all target values or labels and confirm byte-identical source artifacts.

All primary algorithms are deterministic, CPU-only, and Python-first. Average
ranks handle ties; ternary relations encode `-1`, `0`, and `+1`; missing values
remain explicit. Value Euclidean/correlation, rank footrule, pair-Hamming, and
hybrid distances are tested for symmetry, zero diagonal, boundedness where
applicable, tie behaviour, and deterministic byte output. A golden small-matrix
test verifies the global PAM optimum, and permutation tests verify canonical
tie-breaking.

### Representation Audit

For each candidate representation and source-only split, the audit estimates
partition stability, prediction strength, minimum cluster fraction,
non-degeneracy, and margin above a matched permuted/noise null. Hybrid weights
are a finite preregistered grid and are normalised from source distances only.
The audit returns a quality score with components retained separately so that a
high aggregate cannot conceal a degenerate group. Selection and cluster number
are frozen before evaluation labels are available.

### Direct regions and assignment

`RR_DIRECT` will optimise a transparent objective balancing within-region
relation agreement, between-region contrast, profile length, redundancy, and
coverage. Optimisation is deterministic and bounded by a declared candidate
relation budget. A new sample is compared with every frozen profile; assignment
requires sufficient observable relations and a source-calibrated margin over
the next profile. Otherwise it is `UNASSIGNED`. No target sample can change a
profile or the assignment of another target sample; individual-versus-batch
equivalence is a required test.

### Outcomes and analysis

Controlled outcomes are representation-family accuracy, target ARI/NMI,
regret versus a retrospective oracle, NULL false-structure rate, unjustified
HYBRID selection, and association between source audit differences and target
behaviour. Real-cohort outcomes are assignment coverage, `UNASSIGNED` rate,
minimum group size, relation coverage and flip rate, profile-state retention,
assignment margin, profile length, gene count, bootstrap Jaccard, and external
ARI/NMI where a suitable reference exists. Clinical and pathway associations
are evaluated only after freezing and are reported with effect sizes,
uncertainty intervals, and multiplicity control.

Uncertainty will be estimated by resampling independent patients; paired
specimens and technical replicates will remain grouped. Comparisons will report
all preregistered directions and datasets, not only favourable results. A
hierarchical summary across cohorts will supplement, not replace, per-cohort
results. Sensitivity analyses will cover cluster-number uncertainty,
feature-mapping rules, missing relations, and histological mismatch. No
post-label adjustment can change a primary result.

### Expected outputs

The expected scientific outputs are: a tested representation-adequacy and
abstention framework; a direct relational-region algorithm or a clearly
documented negative result; multi-cohort frozen-transfer evidence in two disease
contexts; and an empirical map defining when relational profiles are credible.
The software output will be an open, deterministic reference implementation,
not a clinical device or web portal.

<!-- PAGE_BREAK -->

## 5. Team, feasibility, risk, and impact

The new team separates method construction from independent validation. The PI
will define the mathematical and experimental architecture, supervise all WPs,
and integrate the resulting applicability theory. A doctoral researcher,
employed for at least the scheme-required 36 months, will develop `RR_DIRECT`,
its correctness tests, and stability analysis as a coherent dissertation. A
postdoctoral researcher or specialist analyst will lead cohort curation,
feature mapping, reproducibility review, and frozen validation. External
domain consultation will be named only after formal confirmation. Individual
names and achievements will be inserted from verified CV and institutional
records before submission.

Feasibility is supported by a completed deterministic pilot: a common PAM
engine, source-only preprocessing artifacts, label import firewall, four
distance families, controlled generators, real-data adapters, frozen transfer,
and an automated correctness, determinism, and leakage test suite. The full
controlled benchmark and all decisions have machine-readable evidence.
Crucially, the failed external gate was preserved rather than repaired, showing
that the proposed stopping rules are operational.

The main risks and responses are:

- **Stable nuisance resembles biology.** Technical perturbations, metadata
  diagnostics, matched nulls, and independent cohorts are used; stability alone
  never establishes meaning.
- **The audit ranks candidates but cannot choose reliably.** The output becomes
  an adequacy profile with abstention rather than a universal selector.
- **Direct regions do not beat post-hoc profiles.** The WP2 gate stops the new
  method and retains `RR_POSTHOC` as the supported result.
- **Cross-platform relation coverage is low.** The source-defined mapping and
  threshold are retained; low-coverage samples remain unassigned, and the
  failure defines an applicability boundary.
- **Profiles are stable but label-discordant.** Structural and phenotype
  validity are reported separately; labels cannot rescue training.
- **Quadratic relation space is expensive.** Source-only screening, redundancy
  control, and a fixed candidate budget bound CPU cost. A single-anchor
  restriction is tested only conditionally; anchor sets remain out of scope.
- **A result depends on one cohort or direction.** At least three cohorts per
  disease module and complete directional reporting reduce selection bias.

The project will contribute a disciplined answer to a practical but
under-specified question in omics clustering: which representation makes a
patient grouping defensible and portable? Its broader impact is methodological.
It treats representation,
abstention, interpretability, and transfer as linked objects and supplies an
audit trail that allows reviewers and future users to distinguish learned
evidence from evaluation labels. The project is basic research; it will not
claim clinical utility without separate prospective validation.

<!-- PAGE_BREAK -->

## 6. References

1. Kaufman L, Rousseeuw PJ. *Finding Groups in Data: An Introduction to Cluster
   Analysis*. Wiley; 1990. <https://doi.org/10.1002/9780470316801>
2. Ben-Hur A, Elisseeff A, Guyon I. A stability based method for discovering
   structure in clustered data. *Pacific Symposium on Biocomputing*.
   2002;7:6-17. <https://pubmed.ncbi.nlm.nih.gov/11928511/>
3. Tibshirani R, Walther G. Cluster validation by prediction strength. *Journal
   of Computational and Graphical Statistics*. 2005;14:511-528.
   <https://doi.org/10.1198/106186005X59243>
4. Hubert L, Arabie P. Comparing partitions. *Journal of Classification*.
   1985;2:193-218. <https://doi.org/10.1007/BF01908075>
5. Geman D, d'Avignon C, Naiman DQ, Winslow RL. Classifying gene expression
   profiles from pairwise mRNA comparisons. *Statistical Applications in
   Genetics and Molecular Biology*. 2004;3:Article 19.
   <https://doi.org/10.2202/1544-6115.1071>
6. Tan AC, Naiman DQ, Xu L, Winslow RL, Geman D. Simple decision rules for
   classifying human cancers from gene expression profiles. *Bioinformatics*.
   2005;21:3896-3904. <https://doi.org/10.1093/bioinformatics/bti631>
7. Irizarry RA et al. Exploration, normalization, and summaries of high density
   oligonucleotide array probe level data. *Biostatistics*. 2003;4:249-264.
   <https://doi.org/10.1093/biostatistics/4.2.249>
8. Johnson WE, Li C, Rabinovic A. Adjusting batch effects in microarray
   expression data using empirical Bayes methods. *Biostatistics*.
   2007;8:118-127. <https://doi.org/10.1093/biostatistics/kxj037>
9. Landi MT et al. Gene expression signature of cigarette smoking and its role
   in lung adenocarcinoma development and survival. *PLoS One*. 2008;3:e1651.
   <https://doi.org/10.1371/journal.pone.0001651>
10. Selamat SA et al. Genome-scale analysis of DNA methylation in lung
    adenocarcinoma and integration with mRNA expression. *Genome Research*.
    2012;22:1197-1211. <https://doi.org/10.1101/gr.132662.111>
11. Marisa L et al. Gene expression classification of colon cancer into
    molecular subtypes: characterization, validation, and prognostic value.
    *PLoS Medicine*. 2013;10:e1001453.
    <https://doi.org/10.1371/journal.pmed.1001453>
12. Guinney J et al. The consensus molecular subtypes of colorectal cancer.
    *Nature Medicine*. 2015;21:1350-1356.
    <https://doi.org/10.1038/nm.3967>
13. Kumar A, Rai P, Daume H. Co-regularized multi-view spectral clustering.
    *Advances in Neural Information Processing Systems*. 2011;24:1413-1421.
    <https://proceedings.neurips.cc/paper/2011/hash/31839b036f63806cba3f47b93af8ccb5-Abstract.html>
14. Bertsimas D, Orfanoudaki A, Wiberg H. Interpretable clustering: an
    optimization approach. *Machine Learning*. 2021;110:89-138.
    <https://doi.org/10.1007/s10994-020-05896-2>
15. Eriksson P et al. A comparison of rule-based and centroid single-sample
    multiclass predictors for transcriptomic classification. *Bioinformatics*.
    2022;38:1022-1029. <https://doi.org/10.1093/bioinformatics/btab763>
