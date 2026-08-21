# Representation Adequacy and Transportable Relational Profiles in Omics Clustering

**TRPP method family - detailed project description**
**SONATA BIS 16 | 48 months | primary panel ST6**  
**Scientific draft:** complete in scope and logic. Verified personnel,
institutional, budget, and publication-record data must be entered in OSF by the
applicant and host institution.

## 1. Scientific objective

### 1.1 Problem

Clustering is widely used to seek molecularly distinct patient groups, but its
first consequential choice is often hidden: the representation in which
similarity is calculated. A patient may be described by normalised measurement
values, within-sample ranks, binary or ternary ordering relations, or a mixture
of these views. Each representation encodes a different invariance. Value
geometry retains magnitude but can be sensitive to calibration and scale.
Rank-based geometry discards magnitude and is invariant to sample-wise strictly
monotone transformations, yet it can be unstable around ties. Pair relations
such as `gene A > gene B` are directly readable and potentially transferable,
but gene-specific shifts, missing features, and annotation changes can reverse
them. A hybrid can exploit complementary information but can also fit noise if
its weight is selected retrospectively.

Most workflows select one representation by convention and then optimise the
clustering algorithm. This conflates geometry, grouping, and interpretation.
Moreover, any clustering engine can produce a partition even when the data do
not contain a reproducible group structure. A stable discovery partition may
track a technical nuisance, and a partition that is stable within one cohort
may fail when assigned to new patients. These limitations are especially
important in omics studies, where dimensionality is high, cohorts are modest,
and platforms and populations differ.

The project asks one central question: under which source-observable conditions
should magnitude information be retained, replaced by within-sample relations,
combined with them, or judged insufficient for stable and transportable omics
clustering? A source-only Representation Audit first determines whether VALUE,
RELATIONAL, HYBRID, or `NO_STABLE_STRUCTURE` is supported. For eligible
relational cases, the project will develop **Transportable Relational Patient
Profiles (TRPP)** as sparse regions: short sets of within-patient rules that
define a group and can assign a new patient without reclustering the target
cohort. The entire artifact is frozen before target evaluation, and
insufficient evidence yields `UNASSIGNED`.

### 1.2 Main hypothesis

Measurable signal and shift properties determine whether transportable
grouping should retain values, use within-sample relations, combine both views,
or abstain; within the relational domain, biologically useful patient groups
can be represented by sparse frozen rule sets.

This is not a hypothesis that relations are universally superior. It predicts
distinct competence regimes and permits value geometry or abstention to be the
correct outcome.

<!-- PAGE_BREAK -->

### 1.3 Specific hypotheses and objectives

**H1 - representation adequacy.** Source-only stability, prediction strength,
non-degeneracy, matched-null evidence, and explicit invariance properties can
distinguish competence domains of VALUE, RELATIONAL, and HYBRID and detect
absence of stable structure. The corresponding objective is to build and
validate a representation-adequacy map, not merely a winner-take-all selector.

**H2 - direct relational regions.** Direct joint learning of assignments and
sparse relational profiles can provide equal or better external transfer than
relational PAM followed by post-hoc profile extraction while improving profile
stability, concision, or both. The objective is a deterministic algorithm with
core/optional relations, redundancy control, and a fully replayable trace.

**H3 - frozen transport.** A source-learned profile can retain non-trivial
coverage and external associations in independent cohorts without target
refitting, joint normalisation, or target-guided feature replacement. The
objective is to test this claim in two disease modules with at least three
cohorts each.

**H4 - applicability boundaries.** Signal type, noise, missing features,
platform mapping, and biological composition generate predictable conditions
in which relations help, remain neutral, or fail. The objective is a quantitative
map connecting controlled perturbations with observed multi-cohort failures.

The four objectives are:

1. establish a leakage-controlled Representation Audit with an explicit
   `NO_STABLE_STRUCTURE` outcome;
2. develop and gate direct sparse relational regions against a strong post-hoc
   baseline;
3. evaluate completely frozen profiles in independent lung and colorectal
   cancer cohorts;
4. release an empirical domain-of-applicability map and deterministic reference
   implementation.

### 1.4 What the project will not claim

The project is basic methodological research. It will not claim that unsupervised
groups are diagnoses, that stability proves biological validity, or that a
profile is clinically useful without prospective validation. Target labels
cannot train, select, or rescue a method. Fuzzy clustering, evolutionary
optimisation, deep learning, federated learning, CUDA, and a web portal are
outside scope. Anchor sets are outside the core scope; a single-anchor
restriction is only a conditional efficiency experiment after the direct-
region gate.

## 2. Significance and innovation

### 2.1 Scientific need

Cluster discovery is unusually vulnerable to researcher degrees of freedom.
Unlike supervised prediction, it offers no training outcome against which a
representation can be judged directly. Stability methods test persistence under
perturbation, prediction strength asks whether a partition learned on one split
can be reproduced on another, and external indices compare a frozen partition
with later labels. These address different questions. A coherent workflow must
keep them separate, expose the null case, and demonstrate which data were
available at every decision.

<!-- PAGE_BREAK -->

### 2.2 State of the art and conceptual gap

