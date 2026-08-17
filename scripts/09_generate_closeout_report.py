#!/usr/bin/env python3
"""Generate PILOT-020 tables, six figures, Polish prose, and a verified PDF."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/omics-representation-audit-mpl")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from scipy.stats import spearmanr

from rep_audit.io.canonical_json import atomic_write_canonical_json


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TABLES = DOCS / "tables"
FIGURES = DOCS / "figures"
PDF_OUTPUT = ROOT / "output" / "pdf" / "SONATA_BIS_PILOT_CLOSEOUT_REPORT.pdf"
PALETTE = {
    "navy": "#17365D",
    "blue": "#3E75A6",
    "teal": "#2A9D8F",
    "amber": "#E9A23B",
    "red": "#C94C4C",
    "gray": "#6B7280",
    "light": "#E8EEF4",
    "VALUE": "#3E75A6",
    "RELATIONAL": "#2A9D8F",
    "HYBRID": "#E9A23B",
    "NO_STABLE_STRUCTURE": "#6B7280",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _figure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 12,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _save(fig, name: str) -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / name
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def _make_figures(gate_b: dict, gate_c: dict, within: dict) -> list[Path]:
    _figure_style()
    paths = []

    labels = [
        "Trafność\nmin 0,70",
        "Regret\nmaks 0,05",
        "NULL false\nmaks 0,10",
        "HYBRID/pure\nmaks 0,20",
        "Spearman\nmin 0,40",
    ]
    actual = [
        gate_b["exact_family_identification_rate"],
        gate_b["median_target_ari_regret"],
        gate_b["null_false_structure_rate"],
        gate_b["hybrid_selection_on_pure_rate"],
        gate_b["source_audit_target_performance_spearman"],
    ]
    thresholds = [0.70, 0.05, 0.10, 0.20, 0.40]
    direction = ["min", "max", "max", "max", "min"]
    fig, axes = plt.subplots(1, 5, figsize=(11.5, 2.8), sharey=True)
    for ax, label, value, threshold, criterion in zip(
        axes, labels, actual, thresholds, direction, strict=True
    ):
        passed = value >= threshold if criterion == "min" else value <= threshold
        ax.bar([0], [value], width=0.58, color=PALETTE["teal"] if passed else PALETTE["red"])
        ax.axhline(threshold, color=PALETTE["navy"], linestyle="--", linewidth=1.2)
        ax.set_title(label)
        ax.set_xticks([])
        ax.set_ylim(0, 1.02)
        ax.text(0, min(0.98, value + 0.05), f"{value:.3f}", ha="center", fontweight="bold")
    axes[0].set_ylabel("Wartość metryki")
    fig.subplots_adjust(wspace=0.22)
    paths.append(_save(fig, "figure_01_gate_b.png"))

    rows = sorted(within["datasets"].values(), key=lambda item: item["selected_ari"])
    names = [item["display_id"] for item in rows]
    selected = [item["selected_ari"] for item in rows]
    oracle = [item["oracle_ari"] for item in rows]
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    ax.barh(y - 0.18, selected, height=0.34, color=PALETTE["blue"], label="Wybrana")
    ax.barh(y + 0.18, oracle, height=0.34, color=PALETTE["light"], edgecolor=PALETTE["navy"], label="Oracle post-hoc")
    ax.axvline(0, color="#444444", linewidth=0.8)
    ax.set_yticks(y, names)
    ax.set_xlabel("ARI względem etykiety ewaluacyjnej")
    ax.set_title("11 zbiorów realnych: wybrana reprezentacja a retrospektywny oracle", fontweight="bold")
    ax.legend(frameon=False, loc="lower right")
    paths.append(_save(fig, "figure_02_within_selected_oracle.png"))

    decision_counts = within["decision_counts"]
    decision_order = ["VALUE", "RELATIONAL", "HYBRID", "NO_STABLE_STRUCTURE"]
    fig, ax = plt.subplots(figsize=(6.8, 3.7))
    counts = [decision_counts.get(name, 0) for name in decision_order]
    ax.bar(decision_order, counts, color=[PALETTE[name] for name in decision_order])
    for index, count in enumerate(counts):
        ax.text(index, count + 0.15, str(count), ha="center", fontweight="bold")
    ax.set_ylim(0, max(counts) + 1.2)
    ax.set_ylabel("Liczba zbiorów")
    ax.set_title("Zamrożone decyzje audytu przed odczytem etykiet", fontweight="bold")
    ax.tick_params(axis="x", rotation=15)
    paths.append(_save(fig, "figure_03_within_decisions.png"))

    direction_rows = list(gate_c["directions"].values())
    direction_names = [
        f"{item['source_dataset_id']} →\n{item['target_dataset_id']}"
        for item in direction_rows
    ]
    x = np.arange(2)
    selected_transfer = [item["selected_target_ari_forced"] for item in direction_rows]
    oracle_transfer = [item["oracle_target_ari_forced"] for item in direction_rows]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar(x - 0.18, selected_transfer, width=0.36, color=PALETTE["blue"], label="Wybrana")
    ax.bar(x + 0.18, oracle_transfer, width=0.36, color=PALETTE["light"], edgecolor=PALETTE["navy"], label="Oracle")
    for idx, item in enumerate(direction_rows):
        ax.text(idx, max(selected_transfer[idx], oracle_transfer[idx]) + 0.035, f"regret={item['target_ari_regret']:.3f}", ha="center", fontsize=8)
    ax.set_xticks(x, direction_names)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("ARI na kohorcie target")
    ax.set_title("Transfer zewnętrzny: jeden kierunek przekracza limit regret 0,10", fontweight="bold")
    ax.legend(frameon=False)
    paths.append(_save(fig, "figure_04_gate_c_transfer.png"))

    selected_rows = []
    for item in within["datasets"].values():
        method = next(
            row for row in item["methods"] if row["method_id"] == item["selected_method"]
        )
        selected_rows.append((item, method))
    q_values = [method["source_q"] for _, method in selected_rows]
    ari_values = [item["selected_ari"] for item, _ in selected_rows]
    rho = float(spearmanr(q_values, ari_values).statistic)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for family in ("VALUE", "RELATIONAL", "HYBRID"):
        subset = [pair for pair in selected_rows if pair[0]["selected_decision"] == family]
        ax.scatter(
            [method["source_q"] for _, method in subset],
            [item["selected_ari"] for item, _ in subset],
            s=52,
            color=PALETTE[family],
            label=family,
            alpha=0.9,
        )
    for item, method in selected_rows:
        ax.annotate(item["display_id"], (method["source_q"], item["selected_ari"]), xytext=(4, 3), textcoords="offset points", fontsize=7)
    ax.axhline(0, color="#555555", linewidth=0.7)
    ax.set_xlabel("Source-only Q wybranej metody")
    ax.set_ylabel("ARI względem dostępnej etykiety")
    ax.set_title(f"Stabilność klastra nie gwarantuje zgodności klinicznej (rho={rho:.3f})", fontweight="bold")
    ax.legend(frameon=False)
    paths.append(_save(fig, "figure_05_q_vs_label_ari.png"))

    fig, ax = plt.subplots(figsize=(9.5, 3.1))
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 1)
    ax.axis("off")
    stages = [
        (0.1, "Gate A", "GO\ncorrectness", PALETTE["teal"]),
        (1.3, "Gate B", "GO\n630 pairs", PALETTE["teal"]),
        (2.5, "Real within", "DESCRIPTIVE\n11 datasets", PALETTE["blue"]),
        (3.7, "Gate C", "STOP\nexternal", PALETTE["red"]),
        (4.9, "Gates D/E", "NOT RUN\nblocked", PALETTE["gray"]),
    ]
    for x0, title, status, color in stages:
        box = FancyBboxPatch((x0, 0.24), 0.95, 0.55, boxstyle="round,pad=0.03,rounding_size=0.05", facecolor=color, edgecolor="none")
        ax.add_patch(box)
        ax.text(x0 + 0.475, 0.66, title, ha="center", va="center", color="white", fontweight="bold")
        ax.text(x0 + 0.475, 0.41, status, ha="center", va="center", color="white", fontsize=8)
        if x0 < 4.9:
            ax.annotate("", xy=(x0 + 1.18, 0.515), xytext=(x0 + 0.98, 0.515), arrowprops={"arrowstyle": "->", "color": PALETTE["navy"]})
    ax.set_title("Zamrożony wynik pilota i konsekwencja zakresowa", fontweight="bold")
    paths.append(_save(fig, "figure_06_gate_status.png"))
    return paths


def _tables(gate_b: dict, gate_c: dict, within: dict) -> list[Path]:
    paths = []
    gate_b_rows = [
        {"criterion": "exact family identification", "value": gate_b["exact_family_identification_rate"], "threshold": ">=0.70", "passed": True},
        {"criterion": "median target ARI regret", "value": gate_b["median_target_ari_regret"], "threshold": "<=0.05", "passed": True},
        {"criterion": "NULL false structure", "value": gate_b["null_false_structure_rate"], "threshold": "<=0.10", "passed": True},
        {"criterion": "HYBRID on pure regimes", "value": gate_b["hybrid_selection_on_pure_rate"], "threshold": "<=0.20", "passed": True},
        {"criterion": "source/target Spearman", "value": gate_b["source_audit_target_performance_spearman"], "threshold": ">=0.40", "passed": True},
    ]
    path = TABLES / "gate_b_summary.csv"
    _write_csv(path, ["criterion", "value", "threshold", "passed"], gate_b_rows)
    paths.append(path)

    within_rows = []
    for item in sorted(within["datasets"].values(), key=lambda row: row["display_id"]):
        method = next(row for row in item["methods"] if row["method_id"] == item["selected_method"])
        within_rows.append(
            {
                "dataset": item["display_id"],
                "decision": item["selected_decision"],
                "selected_method": item["selected_method"],
                "source_q": method["source_q"],
                "selected_ari": item["selected_ari"],
                "selected_nmi": item["selected_nmi"],
                "oracle_method": item["oracle_method"],
                "oracle_ari": item["oracle_ari"],
                "ari_regret": item["ari_regret"],
            }
        )
    path = TABLES / "real_within_results.csv"
    _write_csv(path, list(within_rows[0]), within_rows)
    paths.append(path)

    transfer_rows = []
    for item in gate_c["directions"].values():
        transfer_rows.append(
            {
                "direction": item["direction_id"],
                "decision": item["selected_decision"],
                "selected_method": item["selected_method"],
                "selected_ari": item["selected_target_ari_forced"],
                "selected_nmi": item["selected_target_nmi_forced"],
                "oracle_method": item["oracle_method"],
                "oracle_ari": item["oracle_target_ari_forced"],
                "ari_regret": item["target_ari_regret"],
                "coverage": item["selected_assignment_coverage"],
                "min_cluster_fraction": item[
                    "selected_min_assigned_cluster_fraction_of_target"
                ],
            }
        )
    path = TABLES / "external_transfer_results.csv"
    _write_csv(path, list(transfer_rows[0]), transfer_rows)
    paths.append(path)

    method_rows = [
        {"family": "VALUE", "methods": "V_EUC_PAM; V_COR_PAM", "meaning": "source-scaled measurement values", "clustering": "deterministic PAM"},
        {"family": "RELATIONAL", "methods": "R_FOOT_PAM; R_PAIR_PAM", "meaning": "within-sample ranks or ternary pair relations", "clustering": "deterministic PAM"},
        {"family": "HYBRID", "methods": "H_EUC_PAIR_A025/050/075_PAM", "meaning": "source-normalized value plus pair-relation distance", "clustering": "deterministic PAM"},
        {"family": "NO_STABLE_STRUCTURE", "methods": "none", "meaning": "no candidate exceeds NULL-calibrated eligibility", "clustering": "abstention"},
    ]
    path = TABLES / "method_definitions.csv"
    _write_csv(path, list(method_rows[0]), method_rows)
    paths.append(path)

    status_rows = [
        {"item": "Gate A", "status": "GO", "basis": "correctness, determinism, no leakage"},
        {"item": "Gate B", "status": "GO", "basis": "all five frozen simulation criteria passed"},
        {"item": "Real within", "status": "DESCRIPTIVE", "basis": "11/11 frozen before labels; not an external gate"},
        {"item": "Gate C", "status": "STOP", "basis": "one regret 0.105284 > 0.10"},
        {"item": "PILOT-016", "status": "NOT RUN", "basis": "blocked by Gate C STOP"},
        {"item": "PILOT-017", "status": "NOT RUN", "basis": "blocked by Gate C STOP"},
        {"item": "PILOT-018", "status": "NOT RUN", "basis": "blocked by Gate C STOP"},
        {"item": "PILOT-019", "status": "COMPLETE", "basis": "full integrity validation"},
        {"item": "PILOT-020", "status": "COMPLETE", "basis": "tables, six figures, report and grant text"},
    ]
    path = TABLES / "go_stop_decision_log.csv"
    _write_csv(path, list(status_rows[0]), status_rows)
    paths.append(path)
    return paths


def _fmt(value: float) -> str:
    return f"{value:.3f}".replace(".", ",")


def _markdown(gate_b: dict, gate_c: dict, within: dict, evidence: dict) -> str:
    lines = [
        "# Końcowy raport pilota SONATA BIS",
        "",
        "Data zamknięcia: 2026-08-17",
        "",
        f"Protokół SHA-256: `{evidence['protocol_sha256']}`",
        "",
        "## Wynik w jednym zdaniu",
        "",
        "Mechanizm source-only trafnie rozróżnia rodziny reprezentacji w symulacjach (Gate B: GO), ale zewnętrzny transfer nie spełnił zamrożonego limitu w jednym kierunku (Gate C: STOP), dlatego regionów bezpośrednich i anchorów nie uruchomiono i nie należy przedstawiać ich jako zwalidowanych wyników pilota.",
        "",
        "## Co tu właściwie robimy - prostym językiem",
        "",
        "1. Zanim pogrupujemy pacjentów, sprawdzamy, jak ich porównywać: po wartościach, po kolejności/rangach cech albo po połączeniu obu widoków.",
        "2. Każdy widok trafia do dokładnie tego samego deterministycznego PAM, więc porównujemy reprezentacje, a nie różne algorytmy grupowania.",
        "3. PAM wybiera medoid - rzeczywistego, centralnego pacjenta grupy. To jest obecny odpowiednik centroidu.",
        "4. Planowane regiony miały później opisać grupę krótkimi regułami typu `gen_A > gen_B`. Nie zostały wykonane, ponieważ poprzedzająca je bramka zewnętrzna zakończyła się STOP.",
        "5. Etykiety diagnoz nie służą do uczenia ani wyboru reprezentacji. Są odczytywane dopiero po zamrożeniu wszystkich przypisań i służą tylko do końcowej oceny.",
        "",
        "## Zamrożone decyzje",
        "",
        "| Element | Wynik | Interpretacja |",
        "|---|---:|---|",
        "| Gate A | GO | poprawność, deterministyczność i bariery leakage potwierdzone |",
        "| Gate B | GO | wszystkie kryteria pełnej siatki 630 par spełnione |",
        "| 11 zbiorów realnych | opisowe | 11/11 zamrożone przed etykietami; to nie jest walidacja zewnętrzna |",
        "| Gate C | STOP | regret 0,105284 przekroczył limit 0,10 o 0,005284 |",
        "| PILOT-016--018 | NOT RUN | regiony i anchory zablokowane; brak retrospektywnego ratowania |",
        "| PILOT-019--020 | COMPLETE | walidacja, tabele, 6 figur, raport i tekst do wniosku |",
        "",
        "## Gate B - dowód kontrolowany",
        "",
        f"Pełna siatka obejmowała 630 par source-target. Trafność rodziny wyniosła {_fmt(gate_b['exact_family_identification_rate'])}, mediana regret {_fmt(gate_b['median_target_ari_regret'])}, częstość fałszywej struktury NULL {_fmt(gate_b['null_false_structure_rate'])}, wybór HYBRID w czystych reżimach {_fmt(gate_b['hybrid_selection_on_pure_rate'])}, a korelacja Spearmana między różnicami Q i zachowaniem target {_fmt(gate_b['source_audit_target_performance_spearman'])}. Każde kryterium przeszło bez zmiany progu.",
        "",
        "![Gate B](figures/figure_01_gate_b.png)",
        "",
        "## Jedenaście zbiorów realnych - kontrola opisowa",
        "",
        f"Audyt wybrał RELATIONAL dla 8 zbiorów, VALUE dla 2 i HYBRID dla 1. W 9/11 przypadków wybrany wariant był nie dalej niż 0,05 ARI od retrospektywnego oracle; mediana regret wyniosła {_fmt(within['median_ari_regret'])}. Jednocześnie mediana wybranego ARI wyniosła tylko {_fmt(within['median_selected_ari'])}. To znaczy: selektor zwykle wybierał wariant bliski najlepszemu z dostępnych, ale sama stabilna struktura często nie odpowiadała etykiecie klinicznej.",
        "",
        "![Real within](figures/figure_02_within_selected_oracle.png)",
        "",
        "Pełne wartości znajdują się w `tables/real_within_results.csv`. Analiza jest wewnątrzzbiorowa i opisowa; nie zastępuje transferu zewnętrznego.",
        "",
        "## Gate C - walidacja zewnętrzna",
        "",
        "W kierunku GSE19804→GSE10072 wybrana reprezentacja osiągnęła ARI 0,926 i regret 0,000. W kierunku GSE10072→GSE19804 osiągnęła ARI 0,559 przy oracle 0,664, co daje regret 0,105284. Pokrycie i minimalne liczebności klastrów przeszły, lecz warunek regret nie przeszedł. Formalny wynik pozostaje STOP.",
        "",
        "![Gate C](figures/figure_04_gate_c_transfer.png)",
        "",
        "## Co wynik mówi o rankingu i grupowaniu",
        "",
        "Reprezentacja rankingowa/relacyjna ma wyraźną domenę użyteczności: została poprawnie rozpoznana w kontrolowanych reżimach i wybrana w 8/11 realnych audytów. Nie jest jednak automatycznie biologicznie trafna. W kilku kohortach wszystkie warianty miały ARI bliskie zeru mimo stabilności source-only. Audyt odpowiada więc na pytanie «która geometria grupowania jest najbardziej adekwatna według danych source», a nie gwarantuje, że grupy odtworzą konkretną etykietę kliniczną.",
        "",
        "![Q versus ARI](figures/figure_05_q_vs_label_ari.png)",
        "",
        "## Regiony/reguły i centroid",
        "",
        "Obecnie centrum klastra jest medoidem, czyli rzeczywistym pacjentem centralnym pod wybraną odległością. Post-hoc region miał zamienić relacyjny klaster w krótki profil reguł. Direct region miał jednocześnie wyznaczać reguły i przypisania. Anchor miał tylko ograniczać przestrzeń kandydatów. Żaden z tych trzech modułów nie został przetestowany, więc pilot nie dostarcza jeszcze dowodu na ich jakość interpretacyjną ani predykcyjną.",
        "",
        "![Status](figures/figure_06_gate_status.png)",
        "",
        "## Rekomendacja do wniosku SONATA BIS",
        "",
        "Najbezpieczniejsza teza brzmi: różne reprezentacje mają odmienne domeny kompetencji, a source-only Representation Audit może tworzyć mapę adekwatności i jawnie wstrzymywać wnioskowanie. Nie należy twierdzić, że automatyczny wybór został już w pełni potwierdzony zewnętrznie ani że direct regions/anchory mają wyniki pilotażowe. Regiony można pozostawić jako główną hipotezę metodologiczną przyszłego projektu, z walidacją prospektywną i wyraźną bramką przed rozszerzeniem zakresu.",
        "",
        "## Integralność i odtwarzalność",
        "",
        f"PILOT-019 zwalidował 630/630 zadań symulacyjnych, 210 audytów source, 2/2 transfery, 11/11 audytów realnych, 390 raportów NULL dla etapów realnych oraz brak zmian w plikach śledzonych obu repozytoriów referencyjnych. Jeden zastany, nieśledzony plik tymczasowy AIR został wykluczony z adapterów i pozostawiony bez zmian. Hash pełnego drzewa within-dataset: `{evidence['real_within']['tree_sha256']}`.",
        "",
        "Odstępstwa od protokołu: nie zmieniono żadnego kryterium eksperymentalnego. PILOT-016--018 nie wykonano wskutek zamrożonego Gate C STOP; jest to kontrola zakresu, nie ciche odstępstwo.",
    ]
    return "\n".join(lines) + "\n"


def _grant_text(gate_b: dict, within: dict) -> str:
    return f"""# Krótki tekst wynikowy do wniosku SONATA BIS

