"""Local anesthetic drug parameter database.

PK parameters are sourced from published population pharmacokinetic studies.
All parameters are normalized to a 70 kg adult unless otherwise noted.

References are provided in each drug's docstring.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Union

from yoshika.compartments import Compartment


class Drug(Enum):
    """Available local anesthetic drugs."""

    LIDOCAINE = "lidocaine"
    BUPIVACAINE = "bupivacaine"
    ROPIVACAINE = "ropivacaine"
    LEVOBUPIVACAINE = "levobupivacaine"


@dataclass(frozen=True)
class DrugParameters:
    """Pharmacokinetic and pharmacodynamic parameters for a local anesthetic.

    Attributes:
        name: Drug name.
        v1: Volume of central compartment, plasma (L).
        v2: Volume of vessel-rich tissue compartment (L).
        v3: Volume of vessel-poor tissue compartment (L).
        cl: Systemic clearance (L/min).
        q2: Intercompartmental clearance, plasma-brt (L/min).
        q3: Intercompartmental clearance, plasma-bpt (L/min).
        ke0: Effect-site equilibration rate constant (1/min).
        ka_depot: Absorption rate constant from depot/injection site (1/min).
            Used when modeling regional block absorption.
        ec50: Concentration for 50% of maximum effect (mg/L).
        gamma: Hill coefficient for sigmoid Emax model.
        toxic_cns: CNS toxicity threshold plasma concentration (mg/L).
        toxic_cv: Cardiovascular toxicity threshold plasma concentration (mg/L).
        protein_binding: Fraction of drug bound to plasma proteins.
        pka: Acid dissociation constant.
        molecular_weight: Molecular weight (g/mol).
        reference: Literature reference for PK parameters.
    """

    name: str
    v1: float
    v2: float
    v3: float
    cl: float
    q2: float
    q3: float
    ke0: float
    ka_depot: float
    ec50: float
    gamma: float
    toxic_cns: float
    toxic_cv: float
    protein_binding: float
    pka: float
    molecular_weight: float
    reference: str

    @property
    def k10(self) -> float:
        """Elimination rate constant from plasma (1/min)."""
        return self.cl / self.v1

    @property
    def k12(self) -> float:
        """Transfer rate constant from plasma to brt (1/min)."""
        return self.q2 / self.v1

    @property
    def k21(self) -> float:
        """Transfer rate constant from brt to plasma (1/min)."""
        return self.q2 / self.v2

    @property
    def k13(self) -> float:
        """Transfer rate constant from plasma to bpt (1/min)."""
        return self.q3 / self.v1

    @property
    def k31(self) -> float:
        """Transfer rate constant from bpt to plasma (1/min)."""
        return self.q3 / self.v3


# ─────────────────────────────────────────────────────────────────────────────
# Drug parameter database
# ─────────────────────────────────────────────────────────────────────────────

_DRUG_DB: Dict[Union[Drug, str], DrugParameters] = {
    Drug.LIDOCAINE: DrugParameters(
        name="Lidocaine",
        v1=12.0,
        v2=26.0,
        v3=41.0,
        cl=0.64,
        q2=0.81,
        q3=0.26,
        ke0=0.12,
        ka_depot=0.06,
        ec50=3.0,
        gamma=2.0,
        toxic_cns=5.0,
        toxic_cv=10.0,
        protein_binding=0.65,
        pka=7.9,
        molecular_weight=234.34,
        reference=(
            "Tucker GT, Mather LE. Clin Pharmacokinet 1979;4:241-278. "
            "Schnider TW et al. Anesthesiology 1999."
        ),
    ),
    Drug.BUPIVACAINE: DrugParameters(
        name="Bupivacaine",
        v1=8.9,
        v2=22.6,
        v3=51.3,
        cl=0.47,
        q2=0.60,
        q3=0.17,
        ke0=0.077,
        ka_depot=0.04,
        ec50=0.5,
        gamma=3.0,
        toxic_cns=2.0,
        toxic_cv=4.0,
        protein_binding=0.95,
        pka=8.1,
        molecular_weight=288.43,
        reference=(
            "Burm AGL et al. Anesth Analg 1987;65:1281-1284. "
            "Tucker GT et al. Br J Anaesth 1970;42:1040."
        ),
    ),
    Drug.ROPIVACAINE: DrugParameters(
        name="Ropivacaine",
        v1=10.2,
        v2=18.5,
        v3=62.0,
        cl=0.44,
        q2=0.52,
        q3=0.18,
        ke0=0.065,
        ka_depot=0.045,
        ec50=0.8,
        gamma=2.5,
        toxic_cns=2.2,
        toxic_cv=5.3,
        protein_binding=0.94,
        pka=8.1,
        molecular_weight=274.40,
        reference=(
            "Lee A et al. Anesth Analg 2002;94:1542-1546. "
            "Emanuelsson BM et al. Anesth Analg 1995;81:1163-1168."
        ),
    ),
    Drug.LEVOBUPIVACAINE: DrugParameters(
        name="Levobupivacaine",
        v1=9.5,
        v2=24.0,
        v3=48.0,
        cl=0.50,
        q2=0.55,
        q3=0.16,
        ke0=0.075,
        ka_depot=0.042,
        ec50=0.6,
        gamma=2.8,
        toxic_cns=2.5,
        toxic_cv=5.0,
        protein_binding=0.97,
        pka=8.1,
        molecular_weight=288.43,
        reference=(
            "Bardsley H et al. Br J Clin Pharmacol 1998;46:245-249. "
            "Foster RH, Markham A. Drugs 2000;59:551-579."
        ),
    ),
}


class DrugLibrary:
    """Access and manage the local anesthetic drug parameter database."""

    @staticmethod
    def get(drug: Drug) -> DrugParameters:
        """Retrieve PK/PD parameters for a given drug.

        Args:
            drug: Drug enum member.

        Returns:
            DrugParameters for the specified drug.

        Raises:
            KeyError: If the drug is not in the database.
        """
        if drug not in _DRUG_DB:
            raise KeyError(f"Drug '{drug.value}' not found in database.")
        return _DRUG_DB[drug]

    @staticmethod
    def list_drugs() -> list[Union[Drug, str]]:
        """List all available drugs in the database.

        Returns:
            List of Drug enum members and custom drug string keys.
        """
        return list(_DRUG_DB.keys())

    @staticmethod
    def get_by_name(name: str) -> DrugParameters:
        """Retrieve drug parameters by name string (case-insensitive).

        Args:
            name: Drug name string (e.g., "bupivacaine").

        Returns:
            DrugParameters for the matched drug.

        Raises:
            KeyError: If no matching drug is found.
        """
        name_lower = name.lower().strip()
        for drug, params in _DRUG_DB.items():
            key = drug.value if isinstance(drug, Drug) else drug
            if key.lower() == name_lower or params.name.lower() == name_lower:
                return params
        available = [
            d.value if isinstance(d, Drug) else d for d in _DRUG_DB
        ]
        raise KeyError(
            f"Drug '{name}' not found. Available: {available}"
        )

    @staticmethod
    def add_custom_drug(drug_key: str, params: DrugParameters) -> str:
        """Register a custom drug in the database.

        This allows users to add drugs not included in the default library.

        Args:
            drug_key: Unique key string for the custom drug.
            params: DrugParameters instance with all PK/PD parameters.

        Returns:
            The string key used to reference this drug. The drug can be
            retrieved using DrugLibrary.get_by_name().

        Note:
            Custom drugs are stored using the string key and can be
            retrieved using DrugLibrary.get_by_name(drug_key) or
            DrugLibrary.get_by_name(params.name).
        """
        _DRUG_DB[drug_key] = params
        return drug_key

    @staticmethod
    def get_absorption_rates() -> Dict[str, Dict[Compartment, float]]:
        """Get suggested absorption rate constants for different block types.

        Returns a dictionary of block-type descriptions mapped to
        recommended compartment and ka values. These are approximate
        values based on literature and can serve as starting points.

        Returns:
            Dictionary mapping block type description to compartment
            and absorption rate pairs.
        """
        return {
            "successful_peripheral_nerve_block": {
                Compartment.BPT: 0.03,  # slow absorption from avascular site
            },
            "failed_block_intravascular": {
                Compartment.PLASMA: 0.0,  # direct IV, no absorption phase
            },
            "failed_block_vascular_tissue": {
                Compartment.BRT: 0.08,  # faster absorption from vascular tissue
            },
            "epidural": {
                Compartment.DEPOT: 0.05,  # moderate absorption, mixed vascularity
            },
            "subcutaneous_infiltration": {
                Compartment.DEPOT: 0.04,  # moderate-slow absorption
            },
            "wound_infiltration": {
                Compartment.BPT: 0.025,  # slow absorption from wound tissue
            },
        }