PAM is a natural common engine for comparing representations because it accepts
an arbitrary dissimilarity matrix and represents each group by an observed
medoid rather than a synthetic mean. However, PAM does not determine which
dissimilarity is scientifically appropriate and will return a partition under
null structure. Consensus and resampling stability methods quantify
reproducibility, but high stability can be driven by a technical or biological
nuisance unrelated to the phenotype later considered important. Prediction
strength formalises train-to-test reproducibility but does not create a sparse,
transportable group definition.

Within-sample ordering approaches offer attractive invariance and
interpretability. Top-scoring-pair and related classifiers demonstrated that a
small number of relative expression comparisons can support transparent
supervised decisions. Their objective and validation differ fundamentally from
unsupervised patient stratification: class labels select the pairs, while a
cluster profile must emerge without such labels. A post-hoc profile can explain
a given cluster, but explanation after clustering does not show that the rules
were sufficient to define or transfer the group.

Multi-view and multiple-kernel methods already combine representations, and
interpretable clustering already learns tree- or rule-based descriptions.
Consequently, neither view fusion nor rules alone constitute the proposed
novelty. A fitted hybrid can also benefit from target or label information if
weights are selected after evaluation. Batch correction addresses a related
but different problem. Methods such as ComBat can enable joint analysis when
batches are explicitly modelled; they are not appropriate for the project's
primary frozen-transfer claim if fitting them uses the target cohort
distribution. The project therefore compares cohort-wise preprocessing and
source-frozen mapping in the primary analysis, with pooled batch correction
only as a clearly separated secondary analysis that cannot support a frozen-
transfer claim.

### 2.3 Innovation

The innovation lies in the architecture and optimisation target:

- **Adequacy before grouping:** multiple geometries are audited under one
  deterministic clustering engine, with component diagnostics and a null-
  calibrated abstention option.
- **Direct rather than retrospective regions:** sparse relations participate in
  defining assignments, instead of being selected only to describe a completed
  partition.
- **Two forms of abstention:** an analysis may report
  `NO_STABLE_STRUCTURE`, and an individual target sample may be `UNASSIGNED`.
- **Frozen assignment:** each target sample is evaluated using an immutable
  source artifact, and its assignment cannot depend on other target samples.
- **Applicability as a scientific result:** failures caused by gene-specific
  shifts, missing mapping, nuisance, or mixture change are measured and
  synthesised rather than removed from the report.
- **Executable evidence boundary:** label access, artifact hashes, environment,
  decisions, and GO/STOP transitions are machine-checkable.

This combination converts a vague promise of robustness into falsifiable
claims about what is learned, where it applies, and when it must abstain.

<!-- PAGE_BREAK -->

## 3. Preliminary results and starting point

### 3.1 Implemented pilot infrastructure

The completed pilot is a Python-first, deterministic, CPU-only reference
pipeline. It includes a `DatasetBundle` separating measurements from labels; a
source-only preprocessing artifact; average ranks with explicit ties; ternary
pair encoding; value Euclidean/correlation, rank-footrule, pair-Hamming, and
hybrid distances; and one deterministic PAM implementation with golden tests.
The audit layer implements perturbation stability, prediction strength,
non-degeneracy checks, matched NULL calibration, finite-grid representation
selection, frozen target assignment, and immutable prelabel artifacts. Fit and
audit modules cannot import the label loader. Correctness, determinism, and
leakage barriers were tested before larger stages proceeded.

### 3.2 Controlled benchmark

The primary simulation grid contained 630 independently evaluated source-target
pairs across VALUE, RELATIONAL, HYBRID, and NULL regimes, multiple signal
strengths, and domain shifts. The audit identified the generating
representation family in 0.933 of signal replicates. Median target ARI regret
relative to the retrospectively best candidate was 0.000. The false-structure
rate under NULL was 0.067, and HYBRID was selected in 0.000 of pure VALUE or
RELATIONAL regimes. Differences in source-only audit quality were associated
with corresponding differences in target behaviour (Spearman rho = 0.854).
Every preregistered Gate B criterion passed without changing its threshold.
Gate B: GO.

### 3.3 Real-data audits

Eleven heterogeneous expression datasets were then audited within dataset. The
complete decision and assignments for every dataset were written to immutable,
hashed prelabel artifacts before labels were loaded. RELATIONAL was selected in
eight datasets, VALUE in two, and HYBRID in one. The selected method lay within
0.05 ARI of the retrospective within-dataset oracle in 9/11 datasets, with
median regret 0.011. Yet median ARI against available labels was only 0.065.
This is descriptive evidence, not external validation. It demonstrates that
finding a candidate geometry close to the best available geometry and finding a
partition that matches a particular phenotype are empirically distinct tasks.

### 3.4 Frozen external transfer and its consequence

Bidirectional transfer was evaluated between independent lung-expression
cohorts GSE10072 and GSE19804. Each direction selected 200 source features from
a predeclared common universe. Source preprocessing, candidate relations,
distance scales, representation, medoids, and rejection thresholds were frozen
before target labels were evaluated; target samples were assigned without
refitting or joint normalisation.

GSE19804 to GSE10072 selected pair-Hamming and achieved target ARI 0.926,
matching the retrospective oracle with regret 0.000. GSE10072 to GSE19804
selected value-correlation and achieved ARI 0.559 versus oracle 0.664, a regret
of 0.105284. The frozen reverse-direction allowance was 0.10. Gate C: STOP. No
threshold, feature, relation margin, weight, or selector was changed. PILOT-016
to PILOT-018 were not run; direct regions: NOT TESTED; anchors: NOT TESTED. The
labels were used only after all source-only decisions and assignments had been
frozen.

