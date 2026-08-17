# SONATA BIS 16 - default multi-cohort dataset audit

Status: proposal-stage audit; accession-level metadata verified in NCBI GEO on
2026-08-17. Final inclusion still requires a sample-level metadata and feature
mapping audit before preregistration.

## Decision

The default project uses two complementary disease modules:

1. lung adenocarcinoma, initially focused on the strong tumour-versus-adjacent
   lung signal and deliberately including a cross-platform target;
2. colorectal cancer, focused on heterogeneous tumour profiles, molecular
   subtype retention, and clinical associations across independent cohorts.

The two modules test different failure modes. The lung module provides matched
tumour/normal samples and a known platform shift. The colorectal module tests
whether sparse profiles learned in a large heterogeneous tumour cohort remain
recognisable in cohorts with different stage composition and clinical follow-up.
Neither module permits target data to determine the source feature set, number
of groups, relation set, weights, rejection threshold, or preferred method.

## Module L - lung adenocarcinoma

### L1 discovery: GSE10072

- NCBI GEO: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE10072>
- organism and assay: Homo sapiens; expression profiling by array;
- platform: GPL96, Affymetrix Human Genome U133A;
- usable series described by GEO: 107 final expression profiles, comprising 58
  lung adenocarcinoma tumours and 49 non-tumour tissues after averaging technical
  duplicates and quality exclusions;
- strengths: detailed smoking context, tumour/non-tumour contrast, already used
  as one side of the frozen pilot transfer;
- risks: unequal class sizes, partial pairing, smoking heterogeneity, and a
  smaller probe universe than GPL570.

### L2 target 1: GSE19804

- NCBI GEO: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE19804>
- organism and assay: Homo sapiens; expression profiling by array;
- platform: GPL570, Affymetrix Human Genome U133 Plus 2.0;
- samples: 120 profiles, 60 paired lung cancers and adjacent normal tissues;
- context: non-smoking female lung cancer in Taiwan;
- strengths: balanced pairing and a demographic/etiological shift relative to
  GSE10072;
- risks: population and sex are inseparable from cohort/platform, so transfer
  success cannot be attributed to a single factor.

### L3 target 2: GSE32863

- NCBI GEO: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE32863>
- organism and assay: Homo sapiens; expression profiling by array;
- platform: GPL6884, Illumina HumanWG-6 v3.0 expression beadchip;
- samples: 116 expression profiles, 58 lung adenocarcinomas and 58 matched
  adjacent non-tumour tissues;
- strengths: histology aligned with GSE10072 and a deliberate vendor/platform
  shift;
- risks: gene-level mapping is required, probe multiplicity can change within-
  sample orderings, and only relations whose genes are present after frozen
  mapping can be evaluated.

### Lung reserve: GSE18842

- NCBI GEO: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE18842>
- platform and size: GPL570; 46 tumours and 45 controls, nearly all paired;
- reason for reserve status: the tumours include non-small-cell lung cancer with
  adenocarcinoma and squamous-cell heterogeneity. It is useful for a declared
  robustness analysis but is not interchangeable with a pure LUAD target.

### Frozen lung comparison

The primary direction is L1 to L2 and L3. Reverse directions are secondary and
must be declared before labels are opened. Platform mapping is learned from
annotation resources, not from outcome agreement. When several probes map to a
gene, the aggregation rule is fixed on source and applied unchanged. Failure to
meet frozen feature/relation coverage yields `UNASSIGNED` or an ineligible task;
it does not trigger target-guided replacement of genes.

## Module C - colorectal cancer

### C1 discovery: GSE39582

- NCBI GEO: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE39582>
- organism and assay: Homo sapiens; expression profiling by array;
- platform: GPL570, Affymetrix Human Genome U133 Plus 2.0;
- samples: 585 profiles; GEO describes 443 discovery colon cancers, 123
  validation colon cancers, and 19 non-tumour mucosa samples;
- strengths: large sample size, molecular and clinical annotation, published
  subtype structure, and survival information;
- risks: its internal discovery/validation split must not be confused with an
  independent study; non-tumour samples are excluded from the primary tumour-
  subtype analysis.

### C2 target 1: GSE14333

- NCBI GEO: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE14333>
- platform: GPL570;
- samples: 290 primary colorectal tumours;
- strengths: independent patient series, stage information, and prognosis-
  oriented annotation;
- risks: heterogeneous stage composition and original MAS5-based processing;
  raw-data processing must be defined cohort-wise and never jointly with C1.

