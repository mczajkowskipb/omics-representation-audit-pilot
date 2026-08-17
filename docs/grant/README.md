# Grant-facing package

Recommended reading order:

1. `README_FIRST_PL.md` - plain-language status, file map, and next actions;
2. `SONATA_BIS16_DEFAULTS_FROZEN.md` - approved working choices and the items
   that still require factual input;
3. `SONATA_BIS16_SHORT_DESCRIPTION_EN.md` - self-contained short description,
   laid out as five scientific pages plus references;
4. `SONATA_BIS16_DETAILED_DESCRIPTION_EN_DRAFT.md` - self-contained detailed
   description, laid out as thirteen scientific pages plus references;
5. `SONATA_BIS16_POPULAR_SUMMARY_PL.md` and
   `SONATA_BIS16_POPULAR_SUMMARY_EN.md` - one-page public summaries;
6. `SONATA_BIS16_DATASET_AUDIT.md` - default lung and colorectal cohorts,
   inclusion checks, and invalidating risks;
7. `SONATA_BIS16_SCIENTIFIC_CORE_PL.md` - Polish scientific thesis, hypotheses,
   work packages, evaluation, and risks;
8. `SONATA_BIS16_OSF_STARTER_PL_EN.md` - title, keywords, abstract, task names,
   and formal checklist;
9. `SONATA_BIS16_PRELIMINARY_RESULTS_EN.md` - insertion-ready pilot evidence;
10. `SONATA_BIS16_CLAIM_BOUNDARIES.md` - hard overclaiming boundary;
11. `CLAIMS_EVIDENCE.json` - machine-readable values linked to PILOT-019.

Validate after every substantive edit:

```bash
.venv/bin/python scripts/10_validate_grant_package.py
.venv/bin/python scripts/11_generate_grant_pdfs.py
```

Generated PDFs are written to `output/pdf/`. The short description contains
five content pages plus one references page; the detailed description contains
thirteen content pages plus two references pages. The popular summaries are one
page each. `docs/evidence/GRANT_PDF_VALIDATION.json` records page counts and
hashes.

This directory is a grant-writing layer over the immutable pilot evidence. It
must not be used to change experimental thresholds or to imply that blocked
Level-4 methods were run.
