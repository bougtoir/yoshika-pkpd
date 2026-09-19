"""Tests for compartment definitions and initial conditions."""

import pytest

from yoshika.compartments import Compartment, CompartmentModel


class TestCompartment:
    def test_enum_values(self):
        assert Compartment.PLASMA.value == "plasma"
        assert Compartment.BRT.value == "brt"
        assert Compartment.BPT.value == "bpt"
        assert Compartment.DEPOT.value == "depot"


class TestCompartmentModel:
    @pytest.fixture
    def model(self):
        return CompartmentModel(
            v1=10.0, v2=20.0, v3=50.0,
            k10=0.05, k12=0.08, k21=0.04,
            k13=0.02, k31=0.008,
            ka=0.04,
            initial_compartment=Compartment.PLASMA,
            dose_mg=100.0,
        )

    def test_initial_amounts_plasma(self, model):
        amounts = model.get_initial_amounts()
        assert amounts[0] == 0.0   # depot
        assert amounts[1] == 100.0  # plasma
        assert amounts[2] == 0.0   # brt
        assert amounts[3] == 0.0   # bpt

    def test_initial_amounts_bpt(self, model):
        model.initial_compartment = Compartment.BPT
        amounts = model.get_initial_amounts()
        assert amounts[0] == 0.0
        assert amounts[1] == 0.0
        assert amounts[2] == 0.0
        assert amounts[3] == 100.0

    def test_initial_amounts_brt(self, model):
        model.initial_compartment = Compartment.BRT
        amounts = model.get_initial_amounts()
        assert amounts[2] == 100.0

    def test_initial_amounts_depot(self, model):
        model.initial_compartment = Compartment.DEPOT
        amounts = model.get_initial_amounts()
        assert amounts[0] == 100.0

    def test_initial_concentrations(self, model):
        conc = model.get_initial_concentrations()
        assert conc[1] == pytest.approx(100.0 / 10.0)  # plasma

    def test_clearance(self, model):
        assert model.clearance == pytest.approx(0.05 * 10.0)

    def test_intercompartmental_clearance(self, model):
        assert model.intercompartmental_clearance_brt == pytest.approx(0.08 * 10.0)
        assert model.intercompartmental_clearance_bpt == pytest.approx(0.02 * 10.0)

    def test_custom_initial(self, model):
        model.set_custom_initial({
            Compartment.PLASMA: 30.0,
            Compartment.BPT: 70.0,
        })
        amounts = model.get_initial_amounts()
        assert amounts[1] == 30.0
        assert amounts[3] == 70.0
        assert amounts[0] == 0.0
        assert amounts[2] == 0.0

        model.clear_custom_initial()
        amounts = model.get_initial_amounts()
        assert amounts[1] == 100.0

    def test_validate_positive_volumes(self):
        with pytest.raises(ValueError, match="volumes must be positive"):
            CompartmentModel(
                v1=0, v2=20, v3=50,
                k10=0.05, k12=0.08, k21=0.04, k13=0.02, k31=0.008,
            ).validate()

    def test_validate_negative_rate(self):
        with pytest.raises(ValueError, match="non-negative"):
            CompartmentModel(
                v1=10, v2=20, v3=50,
                k10=-0.05, k12=0.08, k21=0.04, k13=0.02, k31=0.008,
            ).validate()

    def test_validate_depot_requires_ka(self):
        with pytest.raises(ValueError, match="ka"):
            CompartmentModel(
                v1=10, v2=20, v3=50,
                k10=0.05, k12=0.08, k21=0.04, k13=0.02, k31=0.008,
                ka=0.0, initial_compartment=Compartment.DEPOT,
            ).validate()

    def test_validate_negative_dose(self):
        with pytest.raises(ValueError, match="non-negative"):
            CompartmentModel(
                v1=10, v2=20, v3=50,
                k10=0.05, k12=0.08, k21=0.04, k13=0.02, k31=0.008,
                dose_mg=-10,
            ).validate()