The failed gate prevents an inflated preliminary claim and strengthens the
project logic. It shows that controlled adequacy is promising but insufficient,
and identifies transfer asymmetry as an object requiring multiple cohorts,
explicit coverage, and direct profile learning.

<!-- PAGE_BREAK -->

## 4. Research plan

### WP1 - Representation adequacy, invariance and clustering abstention (months 1-12)

WP1 will formalise an operational invariance and information-loss taxonomy for
the finite VALUE, rank, ternary-relation, and HYBRID family, and will extend
controlled regimes. It will state which transformations preserve each view and
which remove or reverse information, then test those predictions. Generators
will separate value-magnitude signal, stable relative-order signal,
complementary hybrid signal, and no structure. Orthogonal perturbations will
include global and feature-specific shifts, monotone sample transformations,
variance changes, dropout and missing features, unbalanced groups, nuisance
factors, mapping errors, and source-target mixture changes. Unknown numbers of
groups will be included after the fixed-K correctness layer is locked.

Every primary matched comparison uses the same deterministic PAM. Candidate
cluster numbers and hybrid weights are finite and preregistered. For each
candidate, the source-only audit records perturbation stability, prediction
strength, minimum group fraction, empty/duplicate-medoid conditions, assignment
margin, and excess over a matched permuted or simulated NULL. A candidate is
eligible only if all hard constraints pass; an aggregate quality score ranks
eligible candidates. If none qualifies, the output is
`NO_STABLE_STRUCTURE`.

**Milestones:** M1, expanded deterministic generators and unit tests (month 4);
M2, frozen audit definition and null calibration (month 8); M3, preregistered
controlled benchmark and applicability summary (month 12).

**Gate G1:** predefined minimum family discrimination, maximum NULL false-
structure rate, maximum unjustified HYBRID rate, low target regret, and positive
source/target association must be met on held-out controlled regimes. If the
winner-take-all choice is not supported but diagnostics remain informative, the
scientific output becomes an adequacy vector plus abstention. Target evidence
cannot recalibrate the primary gate.

### WP2 - Direct sparse relational regions (months 7-24)

WP2 starts with an explicit `RR_POSTHOC` baseline: relational PAM creates a
partition, after which relations that are frequent within and contrasting
between groups are selected. This baseline isolates the benefit of direct
learning from the benefit of using relations at all.

`RR_DIRECT` will jointly update assignments and sparse profiles. A profile
contains relation identifiers, expected ternary states, source frequencies,
weights, core/optional status, missingness allowances, and a calibrated
assignment threshold. The objective balances within-profile agreement,
between-profile separation, coverage, number of relations, number of distinct
genes, and redundancy. Inverse duplicates are forbidden. Limits on reuse of one
gene prevent superficially short profiles dominated by one measurement.
Candidate profile lengths 10, 25, and 50 provide interpretable operating points.

Initialisation, candidate ordering, tie-breaking, empty-group repair, and
stopping are deterministic. Every iteration writes an audit trace. Samples may
remain temporarily or finally unassigned if no profile has adequate observable
support and margin.

<!-- PAGE_BREAK -->

### WP2 validation and gate

Correctness tests will cover ternary ties, missing relations, inverse relation
removal, objective monotonicity where required, deterministic ties, empty
groups, and equality between repeated runs. Synthetic recovery experiments will
measure known region recovery in addition to partition agreement. Bootstrap
analysis will match relations by canonical identifiers and report Jaccard,
frequency, state consistency, and gene-level stability.

`RR_DIRECT` is compared with `RR_POSTHOC` under identical source features,
relation budgets, cluster numbers, and transfer tasks. **Gate G2** passes if
direct learning improves external ARI/NMI by at least 0.05, improves bootstrap
profile Jaccard by at least 0.10, or remains within 0.03 of the baseline while
producing a materially shorter profile. The exact definition of materially
shorter will be frozen from source-side simulations before real target labels
are opened. If no criterion passes, direct development stops; the negative
result and post-hoc baseline remain deliverables.

**Milestones:** M4, tested post-hoc baseline (month 12); M5, traceable direct
prototype (month 18); M6, controlled and source-resampling evaluation (month
21); M7, G2 decision (month 24).

### WP3 - Frozen multi-cohort TRPP transfer (months 18-38)

WP3 uses two modules chosen to expose complementary transfer problems.

**Lung adenocarcinoma.** GSE10072 is the default discovery cohort: 107 final
GPL96 profiles, including 58 tumours and 49 non-tumour tissues. GSE19804
provides 120 GPL570 profiles from 60 paired cancers and adjacent normal tissues
in non-smoking women from Taiwan. GSE32863 provides 116 GPL6884 Illumina
profiles from 58 matched lung adenocarcinomas and adjacent non-tumour tissues.
GSE18842 is a declared sensitivity cohort because it includes broader NSCLC
histology. The primary question is not whether tumour/normal can be classified,
but whether the source-supported geometry and concise profile remain applicable
under etiological, population, and platform shifts.

