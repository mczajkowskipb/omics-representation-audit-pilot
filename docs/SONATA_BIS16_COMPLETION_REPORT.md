# SONATA BIS 16 - completion report for the default grant block

Date: 2026-08-17  
Scope: default scientific application package and one-archive handoff  
Protocol status: unchanged and authoritative

## Completed changes

- Frozen the user-approved working defaults: TRPP-centred title, 48 months,
  ST6, PI + doctoral researcher + post-doc/specialist, lung and colorectal
  disease modules, and conditional Girona consultation.
- Audited the default cohort set at accession level against NCBI GEO.
- Prepared a self-contained English short description with five content pages
  plus references.
- Prepared a self-contained English detailed description with thirteen content
  pages plus two reference pages.
- Prepared separate one-page Polish and English popular-science summaries.
- Added a deterministic PDF builder, page-count validation, source/PDF hashes,
  and automated tests.
- Added a Polish start-here guide explaining the scientific sequence and the
  remaining submission work.
- Preserved the pilot's formal scope: Gate B GO, Gate C STOP, and no execution
  of blocked direct-region or anchor experiments.

## Files created

- `docs/grant/README_FIRST_PL.md`
- `docs/grant/SONATA_BIS16_DEFAULTS_FROZEN.md`
- `docs/grant/SONATA_BIS16_DATASET_AUDIT.md`
- `docs/grant/SONATA_BIS16_SHORT_DESCRIPTION_EN.md`
- `docs/grant/SONATA_BIS16_DETAILED_DESCRIPTION_EN_DRAFT.md`
- `docs/grant/SONATA_BIS16_POPULAR_SUMMARY_PL.md`
- `docs/grant/SONATA_BIS16_POPULAR_SUMMARY_EN.md`
- `scripts/11_generate_grant_pdfs.py`
- `tests/unit/test_grant_pdfs.py`
- `requirements-grant.lock`
- `docs/evidence/GRANT_PDF_VALIDATION.json`
- `output/pdf/SONATA_BIS16_SHORT_DESCRIPTION_EN_DRAFT.pdf`
- `output/pdf/SONATA_BIS16_DETAILED_DESCRIPTION_EN_DRAFT.pdf`
- `output/pdf/SONATA_BIS16_POPULAR_SUMMARY_PL.pdf`
- `output/pdf/SONATA_BIS16_POPULAR_SUMMARY_EN.pdf`
- this completion report.

## Files changed

- `docs/grant/README.md`
- `docs/grant/CLAIMS_EVIDENCE.json`
- `docs/evidence/GRANT_PACKAGE_VALIDATION.json`
- `pyproject.toml`

## Tests and results

- focused grant/PDF tests: 7 passed;
- full repository test suite: 145 passed, 0 failed;
- Python bytecode compilation for `src`, `scripts`, and `tests`: passed;
- dependency consistency (`pip check`): no broken requirements;
- grant-claim validation: passed, 0 forbidden overclaims across 11 documents;
- grant-validation repeat: byte-identical;
- PDF repeat generation: byte-identical for all four documents;
- PDF page counts: 6, 15, 1, and 1 as declared;
- visual QA: all 23 generated pages rendered and inspected; no clipping,
  overlap, broken glyphs, or leaked layout markers after correction of one list-
  marker formatting defect.

## Risks detected

- Gate C remains formally STOP. The weaker direction exceeded the frozen
  threshold by 0.005284; this must not be described as a passed external gate.
- Direct relational regions and anchors have no pilot result and must remain
  prospective tasks.
- GSE32863 introduces a vendor/platform shift and requires a frozen gene-mapping
  rule plus explicit relation coverage.
- GSE18842 contains broader NSCLC histology and is a sensitivity cohort, not an
  interchangeable LUAD validation set.
- CMS labels in colorectal cancer are expression-derived and are an external
  reference rather than independent biological ground truth.
- Personnel, budget, institutional, ethics, DMP, CV, publication, and Girona
  details remain factual dependencies that cannot be defaulted safely.

## Deviations from the protocol

None. No pilot threshold changed, no target tuning occurred, no blocked method
was run, and the two reference repositories were not modified.

## Exact next task

Populate the administrative and budget fields from verified institutional and
personal records, insert the final PI track record, confirm any named Girona
collaboration, and then perform a line-by-line OSF/formal compliance review of
the four generated scientific PDFs. No additional pilot experiment is required
for this handoff.

