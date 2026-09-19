"""Utility functions for the yoshika package."""

from __future__ import annotations

from typing import Dict

import numpy as np
from numpy.typing import NDArray

from yoshika.compartments import Compartment


def mg_per_kg_to_mg(dose_mg_per_kg: float, weight_kg: float) -> float:
    """Convert dose from mg/kg to mg.

    Args:
        dose_mg_per_kg: Dose in mg/kg.
        weight_kg: Patient weight in kg.

    Returns:
        Dose in mg.
    """
    return dose_mg_per_kg * weight_kg


def mg_to_mg_per_kg(dose_mg: float, weight_kg: float) -> float:
    """Convert dose from mg to mg/kg.

    Args:
        dose_mg: Dose in mg.
        weight_kg: Patient weight in kg.

    Returns:
        Dose in mg/kg.
    """
    return dose_mg / weight_kg


def concentration_to_free(
    total_concentration: NDArray[np.float64],
    protein_binding: float,
) -> NDArray[np.float64]:
    """Calculate free (unbound) drug concentration.

    Args:
        total_concentration: Total drug concentration (mg/L).
        protein_binding: Fraction bound to plasma proteins (0-1).

    Returns:
        Free drug concentration (mg/L).
    """
    return total_concentration * (1.0 - protein_binding)


def auc_trapezoidal(
    time: NDArray[np.float64],
    concentration: NDArray[np.float64],
) -> float:
    """Calculate AUC using the trapezoidal rule.

    Args:
        time: Time points.
        concentration: Concentration values at each time point.

    Returns:
        Area under the curve (mg*min/L).
    """
    return float(np.trapezoid(concentration, time))


def half_life_terminal(
    time: NDArray[np.float64],
    concentration: NDArray[np.float64],
    tail_fraction: float = 0.3,
) -> float:
    """Estimate terminal elimination half-life.

    Uses log-linear regression on the terminal portion of the
    concentration-time curve.

    Args:
        time: Time points.
        concentration: Concentration values.
        tail_fraction: Fraction of the curve to use for estimation
            (from the end, default 30%).

    Returns:
        Terminal half-life in minutes.
        Returns NaN if estimation fails.
    """
    n = len(concentration)
    start_idx = int(n * (1.0 - tail_fraction))

    tail_time = time[start_idx:]
    tail_conc = concentration[start_idx:]

    # Filter out zero/negative concentrations for log
    mask = tail_conc > 0
    if np.sum(mask) < 2:
        return float("nan")

    log_conc = np.log(tail_conc[mask])
    t_valid = tail_time[mask]

    # Linear regression: log(C) = -lambda * t + intercept
    coeffs = np.polyfit(t_valid, log_conc, 1)
    lam = -coeffs[0]

    if lam <= 0:
        return float("nan")

    return 0.693 / lam  # ln(2) / lambda


def time_above_threshold(
    time: NDArray[np.float64],
    concentration: NDArray[np.float64],
    threshold: float,
) -> float:
    """Calculate time that concentration exceeds a threshold.

    Args:
        time: Time points.
        concentration: Concentration values.
        threshold: Threshold concentration (mg/L).

    Returns:
        Duration above threshold in minutes.
    """
    above = concentration >= threshold
    if not np.any(above):
        return 0.0
    dt = np.diff(time)
    return float(np.sum(dt[above[:-1]]))


def compartment_from_string(name: str) -> Compartment:
    """Convert a string to a Compartment enum.

    Accepts case-insensitive strings: 'plasma', 'brt', 'bpt', 'depot',
    as well as aliases like 'iv', 'central', 'peripheral', etc.

    Args:
        name: Compartment name string.

    Returns:
        Compartment enum member.

    Raises:
        ValueError: If the string doesn't match any compartment.
    """
    aliases: Dict[str, Compartment] = {
        "plasma": Compartment.PLASMA,
        "central": Compartment.PLASMA,
        "v1": Compartment.PLASMA,
        "iv": Compartment.PLASMA,
        "brt": Compartment.BRT,
        "vessel-rich": Compartment.BRT,
        "vessel_rich": Compartment.BRT,
        "v2": Compartment.BRT,
        "bpt": Compartment.BPT,
        "vessel-poor": Compartment.BPT,
        "vessel_poor": Compartment.BPT,
        "v3": Compartment.BPT,
        "depot": Compartment.DEPOT,
        "absorption": Compartment.DEPOT,
        "injection_site": Compartment.DEPOT,
    }
    key = name.lower().strip()
    if key in aliases:
        return aliases[key]
    valid = list(aliases.keys())
    raise ValueError(f"Unknown compartment '{name}'. Valid: {valid}")


def format_pk_summary(
    cmax: float,
    tmax: float,
    auc: float,
    half_life: float,
) -> str:
    """Format PK summary as a readable string.

    Args:
        cmax: Maximum concentration (mg/L).
        tmax: Time to Cmax (min).
        auc: Area under the curve (mg*min/L).
        half_life: Terminal half-life (min).

    Returns:
        Formatted summary string.
    """
    return (
        f"Cmax:      {cmax:.3f} mg/L\n"
        f"Tmax:      {tmax:.1f} min ({tmax / 60:.1f} h)\n"
        f"AUC:       {auc:.1f} mg*min/L ({auc / 60:.1f} mg*h/L)\n"
        f"t1/2 term: {half_life:.1f} min ({half_life / 60:.1f} h)"
    )