**Colorectal cancer.** Tumour samples from GSE39582 form the default discovery
cohort. GEO records 585 GPL570 profiles, including 443 discovery tumours, 123
internal validation tumours, and 19 non-tumour mucosa samples. Independent
targets are GSE14333, with 290 primary colorectal tumours, and GSE33113, with 90
stage-II tumours plus six matched normal samples. The primary tumour analysis
does not use normal samples to create an easy contrast. Published CMS labels,
stage, molecular markers, recurrence, and survival are loaded only for final
evaluation. Because CMS is expression-derived, it is an external reference,
not a label-independent biological truth.

GSE39582's internal split is not counted as an independent study. Every cohort
must pass a sample-level metadata, duplicate, assay, scale, and annotation audit
before the multi-cohort protocol is preregistered.

<!-- PAGE_BREAK -->

### WP3 frozen-transfer protocol

For each module, a discovery analysis fits all preprocessing and modelling
objects on the source cohort. It records sample exclusions, source feature
selection, identifier mapping, probe-to-gene aggregation, candidate relations,
distance normalisation, audit decision, cluster number, medoids or regions,
profile weights, coverage requirements, assignment margins, and rejection
thresholds. The artifact contains ordered identifiers, code revision,
environment, seeds, and cryptographic hashes.

Target cohorts are processed separately. No joint source-target normalisation,
target distribution fitting, target-label feature selection, or target-guided
replacement of missing relations is allowed in the primary analysis. Platform
mapping follows the frozen annotation rule. If coverage is below the declared
threshold, the sample is `UNASSIGNED`; if the task cannot support the profile,
the task is reported ineligible. Assigning one sample alone and within a target
batch must give the same result.

Primary baselines are VALUE PAM, rank-footrule PAM, pair-Hamming PAM, finite-
grid HYBRID PAM, and `RR_POSTHOC`, all using the same source split and
preprocessing boundary. `RR_DIRECT` enters only after G2. A conventional
cluster-then-classify pipeline and pooled harmonisation may be secondary
comparators, clearly labelled as answering different questions. They cannot be
used to validate frozen transfer.

All declared source-to-target directions are reported. Reverse directions are
secondary and preregistered only where sample composition makes them
scientifically interpretable. A poor direction is not averaged away. Dataset
exclusions made after label inspection are prohibited.

**Milestones:** M8, final metadata/mapping audit and preregistration (month 22);
M9, lung prelabel artifacts (month 28); M10, colorectal prelabel artifacts
(month 32); M11, locked evaluation and cross-module synthesis (month 38).

### WP4 - Applicability map, conditional efficiency, and release (months 31-48)

WP4 will link controlled perturbations with observed cohort characteristics.
The map will describe risk as a function of source stability, NULL margin,
feature/relation coverage, relation flip rate, assignment margin, group balance,
platform mapping, and metadata shift. It will distinguish four conclusions:
supported relational transfer, supported value transfer, complementary hybrid
transfer, and insufficient evidence.

Only if G2 passes, a single-anchor restriction may test whether relations
`anchor > feature` reduce computation while retaining performance. It must
achieve at least a fivefold cost reduction, ARI loss no greater than 0.03, and
no material coverage or stability loss. Anchor sets and evolutionary searches
remain excluded.

**Milestones:** M12, applicability model (month 42); M13, conditional efficiency
decision (month 44); M14, reference software, manifests, benchmark, and final
synthesis (month 48).

<!-- PAGE_BREAK -->

## 5. Methods

### 5.1 Data objects and leakage firewall

Each cohort is imported into a `DatasetBundle` containing the measurement
matrix, feature identifiers, sample identifiers, and non-outcome technical
metadata. Evaluation labels are stored in a separate file and exposed through a
dedicated evaluation package. Fit and audit packages are tested to ensure they
cannot import the label loader. Depending on the preregistered question,
clinically descriptive variables that could reveal outcomes are also kept on
the evaluation side.

Source preprocessing produces an immutable artifact. For arrays, the project
will prefer raw-data cohort-wise preprocessing when raw files and annotation
permit it; otherwise it will document the deposited processed scale and perform
predeclared quality checks. Probe filtering and probe-to-gene rules are fitted
or fixed on source. Robust scaling for VALUE uses source location and scale.
Feature selection uses source-only dispersion, normally median absolute
deviation, with stable identifier tie-breaking. Target values never update
these parameters.

### 5.2 Representations and distances

For a sample vector with possible ties, ranks use the average-rank convention.
A pair relation for features j and k is `+1` if x_j exceeds x_k, `-1` if it is
lower, and `0` for an observed tie. Missingness is a separate mask and cannot be
silently encoded as zero. Candidate relations are screened from source by
predeclared prevalence, contrast, and redundancy rules without labels.

VALUE uses source-scaled Euclidean distance and correlation distance where
defined. RELATIONAL uses normalised Spearman-footrule distance between average
ranks and Hamming-type disagreement among observed ternary relations. HYBRID is
a convex combination after each component is scaled by a source-only distance
functional. Candidate weights form a finite frozen grid. Each distance is
tested for symmetry, diagonal zero, bounds where applicable, missingness
handling, and deterministic serialisation.

### 5.3 Deterministic PAM

All matched representations use the same PAM implementation. BUILD and SWAP
steps have canonical sample-identifier tie-breaking, explicit duplicate and
non-finite distance rejection, deterministic empty-group protection, and a
recorded objective trace. Golden tests enumerate all medoid combinations on
small matrices and confirm the global optimum. Repeated-process and permuted-
input tests verify stable canonical output. This design ensures that a
representation comparison is not an accidental comparison of clustering
engines.

