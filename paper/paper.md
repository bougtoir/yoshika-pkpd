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
    orcid: 0000-0001-7261-9062
    affiliation: 1
affiliations:
  - name: Data Science and AI Innovation Research Promotion Center, Shiga University
    index: 1
date: 28 March 2026
bibliography: paper.bib
---

# Code Metadata

| Nr. | Code metadata description | Value |
|:----|:--------------------------|:------|
| C1 | Current code version | v0.1.0 |
| C2 | Permanent link to code/repository | <https://github.com/bougtoir/wip> |
| C3 | Permanent link to Reproducible Capsule | |
| C4 | Legal Code License | MIT |
| C5 | Code versioning system used | git |
| C6 | Software code languages, tools, and services used | Python |
| C7 | Compilation requirements, operating environments & dependencies | Python >= 3.9, NumPy, SciPy, Matplotlib |
| C8 | Link to developer documentation/manual | <https://github.com/bougtoir/wip/blob/master/README.md> |
| C9 | Support email for questions | bougtoir@gmail.com |

# Abstract

yoshika (Yielding Open Simulation of Hybrid Inter-disciplinary Kinetic Absorption)
is an open-source Python package for pharmacokinetic-pharmacodynamic (PKPD) simulation
of local anesthetics with a selectable initial compartment. Traditional three-compartment
pharmacokinetic models assume intravenous administration where drug enters the central
plasma compartment first. In regional anesthesia, however, drug is deposited directly into
tissues: a successful peripheral nerve block deposits drug into vessel-poor tissue, while a
failed block may deposit drug into vessel-rich tissue or directly into plasma. yoshika enables
researchers and clinicians to simulate these clinically distinct scenarios by selecting the
initial compartment of drug deposition and comparing the resulting concentration-time profiles
and pharmacodynamic effects. The package includes built-in parameters for four local
anesthetics (lidocaine, bupivacaine, ropivacaine, levobupivacaine), an effect-site compartment
with sigmoid Emax pharmacodynamic model, and visualization utilities. By quantifying how the
initial compartment determines peak plasma concentration and time-to-toxicity, yoshika supports
the concept of context-sensitive maximum dose recommendations and route-adaptive PKPD simulation
in anesthesia information management systems.

**Keywords:** pharmacokinetics, pharmacodynamics, local anesthetics, regional anesthesia,
compartment model, simulation, Python, initial compartment, systemic toxicity

# 1. Motivation and significance

## 1.1 The initial compartment problem in regional anesthesia

In regional anesthesia and pain medicine, local anesthetics are injected near nerves and
fascial planes rather than intravenously. The pharmacokinetic behavior of these drugs
depends critically on the injection site and block success. Existing PK simulation tools
(e.g., STANPUMP, Tivatrainer, Eleveld models) uniformly assume intravenous administration,
where drug enters the central (plasma) compartment at time zero [@eleveld2018]. This
assumption does not hold for regional anesthesia, where:

- A successful peripheral nerve block deposits the drug bolus into vessel-poor tissue
  (V3/BPT), resulting in slow absorption into plasma with a delayed, attenuated peak
  plasma concentration.
- A failed block with intravascular injection deposits the drug into vessel-rich tissue
  (V2/BRT) or directly into plasma, resulting in rapid systemic exposure and potentially
  toxic concentrations.
- Fascial plane blocks and depot injections involve absorption through a depot compartment
  with first-order absorption kinetics ($k_a$).

To our knowledge, no existing open-source PKPD simulation package explicitly supports
selectable initial compartment for local anesthetics. The Python Anesthesia Simulator
(PAS) [@jeanneteau2024] provides a general framework for anesthetic PK simulation but does
not address the specific problem of initial compartment selection for regional anesthesia
applications.

## 1.2 Clinical significance: initial compartment as a determinant of systemic toxicity risk

