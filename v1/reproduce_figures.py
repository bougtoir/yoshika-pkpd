#!/usr/bin/env python3
"""Reproduce all manuscript figures using the yoshika PKPD package.

This script generates the six figures presented in the CMPB Update manuscript:
  Fig 1: Three-compartment model diagram (plasma highlighted)
  Fig 2: Bupivacaine 150 mg -- plasma concentration by initial compartment
  Fig 3: All four local anesthetics -- plasma concentration comparison
  Fig 4: Bupivacaine -- effect-site response by initial compartment
  Fig 5: Bupivacaine 150 mg from BPT -- full compartment profile
  Fig 6: Bupivacaine 150 mg -- PK/PD summary table by initial compartment

Requirements:
  pip install yoshika matplotlib pandas

Usage:
  python reproduce_figures.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from yoshika import Simulator, Drug, Compartment
from yoshika.drugs import DrugLibrary
from yoshika.plotting import (
    plot_comparison,
    plot_concentration,
    plot_effect,
    plot_compartment_diagram,
)
from yoshika.simulator import Scenario

OUTPUT_DIR = Path(__file__).resolve().parent / "figures"
OUTPUT_DIR.mkdir(exist_ok=True)

DPI = 300
DRUG = Drug.BUPIVACAINE
DOSE_MG = 150.0
WEIGHT_KG = 70.0


def fig1_compartment_diagram():
    """Fig 1: Three-compartment model with selectable initial compartment."""
    fig, ax = plot_compartment_diagram(initial_compartment="plasma")
    fig.savefig(OUTPUT_DIR / "fig1_compartment_diagram_plasma.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  Fig 1 saved.")


def fig2_bupivacaine_comparison():
    """Fig 2: Bupivacaine 150 mg -- plasma concentration by initial compartment."""
    sim = Simulator(drug=DRUG, dose_mg=DOSE_MG, weight_kg=WEIGHT_KG)
    results = sim.compare()  # Plasma, BRT, BPT
    params = DrugLibrary.get(DRUG)
    fig, ax = plot_comparison(results, drug_params=params)
    fig.savefig(OUTPUT_DIR / "fig2_bupivacaine_comparison.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  Fig 2 saved.")
    return results


def fig3_all_drugs_comparison():
    """Fig 3: Plasma concentration comparison for all four local anesthetics."""
    all_drugs = [Drug.LIDOCAINE, Drug.BUPIVACAINE, Drug.ROPIVACAINE, Drug.LEVOBUPIVACAINE]
    compartments = [Compartment.PLASMA, Compartment.BRT, Compartment.BPT]

    fig, axes = plt.subplots(len(compartments), 1, figsize=(12, 5 * len(compartments)))

    for row, comp in enumerate(compartments):
        ax = axes[row]
        for drug in all_drugs:
            params = DrugLibrary.get(drug)
            sim = Simulator(drug=drug, dose_mg=DOSE_MG, weight_kg=WEIGHT_KG)
            result = sim.run(initial_compartment=comp, label=params.name)
            time_h = result.pk.time / 60.0
            ax.plot(time_h, result.pk.plasma_concentration, linewidth=2, label=params.name)
        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Plasma Concentration (mg/L)")
        ax.set_title(f"Initial compartment: {comp.value}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig3_all_drugs_comparison.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  Fig 3 saved.")


def fig4_bupivacaine_effect():
    """Fig 4: Bupivacaine -- effect-site response by initial compartment."""
    sim = Simulator(drug=DRUG, dose_mg=DOSE_MG, weight_kg=WEIGHT_KG)
    results = sim.compare()
    fig, ax = plot_effect(results)
    fig.savefig(OUTPUT_DIR / "fig4_bupivacaine_effect.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  Fig 4 saved.")


def fig5_bupivacaine_bpt_full():
    """Fig 5: Bupivacaine 150 mg from BPT -- full compartment profile."""
    sim = Simulator(drug=DRUG, dose_mg=DOSE_MG, weight_kg=WEIGHT_KG)
    result = sim.run(initial_compartment=Compartment.BPT, label="Successful block (BPT)")
    params = DrugLibrary.get(DRUG)
    fig, ax = plot_concentration(result, drug_params=params)
    fig.savefig(OUTPUT_DIR / "fig5_bupivacaine_bpt_full.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  Fig 5 saved.")


def fig6_summary_table():
    """Fig 6: Bupivacaine 150 mg -- PK/PD summary by initial compartment."""
    sim = Simulator(drug=DRUG, dose_mg=DOSE_MG, weight_kg=WEIGHT_KG)
    results = sim.compare()
    table = Simulator.summary_table(results)

    # Render summary table as a figure
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.axis("off")

    display_cols = ["label", "dose_mg", "Cmax_plasma_mg_L", "Tmax_plasma_min",
                    "peak_effect_pct", "time_to_peak_effect_min"]
    headers = ["Scenario", "Dose (mg)", "Cmax (mg/L)", "Tmax (min)",
               "Peak Effect (%)", "Time to Peak Effect (min)"]
    available = [c for c in display_cols if c in table.columns]
    header_map = dict(zip(display_cols, headers))

    cell_text = []
    for _, row in table[available].iterrows():
        cell_text.append([f"{row[c]:.2f}" if isinstance(row[c], float) else str(row[c])
                          for c in available])

    tbl = ax.table(
        cellText=cell_text,
        colLabels=[header_map.get(c, c) for c in available],
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.2, 1.5)

    ax.set_title(f"Bupivacaine {DOSE_MG:.0f} mg — PK/PD Summary by Initial Compartment",
                 fontsize=13, pad=20)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig6_summary_table.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  Fig 6 saved.")


def main():
    print(f"Output directory: {OUTPUT_DIR}")
    print("Generating figures...")
    fig1_compartment_diagram()
    fig2_bupivacaine_comparison()
    fig3_all_drugs_comparison()
    fig4_bupivacaine_effect()
    fig5_bupivacaine_bpt_full()
    fig6_summary_table()
    print("Done — all figures saved to", OUTPUT_DIR)


if __name__ == "__main__":
    main()