### 5.4 Source-only audit

Perturbations are generated from source without labels and include patient
subsampling, feature subsampling, bounded measurement noise, and relation
dropout. Stability is measured after matching partitions with ARI and pairwise
co-membership summaries. Prediction strength estimates reproducibility from
source train to source validation splits. Hard eligibility checks include
minimum group fraction, absence of duplicate medoids, finite distances, and
excess over a matched NULL threshold. All component values are retained. The
quality score and selection rule are frozen before external evaluation.

<!-- PAGE_BREAK -->

### 5.5 Relational-region model

Let a profile r contain a subset of relations S_r, expected states s_r, weights
w_r, core indicators c_r, and source-derived missingness allowances. For sample
x, its observable agreement with r is the weighted agreement over relations
present in x, penalised when core coverage is insufficient. Assignment uses the
best score only when total coverage, core coverage, absolute score, and margin
over the second-best profile exceed frozen thresholds. Otherwise x is
`UNASSIGNED`.

`RR_POSTHOC` selects S_r after PAM from within-group prevalence and between-
group contrast. `RR_DIRECT` optimises assignments and S_r jointly through
deterministic coordinate updates. Candidate additions and deletions are ordered
canonically; ties are resolved by ordered relation identifiers. The objective
includes compactness, contrast, coverage, profile length, inverse redundancy,
and gene reuse. The algorithm stops when no admissible update improves the
objective beyond a fixed tolerance or a fixed iteration limit is reached. The
trace makes every change replayable.

### 5.6 Evaluation outcomes

For controlled data, primary outcomes are exact representation-family
identification, target ARI and NMI, target ARI regret versus the retrospective
oracle, NULL false-structure rate, HYBRID selection in pure regimes, and
Spearman association between source audit differences and target-performance
differences. Known generative regions add relation precision/recall and state
recovery.

For real cohorts, the project reports:

- eligibility, assignment coverage, `UNASSIGNED` fraction, and minimum group
  size;
- profile length, number of genes, observable relation fraction, core coverage,
  relation flip rate, and assignment margins;
- bootstrap relation Jaccard and state stability;
- frozen ARI/NMI against declared external references where appropriate;
- clinicopathological, molecular, pathway, recurrence, and survival associations
  as evaluation-only outcomes;
- performance and uncertainty for every preregistered cohort and direction.

ARI/NMI quantify agreement, not biological truth. Survival analyses will use
predeclared endpoints and proportional-hazards diagnostics; effect sizes and
confidence intervals will accompany p-values. Molecular and pathway tests will
use multiplicity control. Paired specimens, repeat measures, and technical
replicates are resampled at patient level. Cohort-level estimates will be shown
individually before any hierarchical or meta-analytic summary.

### 5.7 Robustness and negative controls

Negative controls include permuted samples/features, matched NULL generators,
label permutation confined to evaluation, synthetic nuisance structure, and
profiles applied after deliberate feature removal. Sensitivity analyses vary
only factors declared before target-label access: source feature budget,
relation budget, profile size, cluster number range, and mapping rule. Primary
results remain tied to the preregistered configuration.

<!-- PAGE_BREAK -->

## 6. Data modules and validity threats

### 6.1 Lung module

GSE10072, GSE19804, and GSE32863 contain lung tumour and adjacent/non-tumour
expression profiles but differ in platform, population, smoking context, and
sample pairing. This makes them informative for transport and dangerous for
causal interpretation. Cohort identity is a composite shift; success cannot be
attributed to a single technical or biological factor. The core analysis uses
histologically aligned lung adenocarcinoma where metadata permit. GSE18842 is a
broader-NSCLC sensitivity analysis because mixing squamous and adenocarcinoma
could create an easy histology partition.

The tumour/non-tumour signal is intentionally treated as a stress-test scaffold
rather than the ultimate biological discovery. After the representation and
transfer machinery is verified, tumour-only exploratory profiles may be
evaluated under a separately preregistered question if sample size and metadata
support it. They cannot replace a failed primary task.

### 6.2 Colorectal module

GSE39582 offers a large discovery series with molecular and clinical annotation.
GSE14333 and GSE33113 offer independent patient series but differ in stage
composition and original processing. The analysis therefore focuses on
coverage and retention of frozen tumour profiles rather than forcing identical
source group proportions. Normal tissue is excluded from the primary tumour-
subtype task. The internal GSE39582 validation subset is valuable for source
development but is not counted as an independent cohort.

CMS provides a biologically interpretable consensus reference, yet it is built
from gene expression. Agreement with CMS may therefore reflect shared signal
rather than independent truth. Stage, MSI/MMR, mutations, location, treatment,
recurrence, and survival provide complementary evaluation where complete. None
can select the representation or profile.

### 6.3 Threats to validity and mitigation

**Leakage:** joint scaling, feature selection, batch correction, or threshold
selection would invalidate frozen transfer. Mitigation is a physical label
firewall, immutable artifacts, import tests, and target-mutation invariance
tests.

**Annotation instability:** probe-to-gene changes may alter orderings.
Mitigation is a versioned mapping, source-fixed aggregation, coverage reporting,
and a sensitivity analysis across independently declared annotation versions.

