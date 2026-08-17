# SONATA BIS 16 - frozen working defaults

Status: approved working defaults for preparation of the scientific application  
Frozen on: 2026-08-17  
Scientific pilot evidence: commit `9adae889601486ffb5e9e29f29afe16cc1e1e698`

These choices organise the grant draft. They do not change the pilot protocol,
the experimental thresholds, or the formal pilot decisions.

## Identity and duration

- Polish title: Przenosne relacyjne profile pacjentow do interpretowalnego
  grupowania danych omicznych.
- English title: Transportable Relational Patient Profiles for Interpretable
  Clustering of Omics Data.
- Acronym: TRPP.
- Duration: 48 months.
- Primary panel: ST6 - Computer and information sciences.
- Auxiliary descriptors: ST6_11 and ST6_13; ST6_07 may be added only if the
  final OSF vocabulary makes it useful.

## Scientific scope

- Core problem: determine, from the source cohort only, whether value,
  relational, hybrid, or no stable structure is supported before learning a
  patient grouping.
- Core method: direct sparse relational regions that describe groups using
  short within-patient rules and support frozen assignment of new patients.
- Disease modules: lung adenocarcinoma and colorectal cancer.
- Minimum validation design: at least three independent cohorts per disease
  module, with one discovery cohort and at least two frozen target cohorts.
- Primary implementation: Python-first, deterministic, CPU-only.
- Shared comparator: the same deterministic PAM engine for VALUE, RELATIONAL,
  and HYBRID in matched comparisons.
- Label boundary: labels are physically unavailable to fit and audit code and
  are loaded only by the final evaluation layer.
- Transfer boundary: no target refitting, joint source-target normalisation,
  target-driven feature selection, or target-driven threshold selection.
- Explicit outcomes: `NO_STABLE_STRUCTURE` and `UNASSIGNED` are valid results.

## Team model

- Principal investigator: scientific architecture, relational learning,
  methodological supervision, integration, and dissemination.
- Doctoral researcher, at least 36 months: direct relational-region algorithm,
  correctness tests, stability experiments, and thesis-centred analysis.
- Postdoctoral researcher or specialist analyst: independent multi-cohort
  curation, reproducibility, metadata harmonisation, and frozen-transfer
  validation.
- External consultation: Girona may be described only after the institution,
  person, task, and confirmation are formally verified.

## Boundaries retained from the pilot

- Gate B: GO.
- Gate C: STOP.
- direct regions: NOT TESTED.
- anchors: NOT TESTED.
- PILOT-016, PILOT-017, and PILOT-018 remain not run because Gate C stopped the
  pilot sequence.
- Anchor sets are outside the core project. A single-anchor restriction is a
  conditional efficiency experiment only after the direct-region gate passes.
- Fuzzy clustering, evolutionary algorithms, deep learning, federated
  learning, CUDA, and a web portal are outside scope.

## Items that cannot be truthfully defaulted

The following require factual or institutional input before submission and are
therefore left for final completion rather than invented:

- names, employment dates, salaries, and eligibility of team members;
- host-institution identifiers, authorised representatives, and internal
  deadline;
- detailed budget and quotations;
- confirmed international collaborator and letter or email of commitment;
- PI achievements, attached publications, and complete bibliographic record of
  the accepted Artificial Intelligence Review paper;
- overlap statement against the PI's completed and submitted projects;
- ethics and data-protection declarations signed by the host institution.

