"""Tests for PD models."""

import numpy as np
import pytest

from yoshika.pd import EffectSiteModel, EmaxModel, PDResult, SigmoidEmaxModel


class TestEmaxModel:
    def test_zero_concentration(self):
        model = EmaxModel(ec50=1.0)
        result = model.compute_effect(np.array([0.0]))
        assert result[0] == pytest.approx(0.0)

    def test_ec50_gives_50_percent(self):
        model = EmaxModel(ec50=2.0, emax=100.0)
        result = model.compute_effect(np.array([2.0]))
        assert result[0] == pytest.approx(50.0)

    def test_high_concentration(self):
        model = EmaxModel(ec50=1.0, emax=100.0)
        result = model.compute_effect(np.array([1000.0]))
        assert result[0] == pytest.approx(100.0, abs=0.1)

    def test_negative_concentration_clipped(self):
        model = EmaxModel(ec50=1.0)
        result = model.compute_effect(np.array([-1.0]))
        assert result[0] == pytest.approx(0.0)


class TestSigmoidEmaxModel:
    def test_zero_concentration(self):
        model = SigmoidEmaxModel(ec50=1.0, gamma=2.0)
        result = model.compute_effect(np.array([0.0]))
        assert result[0] == pytest.approx(0.0)

    def test_ec50_gives_50_percent(self):
        model = SigmoidEmaxModel(ec50=2.0, gamma=3.0, emax=100.0)
        result = model.compute_effect(np.array([2.0]))
        assert result[0] == pytest.approx(50.0)

    def test_steepness(self):
        """Higher gamma should produce steeper curve."""
        conc = np.array([1.5])
        low_gamma = SigmoidEmaxModel(ec50=2.0, gamma=1.0).compute_effect(conc)
        high_gamma = SigmoidEmaxModel(ec50=2.0, gamma=5.0).compute_effect(conc)
        # Below EC50, higher gamma -> lower effect
        assert high_gamma[0] < low_gamma[0]


class TestEffectSiteModel:
    def test_init_positive_ke0(self):
        with pytest.raises(ValueError, match="positive"):
            EffectSiteModel(ke0=0.0)

        with pytest.raises(ValueError, match="positive"):
            EffectSiteModel(ke0=-0.1)

    def test_compute_basic(self):
        es = EffectSiteModel(ke0=0.1)
        time = np.arange(0, 60, 0.5)
        # Step function: plasma goes to 5 mg/L instantly
        cp = np.full_like(time, 5.0)

        ce = es.compute(time, cp)
        # Effect site should approach plasma concentration
        assert ce[0] == pytest.approx(0.0, abs=0.1)
        assert ce[-1] == pytest.approx(5.0, abs=0.5)

    def test_compute_full(self):
        es = EffectSiteModel(ke0=0.1)
        pd_model = EmaxModel(ec50=2.0, emax=100.0)

        time = np.arange(0, 120, 0.5)
        cp = np.full_like(time, 3.0)

        result = es.compute_full(time, cp, pd_model)
        assert isinstance(result, PDResult)
        assert len(result.effect) == len(time)
        assert result.peak_effect > 0
        # At steady state with Ce=3.0, effect = 100*3/(2+3) = 60%
        assert result.effect[-1] == pytest.approx(60.0, abs=2.0)
