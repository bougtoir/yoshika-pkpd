"""Tests for utility functions."""

import numpy as np
import pytest

from yoshika.compartments import Compartment
from yoshika.utils import (
    auc_trapezoidal,
    compartment_from_string,
    concentration_to_free,
    format_pk_summary,
    half_life_terminal,
    mg_per_kg_to_mg,
    mg_to_mg_per_kg,
    time_above_threshold,
)


class TestDoseConversion:
    def test_mg_per_kg_to_mg(self):
        assert mg_per_kg_to_mg(2.0, 70.0) == pytest.approx(140.0)

    def test_mg_to_mg_per_kg(self):
        assert mg_to_mg_per_kg(140.0, 70.0) == pytest.approx(2.0)


class TestConcentration:
    def test_free_concentration(self):
        total = np.array([10.0, 5.0, 1.0])
        free = concentration_to_free(total, protein_binding=0.95)
        expected = np.array([0.5, 0.25, 0.05])
        np.testing.assert_allclose(free, expected)


class TestAUC:
    def test_constant_concentration(self):
        time = np.arange(0, 60.0, 1.0)
        conc = np.full_like(time, 5.0)
        auc = auc_trapezoidal(time, conc)
        assert auc == pytest.approx(5.0 * 59.0, abs=1.0)

    def test_linear_increase(self):
        time = np.array([0.0, 10.0])
        conc = np.array([0.0, 10.0])
        auc = auc_trapezoidal(time, conc)
        assert auc == pytest.approx(50.0)


class TestHalfLife:
    def test_monoexponential(self):
        lam = 0.01  # rate constant
        t12_expected = 0.693 / lam
        time = np.arange(0, 500, 1.0)
        conc = 10.0 * np.exp(-lam * time)
        t12 = half_life_terminal(time, conc, tail_fraction=0.5)
        assert t12 == pytest.approx(t12_expected, rel=0.05)

    def test_zero_concentration_returns_nan(self):
        time = np.arange(0, 10, 1.0)
        conc = np.zeros_like(time)
        t12 = half_life_terminal(time, conc)
        assert np.isnan(t12)


class TestTimeAboveThreshold:
    def test_all_above(self):
        time = np.arange(0, 10, 1.0)
        conc = np.full_like(time, 5.0)
        tat = time_above_threshold(time, conc, threshold=3.0)
        assert tat == pytest.approx(9.0)

    def test_none_above(self):
        time = np.arange(0, 10, 1.0)
        conc = np.full_like(time, 1.0)
        tat = time_above_threshold(time, conc, threshold=3.0)
        assert tat == 0.0


class TestCompartmentFromString:
    def test_basic_names(self):
        assert compartment_from_string("plasma") == Compartment.PLASMA
        assert compartment_from_string("brt") == Compartment.BRT
        assert compartment_from_string("bpt") == Compartment.BPT
        assert compartment_from_string("depot") == Compartment.DEPOT

    def test_aliases(self):
        assert compartment_from_string("iv") == Compartment.PLASMA
        assert compartment_from_string("central") == Compartment.PLASMA
        assert compartment_from_string("vessel-rich") == Compartment.BRT
        assert compartment_from_string("vessel-poor") == Compartment.BPT
        assert compartment_from_string("v1") == Compartment.PLASMA
        assert compartment_from_string("v2") == Compartment.BRT
        assert compartment_from_string("v3") == Compartment.BPT

    def test_case_insensitive(self):
        assert compartment_from_string("PLASMA") == Compartment.PLASMA
        assert compartment_from_string("BRT") == Compartment.BRT

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown"):
            compartment_from_string("unknown")


class TestFormatPKSummary:
    def test_format(self):
        summary = format_pk_summary(
            cmax=5.0, tmax=30.0, auc=1000.0, half_life=120.0,
        )
        assert "5.000 mg/L" in summary
        assert "30.0 min" in summary
        assert "120.0 min" in summary
