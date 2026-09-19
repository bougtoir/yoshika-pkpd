#!/usr/bin/env python3
"""Safety comparison: yoshika (selectable initial compartment) vs traditional models.

Traditional PK simulators (STANPUMP, Tivatrainer, etc.) are constrained to
model drug entry via the central plasma compartment (V1), equivalent to IV
bolus. For local anesthetic infiltration and fascial plane blocks, this
assumption is incorrect: drug is deposited into tissue, not into plasma.

yoshika's selectable initial compartment allows modelling the actual route:
  - Fascial plane block / infiltration -> Depot (first-order absorption)
  - Successful nerve block -> BPT (vessel-poor tissue)

This script illustrates:
  1. Intravenous-input scenarios produce much higher simulated Cmax values
  2. Intravenous-input scenarios predict Tmax = 0 for non-intravenous examples
  3. Depot/BPT scenarios produce lower, later simulated peaks
  4. Route-aware scenarios generate hypotheses about monitoring windows
     window, which differs from what the IV model predicts

NOTE: Rate constants (k12, k21, k13, k31, k10) are shared across all scenarios.
Only the initial conditions (which compartment receives the dose at t=0) differ.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

# Add parent to path so yoshika is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yoshika import Compartment, Drug  # noqa: E402
from yoshika.drugs import DrugLibrary, DrugParameters  # noqa: E402
from yoshika.model import PKModel, PKResult  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent / "figures"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Clinical scenarios ────────────────────────────────────────────────────
# Fascial plane blocks / infiltration (70 kg adult)
SCENARIOS: Dict[str, Dict] = {
    "Lidocaine 200 mg\n(field block)": {
        "drug": Drug.LIDOCAINE,
        "dose_mg": 200.0,
        "label_short": "Lidocaine\n200 mg",
    },
    "Ropivacaine 150 mg\n(fascial plane block)": {
        "drug": Drug.ROPIVACAINE,
        "dose_mg": 150.0,
        "label_short": "Ropivacaine\n150 mg",
    },
    "Bupivacaine 100 mg\n(fascial plane block)": {
        "drug": Drug.BUPIVACAINE,
        "dose_mg": 100.0,
        "label_short": "Bupivacaine\n100 mg",
    },
    "Bupivacaine 150 mg\n(fascial plane block)": {
        "drug": Drug.BUPIVACAINE,
        "dose_mg": 150.0,
        "label_short": "Bupivacaine\n150 mg",
    },
}

DISCHARGE_TIME_MIN = 120.0  # typical day-surgery discharge: 2 h post-block
LATE_DISCHARGE_MIN = 240.0  # extended monitoring: 4 h

# Colours
C_TRAD = "#d62728"    # red: traditional (IV-forced, V1 start)
C_DEPOT = "#1f77b4"   # blue: fascial plane / depot (yoshika)
C_BPT = "#2ca02c"     # green: successful nerve block (yoshika)
C_DISCHARGE = "#555555"

DURATION_MIN = 480.0  # 8 h simulation


# ── Helper: run a single drug through all scenarios ──────────────────────
def run_scenarios(
    drug: Drug, dose_mg: float, duration: float = DURATION_MIN
) -> Dict[str, Tuple[PKResult, DrugParameters]]:
    """Run traditional (IV) and yoshika (Depot, BPT) scenarios.

    All scenarios share the same rate constants (k12, k21, k13, k31, k10).
    Only the initial conditions differ: which compartment receives the dose.
    """
    params = DrugLibrary.get(drug)
    results: Dict[str, Tuple[PKResult, DrugParameters]] = {}
    for comp, label in [
        (Compartment.PLASMA, "Traditional model (IV-forced, V1)"),
        (Compartment.DEPOT, "yoshika: Fascial plane (Depot)"),
        (Compartment.BPT, "yoshika: Nerve block (BPT)"),
    ]:
        pk = PKModel(
            drug_params=params,
            dose_mg=dose_mg,
            initial_compartment=comp,
        ).solve(duration_min=duration)
        results[label] = (pk, params)
    return results


# ── Figure 7: Plasma conc-time — IV-forced vs fascial plane/BPT ──────────
def fig_safety_panel() -> Figure:
    """4-panel figure: one per clinical scenario.

    Each panel shows:
    - Traditional model (IV-forced): overestimates Cmax, wrong Tmax
    - yoshika Depot (fascial plane): correct absorption-delayed profile
    - yoshika BPT (nerve block): correct tissue-start profile
    - Toxicity thresholds and discharge window
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes_flat = axes.flatten()

    for idx, (title, cfg) in enumerate(SCENARIOS.items()):
        ax: Axes = axes_flat[idx]
        drug = cfg["drug"]
        dose = cfg["dose_mg"]
        results = run_scenarios(drug, dose)
        params = DrugLibrary.get(drug)

        # -- Discharge window shading
        ax.axvspan(
            0, DISCHARGE_TIME_MIN / 60,
            color="#e8f4e8", alpha=0.4, zorder=0,
        )
        ax.axvline(
            DISCHARGE_TIME_MIN / 60, color=C_DISCHARGE,
            linestyle="--", lw=1.2, alpha=0.8,
        )

        # -- Plot curves
        colours = {
            "Traditional model (IV-forced, V1)": C_TRAD,
            "yoshika: Fascial plane (Depot)": C_DEPOT,
            "yoshika: Nerve block (BPT)": C_BPT,
        }
        linestyles = {
            "Traditional model (IV-forced, V1)": "-",
            "yoshika: Fascial plane (Depot)": "-",
            "yoshika: Nerve block (BPT)": "--",
        }
        for label, (pk, _) in results.items():
            t_h = pk.time / 60.0
            cp = pk.plasma_concentration
            color = colours[label]
            ls = linestyles[label]
            ax.plot(t_h, cp, color=color, lw=2, ls=ls, label=label)
            # Cmax marker
            cmax = pk.peak_plasma_concentration
            tmax_h = pk.time_to_peak / 60.0
            ax.plot(tmax_h, cmax, "o", color=color, ms=7, zorder=5)
            ax.annotate(
                f"Cmax={cmax:.2f}\nTmax={pk.time_to_peak:.0f} min",
                xy=(tmax_h, cmax),
                xytext=(12, 8),
                textcoords="offset points",
                fontsize=7,
                color=color,
                arrowprops={"arrowstyle": "->", "color": color, "lw": 0.7},
            )

        # -- Toxicity thresholds
        ax.axhline(
            params.toxic_cns, color="orange", ls="--", lw=1, alpha=0.7,
            label=f"CNS toxicity ({params.toxic_cns} mg/L)",
        )
        ax.axhline(
            params.toxic_cv, color="red", ls="--", lw=1, alpha=0.7,
            label=f"CV toxicity ({params.toxic_cv} mg/L)",
        )

        ax.set_title(title.replace("\n", " "), fontsize=11, fontweight="bold")
        ax.set_xlabel("Time (hours)", fontsize=10)
        ax.set_ylabel("Plasma concentration (mg/L)", fontsize=10)
        ax.set_xlim(0, DURATION_MIN / 60)
        ax.set_ylim(bottom=0)

        # Discharge text (after data so ylim is correct)
        ax.text(
            DISCHARGE_TIME_MIN / 60 + 0.05, ax.get_ylim()[1] * 0.95,
            "Discharge\n(2 h)", fontsize=7, color=C_DISCHARGE, va="top",
        )
        ax.grid(True, alpha=0.25)

        if idx == 0:
            ax.legend(fontsize=7, loc="upper right")

    fig.suptitle(
        "Intravenous-Input vs Route-Aware Scenarios:\n"
        "Plasma Concentration Simulations for Fascial Plane Blocks",
        fontsize=13, fontweight="bold", y=0.99,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    return fig


# ── Figure 8: Tmax bar chart ─────────────────────────────────────────────
def fig_tmax_bars() -> Figure:
    """Bar chart: Tmax from IV-forced vs fascial plane (Depot) vs BPT."""
    labels = []
    tmax_trad: List[float] = []
    tmax_depot: List[float] = []
    tmax_bpt: List[float] = []

    for _title, cfg in SCENARIOS.items():
        drug = cfg["drug"]
        dose = cfg["dose_mg"]
        results = run_scenarios(drug, dose)
        labels.append(cfg["label_short"])

        for lbl, arr in [
            ("Traditional model (IV-forced, V1)", tmax_trad),
            ("yoshika: Fascial plane (Depot)", tmax_depot),
            ("yoshika: Nerve block (BPT)", tmax_bpt),
        ]:
            pk, _ = results[lbl]
            arr.append(pk.time_to_peak)

    x = np.arange(len(labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width, tmax_trad, width,
                   label="Traditional (IV-forced)", color=C_TRAD, alpha=0.85)
    bars2 = ax.bar(x, tmax_depot, width,
                   label="yoshika: Fascial plane (Depot)", color=C_DEPOT, alpha=0.85)
    bars3 = ax.bar(x + width, tmax_bpt, width,
                   label="yoshika: Nerve block (BPT)", color=C_BPT, alpha=0.85)

    # Discharge lines
    ax.axhline(DISCHARGE_TIME_MIN, color=C_DISCHARGE, ls="--", lw=1.5,
               label=f"Typical discharge ({DISCHARGE_TIME_MIN:.0f} min)")
    ax.axhline(LATE_DISCHARGE_MIN, color=C_DISCHARGE, ls=":", lw=1,
               label=f"Extended monitoring ({LATE_DISCHARGE_MIN:.0f} min)")

    # Value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 3,
                    f"{h:.0f}", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("Time to peak plasma concentration, Tmax (min)", fontsize=11)
    ax.set_title(
        "Time to Peak by Initial-Compartment Scenario\n"
        "Intravenous Input Predicts Tmax = 0 for All Simulated Drugs",
        fontsize=13, fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    return fig


# ── Figure 9: Monitoring window timeline ──────────────────────────────────
def fig_monitoring_timeline() -> Figure:
    """Gantt-like timeline: when does Cmax occur relative to discharge?"""
    fig, ax = plt.subplots(figsize=(12, 7))

    y_pos = 0
    y_labels = []
    y_ticks = []
    bar_height = 0.6

    for _title, cfg in SCENARIOS.items():
        drug = cfg["drug"]
        dose = cfg["dose_mg"]
        results = run_scenarios(drug, dose)
        params = DrugLibrary.get(drug)

        scenario_label = cfg["label_short"].replace("\n", " ")

        for comp_label, color, offset in [
            ("Traditional model (IV-forced, V1)", C_TRAD, 0),
            ("yoshika: Fascial plane (Depot)", C_DEPOT, 1),
            ("yoshika: Nerve block (BPT)", C_BPT, 2),
        ]:
            pk, _ = results[comp_label]
            tmax = pk.time_to_peak
            cmax = pk.peak_plasma_concentration
            y = y_pos + offset

            # Monitoring bar (0 to discharge)
            ax.barh(y, DISCHARGE_TIME_MIN, height=bar_height,
                    color="#d0d0d0", edgecolor="#999", lw=0.5, zorder=1)

            # Tmax marker
            ax.plot(tmax, y, "D", color=color, ms=10, zorder=5,
                    markeredgecolor="black", markeredgewidth=0.8)

            # Annotation
            if tmax > DISCHARGE_TIME_MIN:
                ax.annotate(
                    f"Tmax={tmax:.0f} min\n(POST-DISCHARGE)",
                    xy=(tmax, y), xytext=(tmax + 15, y + 0.15),
                    fontsize=7, color="red", fontweight="bold",
                    arrowprops={"arrowstyle": "->", "color": "red", "lw": 0.8},
                )
            else:
                ax.annotate(
                    f"Tmax={tmax:.0f} min",
                    xy=(tmax, y), xytext=(tmax + 15, y + 0.15),
                    fontsize=7, color=color,
                    arrowprops={"arrowstyle": "->", "color": color, "lw": 0.8},
                )

            # Toxicity flag
            if cmax >= params.toxic_cns:
                flag = "OVERESTIMATE" if comp_label.startswith("Traditional") else "CNS risk"
                ax.text(tmax, y - 0.3, flag, fontsize=6,
                        color="orange", ha="center", fontweight="bold")

            short_comp = comp_label.split("(")[0].strip()
            if short_comp.startswith("yoshika:"):
                short_comp = short_comp.replace("yoshika: ", "")
            y_labels.append(f"{scenario_label}\n{short_comp}")
            y_ticks.append(y)

        y_pos += 4

    # Discharge line
    ax.axvline(DISCHARGE_TIME_MIN, color=C_DISCHARGE, ls="--", lw=2, zorder=3)
    ax.text(DISCHARGE_TIME_MIN + 2, y_pos - 1,
            "Typical discharge (2 h)", fontsize=9, color=C_DISCHARGE,
            rotation=90, va="top")

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontsize=7)
    ax.set_xlabel("Time after block (min)", fontsize=11)
    ax.set_title(
        "Monitoring Window by Initial-Compartment Scenario\n"
        "Route-Aware Simulations Place Cmax Later than Intravenous Input",
        fontsize=13, fontweight="bold",
    )
    ax.set_xlim(0, DURATION_MIN)
    ax.grid(True, axis="x", alpha=0.3)

    legend_elements = [
        mpatches.Patch(color="#d0d0d0", edgecolor="#999",
                       label="In-hospital monitoring"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor=C_TRAD,
               ms=10, markeredgecolor="k", label="Traditional (IV-forced)"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor=C_DEPOT,
               ms=10, markeredgecolor="k", label="yoshika: Fascial plane (Depot)"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor=C_BPT,
               ms=10, markeredgecolor="k", label="yoshika: Nerve block (BPT)"),
    ]
    ax.legend(handles=legend_elements, fontsize=8, loc="upper right")
    fig.tight_layout()
    return fig


# ── Figure 10: Cmax comparison ────────────────────────────────────────────
def fig_cmax_toxicity() -> Figure:
    """Cmax: traditional (IV-forced overestimate) vs yoshika (actual route)."""
    labels = []
    cmax_trad: List[float] = []
    cmax_depot: List[float] = []
    cmax_bpt: List[float] = []
    tox_cns_vals: List[float] = []
    tox_cv_vals: List[float] = []

    for _title, cfg in SCENARIOS.items():
        drug = cfg["drug"]
        dose = cfg["dose_mg"]
        results = run_scenarios(drug, dose)
        params = DrugLibrary.get(drug)

        labels.append(cfg["label_short"])
        tox_cns_vals.append(params.toxic_cns)
        tox_cv_vals.append(params.toxic_cv)

        for lbl, arr in [
            ("Traditional model (IV-forced, V1)", cmax_trad),
            ("yoshika: Fascial plane (Depot)", cmax_depot),
            ("yoshika: Nerve block (BPT)", cmax_bpt),
        ]:
            pk, _ = results[lbl]
            arr.append(pk.peak_plasma_concentration)

    x = np.arange(len(labels))
    width = 0.2

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width, cmax_trad, width, label="Traditional (IV-forced)",
           color=C_TRAD, alpha=0.85)
    ax.bar(x, cmax_depot, width, label="yoshika: Fascial plane (Depot)",
           color=C_DEPOT, alpha=0.85)
    ax.bar(x + width, cmax_bpt, width, label="yoshika: Nerve block (BPT)",
           color=C_BPT, alpha=0.85)

    # Toxicity threshold markers
    for i in range(len(labels)):
        ax.plot([i - 0.35, i + 0.35], [tox_cns_vals[i]] * 2,
                "o--", color="orange", lw=1.5, ms=4, alpha=0.8)
        ax.plot([i - 0.35, i + 0.35], [tox_cv_vals[i]] * 2,
                "s--", color="red", lw=1.5, ms=4, alpha=0.8)

    custom = [
        Line2D([0], [0], marker="o", color="orange", ls="--", lw=1.5,
               ms=4, label="CNS toxicity threshold"),
        Line2D([0], [0], marker="s", color="red", ls="--", lw=1.5,
               ms=4, label="CV toxicity threshold"),
    ]
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(handles=handles + custom, fontsize=9, loc="upper right")

    ax.set_ylabel("Peak plasma concentration, Cmax (mg/L)", fontsize=11)
    ax.set_title(
        "Peak Plasma Concentration by Initial-Compartment Scenario\n"
        "Intravenous Input vs Fascial-Plane and Vessel-Poor-Tissue Scenarios",
        fontsize=13, fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    return fig


# ── Summary table data ───────────────────────────────────────────────────
def generate_summary_table() -> str:
    """Generate a markdown summary table of safety-relevant PK metrics."""
    rows: List[str] = []
    header = (
        "| Drug / Dose | Model | Cmax (mg/L) | Tmax (min) | "
        "CNS threshold (mg/L) | CV threshold (mg/L) | "
        "Cmax > CNS? | Tmax > Discharge? |"
    )
    sep = "|" + "|".join(["---"] * 8) + "|"
    rows.append(header)
    rows.append(sep)

    for _title, cfg in SCENARIOS.items():
        drug = cfg["drug"]
        dose = cfg["dose_mg"]
        results = run_scenarios(drug, dose)
        params = DrugLibrary.get(drug)
        drug_label = cfg["label_short"].replace("\n", " ")

        for comp_label in [
            "Traditional model (IV-forced, V1)",
            "yoshika: Fascial plane (Depot)",
            "yoshika: Nerve block (BPT)",
        ]:
            pk, _ = results[comp_label]
            cmax = pk.peak_plasma_concentration
            tmax = pk.time_to_peak
            cns_flag = "Yes" if cmax >= params.toxic_cns else "No"
            discharge_flag = "Yes" if tmax > DISCHARGE_TIME_MIN else "No"
            short = comp_label
            if short.startswith("Traditional"):
                short = "Traditional (IV-forced)"
            elif short.startswith("yoshika: Fascial"):
                short = "Fascial plane (Depot)"
            elif short.startswith("yoshika: Nerve"):
                short = "Nerve block (BPT)"
            row = (
                f"| {drug_label} | {short} | {cmax:.2f} | {tmax:.0f} | "
                f"{params.toxic_cns} | {params.toxic_cv} | "
                f"{cns_flag} | {discharge_flag} |"
            )
            rows.append(row)

    return "\n".join(rows)


# ── Figure: summary table as image ───────────────────────────────────────
def fig_summary_table_image() -> Figure:
    """Render the summary table as a publication-quality figure."""
    cell_data = []
    col_labels = [
        "Drug / Dose", "Model", "Cmax\n(mg/L)", "Tmax\n(min)",
        "CNS\nthreshold", "CV\nthreshold", "Cmax >\nCNS?",
        "Tmax >\nDischarge?",
    ]

    cell_colors = []

    for _title, cfg in SCENARIOS.items():
        drug = cfg["drug"]
        dose = cfg["dose_mg"]
        results = run_scenarios(drug, dose)
        params = DrugLibrary.get(drug)
        drug_label = cfg["label_short"].replace("\n", " ")

        for comp_label, bg in [
            ("Traditional model (IV-forced, V1)", "#ffe0e0"),
            ("yoshika: Fascial plane (Depot)", "#e0e8ff"),
            ("yoshika: Nerve block (BPT)", "#e0ffe0"),
        ]:
            pk, _ = results[comp_label]
            cmax = pk.peak_plasma_concentration
            tmax = pk.time_to_peak
            cns_flag = "Yes" if cmax >= params.toxic_cns else "No"
            discharge_flag = "Yes" if tmax > DISCHARGE_TIME_MIN else "No"
            short = comp_label
            if short.startswith("Traditional"):
                short = "Traditional (IV)"
            elif short.startswith("yoshika: Fascial"):
                short = "Fascial plane"
            elif short.startswith("yoshika: Nerve"):
                short = "Nerve block"

            cns_color = "#ff6666" if cns_flag == "Yes" else "#88cc88"
            discharge_color = "#ff6666" if discharge_flag == "Yes" else "#88cc88"

            row = [
                drug_label, short, f"{cmax:.2f}", f"{tmax:.0f}",
                f"{params.toxic_cns}", f"{params.toxic_cv}",
                cns_flag, discharge_flag,
            ]
            cell_data.append(row)
            cell_colors.append(
                [bg, bg, bg, bg, bg, bg, cns_color, discharge_color]
            )

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.axis("off")
    table = ax.table(
        cellText=cell_data,
        colLabels=col_labels,
        cellColours=cell_colors,
        colColours=["#cccccc"] * 8,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.6)
    ax.set_title(
        "Scenario Comparison of Simulated Cmax and Tmax\n"
        "Rate Constants Shared; Only Initial Compartment Differs",
        fontsize=13, fontweight="bold", pad=20,
    )
    fig.tight_layout()
    return fig


# ── Main ──────────────────────────────────────────────────────────────────
def main() -> None:
    print("Generating safety comparison figures...")
    print("  NOTE: Rate constants (k12, k21, k13, k31, k10) are shared")
    print("  across all scenarios. Only the initial compartment differs.\n")

    fig7 = fig_safety_panel()
    fig7.savefig(OUTPUT_DIR / "fig7_safety_panel.png", dpi=300,
                 bbox_inches="tight")
    print("  fig7_safety_panel.png")
    plt.close(fig7)

    fig8 = fig_tmax_bars()
    fig8.savefig(OUTPUT_DIR / "fig8_tmax_comparison.png", dpi=300,
                 bbox_inches="tight")
    print("  fig8_tmax_comparison.png")
    plt.close(fig8)

    fig9 = fig_monitoring_timeline()
    fig9.savefig(OUTPUT_DIR / "fig9_monitoring_timeline.png", dpi=300,
                 bbox_inches="tight")
    print("  fig9_monitoring_timeline.png")
    plt.close(fig9)

    fig10 = fig_cmax_toxicity()
    fig10.savefig(OUTPUT_DIR / "fig10_cmax_toxicity.png", dpi=300,
                  bbox_inches="tight")
    print("  fig10_cmax_toxicity.png")
    plt.close(fig10)

    fig11 = fig_summary_table_image()
    fig11.savefig(OUTPUT_DIR / "fig11_safety_summary_table.png", dpi=300,
                  bbox_inches="tight")
    print("  fig11_safety_summary_table.png")
    plt.close(fig11)

    print("\nSummary table (Markdown):")
    print(generate_summary_table())

    # Print rate constant info
    print("\n--- Rate constants used (shared across all scenarios) ---")
    for _title, cfg in SCENARIOS.items():
        drug = cfg["drug"]
        params = DrugLibrary.get(drug)
        print(f"\n{params.name}:")
        print(f"  k10={params.k10:.4f}, k12={params.k12:.4f}, "
              f"k21={params.k21:.4f}, k13={params.k13:.4f}, k31={params.k31:.4f}")
        print(f"  V1={params.v1}, V2={params.v2}, V3={params.v3}")
        print(f"  ka_depot={params.ka_depot}")

    print("\nDone.")


if __name__ == "__main__":
    main()
