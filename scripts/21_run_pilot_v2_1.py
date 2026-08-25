#!/usr/bin/env python3
"""Diagnostic identifiability addendum for Pilot v2.

This script does NOT replace or reopen the prospective Pilot-v2 gate.  It tests
an implementation/design issue discovered after v2: the original REL generator
made many cross-pair relations equally class-discriminative, so recovery of six
arbitrarily designated pairs was not identifiable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import adjusted_rand_score

from rep_audit.prototypes.rr_direct import fit_rr_direct, assign_frozen_prototypes

ROOT = Path(__file__).resolve().parents[1]
TRUTH_INDEX_PAIRS = ((0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11))
PAIR_CENTERS = (-36.0, -22.0, -8.0, 8.0, 22.0, 36.0)


def identifiable_relational_dataset(seed: int, n: int, p: int, noise: float):
    if p < 12:
        raise ValueError("p must be at least 12")
    rng = np.random.default_rng(seed)
    y = np.repeat([0, 1], n // 2)
    if len(y) < n:
        y = np.r_[y, 1]

    # Background features occupy separated, class-independent order blocks.
    centers = 100.0 + 5.0 * np.arange(p)
    X = centers[None, :] + rng.normal(0.0, noise, size=(n, p))

    # Only the six within-block truth pairs reverse ordering between groups.
    # Distinct block centers keep cross-block relations class-independent.
    for center, (a, b) in zip(PAIR_CENTERS, TRUTH_INDEX_PAIRS, strict=True):
        signal = np.where(y == 0, 1.8, -1.8)
        X[:, a] = center + signal + rng.normal(0.0, noise, size=n)
        X[:, b] = center - signal + rng.normal(0.0, noise, size=n)

    # Positive sample-wise affine transformations preserve within-sample order.
    scale = np.exp(rng.normal(0.0, 0.8, size=n))
    shift = rng.normal(0.0, 3.0, size=n)
    X = X * scale[:, None] + shift[:, None]

    feature_ids = tuple(f"g{i:03d}" for i in range(p))
    sample_ids = tuple(f"s{i:04d}" for i in range(n))
    truth = tuple((f"g{a:03d}", f"g{b:03d}") for a, b in TRUTH_INDEX_PAIRS)
    return X, feature_ids, sample_ids, y, truth


def exact_pair_recovery(prototypes, truth_pairs) -> float:
    truth = {tuple(sorted(pair)) for pair in truth_pairs}
    learned = {
        tuple(sorted((a, b)))
        for prototype in prototypes
        for a, b, _direction, _support, _contrast in prototype.rules
    }
    return len(truth & learned) / len(truth)


def run(config: dict) -> pd.DataFrame:
    rr = config["rr_direct"]
    s = config["synthetic_identifiable"]
    base = int(config["base_seed"])
    rows = []
    for noise in s["noise_sd"]:
        for replicate in range(int(s["replicates"])):
            seed = base + replicate + int(float(noise) * 1000)
            X, fids, _ids, y, truth = identifiable_relational_dataset(
                seed, int(s["n_source"]), int(s["p"]), float(noise)
            )
            model = fit_rr_direct(
                X,
                fids,
                k=2,
                feature_budget=int(rr["feature_budget"]),
                max_pairs=int(rr["max_pairs"]),
                max_rules=int(rr["max_rules"]),
                min_support=float(rr["min_support"]),
                min_contrast=float(rr["min_contrast"]),
                max_iter=int(rr["max_iter"]),
            )
            source_ari = float(adjusted_rand_score(y, np.asarray(model.labels)))
            recovery = float(exact_pair_recovery(model.prototypes, truth))

            Xt, ft, _idt, yt, _ = identifiable_relational_dataset(
                seed + 500000, int(s["n_target"]), int(s["p"]), float(noise)
            )
            pred, best_score, margin = assign_frozen_prototypes(
                Xt,
                ft,
                model.prototypes,
                min_score=float(rr["frozen_min_score"]),
                min_margin=float(rr["frozen_min_margin"]),
            )
            assigned = pred >= 0
            coverage = float(np.mean(assigned))
            target_ari = (
                float(adjusted_rand_score(yt[assigned], pred[assigned]))
                if assigned.sum() >= 4 and len(set(pred[assigned])) > 1
                else 0.0
            )
            rows.append(
                {
                    "noise": float(noise),
                    "replicate": replicate,
                    "source_ari": source_ari,
                    "exact_pair_recovery": recovery,
                    "target_ari": target_ari,
                    "coverage": coverage,
                    "prototype_size": sum(len(p.rules) for p in model.prototypes),
                    "converged": bool(model.converged),
                    "mean_source_margin": float(np.mean(model.score_margin)),
                    "mean_target_score": float(np.nanmean(best_score)),
                    "mean_target_margin": float(np.nanmean(margin)),
                }
            )
    return pd.DataFrame(rows)


def summarize(frame: pd.DataFrame) -> dict:
    return {
        "schema": "PilotV21IdentifiabilitySummary/v1",
        "status": "DIAGNOSTIC_ADDENDUM_NOT_GATE_RESCUE",
        "pilot_v2_prospective_gate_remains": "STOP",
        "reason_for_addendum": (
            "Original REL generator induced many equally discriminative cross-pair "
            "relations, making exact recovery of six designated pairs non-identifiable."
        ),
        "metrics": {
            "median_source_ari": float(frame.source_ari.median()),
            "median_exact_pair_recovery": float(frame.exact_pair_recovery.median()),
            "median_target_ari": float(frame.target_ari.median()),
            "median_target_coverage": float(frame.coverage.median()),
            "all_replicates_exact_pair_recovery": bool(np.all(frame.exact_pair_recovery == 1.0)),
            "all_replicates_source_ari_at_least_0_75": bool(np.all(frame.source_ari >= 0.75)),
        },
    }


def make_plots(frame: pd.DataFrame, output: Path, dpi: int) -> None:
    figdir = output / "figures"
    figdir.mkdir(parents=True, exist_ok=True)

    agg = frame.groupby("noise")["source_ari"].median()
    plt.figure(figsize=(6, 4))
    plt.plot(agg.index, agg.values, marker="o")
    plt.ylim(-0.02, 1.05)
    plt.xlabel("Noise SD")
    plt.ylabel("Median source ARI")
    plt.title("Pilot v2.1: identifiable relational generator")
    plt.tight_layout()
    plt.savefig(figdir / "fig_v21_source_ari.png", dpi=dpi)
    plt.close()

    agg = frame.groupby("noise")["exact_pair_recovery"].median()
    plt.figure(figsize=(6, 4))
    plt.plot(agg.index, agg.values, marker="o")
    plt.ylim(-0.02, 1.05)
    plt.xlabel("Noise SD")
    plt.ylabel("Median exact-pair recovery")
    plt.title("Pilot v2.1: uniquely identifiable rule recovery")
    plt.tight_layout()
    plt.savefig(figdir / "fig_v21_rule_recovery.png", dpi=dpi)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/pilot_v2_1.yml")
    parser.add_argument("--output", default="results/pilot_v2_1")
    args = parser.parse_args()
    config = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)

    frame = run(config)
    frame.to_csv(output / "identifiable_synthetic.csv", index=False)
    summary = summarize(frame)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    make_plots(frame, output, int(config["reporting"]["figure_dpi"]))

    metrics = summary["metrics"]
    report = [
        "# Pilot v2.1 — identifiability diagnostic addendum",
        "",
        "**Pilot v2 prospective gate remains STOP. This addendum does not change or relax it.**",
        "",
        "The original REL synthetic generator shifted all six left-hand genes together and all six right-hand genes together. Consequently, many cross-pair relations were equally class-discriminative, so exact recovery of only six designated pairs was not an identifiable endpoint.",
        "",
        "This diagnostic generator separates the six signal pairs into distinct order blocks. Only the six within-block relations reverse between groups; cross-block relations are class-independent. RR_DIRECT parameters are unchanged.",
        "",
        "## Diagnostic metrics",
        "",
    ]
    for key, value in metrics.items():
        report.append(f"- **{key}**: {value}")
    report.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "These results may be used to diagnose the failed v2 rule-recovery endpoint, but must not be reported as a retrospective PASS of the original prospective v2 gate.",
            "",
        ]
    )
    (output / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"REPORT: {output / 'REPORT.md'}")


if __name__ == "__main__":
    main()