W pilotażu opracowano deterministyczny, source-only Representation Audit, który przed grupowaniem porównuje reprezentację wartościową, rankingowo-relacyjną i hybrydową przy wspólnym algorytmie PAM oraz dopuszcza wynik NO_STABLE_STRUCTURE. Preprocessing, dobór cech, relacji, wag i medoidów odbywały się bez etykiet; etykiety udostępniano dopiero po zapisaniu kompletnych przypisań.

W kontrolowanej siatce 630 par source-target audyt poprawnie wskazał rodzinę reprezentacji w {100 * gate_b['exact_family_identification_rate']:.1f}% replikacji, przy medianie target-ARI regret {gate_b['median_target_ari_regret']:.3f} i korelacji source-target Spearmana {gate_b['source_audit_target_performance_spearman']:.3f}; wszystkie zamrożone kryteria Gate B zostały spełnione. W 11 heterogenicznych zbiorach ekspresyjnych wybór był w granicy 0,05 ARI od retrospektywnego oracle w {100 * within['selected_within_0_05_of_oracle_rate']:.1f}% przypadków, lecz mediana ARI względem dostępnych etykiet wyniosła tylko {within['median_selected_ari']:.3f}. Pokazuje to, że stabilność niesuperwizowana nie gwarantuje zgodności z pojedynczą etykietą kliniczną.

