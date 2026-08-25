# Apply Pilot v2 to the existing SONATA repository

From `/opt/2026/SonataBis/repo/omics-representation-audit-pilot`:

```bash
git switch main
git pull --ff-only
git switch -c pilot-v2-relational-prototypes
unzip -o /path/to/SONATA_PILOT_V2_PATCH.zip -d /opt/2026/SonataBis/repo/omics-representation-audit-pilot
PYTHON_BIN=.venv/bin/python bash scripts/20_run_pilot_v2.sh
```

Then inspect:

```bash
cat results/pilot_v2/summary.json
cat results/pilot_v2/REPORT.md
git status --short
```

Do **not** merge to `main` until the prospective gate and outputs have been reviewed.