The clinical significance of selectable initial compartment modeling lies in its
direct implications for local anesthetic systemic toxicity (LAST) risk assessment.
Traditional maximum recommended doses for local anesthetics (e.g., bupivacaine
2 mg/kg, lidocaine 4.5 mg/kg without epinephrine) are derived from intravenous
pharmacokinetic studies, where the entire dose enters the central plasma compartment
instantaneously [@rosenberg2004; @decassai2025]. This assumption produces the
highest possible peak plasma concentration (Cmax) for a given dose.

However, in regional anesthesia, the initial compartment of drug deposition
fundamentally alters the concentration-time profile:

- **Successful block (BPT start):** Drug deposited in vessel-poor tissue is
  absorbed slowly into plasma, producing a delayed and attenuated Cmax. The
  block is effective, the duration is long, and systemic exposure is low.
- **Failed block (BRT start):** Drug deposited near vessel-rich tissue is
  absorbed rapidly, producing an earlier and higher Cmax. The block effect is
  short, and systemic exposure approaches IV-like kinetics.
- **Intravascular injection (Plasma start):** Equivalent to IV bolus with
  immediate high Cmax and maximum toxicity risk.

Importantly, "successful/vessel-poor/long-duration/slow-removal" and
"failed/vessel-rich/short-duration/rapid-removal" are pharmacokinetically
synonymous descriptions without positive or negative connotations---they
represent neutral descriptions of drug disposition based on the anatomical
site of deposition.

## 1.3 Context-sensitive maximum dose

We propose that yoshika enables exploration of a *context-sensitive maximum dose*
concept for local anesthetics, analogous to the context-sensitive half-time that
transformed understanding of intravenous drug offset [@hughes1992]. Under this
framework, the effective maximum safe dose is not a single fixed value but varies
with the clinical scenario (\autoref{tab:context_dose}).

: Proposed context-sensitive maximum dose framework. \label{tab:context_dose}

| Scenario | Initial Compartment | Expected Cmax | Dose Implication |
|:---------|:-------------------|:-------------|:-----------------|
| Successful block | BPT (V3) | Low, delayed | Higher dose may be safe |
| Partial block | Mixed (BPT + BRT) | Intermediate | Standard limit applies |
| Failed block | BRT (V2) | Moderate-high, early | Lower dose may be needed |
| Intravascular injection | Plasma (V1) | Very high, immediate | Traditional IV limits apply |
| Epidural | Depot (multi-pathway) | Intermediate, delayed | Depot model approximation |

This framework provides a pharmacokinetic rationale for the empirical observation
that LAST is rare despite frequent exceeding of traditional mg/kg dose limits in
regional anesthesia practice [@rosenberg2004]. When the block is successful, the
drug is sequestered in vessel-poor tissue with slow systemic release---precisely
the scenario where doses above traditional limits are routinely administered safely.

## 1.4 Implications for anesthesia information management systems

Modern anesthesia information management systems (AIMS) increasingly incorporate
real-time PKPD displays for intravenous agents (e.g., propofol, remifentanil)
using standard three-compartment models that assume central compartment input
[@eleveld2018]. When the same AIMS tracks local anesthetic doses administered via
regional techniques, the underlying PK model remains unchanged, producing
predictions based on IV kinetics that may significantly overestimate peak plasma
concentrations after successful regional blocks.

yoshika demonstrates that route-adaptive PKPD simulation---adjusting the initial
compartment based on the documented administration route---is computationally
straightforward and can be integrated into existing AIMS infrastructure. The
mathematical framework (depot-augmented compartment models with first-order
absorption) is well-established and computationally inexpensive. The principal
barrier to implementation is not technical but conceptual: the recognition that
a single pharmacokinetic model cannot adequately describe drug behavior across
fundamentally different routes of administration.

# 2. Software description

## 2.1 Software architecture

yoshika is structured as a modular Python package with the following components:

