"""Tests for the PK model."""

import numpy as np
import pytest

from yoshika.compartments import Compartment
from yoshika.drugs import Drug
from yoshika.model import PKModel, PKResult


class TestPKModel:
    def test_init_with_drug(self):
        model = PKModel(drug=Drug.BUPIVACAINE, dose_mg=150)
        assert model.params.name == "Bupivacaine"

    def test_init_requires_drug_or_params(self):
        with pytest.raises(ValueError, match="Either"):
            PKModel(dose_mg=100)

    def test_solve_plasma_start(self):
        model = PKModel(
            drug=Drug.BUPIVACAINE,
            dose_mg=150,
            initial_compartment=Compartment.PLASMA,
        )
        result = model.solve(duration_min=60)

        assert isinstance(result, PKResult)
        assert len(result.time) > 0
        assert result.time[0] == 0.0
        assert result.time[-1] == pytest.approx(60.0, abs=0.2)

        # Plasma concentration should start high and decrease for IV
        assert result.plasma_concentration[0] > 0
        assert result.plasma_concentration[-1] < result.plasma_concentration[0]

    def test_solve_bpt_start(self):
        model = PKModel(
            drug=Drug.BUPIVACAINE,
            dose_mg=150,
            initial_compartment=Compartment.BPT,
        )
        result = model.solve(duration_min=120)

        # bpt starts with drug, plasma starts at 0
        assert result.bpt_concentration[0] > 0
        assert result.plasma_concentration[0] == 0.0

        # Plasma concentration should rise then fall
        assert result.peak_plasma_concentration > 0
        assert result.time_to_peak > 0

    def test_solve_brt_start(self):
        model = PKModel(
            drug=Drug.BUPIVACAINE,
            dose_mg=150,
            initial_compartment=Compartment.BRT,
        )
        result = model.solve(duration_min=120)

        assert result.brt_concentration[0] > 0
        assert result.plasma_concentration[0] == 0.0

    def test_solve_depot_start(self):
        model = PKModel(
            drug=Drug.BUPIVACAINE,
            dose_mg=150,
            initial_compartment=Compartment.DEPOT,
        )
        result = model.solve(duration_min=120)

        assert result.depot_amount[0] == 150.0
        assert result.plasma_concentration[0] == 0.0
        # Depot amount should decrease over time
        assert result.depot_amount[-1] < result.depot_amount[0]

    def test_mass_balance(self):
        """Total drug in system should not exceed initial dose (accounting for elimination)."""
        model = PKModel(
            drug=Drug.LIDOCAINE,
            dose_mg=200,
            initial_compartment=Compartment.PLASMA,
        )
        result = model.solve(duration_min=60)

        # At t=0, total = dose
        assert result.total_drug_in_system[0] == pytest.approx(200.0, abs=0.1)
        # Total should decrease over time (due to elimination)
        assert result.total_drug_in_system[-1] < result.total_drug_in_system[0]

    def test_different_compartments_different_profiles(self):
        """Different initial compartments should produce different Cmax and Tmax."""
        results = {}
        for cpt in [Compartment.PLASMA, Compartment.BRT, Compartment.BPT]:
            model = PKModel(
                drug=Drug.BUPIVACAINE,
                dose_mg=150,
                initial_compartment=cpt,
            )
            results[cpt] = model.solve(duration_min=360)

        # IV (plasma) should have highest Cmax
        assert (
            results[Compartment.PLASMA].peak_plasma_concentration
            > results[Compartment.BPT].peak_plasma_concentration
        )

        # BPT should have later Tmax than plasma
        assert (
            results[Compartment.BPT].time_to_peak
            > results[Compartment.PLASMA].time_to_peak
        )

    def test_solve_with_infusion(self):
        model = PKModel(
            drug=Drug.LIDOCAINE,
            dose_mg=0,
            initial_compartment=Compartment.PLASMA,
        )
        result = model.solve_with_infusion(
            infusion_rate_mg_per_min=1.0,
            infusion_duration_min=30.0,
            total_duration_min=120.0,
        )

        assert len(result.time) > 0
        # Concentration should build up during infusion
        idx_30 = np.argmin(np.abs(result.time - 30.0))
        assert result.plasma_concentration[idx_30] > 0

    def test_result_shapes(self):
        model = PKModel(drug=Drug.ROPIVACAINE, dose_mg=100)
        result = model.solve(duration_min=60, dt=1.0)

        n = len(result.time)
        assert result.amounts.shape == (4, n)
        assert result.concentrations.shape == (4, n)
