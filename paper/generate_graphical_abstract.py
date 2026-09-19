"""Generate the graphical abstract for the Array manuscript.

One-panel visual summary: selectable initial compartment -> divergent predicted
plasma profiles -> external validation against published data.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from yoshika import Compartment, Drug
from yoshika.drugs import DrugLibrary
from yoshika.model import PKModel

OUT = Path(__file__).parent / "figures" / "fig0_graphical_abstract.png"

BLUE = "#1f6fb2"
RED = "#c0392b"
GREEN = "#2e8b57"
GREY = "#555555"


def _profile(compartment: Compartment, dose: float = 150.0):
    params = DrugLibrary.get(Drug.ROPIVACAINE)
    res = PKModel(
        drug_params=params, dose_mg=dose, initial_compartment=compartment
    ).solve(duration_min=180)
    return np.asarray(res.time), np.asarray(res.plasma_concentration)


def main() -> None:
    fig = plt.figure(figsize=(12, 5.0), dpi=300)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.15, 1.0], wspace=0.32)

    # --- Panel 1: the choice -------------------------------------------------
    ax0 = fig.add_subplot(gs[0, 0])
    ax0.axis("off")
    ax0.set_title("Select the initial compartment", fontsize=12, fontweight="bold")
    boxes = [
        ("Plasma\n(intravascular)", RED, 0.78),
        ("Vessel-rich tissue\n(\u201cfailed block\u201d)", "#e08a2e", 0.57),
        ("Vessel-poor tissue\n(\u201csuccessful block\u201d)", GREEN, 0.36),
        ("Depot\n(fascial plane / epidural)", BLUE, 0.15),
    ]
    for label, color, y in boxes:
        box = FancyBboxPatch(
            (0.08, y), 0.84, 0.15,
            boxstyle="round,pad=0.02", linewidth=1.6,
            edgecolor=color, facecolor=color + "22",
        )
        ax0.add_patch(box)
        ax0.text(0.5, y + 0.075, label, ha="center", va="center", fontsize=9.5)
    ax0.text(0.5, 0.02, "Same disposition parameters;\nonly the input differs",
             ha="center", va="center", fontsize=9, style="italic", color=GREY)
    ax0.set_xlim(0, 1)
    ax0.set_ylim(0, 1)

    # --- Panel 2: divergent profiles ----------------------------------------
    ax1 = fig.add_subplot(gs[0, 1])
    t, c = _profile(Compartment.PLASMA)
    ax1.plot(t, c, color=RED, lw=2.2, label="IV-forced (conventional)")
    t, c = _profile(Compartment.DEPOT)
    ax1.plot(t, c, color=BLUE, lw=2.2, label="Depot (fascial plane)")
    t, c = _profile(Compartment.BPT)
    ax1.plot(t, c, color=GREEN, lw=2.2, ls="--", label="Vessel-poor tissue")
    ax1.axhline(2.2, color=GREY, ls=":", lw=1.2)
    ax1.text(178, 2.35, "CNS threshold", ha="right", fontsize=8, color=GREY)
    ax1.set_xlabel("Time (min)", fontsize=10)
    ax1.set_ylabel("Plasma concentration (mg/L)", fontsize=10)
    ax1.set_title("Input route drives peak & timing", fontsize=12, fontweight="bold")
    ax1.set_ylim(0, 16)
    ax1.set_xlim(0, 180)
    ax1.legend(fontsize=8.2, loc="upper right", frameon=False)
    ax1.annotate("~10\u00d7 lower,\ndelayed peak",
                 xy=(20, 4.5), xytext=(70, 9.5), fontsize=9, color=BLUE,
                 arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.4))

    # --- Panel 3: validation -------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 2])
    obs = np.array([2.4, 2.5, 1.1, 0.9, 1.83, 1.79, 1.3, 1.28, 1.28, 2.3])
    pred = np.array([4.69, 5.87, 2.2, 1.28, 1.4, 1.03, 1.3, 1.21, 1.06, 3.7])
    lim = [0.5, 8]
    ax2.plot(lim, lim, color="k", lw=1.2)
    ax2.fill_between(lim, [x / 2 for x in lim], [x * 2 for x in lim],
                     color="0.85", alpha=0.6, zorder=0)
    ax2.scatter(obs, pred, s=55, color=BLUE, edgecolor="k", zorder=3)
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlim(lim)
    ax2.set_ylim(lim)
    ax2.set_xlabel("Observed $C_{max}$ (mg/L)", fontsize=10)
    ax2.set_ylabel("Predicted $C_{max}$ (mg/L)", fontsize=10)
    ax2.set_title("Validated vs published data", fontsize=12, fontweight="bold")
    ax2.text(0.05, 0.93,
             "90% within 2-fold\nGMFE 1.51,  r = 0.81\n(n = 10 studies)",
             transform=ax2.transAxes, fontsize=9.2, va="top",
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=BLUE))

    # connecting arrows
    for x in (0.345, 0.66):
        fig.add_artist(FancyArrowPatch(
            (x, 0.5), (x + 0.02, 0.5), transform=fig.transFigure,
            arrowstyle="-|>", mutation_scale=22, color=GREY, lw=2))

    fig.suptitle(
        "yoshika: selectable initial-compartment simulation for local anesthetics",
        fontsize=13.5, fontweight="bold", y=1.02)
    fig.savefig(OUT, dpi=300, bbox_inches="tight")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
