"""
yoshika - Yielding Open Simulation of Hybrid Inter-disciplinary Kinetic Absorption

A PKPD package for local anesthetics with selectable initial compartment.

Traditional 3-compartment PK models (Marsh, Schnider, Eleveld, etc.) assume
intravenous administration where drug enters plasma (V1) first. However, in
regional anesthesia:
  - Successful block -> drug starts in vessel-poor tissue (bpt/V3)
  - Failed block -> drug starts in vessel-rich tissue (brt/V2) or plasma

yoshika allows selecting the initial compartment to simulate these clinically
distinct scenarios and compare their pharmacokinetic profiles.

Clinical mapping:
  - Epidural administration can be approximated using the Depot compartment,
    as the absorption from the epidural space follows approximately first-order
    kinetics (vascular uptake from epidural venous plexus).
  - Spinal (intrathecal) administration is not modeled, as it is predominantly
    a single-shot technique with small doses and involves unique CSF-based
    pharmacokinetics that differ from the peripheral compartment model.
"""

__version__ = "0.1.0"

from yoshika.compartments import Compartment, CompartmentModel
from yoshika.drugs import Drug, DrugLibrary
from yoshika.model import PKModel
from yoshika.pd import EffectSiteModel, EmaxModel, PDModel, SigmoidEmaxModel
from yoshika.plotting import plot_comparison, plot_concentration, plot_effect
from yoshika.simulator import SimulationResult, Simulator

__all__ = [
    "__version__",
    "Compartment",
    "CompartmentModel",
    "Drug",
    "DrugLibrary",
    "PKModel",
    "PDModel",
    "EmaxModel",
    "SigmoidEmaxModel",
    "EffectSiteModel",
    "Simulator",
    "SimulationResult",
    "plot_concentration",
    "plot_comparison",
    "plot_effect",
]
