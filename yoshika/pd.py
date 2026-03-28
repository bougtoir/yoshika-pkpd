"""Pharmacodynamic models for local anesthetics.

Includes effect-site concentration calculation and Emax/sigmoid Emax
models for predicting nerve block effect intensity.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp


@dataclass
class PDResult:
    """Result of a pharmacodynamic simulation.

    Attributes:
        time: Time points in minutes.
        effect_site_concentration: Effect-site concentration over time (mg/L).
        effect: Drug effect over time (0-100% scale).
    """

    time: NDArray[np.float64]
    effect_site_concentration: NDArray[np.float64]
    effect: NDArray[np.float64]

    @property
    def peak_effect(self) -> float:
        """Maximum drug effect (%)."""
        return float(np.max(self.effect))

    @property
    def time_to_peak_effect(self) -> float:
        """Time to maximum drug effect (min)."""
        idx = int(np.argmax(self.effect))
        return float(self.time[idx])

    @property
    def onset_time(self, threshold: float = 50.0) -> float:
        """Time to reach threshold effect level (min).

        Args:
            threshold: Effect threshold in % (default: 50%).

        Returns:
            Time in minutes to first reach the threshold.
            Returns infinity if threshold is never reached.
        """
        above = np.where(self.effect >= threshold)[0]
        if len(above) == 0:
            return float("inf")
        return float(self.time[above[0]])

    @property
    def duration_above_threshold(self, threshold: float = 50.0) -> float:
        """Duration of effect above threshold (min).

        Args:
            threshold: Effect threshold in % (default: 50%).

        Returns:
            Duration in minutes where effect exceeds threshold.
        """
        above = self.effect >= threshold
        if not np.any(above):
            return 0.0
        dt = np.diff(self.time)
        return float(np.sum(dt[above[:-1]]))


class PDModel(ABC):
    """Abstract base class for pharmacodynamic models."""

    @abstractmethod
    def compute_effect(self, concentration: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute drug effect from concentration.

        Args:
            concentration: Drug concentration array (mg/L).

        Returns:
            Effect array (0-100% scale).
        """


class EmaxModel(PDModel):
    """Simple Emax pharmacodynamic model.

    Effect = Emax * C / (EC50 + C)

    Attributes:
        emax: Maximum achievable effect (%, default 100).
        ec50: Concentration for 50% of maximum effect (mg/L).
    """

    def __init__(self, ec50: float, emax: float = 100.0) -> None:
        self.ec50 = ec50
        self.emax = emax

    def compute_effect(self, concentration: NDArray[np.float64]) -> NDArray[np.float64]:
        c = np.maximum(concentration, 0.0)
        return self.emax * c / (self.ec50 + c)


class SigmoidEmaxModel(PDModel):
    """Sigmoid Emax (Hill equation) pharmacodynamic model.

    Effect = Emax * C^gamma / (EC50^gamma + C^gamma)

    Attributes:
        emax: Maximum achievable effect (%, default 100).
        ec50: Concentration for 50% of maximum effect (mg/L).
        gamma: Hill coefficient (steepness of the curve).
    """

    def __init__(self, ec50: float, gamma: float, emax: float = 100.0) -> None:
        self.ec50 = ec50
        self.gamma = gamma
        self.emax = emax

    def compute_effect(self, concentration: NDArray[np.float64]) -> NDArray[np.float64]:
        c = np.maximum(concentration, 0.0)
        c_gamma = np.power(c, self.gamma)
        ec50_gamma = self.ec50 ** self.gamma
        return self.emax * c_gamma / (ec50_gamma + c_gamma)


class EffectSiteModel:
    """Effect-site compartment model.

    Computes the effect-site concentration from plasma concentration
    using a first-order equilibration model:

        dCe/dt = ke0 * (Cp - Ce)

    where Ce is effect-site concentration, Cp is plasma concentration,
    and ke0 is the equilibration rate constant.
    """

    def __init__(self, ke0: float) -> None:
        """Initialize effect-site model.

        Args:
            ke0: Effect-site equilibration rate constant (1/min).
        """
        if ke0 <= 0:
            raise ValueError("ke0 must be positive.")
        self.ke0 = ke0

    def compute(
        self,
        time: NDArray[np.float64],
        plasma_concentration: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Compute effect-site concentration over time.

        Uses linear interpolation of plasma concentration to drive the
        effect-site ODE.

        Args:
            time: Time points (min).
            plasma_concentration: Plasma concentration at each time point (mg/L).

        Returns:
            Effect-site concentration array (mg/L).
        """

        def ode(t: float, y: NDArray[np.float64]) -> list[float]:
            cp = float(np.interp(t, time, plasma_concentration))
            return [self.ke0 * (cp - y[0])]

        sol = solve_ivp(
            ode,
            (float(time[0]), float(time[-1])),
            [0.0],
            t_eval=time,
            method="RK45",
            max_step=1.0,
            rtol=1e-8,
            atol=1e-10,
        )

        if not sol.success:
            raise RuntimeError(f"Effect-site ODE solver failed: {sol.message}")

        return sol.y[0]

    def compute_full(
        self,
        time: NDArray[np.float64],
        plasma_concentration: NDArray[np.float64],
        pd_model: PDModel,
    ) -> PDResult:
        """Compute effect-site concentration and drug effect.

        Args:
            time: Time points (min).
            plasma_concentration: Plasma concentration at each time point (mg/L).
            pd_model: PD model to compute effect from effect-site concentration.

        Returns:
            PDResult with effect-site concentration and effect.
        """
        ce = self.compute(time, plasma_concentration)
        effect = pd_model.compute_effect(ce)
        return PDResult(
            time=time,
            effect_site_concentration=ce,
            effect=effect,
        )