**Confounding:** cohort, platform, population, histology, and treatment may be
inseparable. Mitigation is per-cohort reporting, declared sensitivity cohorts,
controlled perturbations, and restrained causal language.

**Selective reporting:** a method can appear transferable if only favourable
directions are retained. Mitigation is preregistration, complete task manifests,
and publication of ineligible and failed tasks.

**Circular biological evaluation:** expression-derived subtype labels share
information with expression clusters. Mitigation is explicit classification of
CMS as a reference, separate clinical endpoints, and no label-guided learning.

<!-- PAGE_BREAK -->

## 7. Project governance, reproducibility, and data management

### 7.1 Decision governance

Every WP has a frozen analysis specification and an explicit transition.
Threshold changes are allowed only before the relevant target evaluation and
must create a new version; they cannot rewrite a completed primary result. Gate
failure changes downstream scope exactly as declared. The decision log records
who approved a change, which evidence was available, and which artifacts became
obsolete. Negative results are retained.

### 7.2 Software and computational reproducibility

The reference implementation is Python-first and CPU-only. Dependencies are
pinned, environments are recorded, and pseudorandom components use explicit
seeds and deterministic ordering. Canonical JSON serialisation supports byte-
level comparison of model artifacts. Continuous tests cover numerical
correctness, determinism across processes, label import boundaries, target
mutation invariance, individual/batch assignment equivalence, and schema
validation. Larger benchmark stages start only after their acceptance suite
passes.

Public releases will contain source code, synthetic generators, configuration
schemas, dataset accession manifests, annotation hashes, tests, and aggregated
results. Raw public repositories will be referenced rather than redistributed
when their terms or size make redistribution inappropriate. Derived artifacts
will avoid direct identifiers. Each release will include environment and
provenance metadata.

### 7.3 Data management and ethics

The default datasets are public, de-identified omics cohorts. Before use, the
team will review repository terms, consent restrictions, controlled-access
requirements, and the host institution's ethics guidance. Only data necessary
for the declared research questions will be processed. Local working copies
will be access-controlled and integrity-checked. Public outputs will contain
code, non-identifying manifests, model profiles, and aggregate results unless
the original terms impose stricter limits.

The method is not a medical device and will not produce treatment advice.
Profiles will be presented as research hypotheses. Any later prospective or
clinical study would require separate ethical, regulatory, and clinical
validation. The final OSF data-management and ethics forms will be completed
with the host institution using the verified storage, retention, backup, and
responsibility arrangements.

### 7.4 Open science

The project will preregister primary simulations, cohort roles, gates, and
evaluation order. Manuscripts will distinguish confirmatory from exploratory
analyses. Code and reproducible artifacts will be released at stable revisions,
with licences compatible with source datasets and dependencies. Results will
include failures and applicability limits, reducing incentives to report only
successful transfers.

## 8. Team and feasibility

The PI will lead scientific design, relational-learning methodology, gate
decisions, supervision, and synthesis. A doctoral researcher employed for at
least 36 months will develop `RR_DIRECT`, tests, and stability theory as a
coherent dissertation project. A competitively recruited postdoctoral
researcher or specialist analyst will independently curate cohorts, harmonise
metadata, verify frozen artifacts, and lead replication. Confirmed external
consultants may advise on biological interpretation but will not own the core
method or replace independent validation.

<!-- PAGE_BREAK -->

### 8.1 Why a new team is necessary

The work combines three substantial and deliberately separated responsibilities:
algorithm development, multi-cohort bioinformatics, and independent
reproducibility review. A single investigator performing all three would create
a bottleneck and increase confirmation bias. The doctoral project gives depth
to direct-region methodology; the postdoctoral/specialist role ensures that
cohort curation and target evaluation are not informal extensions of method
development. The PI integrates the work and is accountable for all frozen
decisions.

The named-team section will be completed only after eligibility, employment,
prior joint-project restrictions, and institutional rules are checked. No
person's achievements or commitment are inferred in this scientific draft.

### 8.2 Feasibility

The pilot provides operational infrastructure rather than a mock-up. It already
implements the data boundary, source artifacts, representations, distances,
deterministic PAM, controlled grids, real-data adapters, frozen assignment,
evidence validation, automated reports, and tests of correctness, determinism,
and leakage. The complete 630-pair benchmark was executed. The formal STOP at
Gate C shows that stopping logic works in practice. The project begins from
tested Level-1 to Level-3 components while keeping direct regions as genuine
research.

Public cohorts make the 48-month plan realistic without depending on new sample
recruitment. The main resource requirement is staff time and deterministic CPU
compute. Relation screening and explicit candidate budgets bound the quadratic
feature-pair space. Intermediate artifacts permit restart and audit. The two
disease modules offer replication without turning the project into a broad
disease survey.

## 9. Risk register and fallback results

1. **No representation reliably clears the NULL boundary.** Report the
   conditions and retain abstention as the result; do not lower thresholds using
   target labels.
2. **Source diagnostics predict only a ranking, not an exact winner.** Publish
   an adequacy vector and uncertainty rather than a universal selector.
3. **Direct regions do not improve on post-hoc profiles.** Stop `RR_DIRECT` at
   G2; release the negative comparison and use `RR_POSTHOC` downstream.
4. **Cross-platform coverage is inadequate.** Report ineligibility or
   `UNASSIGNED`; analyse mapping sensitivity without replacing relations based
   on target outcomes.
