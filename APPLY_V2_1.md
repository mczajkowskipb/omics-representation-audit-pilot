# Apply Pilot v2.1 diagnostic addendum

From repository root:

```bash
unzip -o /opt/2026/SonataBis/tmp/SONATA_PILOT_V2_1_IDENTIFIABILITY.zip -d .
rm -rf results/pilot_v2_1
PYTHON_BIN=.venv/bin/python bash scripts/21_run_pilot_v2_1.sh
```

Do not delete or overwrite `results/pilot_v2`; Pilot v2 remains the prospective STOP record.
