---
title: 'yoshika: A Python Package for Pharmacokinetic-Pharmacodynamic Simulation of Local Anesthetics with Selectable Initial Compartment'
tags:
  - Python
  - pharmacokinetics
  - pharmacodynamics
  - local anesthetics
  - regional anesthesia
  - compartment model
  - simulation
authors:
  - name: Tatsuki Onishi
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: "[Affiliation]"
    index: 1
date: 28 March 2026
bibliography: paper.bib
---

# Summary

yoshika (Yielding Open Simulation of Hybrid Inter-disciplinary Kinetic Absorption)
is a Python package for pharmacokinetic-pharmacodynamic (PKPD) simulation of local
anesthetics with a selectable initial compartment. Traditional three-compartment PK
models assume intravenous administration where drug enters the central plasma compartment
(V1) first. However, in regional anesthesia, the drug is deposited directly into tissues:
a successful peripheral nerve block deposits drug into vessel-poor tissue (V3), while a
failed block may result in intravascular injection into vessel-rich tissue (V2) or directly
into plasma. yoshika enables researchers and clinicians to simulate these clinically distinct
scenarios by selecting the initial compartment and comparing the resulting concentration-time
profiles and pharmacodynamic effects.

# Statement of Need

In regional anesthesia and pain medicine, local anesthetics are injected near nerves and
fascial planes rather than intravenously. The pharmacokinetic behavior of these drugs
depends critically on the injection site and block success. Existing PK simulation tools
(e.g., STANPUMP, Tivatrainer, Eleveld models) uniformly assume IV administration, where
drug enters the central (plasma) compartment at time zero [@eleveld2018]. This assumption
does not hold for regional anesthesia, where:

- A successful peripheral nerve block deposits the drug bolus into vessel-poor tissue
  (V3/BPT), resulting in slow absorption into plasma with a delayed, attenuated peak
  plasma concentration.
- A failed block with intravascular injection deposits the drug into vessel-rich tissue
  (V2/BRT) or directly into plasma, resulting in rapid systemic exposure and potentially
  toxic concentrations.
- Fascial plane blocks and depot injections involve absorption through a depot compartment
  with first-order absorption kinetics (ka).

The ability to model these different initial conditions is essential for:

- Redefining maximum recommended doses based on the actual administration route rather
  than IV equivalence [@rosenberg2004].
- Predicting time-to-toxicity for different block success/failure scenarios.
- Comparing the safety profiles of different local anesthetics in regional anesthesia contexts.
- Educational simulation in anesthesia training programs.

To our knowledge, yoshika is the first open-source PKPD simulation package that explicitly
supports selectable initial compartment for local anesthetics. The Python Anesthesia Simulator
(PAS) [@jeanneteau2024] provides a general framework for anesthetic PK simulation but does not
address the specific problem of initial compartment selection for regional anesthesia applications.

# Implementation

## Pharmacokinetic Model

yoshika implements a standard three-compartment mammillary PK model with an optional depot
compartment. The system of ordinary differential equations (ODEs) is:

$$\frac{dA_{depot}}{dt} = -k_a \cdot A_{depot}$$

$$\frac{dA_1}{dt} = k_a \cdot A_{depot} - (k_{10} + k_{12} + k_{13}) \cdot A_1 + k_{21} \cdot A_2 + k_{31} \cdot A_3$$

$$\frac{dA_2}{dt} = k_{12} \cdot A_1 - k_{21} \cdot A_2$$

$$\frac{dA_3}{dt} = k_{13} \cdot A_1 - k_{31} \cdot A_3$$

where $A_1$, $A_2$, $A_3$ are drug amounts in plasma (V1), vessel-rich tissue (V2/BRT), and
vessel-poor tissue (V3/BPT), respectively; $A_{depot}$ is the amount in the depot compartment;
$k_{10}$ is the elimination rate constant; $k_{12}$, $k_{21}$, $k_{13}$, $k_{31}$ are
intercompartmental transfer rate constants; and $k_a$ is the absorption rate constant from the depot.

The initial conditions are set according to the selected compartment (\autoref{tab:initial_conditions}):

: Initial conditions for each selectable compartment. \label{tab:initial_conditions}

| Initial Compartment       | $A_{depot}(0)$ | $A_1(0)$ | $A_2(0)$ | $A_3(0)$ |
|:--------------------------|:---------------|:---------|:---------|:---------|
| Plasma (IV)               | 0              | Dose     | 0        | 0        |
| BRT (failed block)        | 0              | 0        | Dose     | 0        |
| BPT (successful block)    | 0              | 0        | 0        | Dose     |
| Depot (fascial plane)     | Dose           | 0        | 0        | 0        |

The ODEs are solved numerically using `scipy.integrate.solve_ivp` with the RK45 method
(explicit Runge-Kutta of order 5(4), Dormand-Prince) [@virtanen2020]. Concentrations are
computed as $C_i = A_i / V_i$ at each time point.

## Pharmacodynamic Model

