"""Compartment definitions and initial condition configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

import numpy as np
from numpy.typing import NDArray


class Compartment(Enum):
    """Available compartments in the PK model.

    Attributes:
        PLASMA: Central compartment (V1) - traditional IV administration site.
        BRT: Vessel-rich tissue compartment (V2) - rapid equilibrium tissue.
            Drug enters here in failed blocks (e.g., intravascular injection).
        BPT: Vessel-poor tissue compartment (V3) - slow equilibrium tissue.
            Drug enters here in successful regional blocks.
        DEPOT: Absorption compartment for first-order absorption kinetics.
            Models the injection site before drug enters the systemic circulation.
    """

    PLASMA = "plasma"
    BRT = "brt"
    BPT = "bpt"
    DEPOT = "depot"


@dataclass
class CompartmentModel:
    """Configuration for a multi-compartment pharmacokinetic model.

    This class holds the volumes, rate constants, and initial conditions
    for a 3-compartment model with optional depot (absorption) compartment.

    Attributes:
        v1: Volume of central compartment (plasma) in liters.
        v2: Volume of vessel-rich tissue compartment in liters.
        v3: Volume of vessel-poor tissue compartment in liters.
        k10: Elimination rate constant from plasma (1/min).
        k12: Transfer rate constant from plasma to brt (1/min).
        k21: Transfer rate constant from brt to plasma (1/min).
        k13: Transfer rate constant from plasma to bpt (1/min).
        k31: Transfer rate constant from bpt to plasma (1/min).
        ka: Absorption rate constant from depot compartment (1/min).
            Only used when initial_compartment is DEPOT.
        initial_compartment: Which compartment receives the initial dose.
        dose_mg: Total dose administered in milligrams.
    """

    v1: float
    v2: float
    v3: float
    k10: float
    k12: float
    k21: float
    k13: float
    k31: float
    ka: float = 0.0
    initial_compartment: Compartment = Compartment.PLASMA
    dose_mg: float = 0.0
    _custom_initial: Optional[Dict[Compartment, float]] = field(
        default=None, repr=False
    )

    def get_initial_amounts(self) -> NDArray[np.float64]:
        """Calculate initial drug amounts (mg) in each compartment.

        Returns:
            Array of shape (4,) with amounts in [depot, plasma, brt, bpt].
            The dose is placed entirely in the selected initial compartment.
        """
        if self._custom_initial is not None:
            return np.array(
                [
                    self._custom_initial.get(Compartment.DEPOT, 0.0),
                    self._custom_initial.get(Compartment.PLASMA, 0.0),
                    self._custom_initial.get(Compartment.BRT, 0.0),
                    self._custom_initial.get(Compartment.BPT, 0.0),
                ],
                dtype=np.float64,
            )

        amounts = np.zeros(4, dtype=np.float64)
        compartment_index = {
            Compartment.DEPOT: 0,
            Compartment.PLASMA: 1,
            Compartment.BRT: 2,
            Compartment.BPT: 3,
        }
        idx = compartment_index[self.initial_compartment]
        amounts[idx] = self.dose_mg
        return amounts

    def get_initial_concentrations(self) -> NDArray[np.float64]:
        """Calculate initial drug concentrations (mg/L) in each compartment.

        Returns:
            Array of shape (4,) with concentrations in
            [depot (amount), plasma (mg/L), brt (mg/L), bpt (mg/L)].
            Note: depot returns amount (mg) since it has no defined volume.
        """
        amounts = self.get_initial_amounts()
        volumes = np.array([1.0, self.v1, self.v2, self.v3], dtype=np.float64)
        return amounts / volumes

    @property
    def clearance(self) -> float:
        """Total systemic clearance (L/min)."""
        return self.k10 * self.v1

    @property
    def intercompartmental_clearance_brt(self) -> float:
        """Intercompartmental clearance between plasma and brt (L/min)."""
        return self.k12 * self.v1

    @property
    def intercompartmental_clearance_bpt(self) -> float:
        """Intercompartmental clearance between plasma and bpt (L/min)."""
        return self.k13 * self.v1

    def set_custom_initial(self, amounts: Dict[Compartment, float]) -> None:
        """Set custom initial amounts for advanced scenarios.

        Args:
            amounts: Dictionary mapping compartments to initial amounts (mg).
        """
        self._custom_initial = amounts

    def clear_custom_initial(self) -> None:
        """Clear custom initial conditions and revert to standard behavior."""
        self._custom_initial = None

    def validate(self) -> None:
        """Validate model parameters.

        Raises:
            ValueError: If any parameter is invalid.
        """
        if self.v1 <= 0 or self.v2 <= 0 or self.v3 <= 0:
            raise ValueError("All compartment volumes must be positive.")
        if self.k10 < 0 or self.k12 < 0 or self.k21 < 0:
            raise ValueError("Rate constants must be non-negative.")
        if self.k13 < 0 or self.k31 < 0:
            raise ValueError("Rate constants must be non-negative.")
        if self.initial_compartment == Compartment.DEPOT and self.ka <= 0:
            raise ValueError(
                "Absorption rate constant (ka) must be positive "
                "when using DEPOT compartment."
            )
        if self.dose_mg < 0:
            raise ValueError("Dose must be non-negative.")
