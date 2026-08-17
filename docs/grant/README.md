# Grant-facing package

Recommended reading order:

1. `SONATA_BIS16_SCIENTIFIC_CORE_PL.md` — scientific thesis, hypotheses,
   objectives, work packages, evaluation and risks;
2. `SONATA_BIS16_OSF_STARTER_PL_EN.md` — title, keywords, abstract, popular
   summaries, research-task names and formal checklist;
3. `SONATA_BIS16_PRELIMINARY_RESULTS_EN.md` — insertion-ready evidence section;
4. `SONATA_BIS16_CLAIM_BOUNDARIES.md` — allowed interpretations and hard
   overclaiming boundary;
5. `CLAIMS_EVIDENCE.json` — machine-readable values linked to PILOT-019.

Validate after every substantive edit:

```bash
.venv/bin/python scripts/10_validate_grant_package.py
```

This directory is a grant-writing layer over the immutable pilot evidence. It
must not be used to change experimental thresholds or to imply that blocked
Level-4 methods were run.
