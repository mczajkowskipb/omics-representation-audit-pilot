#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "results" / "pilot_v2"
V21 = ROOT / "results" / "pilot_v2_1"
DEST = ROOT / "docs" / "pilot_v2" / "evidence"


def require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required pilot artifact missing: {path}")
    return path


def copy_file(src: Path, dst: Path) -> None:
    require(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def md_table(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in df.itertuples(index=False, name=None):
        vals = []
        for v in row:
            if isinstance(v, float):
                vals.append("NA" if pd.isna(v) else f"{v:.3f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    v2_summary = json.loads(require(V2 / "summary.json").read_text(encoding="utf-8"))
    v21_summary = json.loads(require(V21 / "summary.json").read_text(encoding="utf-8"))
    if v2_summary.get("schema") != "PilotV2Summary/v1":
        raise ValueError("unexpected Pilot v2 summary schema")
    if v21_summary.get("schema") != "PilotV21IdentifiabilitySummary/v1":
        raise ValueError("unexpected Pilot v2.1 summary schema")
    if v2_summary.get("gate_go") is not False:
        raise ValueError("collector expects the observed prospective Pilot v2 STOP; refusing to rewrite history")
    if v21_summary.get("pilot_v2_prospective_gate_remains") != "STOP":
        raise ValueError("v2.1 must preserve the original Pilot v2 STOP")

    if DEST.exists():
        shutil.rmtree(DEST)
    (DEST / "v2" / "figures").mkdir(parents=True, exist_ok=True)
    (DEST / "v2_1" / "figures").mkdir(parents=True, exist_ok=True)

    for name in ["summary.json", "REPORT.md", "synthetic.csv", "real_prelabel.json", "real_evaluation.csv", "transfer_evaluation.csv"]:
        copy_file(V2 / name, DEST / "v2" / name)
    for fig in sorted(require(V2 / "figures").glob("*.png")):
        copy_file(fig, DEST / "v2" / "figures" / fig.name)

    for name in ["summary.json", "REPORT.md", "identifiable_synthetic.csv"]:
        copy_file(V21 / name, DEST / "v2_1" / name)
    for fig in sorted(require(V21 / "figures").glob("*.png")):
        copy_file(fig, DEST / "v2_1" / "figures" / fig.name)

    real = pd.read_csv(V2 / "real_evaluation.csv")
    transfer = pd.read_csv(V2 / "transfer_evaluation.csv")
    pivot = real.pivot(index="dataset", columns="method", values="ari").reset_index()

    m = v2_summary["metrics"]
    checks = v2_summary["prospective_gate"]
    m21 = v21_summary["metrics"]
    check_lines = [f"- `{name}`: {'PASS' if value else 'FAIL'}" for name, value in checks.items()]

    report = [
        "# Pilot v2 / v2.1 evidence snapshot",
        "",
        "This directory contains compact, tracked evidence copied from the reproducible run directories under `results/`. The original result directories remain ignored by Git; this snapshot is intended for repository review and grant-facing traceability.",
        "",
        "## Scientific status",
        "",
        "**Pilot v2 prospective gate: STOP.** Four of five preregistered criteria passed; exact designated-pair recovery failed. Thresholds were not relaxed after observing the result.",
        "",
        *check_lines,
        "",
        "Pilot v2.1 is a diagnostic identifiability addendum only. It does not convert Pilot v2 to GO and must not be reported as a retrospective gate rescue.",
        "",
        "## Pilot v2 key metrics",
        "",
        f"- synthetic RR_DIRECT median ARI: **{m['synthetic_rel_median_ari']:.4f}**",
        f"- synthetic designated-pair recovery: **{m['synthetic_rel_median_rule_recovery']:.4f}**",
        f"- NULL high-confidence false-structure rate: **{m['null_high_confidence_rate']:.4f}**",
        f"- real RR_DIRECT median ARI: **{m['real_rr_median_ari']:.4f}**",
        f"- real RELATION/PAM median ARI: **{m['real_relation_pam_median_ari']:.4f}**",
        f"- median real RR_DIRECT − RELATION/PAM ARI: **{m['real_median_difference_rr_minus_relation']:.4f}**",
        f"- best frozen transfer ARI: **{m['best_transfer_ari']:.4f}**",
        f"- coverage at best transfer ARI: **{m['best_transfer_coverage_at_best_ari']:.4f}**",
        "",
        "The low median ARI on the eleven real within-dataset tasks is evidence against claiming broad real-data superiority at this stage. The strong frozen transfer result is promising but should be presented as a pilot observation, not definitive external validation of the full future framework.",
        "",
        "## Eleven real omics datasets",
        "",
        md_table(pivot),
        "",
        "## Frozen transfer",
        "",
        md_table(transfer),
        "",
        "## Pilot v2.1 identifiability diagnostic",
        "",
        f"- median source ARI: **{m21['median_source_ari']:.4f}**",
        f"- median exact-pair recovery: **{m21['median_exact_pair_recovery']:.4f}**",
        f"- median frozen-target ARI: **{m21['median_target_ari']:.4f}**",
        f"- median target coverage: **{m21['median_target_coverage']:.4f}**",
        f"- all replicates exact-pair recovery: **{m21['all_replicates_exact_pair_recovery']}**",
        f"- all replicates source ARI ≥ 0.75: **{m21['all_replicates_source_ari_at_least_0_75']}**",
        "",
        "The v2.1 result supports the diagnosis that the original exact-recovery endpoint was non-identifiable because many cross-pair relations were equally discriminative. RR_DIRECT hyperparameters were unchanged.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "PYTHON_BIN=.venv/bin/python bash scripts/20_run_pilot_v2.sh",
        "PYTHON_BIN=.venv/bin/python bash scripts/21_run_pilot_v2_1.sh",
        ".venv/bin/python scripts/22_collect_pilot_v2_evidence.py",
        "```",
        "",
        "Real-data inputs are not duplicated here. They are loaded through the repository's integrity-checked reference adapters and manifests, preserving the existing source-only / evaluation-label separation.",
        "",
    ]
    (ROOT / "docs" / "pilot_v2" / "PILOT_EVIDENCE.md").write_text("\n".join(report), encoding="utf-8")

    files = sorted(p for p in DEST.rglob("*") if p.is_file())
    manifest = [f"{sha256(p)}  {p.relative_to(ROOT).as_posix()}" for p in files]
    (DEST / "SHA256SUMS.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")

    print(f"Collected {len(files)} compact evidence files")
    print(f"Evidence report: {ROOT / 'docs' / 'pilot_v2' / 'PILOT_EVIDENCE.md'}")
    print(f"Checksums: {DEST / 'SHA256SUMS.txt'}")


if __name__ == "__main__":
    main()
