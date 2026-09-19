"""Three-compartment pharmacokinetic model with selectable initial compartment.

This module implements the core ODE system for a 3-compartment PK model
(plasma, vessel-rich tissue, vessel-poor tissue) with an optional depot
(absorption) compartment. The key feature is the ability to select which
compartment receives the initial drug dose, enabling simulation of different
regional anesthesia scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from yoshika.compartments import Compartment, CompartmentModel
from yoshika.drugs import Drug, DrugLibrary, DrugParameters


@dataclass
class PKResult:
    """Result of a pharmacokinetic simulation.

    Attributes:
        time: Time points in minutes.
        amounts: Drug amounts (mg) in each compartment over time.
            Shape (4, n_timepoints): [depot, plasma, brt, bpt].
        concentrations: Drug concentrations (mg/L) in each compartment.
            Shape (4, n_timepoints): [depot(mg), plasma(mg/L), brt(mg/L), bpt(mg/L)].
        model: The CompartmentModel used for simulation.
    """

    time: NDArray[np.float64]
    amounts: NDArray[np.float64]
    concentrations: NDArray[np.float64]
    model: CompartmentModel

    @property
    def plasma_concentration(self) -> NDArray[np.float64]:
        """Plasma concentration over time (mg/L)."""
        return self.concentrations[1]

    @property
    def brt_concentration(self) -> NDArray[np.float64]:
        """Vessel-rich tissue concentration over time (mg/L)."""
        return self.concentrations[2]

    @property
    def bpt_concentration(self) -> NDArray[np.float64]:
        """Vessel-poor tissue concentration over time (mg/L)."""
        return self.concentrations[3]

    @property
    def depot_amount(self) -> NDArray[np.float64]:
        """Drug amount remaining in depot compartment (mg)."""
        return self.amounts[0]

    @property
    def peak_plasma_concentration(self) -> float:
        """Maximum plasma concentration (Cmax, mg/L)."""
        return float(np.max(self.plasma_concentration))

    @property
    def time_to_peak(self) -> float:
        """Time to maximum plasma concentration (Tmax, min)."""
        idx = int(np.argmax(self.plasma_concentration))
        return float(self.time[idx])

    @property
    def total_drug_in_system(self) -> NDArray[np.float64]:
        """Total drug amount remaining in the system over time (mg)."""
        return np.sum(self.amounts, axis=0)


class PKModel:
    """Three-compartment pharmacokinetic model with selectable initial compartment.

    This model solves the following ODE system:

        dA_depot/dt  = -ka * A_depot
        dA_plasma/dt = ka * A_depot - (k10 + k12 + k13) * A_plasma
                       + k21 * A_brt + k31 * A_bpt
        dA_brt/dt    = k12 * A_plasma - k21 * A_brt
        dA_bpt/dt    = k13 * A_plasma - k31 * A_bpt

    where A represents drug amounts (mg) and k are rate constants (1/min).

    The initial compartment determines where the dose is placed at t=0:
      - PLASMA: Traditional IV administration
      - BRT: Failed block (intravascular injection into vascular tissue)
      - BPT: Successful peripheral nerve block
      - DEPOT: Injection site with first-order absorption (also used to
        approximate epidural administration)

    Note on epidural administration:
        Epidural administration can be approximated using the DEPOT
        compartment. The drug injected into the epidural space is absorbed
        into systemic circulation primarily via epidural venous plexus
        uptake, following approximately first-order kinetics. Users can
        adjust ka to match published epidural absorption rates.

    Note on spinal (intrathecal) administration:
        Spinal administration is not modeled. It is predominantly a
        single-shot technique with small doses (e.g., bupivacaine 10-15 mg)
        and involves unique CSF-based pharmacokinetics that differ from
        the peripheral compartment model.
    """

    def __init__(
        self,
        drug: Optional[Drug] = None,
        drug_params: Optional[DrugParameters] = None,
        dose_mg: float = 100.0,
        initial_compartment: Compartment = Compartment.PLASMA,
        weight_kg: float = 70.0,
        ka_override: Optional[float] = None,
    ) -> None:
        """Initialize the PK model.

        Args:
            drug: Drug enum to use parameters from the built-in database.
            drug_params: Custom DrugParameters (takes precedence over drug).
            dose_mg: Total dose in milligrams.
            initial_compartment: Which compartment receives the initial dose.
            weight_kg: Patient weight in kg (for future allometric scaling).
            ka_override: Override the default absorption rate constant (1/min).
                Only used when initial_compartment is DEPOT.

        Raises:
            ValueError: If neither drug nor drug_params is provided.
        """
        if drug_params is not None:
            self._params = drug_params
        elif drug is not None:
            self._params = DrugLibrary.get(drug)
        else:
            raise ValueError("Either 'drug' or 'drug_params' must be provided.")

        self._dose_mg = dose_mg
        self._initial_compartment = initial_compartment
        self._weight_kg = weight_kg

        ka = ka_override if ka_override is not None else self._params.ka_depot
        self._compartment_model = CompartmentModel(
            v1=self._params.v1,
            v2=self._params.v2,
            v3=self._params.v3,
            k10=self._params.k10,
            k12=self._params.k12,
            k21=self._params.k21,
            k13=self._params.k13,
            k31=self._params.k31,
            ka=ka,
            initial_compartment=initial_compartment,
            dose_mg=dose_mg,
        )
        self._compartment_model.validate()

    @property
    def params(self) -> DrugParameters:
        """Drug parameters used in this model."""
        return self._params

    @property
    def compartment_model(self) -> CompartmentModel:
        """The underlying compartment model configuration."""
        return self._compartment_model

    def _ode_system(
        self, t: float, y: NDArray[np.float64]
    ) -> list[float]:
        """ODE system for the 3-compartment model with depot.

        Args:
            t: Current time (unused, autonomous system).
            y: State vector [A_depot, A_plasma, A_brt, A_bpt] in mg.

        Returns:
            Derivatives [dA_depot/dt, dA_plasma/dt, dA_brt/dt, dA_bpt/dt].
        """
        a_depot, a_plasma, a_brt, a_bpt = y
        m = self._compartment_model

        da_depot = -m.ka * a_depot
        da_plasma = (
            m.ka * a_depot
            - (m.k10 + m.k12 + m.k13) * a_plasma
            + m.k21 * a_brt
            + m.k31 * a_bpt
        )
        da_brt = m.k12 * a_plasma - m.k21 * a_brt
        da_bpt = m.k13 * a_plasma - m.k31 * a_bpt

        return [da_depot, da_plasma, da_brt, da_bpt]

    def solve(
        self,
        duration_min: float = 360.0,
        dt: float = 0.1,
        method: str = "RK45",
        max_step: float = 1.0,
    ) -> PKResult:
        """Solve the ODE system and return concentration-time profiles.

        Args:
            duration_min: Simulation duration in minutes.
            dt: Time step for output (minutes).
            method: ODE solver method (default: 'RK45').
            max_step: Maximum internal step size for the solver.

        Returns:
            PKResult with time, amounts, and concentrations.
        """
        y0 = self._compartment_model.get_initial_amounts()
        t_span = (0.0, duration_min)
        t_eval = np.arange(0.0, duration_min + dt, dt)

        sol = solve_ivp(
            self._ode_system,
            t_span,
            y0,
            method=method,
            t_eval=t_eval,
            max_step=max_step,
            rtol=1e-8,
            atol=1e-10,
        )

        if not sol.success:
            raise RuntimeError(f"ODE solver failed: {sol.message}")

        amounts = sol.y  # shape (4, n_timepoints)
        volumes = np.array(
            [1.0, self._compartment_model.v1, self._compartment_model.v2,
             self._compartment_model.v3]
        )
        concentrations = amounts / volumes[:, np.newaxis]

        return PKResult(
            time=sol.t,
            amounts=amounts,
            concentrations=concentrations,
            model=self._compartment_model,
        )

    def solve_with_infusion(
        self,
        infusion_rate_mg_per_min: float,
        infusion_duration_min: float,
        total_duration_min: float = 360.0,
        dt: float = 0.1,
        method: str = "RK45",
    ) -> PKResult:
        """Solve with continuous infusion into the selected compartment.

        Args:
            infusion_rate_mg_per_min: Infusion rate (mg/min).
            infusion_duration_min: Duration of infusion (min).
            total_duration_min: Total simulation duration (min).
            dt: Time step for output (minutes).
            method: ODE solver method.

        Returns:
            PKResult with time, amounts, and concentrations.
        """
        compartment_idx = {
            Compartment.DEPOT: 0,
            Compartment.PLASMA: 1,
            Compartment.BRT: 2,
            Compartment.BPT: 3,
        }
        target_idx = compartment_idx[self._initial_compartment]

        def ode_with_infusion(
            t: float, y: NDArray[np.float64]
        ) -> list[float]:
            dydt = self._ode_system(t, y)
            if t <= infusion_duration_min:
                dydt[target_idx] += infusion_rate_mg_per_min
            return dydt

        y0 = np.zeros(4, dtype=np.float64)
        t_span = (0.0, total_duration_min)
        t_eval = np.arange(0.0, total_duration_min + dt, dt)

        sol = solve_ivp(
            ode_with_infusion,
            t_span,
            y0,
            method=method,
            t_eval=t_eval,
            max_step=1.0,
            rtol=1e-8,
            atol=1e-10,
        )

        if not sol.success:
            raise RuntimeError(f"ODE solver failed: {sol.message}")

        amounts = sol.y
        volumes = np.array(
            [1.0, self._compartment_model.v1, self._compartment_model.v2,
             self._compartment_model.v3]
        )
        concentrations = amounts / volumes[:, np.newaxis]

        return PKResult(
            time=sol.t,
            amounts=amounts,
            concentrations=concentrations,
            model=self._compartment_model,
        )