yoshika includes an effect-site compartment linked to the central compartment via a
first-order rate constant $k_{e0}$:

$$\frac{dC_e}{dt} = k_{e0} \cdot (C_p - C_e)$$

where $C_e$ is the effect-site concentration and $C_p$ is the plasma concentration.
The drug effect is computed using a sigmoid Emax model:

$$E = E_{max} \cdot \frac{C_e^{\gamma}}{EC_{50}^{\gamma} + C_e^{\gamma}}$$

## Drug Database

The package includes pharmacokinetic parameters for four commonly used local anesthetics:
lidocaine, bupivacaine, ropivacaine, and levobupivacaine [@tucker1979; @burm1989]. Parameters
include compartment volumes ($V_1$, $V_2$, $V_3$), clearances ($CL$, $Q_2$, $Q_3$), effect-site
equilibration rate ($k_{e0}$), $EC_{50}$, Hill coefficient ($\gamma$), protein binding fraction,
and toxicity thresholds for CNS and cardiovascular systems. Users can also define custom drug
parameters.

## Software Architecture

yoshika is structured as a modular Python package with the following components:

- **compartments**: Compartment definitions and initial condition logic.
- **drugs**: Drug parameter database with four built-in local anesthetics.
- **model**: Three-compartment PK ODE model with scipy solver.
- **pd**: Pharmacodynamic models (Emax, sigmoid Emax, effect-site equilibration).
- **simulator**: High-level API for single simulations and multi-scenario comparison.
- **plotting**: Matplotlib-based visualization utilities.
- **utils**: Utility functions for AUC, half-life, and unit conversion.

# Example Usage

The following example demonstrates the core functionality of yoshika: comparing plasma
concentration profiles of bupivacaine 150 mg administered to a 70 kg patient across three
initial compartment scenarios.

```python
from yoshika import Simulator, Drug, Compartment
from yoshika.plotting import plot_comparison
from yoshika.drugs import DrugLibrary

sim = Simulator(drug=Drug.BUPIVACAINE, dose_mg=150, weight_kg=70)
results = sim.compare()  # Plasma, BRT, BPT scenarios
table = Simulator.summary_table(results)
print(table)

params = DrugLibrary.get(Drug.BUPIVACAINE)
fig, ax = plot_comparison(results, drug_params=params)
fig.savefig("comparison.png", dpi=300)
```

# Figures

![Three-compartment model with selectable initial compartment (plasma highlighted).\label{fig:compartment}](figures/fig1_compartment_diagram_plasma.png){ width=80% }

![Bupivacaine 150 mg -- Plasma concentration by initial compartment with toxicity thresholds.\label{fig:bupivacaine}](figures/fig2_bupivacaine_comparison.png){ width=80% }

![Plasma concentration comparison for all four local anesthetics by initial compartment.\label{fig:all_drugs}](figures/fig3_all_drugs_comparison.png){ width=80% }

![Bupivacaine -- Effect-site response by initial compartment.\label{fig:effect}](figures/fig4_bupivacaine_effect.png){ width=80% }

![Bupivacaine 150 mg from BPT -- Full compartment concentration profile.\label{fig:full_profile}](figures/fig5_bupivacaine_bpt_full.png){ width=80% }

![Bupivacaine 150 mg -- PK/PD summary by initial compartment.\label{tab:summary}](figures/fig6_summary_table.png){ width=80% }

# Clinical Application: Epidural Administration

Epidural administration can be approximated using the Depot compartment in yoshika.
In epidural anesthesia, the drug is injected into the epidural space and is absorbed
into the systemic circulation primarily through epidural venous plexus uptake, with
concurrent diffusion across the dura into the cerebrospinal fluid (CSF). This absorption
process follows approximately first-order kinetics, which is modeled by the depot
compartment's absorption rate constant ($k_a$). While the actual epidural pharmacokinetics
involves parallel pathways (vascular absorption, dural penetration, and epidural fat
sequestration), the depot model provides a reasonable first-order approximation of the
systemic absorption phase [@burm1989].

Users can adjust the $k_a$ parameter to match published epidural absorption rates for
specific local anesthetics. For example, epidural lidocaine has a reported systemic
absorption half-life of approximately 10--20 minutes, corresponding to $k_a$ values of
0.035--0.069 min$^{-1}$.

# Limitations: Spinal (Intrathecal) Administration

Spinal (subarachnoid/intrathecal) administration is not modeled in the current version
of yoshika. Intrathecal injection delivers drug directly into the cerebrospinal fluid
(CSF), involving unique pharmacokinetics (CSF spread, direct spinal cord uptake, and
subsequent systemic absorption) that differ fundamentally from the peripheral compartment
model. Additionally, spinal anesthesia is predominantly a single-shot technique with
relatively small doses (e.g., bupivacaine 10--15 mg), making systemic toxicity modeling
less clinically relevant compared to larger-dose peripheral nerve blocks and epidural
techniques. Future versions of yoshika may incorporate a CSF compartment to model
intrathecal pharmacokinetics.

# Acknowledgements

[To be completed]

# References