### C3 target 2: GSE33113

- NCBI GEO: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE33113>
- platform: GPL570;
- samples: 90 AJCC stage II primary colorectal tumours and six matched normal
  colon samples;
- strengths: stage-restricted external cohort with long-term follow-up;
- risks: smaller sample size and stage restriction change the target mixture;
  the primary analysis therefore assesses frozen profile coverage and retention,
  not forced reproduction of source proportions.

### Colorectal evaluation boundary

The primary source model is learned from C1 tumour samples only. C2 and C3 are
processed separately using the frozen source specification. Published CMS
assignments, stage, molecular markers, and outcomes are evaluation-only. CMS is
itself expression-derived and is therefore treated as a useful external
reference, not as independent biological ground truth. Clinical association,
profile retention, coverage, and stability are reported alongside ARI/NMI.

## Inclusion and exclusion checks before analysis

Each cohort must pass a versioned sample-level audit before it is admitted:

1. unique sample and patient identifiers, with technical replicates and paired
   specimens identified;
2. declared tissue, histology, stage, treatment, outcome, and censoring fields,
   with missingness quantified before model fitting;
3. raw or processed matrix provenance, log scale, normalisation history, probe
   annotation version, and feature identifier type;
4. duplicate and cross-study sample detection where technically possible;
5. source-only quality control and feature selection;
6. a frozen gene/probe mapping table and frozen relation-coverage threshold;
7. physically separate evaluation-label file, inaccessible to fit/audit imports;
8. a prelabel artifact with configuration, hashes, selected method, profiles,
   thresholds, assignments, and software/environment manifest;
9. evaluation only after the prelabel artifact validates;
10. complete reporting of excluded samples, ineligible tasks, `UNASSIGNED`
    cases, and failed transfer directions.

## Risks capable of invalidating an experiment

- Joint source-target normalisation or batch correction would leak the target
  distribution into the fitted artifact.
- Choosing probes, genes, relations, cluster number, hybrid weight, or rejection
  threshold after inspecting target labels would invalidate frozen transfer.
- Treating paired samples as statistically independent in uncertainty estimates
  would overstate precision.
- Mixing LUAD and broader NSCLC without a declared sensitivity analysis would
  confound histology with cohort.
- Mapping probes by their observed target performance would turn annotation into
  label-guided feature selection.
- Calling a stable partition biologically correct solely because it is stable
  would repeat the failure exposed by the pilot's low median label agreement.
- Selecting only favourable transfer directions or excluding low-coverage
  targets after seeing results would create survivorship bias.
- Reusing GSE39582's internal validation subset as if it were an independent
  cohort would overstate external evidence.

## Primary references for cohort interpretation

- Landi MT et al. Gene expression signature of cigarette smoking and its role
  in lung adenocarcinoma development and survival. *PLoS One*. 2008;3:e1651.
  <https://doi.org/10.1371/journal.pone.0001651>
- Lu TP et al. Identification of a novel biomarker, SEMA5A, for non-small cell
  lung carcinoma in nonsmoking women. *Cancer Epidemiology Biomarkers and
  Prevention*. 2010;19:2590-2597. <https://doi.org/10.1158/1055-9965.EPI-10-0332>
- Selamat SA et al. Genome-scale analysis of DNA methylation in lung
  adenocarcinoma and integration with mRNA expression. *Genome Research*.
  2012;22:1197-1211. <https://doi.org/10.1101/gr.132662.111>
- Marisa L et al. Gene expression classification of colon cancer into molecular
  subtypes: characterization, validation, and prognostic value. *PLoS Medicine*.
  2013;10:e1001453. <https://doi.org/10.1371/journal.pmed.1001453>
- Jorissen RN et al. Metastasis-associated gene expression changes predict poor
  outcomes in patients with Dukes stage B and C colorectal cancer. *Clinical
  Cancer Research*. 2009;15:7642-7651.
  <https://doi.org/10.1158/1078-0432.CCR-09-1431>
- de Sousa E Melo F et al. Poor-prognosis colon cancer is defined by a
  molecularly distinct subtype and develops from serrated precursor lesions.
  *Nature Medicine*. 2013;19:614-618. <https://doi.org/10.1038/nm.3174>
- Guinney J et al. The consensus molecular subtypes of colorectal cancer.
  *Nature Medicine*. 2015;21:1350-1356.
  <https://doi.org/10.1038/nm.3967>