5. **Stable profiles lack clinical association.** Separate structural from
   phenotype validity; the negative association is scientifically meaningful.
6. **Profiles track technical or cellular-composition nuisance.** Use metadata
   diagnostics, controlled nuisance regimes, pathway/cell-content assessment,
   and cross-cohort behaviour; avoid causal claims.
7. **Computation is excessive.** Reduce the source candidate budget by a
   preregistered unsupervised rule. Test a single-anchor restriction only after
   G2; do not introduce evolutionary or GPU methods.
8. **One disease module becomes unusable because metadata or terms change.** A
   reserve cohort may replace it only after a documented prelabel audit and
   before any target-label comparison; the original exclusion remains public.

<!-- PAGE_BREAK -->

## 10. Schedule, deliverables, and success criteria

### 10.1 Timeline

- **Months 1-6:** recruit team; lock data governance; extend generators and
  correctness suite; perform accession-to-sample metadata audit.
- **Months 7-12:** freeze and run WP1 benchmark; calibrate abstention; decide
  G1; implement `RR_POSTHOC`.
- **Months 13-18:** implement direct optimisation, trace, missingness, and
  core/optional profiles; run synthetic recovery and determinism tests.
- **Months 19-24:** compare direct and post-hoc profiles; freeze and decide G2;
  preregister accepted cohort mappings and WP3 tasks.
- **Months 25-32:** generate lung and colorectal prelabel artifacts; perform
  independent integrity review before labels are loaded.
- **Months 33-38:** execute locked evaluation, sensitivity analyses, and
  complete per-cohort reporting.
- **Months 39-44:** estimate applicability map; run the conditional single-
  anchor experiment only if authorised by G2.
- **Months 45-48:** integrate theory and empirical results; archive the
  reproducible benchmark and reference implementation.

### 10.2 Deliverables

- D1: versioned Representation Audit specification, generators, and NULL
  calibration;
- D2: controlled competence map with G1 record;
- D3: tested `RR_POSTHOC` baseline;
- D4: `RR_DIRECT` implementation and G2 comparison, including a negative result
  if applicable;
- D5: lung module prelabel and evaluation artifacts;
- D6: colorectal module prelabel and evaluation artifacts;
- D7: cross-module applicability map and conditional efficiency decision;
- D8: open Python reference package, documentation, tests, manifests, and final
  synthesis.

### 10.3 Criteria for success

Project success is not defined as relational victory on every dataset. It
requires: correct and deterministic implementations; demonstrated absence of
target/label leakage; calibrated false-structure control; honest operation of
G1/G2; at least two fully audited multi-cohort modules unless a documented data
eligibility failure intervenes; complete reporting of coverage and negative
directions; and a usable map distinguishing supported transfer from abstention.

The strongest positive result would be a concise direct profile that retains
assignments and external associations across independent platforms. A valid
negative result would show that post-hoc profiles, value geometry, or abstention
is preferable under identifiable conditions. Both advance the central goal:
making omics clustering more interpretable, falsifiable, and transport-aware.

## 11. Expected scientific impact

The project will shift emphasis from producing a partition to justifying a
frozen patient representation. It will provide researchers with evidence about when a
within-sample relational description is credible, when magnitude information
must be retained, and when data do not support grouping. Direct regions will
connect unsupervised discovery with an interpretable rule-based assignment
mechanism, while the applicability map will prevent invariance claims from
being generalised beyond observed conditions.

The project also contributes a reproducibility pattern applicable beyond omics:
physical label separation, prelabel artifacts, common engines for representation
comparisons, explicit null outcomes, and irreversible evaluation gates. The
result will be an open research method and evidence base, not a portal or
clinical product.

<!-- PAGE_BREAK -->

## 12. References

1. Kaufman L, Rousseeuw PJ. *Finding Groups in Data: An Introduction to Cluster
   Analysis*. Wiley; 1990. <https://doi.org/10.1002/9780470316801>
2. Ben-Hur A, Elisseeff A, Guyon I. A stability based method for discovering
   structure in clustered data. *Pacific Symposium on Biocomputing*.
   2002;7:6-17. <https://pubmed.ncbi.nlm.nih.gov/11928511/>
3. Tibshirani R, Walther G. Cluster validation by prediction strength. *Journal
   of Computational and Graphical Statistics*. 2005;14:511-528.
   <https://doi.org/10.1198/106186005X59243>
4. Lange T, Roth V, Braun ML, Buhmann JM. Stability-based validation of
   clustering solutions. *Neural Computation*. 2004;16:1299-1323.
   <https://doi.org/10.1162/089976604773717621>
5. Hubert L, Arabie P. Comparing partitions. *Journal of Classification*.
   1985;2:193-218. <https://doi.org/10.1007/BF01908075>
6. von Luxburg U. Clustering stability: an overview. *Foundations and Trends in
   Machine Learning*. 2010;2:235-274. <https://doi.org/10.1561/2200000008>
7. Geman D, d'Avignon C, Naiman DQ, Winslow RL. Classifying gene expression
   profiles from pairwise mRNA comparisons. *Statistical Applications in
   Genetics and Molecular Biology*. 2004;3:Article 19.
   <https://doi.org/10.2202/1544-6115.1071>
