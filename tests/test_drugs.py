"""Tests for the drug parameter database."""

import pytest

from yoshika.compartments import Compartment
from yoshika.drugs import Drug, DrugLibrary


class TestDrug:
    def test_enum_values(self):
        assert Drug.LIDOCAINE.value == "lidocaine"
        assert Drug.BUPIVACAINE.value == "bupivacaine"
        assert Drug.ROPIVACAINE.value == "ropivacaine"
        assert Drug.LEVOBUPIVACAINE.value == "levobupivacaine"


class TestDrugParameters:
    def test_rate_constants(self):
        params = DrugLibrary.get(Drug.BUPIVACAINE)
        assert params.k10 == pytest.approx(params.cl / params.v1)
        assert params.k12 == pytest.approx(params.q2 / params.v1)
        assert params.k21 == pytest.approx(params.q2 / params.v2)
        assert params.k13 == pytest.approx(params.q3 / params.v1)
        assert params.k31 == pytest.approx(params.q3 / params.v3)

    def test_all_parameters_positive(self):
        for drug in Drug:
            params = DrugLibrary.get(drug)
            assert params.v1 > 0
            assert params.v2 > 0
            assert params.v3 > 0
            assert params.cl > 0
            assert params.q2 > 0
            assert params.q3 > 0
            assert params.ke0 > 0
            assert params.ka_depot > 0
            assert params.ec50 > 0
            assert params.gamma > 0
            assert params.toxic_cns > 0
            assert params.toxic_cv > 0
            assert 0 < params.protein_binding < 1

    def test_toxicity_order(self):
        """CNS toxicity should occur at lower concentrations than CV toxicity."""
        for drug in Drug:
            params = DrugLibrary.get(drug)
            assert params.toxic_cns < params.toxic_cv


class TestDrugLibrary:
    def test_get(self):
        params = DrugLibrary.get(Drug.LIDOCAINE)
        assert params.name == "Lidocaine"

    def test_list_drugs(self):
        drugs = DrugLibrary.list_drugs()
        assert len(drugs) == 4
        assert Drug.LIDOCAINE in drugs
        assert Drug.BUPIVACAINE in drugs

    def test_get_by_name(self):
        params = DrugLibrary.get_by_name("bupivacaine")
        assert params.name == "Bupivacaine"

        params = DrugLibrary.get_by_name("LIDOCAINE")
        assert params.name == "Lidocaine"

    def test_get_by_name_not_found(self):
        with pytest.raises(KeyError, match="not found"):
            DrugLibrary.get_by_name("unknown_drug")

    def test_absorption_rates(self):
        rates = DrugLibrary.get_absorption_rates()
        assert "successful_peripheral_nerve_block" in rates
        assert "failed_block_intravascular" in rates
        assert Compartment.BPT in rates["successful_peripheral_nerve_block"]
        assert Compartment.PLASMA in rates["failed_block_intravascular"]