Dwukierunkowy transfer GSE10072/GSE19804 dał jeden wynik silny (ARI 0,926; regret 0,000), natomiast w kierunku odwrotnym regret 0,105 przekroczył zamrożony limit 0,10. Gate C zakończył się formalnym STOP. W konsekwencji pilot wspiera tezę o domenach kompetencji reprezentacji i potrzebie jawnego mechanizmu wstrzymania, ale nie uzasadnia jeszcze silnego twierdzenia o w pełni zwalidowanym automatycznym selektorze. Sparse relational regions pozostają hipotezą metodologiczną projektu; direct regions i anchory nie były w pilotażu uruchamiane ani oceniane.
"""


def _pdf(gate_b: dict, gate_c: dict, within: dict, evidence: dict, figures: list[Path]) -> None:
    PDF_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    font_root = Path("/usr/share/fonts/truetype/dejavu")
    pdfmetrics.registerFont(TTFont("DejaVu", font_root / "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", font_root / "DejaVuSans-Bold.ttf"))
    styles = getSampleStyleSheet()
    body = ParagraphStyle("BodyPL", parent=styles["BodyText"], fontName="DejaVu", fontSize=9.2, leading=13, spaceAfter=7, alignment=TA_LEFT)
    heading = ParagraphStyle("HeadingPL", parent=styles["Heading2"], fontName="DejaVu-Bold", textColor=colors.HexColor(PALETTE["navy"]), fontSize=15, leading=18, spaceBefore=8, spaceAfter=8)
    title = ParagraphStyle("TitlePL", parent=styles["Title"], fontName="DejaVu-Bold", textColor=colors.HexColor(PALETTE["navy"]), fontSize=23, leading=27, alignment=TA_CENTER, spaceAfter=12)
    small = ParagraphStyle("SmallPL", parent=body, fontSize=7.6, leading=10)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("DejaVu", 7.5)
        canvas.setFillColor(colors.HexColor(PALETTE["gray"]))
        canvas.drawString(18 * mm, 12 * mm, "SONATA BIS - Omics Representation Audit Pilot")
        canvas.drawRightString(192 * mm, 12 * mm, f"strona {doc.page}")
        canvas.restoreState()

    def invariant_canvas(*args, **kwargs):
        kwargs["invariant"] = 1
        return pdf_canvas.Canvas(*args, **kwargs)

    document = SimpleDocTemplate(
        str(PDF_OUTPUT),
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="SONATA BIS Pilot Closeout Report",
        author="Marcin Czajkowski",
    )
    story = [
        Spacer(1, 22 * mm),
        Paragraph("Końcowy raport pilota SONATA BIS", title),
        Paragraph("Omics Representation Audit: wartości, rangi, relacje i zamrożony transfer", ParagraphStyle("Subtitle", parent=body, alignment=TA_CENTER, fontSize=12, leading=16)),
        Spacer(1, 12 * mm),
        Paragraph("Wynik: Gate B = GO, Gate C = STOP", ParagraphStyle("Decision", parent=heading, alignment=TA_CENTER, textColor=colors.HexColor(PALETTE["red"]))),
        Spacer(1, 10 * mm),
        Paragraph("Data zamknięcia: 17 sierpnia 2026", ParagraphStyle("Date", parent=body, alignment=TA_CENTER)),
        Paragraph(f"Protokół SHA-256: {evidence['protocol_sha256']}", ParagraphStyle("Hash", parent=small, alignment=TA_CENTER)),
        PageBreak(),
        Paragraph("Podsumowanie wykonawcze", heading),
        Paragraph("Pilot potwierdził w symulacjach, że różne reprezentacje danych mają odmienne domeny kompetencji i że source-only audit może je rozróżniać. Nie potwierdził jednak całej ścieżki zewnętrznej: jeden kierunek transferu przekroczył zamrożony limit regret o 0,005284. Wyniku nie dostrajano po etykietach, dlatego formalna decyzja pozostaje STOP.", body),
        Paragraph("Co dzieje się w pipeline", heading),
        Paragraph("Najpierw bez etykiet wybierany jest sposób porównywania pacjentów: wartości, relacje rankingowe albo hybryda. Wszystkie warianty korzystają z tego samego deterministycznego PAM. Centrum klastra jest medoidem - rzeczywistym pacjentem. Etykiety są otwierane dopiero po zamrożeniu decyzji i przypisań. Planowane regiony miały później zamienić relacyjny klaster w krótki zestaw reguł; nie zostały uruchomione po Gate C STOP.", body),
        Image(str(figures[5]), width=174 * mm, height=57 * mm),
        PageBreak(),
        Paragraph("Gate B - pełna siatka symulacyjna", heading),
        Paragraph(f"W 630 parach source-target trafność rodziny wyniosła {_fmt(gate_b['exact_family_identification_rate'])}; mediana regret {_fmt(gate_b['median_target_ari_regret'])}; false structure NULL {_fmt(gate_b['null_false_structure_rate'])}; HYBRID w czystych reżimach {_fmt(gate_b['hybrid_selection_on_pure_rate'])}; Spearman {_fmt(gate_b['source_audit_target_performance_spearman'])}. Wszystkie progi spełniono bez zmiany kryteriów.", body),
        Image(str(figures[0]), width=178 * mm, height=43 * mm),
        PageBreak(),
        Paragraph("Jedenaście zbiorów realnych", heading),
        Paragraph(f"Przed odczytem etykiet zamrożono 8 decyzji RELATIONAL, 2 VALUE i 1 HYBRID. Mediana regret względem retrospektywnego oracle wyniosła {_fmt(within['median_ari_regret'])}, ale mediana ARI tylko {_fmt(within['median_selected_ari'])}. To kontrola zachowania na danych realnych, a nie walidacja zewnętrzna.", body),
        Image(str(figures[1]), width=168 * mm, height=111 * mm),
        PageBreak(),
        Paragraph("Wyniki within-dataset", heading),
    ]
    table_data = [["Zbiór", "Decyzja", "Metoda", "ARI", "Oracle", "Regret"]]
    for item in sorted(within["datasets"].values(), key=lambda row: row["display_id"]):
        table_data.append([
            item["display_id"], item["selected_decision"], item["selected_method"],
            f"{item['selected_ari']:.3f}", f"{item['oracle_ari']:.3f}", f"{item['ari_regret']:.3f}",
        ])
    table = Table(table_data, colWidths=[25 * mm, 30 * mm, 47 * mm, 19 * mm, 19 * mm, 19 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.2),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PALETTE["navy"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C3CF")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6F9")]),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([
        table,
        Spacer(1, 5 * mm),
        Image(str(figures[2]), width=155 * mm, height=84 * mm),
        PageBreak(),
        Paragraph("Stabilność a zgodność kliniczna", heading),
        Paragraph("Source-only Q mierzy odtwarzalność i odporność klastra, a nie zgodność z konkretną diagnozą. Słaba opisowa zależność Q-ARI dla 11 wybranych metod pokazuje, że stabilna struktura może odzwierciedlać inną biologię lub czynnik techniczny.", body),
        Image(str(figures[4]), width=170 * mm, height=113 * mm),
        PageBreak(),
        Paragraph("Gate C - transfer zewnętrzny", heading),
        Paragraph("GSE19804 do GSE10072: ARI 0,926, regret 0,000. GSE10072 do GSE19804: ARI 0,559, oracle 0,664, regret 0,105284. Pokrycie i wielkości klastrów przeszły, lecz zamrożony warunek regret nie przeszedł.", body),
        Image(str(figures[3]), width=170 * mm, height=99 * mm),
        PageBreak(),
        Paragraph("Konsekwencje dla SONATA BIS", heading),
        Paragraph("Wniosek może bezpiecznie opierać się na mapie adekwatności reprezentacji, jawnej możliwości wstrzymania oraz potrzebie interpretowalnych relacyjnych opisów. Nie powinien twierdzić, że zewnętrzny automatyczny wybór, direct regions lub anchory zostały już pozytywnie zwalidowane. Sparse relational regions pozostają hipotezą przyszłej pracy z prospektywną bramką walidacyjną.", body),
        Paragraph("Zakres niewykonany", heading),
        Paragraph("PILOT-016 post-hoc profiles, PILOT-017 direct sparse relational regions i PILOT-018 conditional anchors: NOT RUN, zablokowane przez Gate C STOP. Nie zmieniono progu, alpha, margin, coverage ani selektora po obejrzeniu etykiet.", body),
        Paragraph("Odtwarzalność", heading),
        Paragraph(f"PILOT-019: wszystkie kontrole integralności przeszły. Zwalidowano 630 zadań, 210 audytów source, 2 transfery, 11 audytów realnych i 390 realnych raportów NULL. Hash drzewa within-dataset: {evidence['real_within']['tree_sha256']}.", small),
    ])
    document.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
        canvasmaker=invariant_canvas,
    )


def main() -> int:
    gate_b = _read(ROOT / "results/full630_primary/gate_b_summary.json")
    gate_c = _read(ROOT / "results/real_lung_primary/gate_c_summary.json")
    within = _read(ROOT / "results/real_within_primary/within_summary.json")
    evidence = _read(DOCS / "evidence/PILOT_019_VALIDATION.json")
    if evidence.get("all_integrity_checks_passed") is not True:
        raise ValueError("PILOT-020 is blocked until PILOT-019 passes")
    table_paths = _tables(gate_b, gate_c, within)
    figure_paths = _make_figures(gate_b, gate_c, within)
    markdown_path = DOCS / "PILOT_FINAL_REPORT.md"
    markdown_path.write_text(_markdown(gate_b, gate_c, within, evidence), encoding="utf-8")
    grant_path = DOCS / "SONATA_BIS_PILOT_TEXT_PL.md"
    grant_path.write_text(_grant_text(gate_b, within), encoding="utf-8")
    _pdf(gate_b, gate_c, within, evidence, figure_paths)
    deliverables = table_paths + figure_paths + [markdown_path, grant_path, PDF_OUTPUT]
    record = {
        "schema": "Pilot020Deliverables/v1",
        "status": "COMPLETE",
        "table_count": len(table_paths),
        "figure_count": len(figure_paths),
        "files": {
            str(path.relative_to(ROOT)): {"sha256": _sha(path), "size_bytes": path.stat().st_size}
            for path in sorted(deliverables)
        },
        "scope": {
            "PILOT-016": "NOT_RUN_BLOCKED_BY_GATE_C_STOP",
            "PILOT-017": "NOT_RUN_BLOCKED_BY_GATE_C_STOP",
            "PILOT-018": "NOT_RUN_BLOCKED_BY_GATE_C_STOP",
            "PILOT-019": "VALIDATED",
            "PILOT-020": "COMPLETE",
        },
    }
    atomic_write_canonical_json(DOCS / "evidence/PILOT_020_DELIVERABLES.json", record)
    print(json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
