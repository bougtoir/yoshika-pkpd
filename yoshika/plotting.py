"""Visualization utilities for PKPD simulation results.

Provides publication-quality figures for concentration-time curves,
toxicity thresholds, multi-scenario comparisons, and PD effect plots.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from yoshika.drugs import DrugParameters
from yoshika.simulator import SimulationResult

# Publication-quality style defaults
_COLORS = [
    "#1f77b4",  # blue
    "#d62728",  # red
    "#2ca02c",  # green
    "#ff7f0e",  # orange
    "#9467bd",  # purple
    "#8c564b",  # brown
]

_COMPARTMENT_LABELS = {
    "plasma": "Plasma (V1)",
    "brt": "Vessel-rich tissue (V2)",
    "bpt": "Vessel-poor tissue (V3)",
    "depot": "Depot (injection site)",
}


def plot_concentration(
    result: SimulationResult,
    show_toxicity: bool = True,
    drug_params: Optional[DrugParameters] = None,
    figsize: Tuple[float, float] = (10, 6),
    title: Optional[str] = None,
) -> Tuple[Figure, Axes]:
    """Plot concentration-time curves for all compartments.

    Args:
        result: SimulationResult to plot.
        show_toxicity: Whether to show toxicity threshold lines.
        drug_params: Drug parameters for toxicity thresholds.
            If None, thresholds are not shown.
        figsize: Figure size (width, height) in inches.
        title: Custom title. If None, auto-generated.

    Returns:
        Tuple of (Figure, Axes).
    """
    fig, ax = plt.subplots(figsize=figsize)

    time_hours = result.pk.time / 60.0

    ax.plot(
        time_hours, result.pk.plasma_concentration,
        color=_COLORS[0], linewidth=2, label="Plasma",
    )
    ax.plot(
        time_hours, result.pk.brt_concentration,
        color=_COLORS[1], linewidth=1.5, linestyle="--", label="Vessel-rich tissue",
    )
    ax.plot(
        time_hours, result.pk.bpt_concentration,
        color=_COLORS[2], linewidth=1.5, linestyle=":", label="Vessel-poor tissue",
    )

    if result.pd is not None:
        ax.plot(
            time_hours, result.pd.effect_site_concentration,
            color=_COLORS[3], linewidth=1.5, linestyle="-.",
            label="Effect site",
        )

    if show_toxicity and drug_params is not None:
        ax.axhline(
            y=drug_params.toxic_cns, color="orange", linestyle="--",
            linewidth=1, alpha=0.8, label=f"CNS toxicity ({drug_params.toxic_cns} mg/L)",
        )
        ax.axhline(
            y=drug_params.toxic_cv, color="red", linestyle="--",
            linewidth=1, alpha=0.8, label=f"CV toxicity ({drug_params.toxic_cv} mg/L)",
        )

    ax.set_xlabel("Time (hours)", fontsize=12)
    ax.set_ylabel("Concentration (mg/L)", fontsize=12)

    if title is None:
        title = f"{result.drug_name} {result.dose_mg}mg — {result.label}"
    ax.set_title(title, fontsize=14)

    ax.legend(fontsize=10, loc="upper right")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    fig.tight_layout()

    return fig, ax


def plot_comparison(
    results: List[SimulationResult],
    compartment: str = "plasma",
    show_toxicity: bool = True,
    drug_params: Optional[DrugParameters] = None,
    figsize: Tuple[float, float] = (12, 7),
    title: Optional[str] = None,
) -> Tuple[Figure, Axes]:
    """Plot plasma concentration comparison across scenarios.

    Args:
        results: List of SimulationResult to compare.
        compartment: Which compartment to plot ('plasma', 'brt', 'bpt').
        show_toxicity: Whether to show toxicity threshold lines.
        drug_params: Drug parameters for toxicity thresholds.
        figsize: Figure size.
        title: Custom title.

    Returns:
        Tuple of (Figure, Axes).
    """
    fig, ax = plt.subplots(figsize=figsize)

    for i, result in enumerate(results):
        time_hours = result.pk.time / 60.0
        color = _COLORS[i % len(_COLORS)]

        if compartment == "plasma":
            concentration = result.pk.plasma_concentration
        elif compartment == "brt":
            concentration = result.pk.brt_concentration
        elif compartment == "bpt":
            concentration = result.pk.bpt_concentration
        else:
            raise ValueError(f"Unknown compartment: {compartment}")

        ax.plot(
            time_hours, concentration,
            color=color, linewidth=2, label=result.label,
        )

        # Mark Cmax
        if compartment == "plasma":
            cmax = result.pk.peak_plasma_concentration
            tmax = result.pk.time_to_peak / 60.0
            ax.plot(tmax, cmax, "o", color=color, markersize=8, zorder=5)
            ax.annotate(
                f"Cmax={cmax:.2f}",
                xy=(tmax, cmax),
                xytext=(10, 10),
                textcoords="offset points",
                fontsize=8,
                color=color,
                arrowprops={"arrowstyle": "->", "color": color, "lw": 0.8},
            )

    if show_toxicity and drug_params is not None:
        ax.axhline(
            y=drug_params.toxic_cns, color="orange", linestyle="--",
            linewidth=1.5, alpha=0.8,
            label=f"CNS toxicity ({drug_params.toxic_cns} mg/L)",
        )
        ax.axhline(
            y=drug_params.toxic_cv, color="red", linestyle="--",
            linewidth=1.5, alpha=0.8,
            label=f"CV toxicity ({drug_params.toxic_cv} mg/L)",
        )

    compartment_label = _COMPARTMENT_LABELS.get(compartment, compartment)
    ax.set_xlabel("Time (hours)", fontsize=12)
    ax.set_ylabel(f"{compartment_label} Concentration (mg/L)", fontsize=12)

    if title is None:
        drug_name = results[0].drug_name if results else "Drug"
        title = (
            f"{drug_name} — {compartment_label} Concentration\n"
            f"by Initial Compartment"
        )
    ax.set_title(title, fontsize=14)

    ax.legend(fontsize=10, loc="upper right")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    fig.tight_layout()

    return fig, ax


def plot_effect(
    results: List[SimulationResult],
    figsize: Tuple[float, float] = (12, 7),
    title: Optional[str] = None,
) -> Tuple[Figure, Axes]:
    """Plot drug effect comparison across scenarios.

    Args:
        results: List of SimulationResult with PD data.
        figsize: Figure size.
        title: Custom title.

    Returns:
        Tuple of (Figure, Axes).
    """
    fig, ax = plt.subplots(figsize=figsize)

    for i, result in enumerate(results):
        if result.pd is None:
            continue

        time_hours = result.pk.time / 60.0
        color = _COLORS[i % len(_COLORS)]

        ax.plot(
            time_hours, result.pd.effect,
            color=color, linewidth=2, label=result.label,
        )

    ax.set_xlabel("Time (hours)", fontsize=12)
    ax.set_ylabel("Effect (%)", fontsize=12)

    if title is None:
        drug_name = results[0].drug_name if results else "Drug"
        title = f"{drug_name} — Effect-site Response by Initial Compartment"
    ax.set_title(title, fontsize=14)

    ax.legend(fontsize=10, loc="upper right")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 105)
    fig.tight_layout()

    return fig, ax


def plot_compartment_diagram(
    initial_compartment: str = "plasma",
    figsize: Tuple[float, float] = (10, 6),
) -> Tuple[Figure, Axes]:
    """Draw a schematic compartment model diagram.

    Shows the 3-compartment model with depot and highlights
    the selected initial compartment.

    Args:
        initial_compartment: Which compartment to highlight
            ('plasma', 'brt', 'bpt', 'depot').
        figsize: Figure size.

    Returns:
        Tuple of (Figure, Axes).
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.set_aspect("equal")
    ax.axis("off")

    # Box definitions: (x_center, y_center, width, height, label, key)
    boxes = [
        (2.5, 3.5, 2.0, 1.5, "DEPOT\n(injection site)", "depot"),
        (5.5, 5.0, 2.5, 1.5, "PLASMA (V1)\n(central)", "plasma"),
        (8.5, 3.0, 2.0, 1.5, "BRT (V2)\n(vessel-rich)", "brt"),
        (5.5, 1.0, 2.5, 1.5, "BPT (V3)\n(vessel-poor)", "bpt"),
    ]

    for x, y, w, h, label, key in boxes:
        color = "#FFD700" if key == initial_compartment else "#E8E8E8"
        edge_color = "#B8860B" if key == initial_compartment else "#666666"
        lw = 3 if key == initial_compartment else 1.5

        rect = plt.Rectangle(
            (x - w / 2, y - h / 2), w, h,
            facecolor=color, edgecolor=edge_color,
            linewidth=lw, zorder=2,
        )
        ax.add_patch(rect)
        ax.text(
            x, y, label, ha="center", va="center",
            fontsize=9, fontweight="bold" if key == initial_compartment else "normal",
            zorder=3,
        )

    # Arrows
    arrow_style = dict(
        arrowstyle="<->", color="#333333", lw=1.5,
        connectionstyle="arc3,rad=0",
    )
    # depot -> plasma
    ax.annotate(
        "", xy=(4.25, 4.5), xytext=(3.5, 4.0),
        arrowprops=dict(arrowstyle="->", color="#333333", lw=1.5),
    )
    ax.text(3.6, 4.5, "ka", fontsize=9, color="#333333")

    # plasma <-> brt
    ax.annotate("", xy=(7.5, 4.0), xytext=(6.75, 4.75), arrowprops=arrow_style)
    ax.text(7.3, 4.6, "k12/k21", fontsize=8, color="#333333")

    # plasma <-> bpt
    ax.annotate("", xy=(5.5, 1.75), xytext=(5.5, 4.25), arrowprops=arrow_style)
    ax.text(5.7, 3.0, "k13/k31", fontsize=8, color="#333333")

    # plasma -> elimination
    ax.annotate(
        "", xy=(4.0, 5.5), xytext=(4.25, 5.2),
        arrowprops=dict(arrowstyle="->", color="red", lw=1.5),
    )
    ax.text(3.3, 5.6, "k10\n(elimination)", fontsize=8, color="red")

    # Title
    ax.text(
        5.0, 6.8,
        f"3-Compartment Model — Initial: {initial_compartment.upper()}",
        ha="center", va="center", fontsize=13, fontweight="bold",
    )

    fig.tight_layout()
    return fig, ax
