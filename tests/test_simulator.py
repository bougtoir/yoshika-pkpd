"""Tests for the simulation engine."""

import pytest

from yoshika.compartments import Compartment
from yoshika.drugs import Drug
from yoshika.simulator import Scenario, SimulationResult, Simulator


class TestSimulator:
    def test_init_with_drug(self):
        sim = Simulator(drug=Drug.BUPIVACAINE, dose_mg=150)
        result = sim.run(initial_compartment=Compartment.PLASMA)
        assert isinstance(result, SimulationResult)
        assert result.drug_name == "Bupivacaine"
        assert result.dose_mg == 150

    def test_init_requires_drug(self):
        with pytest.raises(ValueError, match="Either"):
            Simulator(dose_mg=100)

    def test_run_with_pd(self):
        sim = Simulator(drug=Drug.LIDOCAINE, dose_mg=200, compute_pd=True)
        result = sim.run(initial_compartment=Compartment.PLASMA)
        assert result.pd is not None
        assert result.pd.peak_effect > 0

    def test_run_without_pd(self):
        sim = Simulator(drug=Drug.LIDOCAINE, dose_mg=200, compute_pd=False)
        result = sim.run(initial_compartment=Compartment.PLASMA)
        assert result.pd is None

    def test_summary(self):
        sim = Simulator(drug=Drug.BUPIVACAINE, dose_mg=150)
        result = sim.run(initial_compartment=Compartment.PLASMA)
        summary = result.summary()
        assert "Cmax_plasma_mg_L" in summary
        assert "Tmax_plasma_min" in summary
        assert summary["dose_mg"] == 150

    def test_to_dataframe(self):
        sim = Simulator(drug=Drug.BUPIVACAINE, dose_mg=150)
        result = sim.run(initial_compartment=Compartment.PLASMA, duration_min=60)
        df = result.to_dataframe()
        assert "time_min" in df.columns
        assert "plasma_mg_L" in df.columns
        assert "effect_pct" in df.columns
        assert len(df) > 0

    def test_compare_default_scenarios(self):
        sim = Simulator(drug=Drug.BUPIVACAINE, dose_mg=150, duration_min=120)
        results = sim.compare()
        assert len(results) == 3
        # Check different initial compartments
        compartments = {r.initial_compartment for r in results}
        assert Compartment.PLASMA in compartments
        assert Compartment.BRT in compartments
        assert Compartment.BPT in compartments

    def test_compare_custom_scenarios(self):
        sim = Simulator(drug=Drug.ROPIVACAINE, dose_mg=150)
        scenarios = [
            Scenario(Compartment.PLASMA, "IV"),
            Scenario(Compartment.BPT, "Block", dose_mg=200),
        ]
        results = sim.compare(scenarios=scenarios)
        assert len(results) == 2
        assert results[0].dose_mg == 150
        assert results[1].dose_mg == 200

    def test_compare_drugs(self):
        sim = Simulator(drug=Drug.LIDOCAINE, dose_mg=150, duration_min=60)
        results = sim.compare_drugs(
            drugs=[Drug.LIDOCAINE, Drug.BUPIVACAINE],
            initial_compartment=Compartment.PLASMA,
        )
        assert len(results) == 2
        assert results[0].drug_name == "Lidocaine"
        assert results[1].drug_name == "Bupivacaine"

    def test_results_to_dataframe(self):
        sim = Simulator(drug=Drug.BUPIVACAINE, dose_mg=150, duration_min=60)
        results = sim.compare()
        df = Simulator.results_to_dataframe(results)
        assert len(df) > 0
        labels = df["label"].unique()
        assert len(labels) == 3

    def test_summary_table(self):
        sim = Simulator(drug=Drug.BUPIVACAINE, dose_mg=150, duration_min=60)
        results = sim.compare()
        table = Simulator.summary_table(results)
        assert len(table) == 3
        assert "Cmax_plasma_mg_L" in table.columns
        assert "label" in table.columns