8. Tan AC, Naiman DQ, Xu L, Winslow RL, Geman D. Simple decision rules for
   classifying human cancers from gene expression profiles. *Bioinformatics*.
   2005;21:3896-3904. <https://doi.org/10.1093/bioinformatics/bti631>
9. Eddy JA, Sung J, Geman D, Price ND. Relative expression analysis for
   molecular cancer diagnosis and prognosis. *Technology in Cancer Research
   and Treatment*. 2010;9:149-159.
   <https://doi.org/10.1177/153303461000900204>
10. Irizarry RA et al. Exploration, normalization, and summaries of high density
    oligonucleotide array probe level data. *Biostatistics*. 2003;4:249-264.
    <https://doi.org/10.1093/biostatistics/4.2.249>
11. Johnson WE, Li C, Rabinovic A. Adjusting batch effects in microarray
    expression data using empirical Bayes methods. *Biostatistics*.
    2007;8:118-127. <https://doi.org/10.1093/biostatistics/kxj037>
12. McCall MN, Bolstad BM, Irizarry RA. Frozen robust multiarray analysis
    (fRMA). *Biostatistics*. 2010;11:242-253.
    <https://doi.org/10.1093/biostatistics/kxp059>
13. Landi MT et al. Gene expression signature of cigarette smoking and its role
    in lung adenocarcinoma development and survival. *PLoS One*. 2008;3:e1651.
    <https://doi.org/10.1371/journal.pone.0001651>
14. Lu TP et al. Identification of a novel biomarker, SEMA5A, for non-small cell
    lung carcinoma in nonsmoking women. *Cancer Epidemiology Biomarkers and
    Prevention*. 2010;19:2590-2597.
    <https://doi.org/10.1158/1055-9965.EPI-10-0332>
15. Selamat SA et al. Genome-scale analysis of DNA methylation in lung
    adenocarcinoma and integration with mRNA expression. *Genome Research*.
    2012;22:1197-1211. <https://doi.org/10.1101/gr.132662.111>

<!-- PAGE_BREAK -->

16. Sanchez-Palencia A et al. Gene expression profiling reveals novel
    biomarkers in nonsmall cell lung cancer. *International Journal of Cancer*.
    2011;129:355-364. <https://doi.org/10.1002/ijc.25704>
17. Marisa L et al. Gene expression classification of colon cancer into
    molecular subtypes: characterization, validation, and prognostic value.
    *PLoS Medicine*. 2013;10:e1001453.
    <https://doi.org/10.1371/journal.pmed.1001453>
18. Jorissen RN et al. Metastasis-associated gene expression changes predict
    poor outcomes in patients with Dukes stage B and C colorectal cancer.
    *Clinical Cancer Research*. 2009;15:7642-7651.
    <https://doi.org/10.1158/1078-0432.CCR-09-1431>
19. de Sousa E Melo F et al. Poor-prognosis colon cancer is defined by a
    molecularly distinct subtype and develops from serrated precursor lesions.
    *Nature Medicine*. 2013;19:614-618. <https://doi.org/10.1038/nm.3174>
20. Guinney J et al. The consensus molecular subtypes of colorectal cancer.
    *Nature Medicine*. 2015;21:1350-1356.
    <https://doi.org/10.1038/nm.3967>
21. Marusyk A, Almendro V, Polyak K. Intra-tumour heterogeneity: a looking glass
    for cancer? *Nature Reviews Cancer*. 2012;12:323-334.
    <https://doi.org/10.1038/nrc3261>
22. McShane LM et al. REporting recommendations for tumour MARKer prognostic
    studies (REMARK). *British Journal of Cancer*. 2005;93:387-391.
    <https://doi.org/10.1038/sj.bjc.6602678>
23. Boulesteix AL, Lauer S, Eugster MJA. A plea for neutral comparison studies
    in computational sciences. *PLoS One*. 2013;8:e61562.
    <https://doi.org/10.1371/journal.pone.0061562>
24. Ioannidis JPA et al. Repeatability of published microarray gene expression
    analyses. *Nature Genetics*. 2009;41:149-155.
    <https://doi.org/10.1038/ng.295>
25. Kumar A, Rai P, Daume H. Co-regularized multi-view spectral clustering.
    *Advances in Neural Information Processing Systems*. 2011;24:1413-1421.
    <https://proceedings.neurips.cc/paper/2011/hash/31839b036f63806cba3f47b93af8ccb5-Abstract.html>
26. Bertsimas D, Orfanoudaki A, Wiberg H. Interpretable clustering: an
    optimization approach. *Machine Learning*. 2021;110:89-138.
    <https://doi.org/10.1007/s10994-020-05896-2>
27. Carrizosa E, Kurishchenko K, Marin A, Romero Morales D. On clustering and
    interpreting with rules by means of mathematical optimization. *Computers
    and Operations Research*. 2023;154:106180.
    <https://doi.org/10.1016/j.cor.2023.106180>
28. Eriksson P et al. A comparison of rule-based and centroid single-sample
    multiclass predictors for transcriptomic classification. *Bioinformatics*.
    2022;38:1022-1029. <https://doi.org/10.1093/bioinformatics/btab763>
29. Guan Q et al. Differential expression analysis for individual cancer
    samples based on robust within-sample relative gene expression orderings
    across multiple profiling platforms. *Oncotarget*. 2016;7:68909-68920.
    <https://doi.org/10.18632/oncotarget.11996>
