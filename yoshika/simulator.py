"""High-level simulation engine for PKPD analysis.

Provides a convenient interface for running single simulations and
multi-scenario comparisons with different initial compartments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from yoshika.compartments import Compartment
from yoshika.drugs import Drug, DrugLibrary, DrugParameters
from yoshika.model import PKModel, PKResult
from yoshika.pd import EffectSiteModel, PDModel, PDResult, SigmoidEmaxModel


@dataclass
class SimulationResult:
    """Combined PK and PD simulation result.

    Attributes:
        pk: Pharmacokinetic result.
        pd: Pharmacodynamic result (None if PD was not computed).
        label: Descriptive label for this simulation scenario.
        drug: Drug used in the simulation.
        dose_mg: Dose administered (mg).
        initial_compartment: Initial compartment for the dose.
    """

    pk: PKResult
    pd: Optional[PDResult]
    label: str
    drug_name: str
    dose_mg: float
    initial_compartment: Compartment

    def summary(self) -> Dict[str, float]:
        """Generate a summary dictionary of key PK/PD metrics.

        Returns:
            Dictionary with Cmax, Tmax, and PD metrics if available.
        """
        result: Dict[str, float] = {
            "dose_mg": self.dose_mg,
            "Cmax_plasma_mg_L": self.pk.peak_plasma_concentration,
            "Tmax_plasma_min": self.pk.time_to_peak,
        }
        if self.pd is not None:
            result["peak_effect_pct"] = self.pd.peak_effect
            result["time_to_peak_effect_min"] = self.pd.time_to_peak_effect
        return result

    def to_dataframe(self) -> pd.DataFrame:
        """Convert time-course data to a pandas DataFrame.

        Returns:
            DataFrame with columns for time, concentrations, and effect.
        """
        data: Dict[str, NDArray[np.float64]] = {
            "time_min": self.pk.time,
            "plasma_mg_L": self.pk.plasma_concentration,
            "brt_mg_L": self.pk.brt_concentration,
            "bpt_mg_L": self.pk.bpt_concentration,
            "depot_mg": self.pk.depot_amount,
        }
        if self.pd is not None:
            data["effect_site_mg_L"] = self.pd.effect_site_concentration
            data["effect_pct"] = self.pd.effect
        df = pd.DataFrame(data)
        df["label"] = self.label
        df["drug"] = self.drug_name
        df["initial_compartment"] = self.initial_compartment.value
        return df


@dataclass
class Scenario:
    """A simulation scenario definition.

    Attributes:
        initial_compartment: Which compartment receives the dose.
        label: Descriptive label.
        dose_mg: Optional dose override.
        ka_override: Optional absorption rate override.
    """

    initial_compartment: Compartment
    label: str
    dose_mg: Optional[float] = None
    ka_override: Optional[float] = None


class Simulator:
    """High-level simulation engine for local anesthetic PKPD.

    Provides methods for single simulation and multi-scenario comparison.

    Example:
        >>> from yoshika import Simulator, Drug, Compartment
        >>> sim = Simulator(drug=Drug.BUPIVACAINE, dose_mg=150, weight_kg=70)
        >>> result = sim.run(initial_compartment=Compartment.BPT)
        >>> print(f"Cmax: {result.pk.peak_plasma_concentration:.2f} mg/L")
    """

    def __init__(
        self,
        drug: Optional[Drug] = None,
        drug_params: Optional[DrugParameters] = None,
        dose_mg: float = 100.0,
        weight_kg: float = 70.0,
        duration_min: float = 360.0,
        compute_pd: bool = True,
    ) -> None:
        """Initialize the simulator.

        Args:
            drug: Drug enum to use from the built-in database.
            drug_params: Custom drug parameters (takes precedence over drug).
            dose_mg: Default dose in milligrams.
            weight_kg: Patient weight in kg.
            duration_min: Default simulation duration in minutes.
            compute_pd: Whether to compute PD (effect) by default.
        """
        if drug_params is not None:
            self._drug_params = drug_params
        elif drug is not None:
            self._drug_params = DrugLibrary.get(drug)
        else:
            raise ValueError("Either 'drug' or 'drug_params' must be provided.")

        self._drug = drug
        self._dose_mg = dose_mg
        self._weight_kg = weight_kg
        self._duration_min = duration_min
        self._compute_pd = compute_pd

    def run(
        self,
        initial_compartment: Compartment = Compartment.PLASMA,
        dose_mg: Optional[float] = None,
        duration_min: Optional[float] = None,
        ka_override: Optional[float] = None,
        label: Optional[str] = None,
        compute_pd: Optional[bool] = None,
    ) -> SimulationResult:
        """Run a single PKPD simulation.

        Args:
            initial_compartment: Which compartment receives the dose.
            dose_mg: Dose override (uses default if None).
            duration_min: Duration override (uses default if None).
            ka_override: Override absorption rate constant.
            label: Descriptive label for this scenario.
            compute_pd: Override default PD computation flag.

        Returns:
            SimulationResult with PK and optional PD data.
        """
        dose = dose_mg if dose_mg is not None else self._dose_mg
        duration = duration_min if duration_min is not None else self._duration_min
        do_pd = compute_pd if compute_pd is not None else self._compute_pd

        if label is None:
            label = f"{self._drug_params.name} {dose}mg -> {initial_compartment.value}"

        pk_model = PKModel(
            drug_params=self._drug_params,
            dose_mg=dose,
            initial_compartment=initial_compartment,
            weight_kg=self._weight_kg,
            ka_override=ka_override,
        )
        pk_result = pk_model.solve(duration_min=duration)

        pd_result: Optional[PDResult] = None
        if do_pd:
            effect_site = EffectSiteModel(ke0=self._drug_params.ke0)
            pd_model: PDModel = SigmoidEmaxModel(
                ec50=self._drug_params.ec50,
                gamma=self._drug_params.gamma,
            )
            pd_result = effect_site.compute_full(
                pk_result.time,
                pk_result.plasma_concentration,
                pd_model,
            )

        return SimulationResult(
            pk=pk_result,
            pd=pd_result,
            label=label,
            drug_name=self._drug_params.name,
            dose_mg=dose,
            initial_compartment=initial_compartment,
        )

    def compare(
        self,
        scenarios: Optional[List[Scenario]] = None,
        duration_min: Optional[float] = None,
    ) -> List[SimulationResult]:
        """Run multiple scenarios for comparison.

        If no scenarios are provided, runs the three standard scenarios:
          1. IV (plasma) - traditional model
          2. Failed block (brt) - intravascular injection
          3. Successful block (bpt) - regional anesthesia

        Args:
            scenarios: List of Scenario objects to simulate.
            duration_min: Duration override for all scenarios.

        Returns:
            List of SimulationResult, one per scenario.
        """
        if scenarios is None:
            scenarios = [
                Scenario(
                    initial_compartment=Compartment.PLASMA,
                    label="IV administration (plasma)",
                ),
                Scenario(
                    initial_compartment=Compartment.BRT,
                    label="Failed block (vessel-rich tissue)",
                ),
                Scenario(
                    initial_compartment=Compartment.BPT,
                    label="Successful block (vessel-poor tissue)",
                ),
            ]

        results: List[SimulationResult] = []
        for scenario in scenarios:
            result = self.run(
                initial_compartment=scenario.initial_compartment,
                dose_mg=scenario.dose_mg,
                duration_min=duration_min,
                ka_override=scenario.ka_override,
                label=scenario.label,
            )
            results.append(result)

        return results

    def compare_drugs(
        self,
        drugs: List[Drug],
        initial_compartment: Compartment = Compartment.PLASMA,
        dose_mg: Optional[float] = None,
        duration_min: Optional[float] = None,
    ) -> List[SimulationResult]:
        """Compare multiple drugs with the same scenario.

        Args:
            drugs: List of Drug enums to compare.
            initial_compartment: Compartment for all drugs.
            dose_mg: Dose for all drugs (uses each drug's default if None).
            duration_min: Simulation duration.

        Returns:
            List of SimulationResult, one per drug.
        """
        results: List[SimulationResult] = []
        for drug in drugs:
            params = DrugLibrary.get(drug)
            sim = Simulator(
                drug_params=params,
                dose_mg=dose_mg if dose_mg is not None else self._dose_mg,
                weight_kg=self._weight_kg,
                duration_min=duration_min if duration_min is not None else self._duration_min,
                compute_pd=self._compute_pd,
            )
            result = sim.run(
                initial_compartment=initial_compartment,
                label=f"{params.name} -> {initial_compartment.value}",
            )
            results.append(result)

        return results

    @staticmethod
    def results_to_dataframe(results: List[SimulationResult]) -> pd.DataFrame:
        """Combine multiple simulation results into a single DataFrame.

        Args:
            results: List of SimulationResult objects.

        Returns:
            Combined DataFrame with all time-course data.
        """
        frames = [r.to_dataframe() for r in results]
        return pd.concat(frames, ignore_index=True)

    @staticmethod
    def summary_table(results: List[SimulationResult]) -> pd.DataFrame:
        """Create a summary comparison table.

        Args:
            results: List of SimulationResult objects.

        Returns:
            DataFrame with one row per scenario and key PK/PD metrics.
        """
        rows = []
        for r in results:
            row = r.summary()
            row["label"] = r.label
            row["drug"] = r.drug_name
            row["initial_compartment"] = r.initial_compartment.value
            rows.append(row)
        return pd.DataFrame(rows)