- **compartments**: Compartment definitions (`PLASMA`, `BRT`, `BPT`, `DEPOT`) and initial condition logic.
- **drugs**: Drug parameter database with four built-in local anesthetics (lidocaine, bupivacaine, ropivacaine, levobupivacaine) and custom drug support.
- **model**: Three-compartment PK ODE model solved with SciPy's `solve_ivp` (RK45 method) [@virtanen2020].
- **pd**: Pharmacodynamic models (Emax, sigmoid Emax, effect-site equilibration).
- **simulator**: High-level API for single simulations and multi-scenario comparison.
- **plotting**: Matplotlib-based visualization utilities for concentration-time curves, effect profiles, and comparison plots.
- **utils**: Utility functions for AUC calculation, half-life estimation, and unit conversion.

The package follows a clean separation of concerns: the PK model (ODE system) is independent of the PD model, and both are independent of the drug parameter database. This design allows users to substitute custom drug parameters, modify the PD model, or extend the compartment structure without affecting other components.

## 2.2 Software functionalities

### 2.2.1 Pharmacokinetic model

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

### 2.2.2 Pharmacodynamic model

yoshika includes an effect-site compartment linked to the central compartment via a
first-order rate constant $k_{e0}$:

$$\frac{dC_e}{dt} = k_{e0} \cdot (C_p - C_e)$$

where $C_e$ is the effect-site concentration and $C_p$ is the plasma concentration.
The drug effect is computed using a sigmoid Emax model:

$$E = E_{max} \cdot \frac{C_e^{\gamma}}{EC_{50}^{\gamma} + C_e^{\gamma}}$$

### 2.2.3 Drug database

The package includes pharmacokinetic parameters for four commonly used local anesthetics:
lidocaine, bupivacaine, ropivacaine, and levobupivacaine [@tucker1979; @burm1989]. Parameters
include compartment volumes ($V_1$, $V_2$, $V_3$), clearances ($CL$, $Q_2$, $Q_3$), effect-site
equilibration rate ($k_{e0}$), $EC_{50}$, Hill coefficient ($\gamma$), protein binding fraction,
and toxicity thresholds for CNS and cardiovascular systems. Users can also define custom drug
parameters via the `DrugLibrary.add_custom()` API.

### 2.2.4 Epidural administration approximation

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

### 2.2.5 Limitations: spinal (intrathecal) administration

Spinal (subarachnoid/intrathecal) administration is not modeled in the current version
of yoshika. Intrathecal injection delivers drug directly into the cerebrospinal fluid
(CSF), involving unique pharmacokinetics (CSF spread, direct spinal cord uptake, and
subsequent systemic absorption) that differ fundamentally from the peripheral compartment
model. Additionally, spinal anesthesia is predominantly a single-shot technique with
relatively small doses (e.g., bupivacaine 10--15 mg), making systemic toxicity modeling
less clinically relevant compared to larger-dose peripheral nerve blocks and epidural
techniques.

# 3. Illustrative examples

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

\autoref{fig:compartment} shows the three-compartment model with selectable initial compartment.
\autoref{fig:bupivacaine} demonstrates the dramatic differences in plasma concentration-time
profiles when bupivacaine 150 mg is administered to the same patient but with different initial
compartments. The plasma-start scenario (equivalent to IV bolus) produces the highest and earliest
Cmax, exceeding the CNS toxicity threshold. The BRT-start scenario (failed block) shows intermediate
kinetics, while the BPT-start scenario (successful block) produces the lowest and most delayed Cmax,
remaining below toxicity thresholds throughout.

\autoref{fig:all_drugs} extends this comparison to all four local anesthetics.
\autoref{fig:effect} shows the effect-site concentration and pharmacodynamic response for
bupivacaine across initial compartments. \autoref{fig:full_profile} shows the full
compartment concentration profile for bupivacaine from BPT. \autoref{tab:summary} provides
a PK/PD summary table comparing key parameters across initial compartments.

![Three-compartment model with selectable initial compartment (plasma highlighted).\label{fig:compartment}](figures/fig1_compartment_diagram_plasma.png){ width=80% }

![Bupivacaine 150 mg -- Plasma concentration by initial compartment with toxicity thresholds.\label{fig:bupivacaine}](figures/fig2_bupivacaine_comparison.png){ width=80% }

![Plasma concentration comparison for all four local anesthetics by initial compartment.\label{fig:all_drugs}](figures/fig3_all_drugs_comparison.png){ width=80% }

![Bupivacaine -- Effect-site response by initial compartment.\label{fig:effect}](figures/fig4_bupivacaine_effect.png){ width=80% }

![Bupivacaine 150 mg from BPT -- Full compartment concentration profile.\label{fig:full_profile}](figures/fig5_bupivacaine_bpt_full.png){ width=80% }

![Bupivacaine 150 mg -- PK/PD summary by initial compartment.\label{tab:summary}](figures/fig6_summary_table.png){ width=80% }

# 4. Impact

yoshika addresses a gap in the pharmacokinetic simulation landscape by providing the first
open-source tool that allows users to select the initial compartment of drug deposition for
local anesthetics. The impact of this software extends across several domains:

**Clinical pharmacology and toxicology.** By quantifying how the initial compartment
determines peak plasma concentration and time-to-toxicity, yoshika provides a computational
basis for reconsidering maximum recommended doses of local anesthetics. The context-sensitive
maximum dose framework (\autoref{tab:context_dose}) challenges the longstanding practice of
applying IV-derived mg/kg limits to regional anesthesia, where absorption kinetics differ
fundamentally from intravenous administration.

**Anesthesia information management systems.** yoshika demonstrates that route-adaptive PKPD
simulation is computationally feasible with standard ODE solvers and can be integrated into
existing AIMS infrastructure. This provides a proof-of-concept for AIMS vendors seeking to
implement administration-route-specific pharmacokinetic predictions.

**Clinical decision support.** Block success can serve as a real-time pharmacokinetic risk
indicator. If block success is inferred from clinical assessment (e.g., onset of sensory
block within expected timeframes), clinicians could update their toxicity risk assessment
in real time using yoshika's simulation framework. A confirmed successful block indicates
a low-risk pharmacokinetic trajectory (slow absorption from BPT), while failure to achieve
blockade should prompt heightened vigilance and conservative redosing decisions.

**Education and training.** yoshika provides an interactive simulation environment for
anesthesia trainees to visualize how different injection sites and block outcomes affect
drug disposition, reinforcing the pharmacokinetic principles underlying safe regional
anesthesia practice.

**Research.** The modular design of yoshika facilitates extension to new drug models,
custom compartment configurations, and population pharmacokinetic analyses. Future research
directions include systematic measurement of plasma concentration profiles after various
regional block types with concurrent documentation of block success, to parameterize
compartment-specific absorption models, and prospective validation of the context-sensitive
maximum dose framework.

# 5. Conclusions

yoshika is an open-source Python package that fills a specific gap in pharmacokinetic
simulation tools: the ability to select the initial compartment of drug deposition for
local anesthetics in regional anesthesia. By enabling simulation of clinically distinct
scenarios---successful block (BPT start), failed block (BRT start), intravascular injection
(Plasma start), and depot absorption (fascial plane/epidural)---yoshika provides a
computational framework for exploring context-sensitive maximum dose recommendations and
route-adaptive PKPD simulation.

The clinical significance of this approach is substantial: traditional mg/kg dose limits
derived from IV pharmacokinetics do not account for the fundamentally different absorption
kinetics of regional anesthesia. yoshika quantifies these differences and supports the
development of evidence-based, route-specific dose guidelines. The software is freely
available under the MIT license and can be installed via pip.

# Declaration of competing interest

The authors declare that they have no known competing financial interests or personal
relationships that could have appeared to influence the work reported in this paper.

# CRediT authorship contribution statement

**Tatsuki Onishi:** Conceptualization, Methodology, Software, Validation, Writing -- Original Draft, Writing -- Review & Editing.

# Acknowledgements

None.

# References
