---
title: 'yoshika: A Python Package for Pharmacokinetic-Pharmacodynamic Simulation of Local Anesthetics with Selectable Initial Compartment'
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

# Highlights

- Open-source comparison of initial-compartment scenarios for local anesthetics
- Standard PK equations; scenarios differ only in input and absorption
- External validation: 90% of predicted Cmax values were within two-fold
- Intravenous input overstates and mis-times non-IV peak concentrations
- Framework for exploratory, route-aware dosing and monitoring hypotheses

# Abstract

yoshika (Yielding Open Simulation of Hybrid Inter-disciplinary Kinetic Absorption) is an
open-source Python package for pharmacokinetic-pharmacodynamic (PKPD) simulation of local
anesthetics with selectable initial compartments. It uses a conventional three-compartment
model; its contribution is a reproducible methodology that makes drug-deposition assumptions
explicit and systematically comparable. Conventional simulators place the entire dose in
plasma at time zero, whereas regional anesthesia deposits drug in tissue for subsequent
absorption. yoshika allows initial placement in plasma, vessel-rich tissue, vessel-poor
tissue, or a depot and compares concentration-time profiles and pharmacodynamic effects using
shared disposition parameters. It includes built-in parameters for lidocaine, bupivacaine,
ropivacaine, and levobupivacaine, an effect-site compartment with a sigmoid Emax model,
visualization tools, and tests. External validation used Cmax and Tmax from ten published
clinical pharmacokinetic records spanning intercostal, fascial-plane, peripheral-nerve, and
epidural routes. With the depot absorption rate calibrated to observed Tmax, 90% of predicted
Cmax values were within two-fold of observations (geometric mean fold error, 1.51; Pearson
r = 0.81). The intravenous-input assumption overestimated Cmax approximately tenfold and
predicted an instantaneous peak. yoshika is intended for exploratory and educational
generation of route-aware hypotheses about peak exposure and monitoring windows, not as a
validated clinical dosing tool.

**Keywords:** pharmacokinetics; pharmacodynamics; local anesthetics; regional anesthesia;
compartment model; simulation; selectable initial compartment; systemic toxicity

# 1. Introduction

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
(PAS) [@aubouinpairault2023] provides a general framework for anesthetic PK simulation but does
not address the specific problem of initial compartment selection for regional anesthesia
applications.

We emphasize at the outset what yoshika is and is not. Mathematically, changing the
compartment that receives the dose at $t = 0$ is a trivial change of initial conditions
in a standard three-compartment model; it is not a new pharmacokinetic model, and we do
not claim it to be. The contribution is instead a *methodological and software* one:
a reproducible, open framework that makes the initial-compartment choice explicit and
lets it be varied systematically, together with the observation---often overlooked in
routine practice and in intravenous (IV)-oriented simulators---that this choice has large and
clinically meaningful consequences for the predicted concentration-time profile. Whether
the resulting predictions correspond to reality is an empirical question, which we address
by external validation against published plasma concentration data (§3.3).

## 1.2 Clinical motivation: initial compartment and systemic toxicity risk

A potential clinical relevance of selectable initial compartment modeling lies in its
implications for local anesthetic systemic toxicity (LAST) risk assessment.
Traditional maximum recommended doses for local anesthetics (e.g., bupivacaine
2 mg/kg, lidocaine 4.5 mg/kg without epinephrine) are derived largely from intravenous
and systemic pharmacokinetic studies, where the entire dose is assumed to enter the
central plasma compartment instantaneously [@rosenberg2004; @decassai2022]. This
assumption produces the highest possible peak plasma concentration ($C_{max}$) for a given dose.

Changing the initial compartment changes the simulated concentration-time profile in
qualitatively different ways. We use the following scenario labels throughout; they are
heuristic modelling scenarios, not validated anatomical mappings (see the caveat below):

- **Vessel-poor-tissue start (labelled "successful block"):** the initial amount is
  placed in the peripheral compartment with the smaller return rate constant, so it is
  released slowly into plasma, producing a delayed and attenuated $C_{max}$.
- **Vessel-rich-tissue start (labelled "failed / vascular-rich block"):** the initial
  amount is placed in the peripheral compartment with the faster return, producing an
  earlier and higher $C_{max}$ approaching intravenous-like kinetics.
- **Plasma start (intravascular injection):** equivalent to an intravenous bolus, with
  an immediate high $C_{max}$.
- **Depot start (fascial plane / infiltration / epidural):** first-order absorption into
  plasma through the depot rate constant $k_a$.

An important caveat, raised in review and which we make explicit here: the peripheral
compartments V2 and V3 of a mammillary model are *lumped, fitted* compartments, not
literal anatomical spaces. They therefore cannot be equated in a one-to-one fashion with
"vessel-rich tissue", "vessel-poor tissue", a "successful" or "failed" block, or a
"fascial plane" without independent validation. The scenario labels are used as
convenient shorthand for distinct initial-condition/absorption regimes; the empirical
question of whether they reproduce real plasma concentrations is addressed in §3.3.

## 1.3 Context-sensitive maximum dose

We propose that yoshika enables exploration of a *context-sensitive maximum dose*
concept for local anesthetics, analogous to the context-sensitive half-time that
transformed understanding of intravenous drug offset [@hughes1992]. Under this
framework, the effective maximum safe dose is not a single fixed value but varies
with the clinical scenario (\autoref{tab:context_dose}).

: Proposed context-sensitive maximum dose framework. \label{tab:context_dose}

| Scenario | Initial Compartment | Expected $C_{max}$ | Dose Implication |
|:---------|:-------------------|:-------------|:-----------------|
| Successful block | BPT (V3) | Low, delayed | Higher dose may be safe |
| Partial block | Mixed (BPT + BRT) | Intermediate | Standard limit applies |
| Failed block | BRT (V2) | Moderate-high, early | Lower dose may be needed |
| Intravascular injection | Plasma (V1) | Very high, immediate | Traditional IV limits apply |
| Epidural | Depot (multi-pathway) | Intermediate, delayed | Depot model approximation |

This framework offers a possible pharmacokinetic rationale for the empirical observation
that LAST is relatively rare despite frequent exceeding of traditional mg/kg dose limits in
regional anesthesia practice [@rosenberg2004]. If the slow-release (vessel-poor-tissue)
scenario approximates a successful block, it would be consistent with the observation that
doses above traditional limits are often tolerated. We stress that this remains a hypothesis
to be tested prospectively rather than a demonstrated result.

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

## 1.5 Why the initial compartment matters for fascial plane blocks

Conventional PK simulators (e.g., STANPUMP, Tivatrainer, or similar model-based
infusion tools) are constrained to model drug entry via the central plasma compartment
(V1), equivalent to intravenous bolus injection. For local anesthetic infiltration
and fascial plane blocks, this assumption is physiologically inappropriate: drug is deposited
into tissue (fascial planes, subcutaneous tissue) and absorbed over time, rather than
entering the bloodstream instantaneously. The distinguishing feature of yoshika is the
ability to select an initial compartment intended to represent the documented route of
administration.

Importantly, the inter-compartmental rate constants ($k_{12}$, $k_{21}$, $k_{13}$,
$k_{31}$, $k_{10}$) are shared across all simulation scenarios. The only difference
between the traditional and yoshika models is which compartment receives the drug at
$t = 0$. This single change in initial conditions produces substantially different
predictions, which we present in detail in §3.2:

- **$C_{max}$ magnitude:** The intravenous-input model predicts
  $C_{max}$ of 11--17 mg/L for standard doses, far exceeding toxicity thresholds.
  Such concentrations are not consistent with the plasma concentrations reported after
  fascial plane blocks or infiltration, which are typically a few mg/L (§3.3).
  yoshika's depot model predicts $C_{max}$ of 2--4 mg/L, closer to the range reported
  in published pharmacokinetic studies.
- **$T_{max}$ timing:** The intravenous-input model predicts $T_{max} = 0$
  (instantaneous peak) for all drugs. yoshika's depot model predicts a delayed
  $T_{max}$ (of order 10--40 minutes depending on the assumed absorption rate), and the
  vessel-poor-tissue scenario predicts a still later peak. Published studies likewise
  report peaks tens of minutes after injection rather than at $t = 0$ (§3.3), so the
  delayed peak is the more plausible representation of the period during which plasma
  concentration is rising.

For fascial plane blocks used in ambulatory surgery, this suggests two practical points.
First, the intravenous-input model may be misleading in predicting supratoxic
$C_{max}$ values that are not observed clinically after non-intravenous administration.
Second, it provides no information about when the peak occurs, because it assumes the
peak has already passed at $t = 0$. A route-aware simulation instead points to a
later monitoring window based on the documented route of administration (§3.2).

When the depot-model $C_{max}$ approaches toxicity thresholds---for example, in
simulations with ropivacaine 150 mg and bupivacaine 150 mg the predicted $C_{max}$ can
approach or exceed the central nervous system (CNS) threshold at higher assumed absorption rates---the delayed
$T_{max}$ becomes potentially relevant, suggesting monitoring beyond the first minutes
after injection. These remain model-based hypotheses that require prospective
confirmation.

Modelling a route-appropriate initial compartment is therefore proposed not as a
clinically proven method but as a more plausible starting point than the
intravenous-input assumption for exploring the systemic behaviour of regional
anesthesia techniques in which drug does not enter plasma directly
[@neal2018; @macfarlane2021; @digregorio2010].

# 2. Software architecture and design

## 2.1 Package structure

yoshika is structured as a modular Python package with the following components:

- **compartments**: Compartment definitions (`PLASMA`, `BRT`, `BPT`, `DEPOT`) and initial condition logic.
- **drugs**: Drug parameter database with four built-in local anesthetics (lidocaine, bupivacaine, ropivacaine, levobupivacaine) and custom drug support.
- **model**: Three-compartment PK ordinary differential equation (ODE) model solved with SciPy's `solve_ivp` (RK45 method) [@virtanen2020].
- **pd**: Pharmacodynamic models (Emax, sigmoid Emax, effect-site equilibration).
- **simulator**: High-level API for single simulations and multi-scenario comparison.
- **plotting**: Matplotlib-based visualization utilities for concentration-time curves, effect profiles, and comparison plots.
- **utils**: Utility functions for area under the curve (AUC) calculation, half-life estimation, and unit conversion.

The package follows a clean separation of concerns: the PK model (ODE system) is independent of the PD model, and both are independent of the drug parameter database. This design allows users to substitute custom drug parameters, modify the PD model, or extend the compartment structure without affecting other components.

## 2.2 Software functionalities

### 2.2.1 Pharmacokinetic model

yoshika implements a standard three-compartment mammillary PK model with an optional depot
compartment. The system of ODEs is:

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
and toxicity thresholds for CNS and cardiovascular (CV) systems. The complete built-in parameter
set, with units and literature sources, is given in \autoref{tab:drug_params}. All disposition
parameters are derived from intravenous or systemic pharmacokinetic studies; this provenance
is central to the validation and limitations discussed in §3.3 and §4. Users can also define
custom drug parameters via the `DrugLibrary.add_custom()` API.

: Built-in drug parameters with units and sources. Rate constants used internally are derived as $k_{10}=CL/V_1$, $k_{12}=Q_2/V_1$, $k_{21}=Q_2/V_2$, $k_{13}=Q_3/V_1$, $k_{31}=Q_3/V_3$. \label{tab:drug_params}

| Parameter (unit) | Lidocaine | Bupivacaine | Ropivacaine | Levobupivacaine |
|:-----------------|----------:|------------:|------------:|----------------:|
| $V_1$ (L)                     | 12.0 | 8.9  | 10.2 | 9.5  |
| $V_2$ (L)                     | 26.0 | 22.6 | 18.5 | 24.0 |
| $V_3$ (L)                     | 41.0 | 51.3 | 62.0 | 48.0 |
| $CL$ (L min$^{-1}$)           | 0.64 | 0.47 | 0.44 | 0.50 |
| $Q_2$ (L min$^{-1}$)          | 0.81 | 0.60 | 0.52 | 0.55 |
| $Q_3$ (L min$^{-1}$)          | 0.26 | 0.17 | 0.18 | 0.16 |
| $k_{e0}$ (min$^{-1}$)         | 0.12 | 0.077| 0.065| 0.075|
| $k_a$ depot default (min$^{-1}$) | 0.06 | 0.04 | 0.045| 0.042|
| $EC_{50}$ (mg L$^{-1}$)       | 3.0  | 0.5  | 0.8  | 0.6  |
| $\gamma$ (Hill, dimensionless)| 2.0  | 3.0  | 2.5  | 2.8  |
| CNS toxic threshold (mg L$^{-1}$) | 5.0 | 2.0 | 2.2 | 2.5 |
| CV toxic threshold (mg L$^{-1}$)  | 10.0| 4.0 | 5.3 | 5.0 |
| Protein binding (fraction)    | 0.65 | 0.95 | 0.94 | 0.97 |
| $pK_a$                        | 7.9  | 8.1  | 8.1  | 8.1  |
| Molecular weight (g mol$^{-1}$)| 234.3| 288.4| 274.4| 288.4|

Disposition sources: lidocaine and bupivacaine [@tucker1979; @burm1989]; ropivacaine and
levobupivacaine disposition and toxicity thresholds are taken from the manufacturer and
review literature cited in the package source. Values are provided as reasonable defaults
for illustration and can be overridden by the user.

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

## 2.3 Availability, installation, documentation, and testing

yoshika is released under the MIT license. The source code, documentation, and issue
tracker are hosted on a public repository, and tagged releases are archived and installable
from the Python Package Index (PyPI). The results in this paper were produced with version
0.1.0. Installation requires only a standard scientific Python stack (Python $\geq$ 3.9,
NumPy, SciPy, Matplotlib) and is performed with a single command:

```
pip install yoshika
```

The package ships with a test suite (executed with `pytest`) covering: (i) mass conservation
of the ODE system in the absence of elimination; (ii) agreement of the numerical central-compartment
solution with the closed-form one-compartment bolus solution as a limiting case; (iii) monotonic
ordering of predicted $C_{max}$ across initial compartments (plasma $\geq$ vessel-rich $\geq$
vessel-poor); and (iv) reproduction of the published $C_{max}$/$T_{max}$ comparison in §3.3 from the
bundled reference dataset. Worked examples, including all code used to generate the figures in
this paper, are provided in the repository.

# 3. Results and illustrative examples

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

![Three-compartment model with selectable initial compartment (plasma highlighted).\label{fig:compartment}](figures/fig1_compartment_diagram_plasma.png){ width=80% }

\autoref{fig:bupivacaine} demonstrates the differences in plasma concentration-time profiles
when bupivacaine 150 mg is administered to the same patient but with different initial
compartments. The plasma-start scenario (equivalent to IV bolus) produces the highest and earliest
$C_{max}$, exceeding the CNS toxicity threshold. The BRT-start scenario (failed block) shows intermediate
kinetics, while the BPT-start scenario (successful block) produces the lowest and most delayed $C_{max}$,
remaining below toxicity thresholds throughout.

![Bupivacaine 150 mg -- Plasma concentration by initial compartment with toxicity thresholds.\label{fig:bupivacaine}](figures/fig2_bupivacaine_comparison.png){ width=80% }

\autoref{fig:all_drugs} extends this comparison to all four local anesthetics.

![Plasma concentration comparison for all four local anesthetics by initial compartment.\label{fig:all_drugs}](figures/fig3_all_drugs_comparison.png){ width=80% }

\autoref{fig:effect} shows the effect-site concentration and pharmacodynamic response for
bupivacaine across initial compartments.

![Bupivacaine -- Effect-site response by initial compartment.\label{fig:effect}](figures/fig4_bupivacaine_effect.png){ width=80% }

\autoref{fig:full_profile} shows the full compartment concentration profile for bupivacaine
from BPT.

![Bupivacaine 150 mg from BPT -- Full compartment concentration profile.\label{fig:full_profile}](figures/fig5_bupivacaine_bpt_full.png){ width=80% }

\autoref{fig:summary} provides a PKPD summary comparing key parameters across initial compartments.

![Bupivacaine 150 mg -- PKPD summary by initial compartment.\label{fig:summary}](figures/fig6_summary_table.png){ width=80% }

## 3.2 Illustrative comparison: intravenous-input model vs route-aware scenarios

Conventional PK simulators are constrained to assume intravenous entry
(Compartment.PLASMA). For fascial plane blocks and infiltration, yoshika instead lets
the user select a route-aware initial compartment (Compartment.DEPOT for
fascial plane / infiltration, Compartment.BPT for the vessel-poor-tissue / "successful
block" scenario). The rate constants are identical across all scenarios; only the initial
conditions differ. The values below are illustrative simulation outputs, not measured or
clinically proven predictions; §3.3 compares them against published data.

```python
from yoshika import Compartment, Drug
from yoshika.drugs import DrugLibrary
from yoshika.model import PKModel

params = DrugLibrary.get(Drug.BUPIVACAINE)

# Conventional: forced IV entry (V1/plasma) — inappropriate for fascial plane block
pk_iv = PKModel(
    drug_params=params, dose_mg=150,
    initial_compartment=Compartment.PLASMA
).solve(duration_min=480)

# yoshika: fascial plane block deposits drug in depot compartment
pk_depot = PKModel(
    drug_params=params, dose_mg=150,
    initial_compartment=Compartment.DEPOT
).solve(duration_min=480)

print(f"Traditional (IV): Cmax={pk_iv.peak_plasma_concentration:.2f} mg/L, "
      f"Tmax={pk_iv.time_to_peak:.0f} min")
print(f"yoshika (Depot):  Cmax={pk_depot.peak_plasma_concentration:.2f} mg/L, "
      f"Tmax={pk_depot.time_to_peak:.0f} min")
# Conventional (IV): Cmax=16.85 mg/L, Tmax=0 min   <- likely overstated for depot route
# yoshika (Depot):  Cmax=3.10 mg/L,  Tmax=14 min   <- plausible for fascial plane
```

\autoref{fig:safety_panel} shows the predicted plasma concentration--time
profiles for four fascial plane block / infiltration scenarios. The
intravenous-input model (red curves) predicts instantaneous supratoxic $C_{max}$ values
(11--17 mg/L) that are not consistent with the concentrations reported after non-intravenous
administration (§3.3). yoshika's depot model (blue curves) predicts a first-order absorption
profile with $C_{max}$ of 2--4 mg/L peaking at 12--16 minutes (for the default absorption
rates). The vessel-poor-tissue scenario (green dashed curves) yields $C_{max}$ of 0.35--0.85
mg/L peaking substantially later.

![Plasma concentration--time curves: intravenous-input model (red) vs yoshika fascial plane/depot (blue) and vessel-poor-tissue/BPT (green dashed) for four day-surgery scenarios. Green shading = in-hospital monitoring (0--2 h). Dashed lines = CNS and CV toxicity thresholds. Rate constants are shared; only the initial compartment differs.\label{fig:safety_panel}](figures/fig7_safety_panel.png){ width=95% }

\autoref{fig:tmax_comparison} compares $T_{max}$ across models and drugs.
The intravenous-input model invariably predicts $T_{max} = 0$---providing no
information about when a peak would occur. yoshika's depot model
yields $T_{max}$ of 12--16 minutes for the default absorption rates, while the
vessel-poor-tissue scenario yields much later peaks.

![Time to peak plasma concentration ($T_{max}$) by model and drug/dose. The intravenous-input model predicts $T_{max} = 0$ for all drugs (IV assumption). The depot scenario yields $T_{max}$ at 12--16 min and the vessel-poor-tissue scenario at 72--119 min (default absorption rates). Horizontal lines = discharge (120 min) and extended monitoring (240 min). Simulation outputs, not measured values.\label{fig:tmax_comparison}](figures/fig8_tmax_comparison.png){ width=80% }

\autoref{fig:monitoring_timeline} maps $T_{max}$ onto a clinical timeline relative
to typical day-surgery discharge (2 hours). Grey bars represent the in-hospital
monitoring period. The intravenous-input model's $T_{max} = 0$ implies the peak is over
immediately, whereas a route-aware simulation points to a later window
during which plasma concentration is still rising.

![Monitoring window: when does $C_{max}$ occur relative to discharge? Diamond markers = $T_{max}$ under each model. The intravenous-input model (red) places the peak at $t = 0$. The route-aware scenarios place the simulated peak later, in the fascial plane and vessel-poor-tissue cases. Simulation scenarios, not clinically proven predictions.\label{fig:monitoring_timeline}](figures/fig9_monitoring_timeline.png){ width=95% }

\autoref{fig:cmax_toxicity} compares $C_{max}$ against CNS and cardiovascular
toxicity thresholds. The intravenous-input model's overestimation is
apparent: predicted $C_{max}$ values exceed even the CV toxicity threshold for all
drugs, whereas the depot model shows $C_{max}$ near or below the CNS threshold.

![Peak plasma concentration ($C_{max}$) vs toxicity thresholds. The intravenous-input model predicts $C_{max}$ well above the thresholds for non-intravenous routes; the depot and vessel-poor-tissue scenarios predict lower values closer to those reported in published studies (§3.3). Simulation outputs.\label{fig:cmax_toxicity}](figures/fig10_cmax_toxicity.png){ width=80% }

\autoref{fig:safety_summary} summarizes these simulations, noting that the
depot model can predict $C_{max}$ near or above the CNS threshold for ropivacaine 150 mg and
bupivacaine 100--150 mg---model-based signals that, if borne out, would warrant
monitoring through $T_{max}$.

![Safety summary: rate constants shared across all models; only initial compartment differs. Red cells = $C_{max}$ exceeds CNS threshold or $T_{max}$ exceeds discharge time. Pink rows = intravenous-input; blue = fascial plane (depot); green = vessel-poor-tissue (BPT).\label{fig:safety_summary}](figures/fig11_safety_summary_table.png){ width=95% }

## 3.3 External validation against published plasma concentration data

The illustrative outputs above raise an empirical question central to this work: can a
three-compartment model with disposition parameters derived from intravenous data, combined
with a first-order absorption (depot) input, reproduce plasma concentrations actually observed
after non-intravenous administration? To address the concern that the model's clinical
interpretation is otherwise unvalidated, we compared model predictions against ten records
digitized from published clinical pharmacokinetic studies spanning intercostal blocks
[@behnke2002; @kopacz1994], fascial plane blocks (transversus abdominis plane [TAP] and rectus
sheath) [@murouchi2015], peripheral nerve blocks (brachial and axillary plexus)
[@hickey1990; @vainionpaa1995], and epidural administration [@inoue1985], covering
ropivacaine, bupivacaine, and lidocaine.

For each study we used the built-in disposition parameters unchanged and calibrated only the
depot absorption rate constant $k_a$ so that the predicted time-to-peak matched the reported
$T_{max}$ (a single degree of freedom per study, reflecting that absorption rate is the
route- and site-specific quantity not contained in intravenous disposition data). We then
compared the predicted peak concentration $C_{max}$ against the observed value, and contrasted
this with the intravenous-input ("IV-forced") baseline in which the whole dose is placed in
plasma at $t = 0$. The full record set is given in \autoref{tab:validation}.

: External validation against published plasma concentration data. $k_a$ was calibrated to the observed $T_{max}$; disposition parameters were unchanged. Fold error is predicted/observed $C_{max}$. The IV-forced baseline predicts $T_{max}=0$ for every record. \label{tab:validation}

| Study (route) | Drug | Dose (mg) | Obs $C_{max}$ | Pred $C_{max}$ | Fold | Obs $T_{max}$ (min) | IV $C_{max}$ | Ref |
|:--------------|:-----|----------:|--------------:|---------------:|-----:|--------------------:|-------------:|:----|
| Intercostal 0.75% (venous) | ropivacaine | 150 | 2.4 | 4.69 | 1.96 | 11 | 14.7 | [@behnke2002] |
| Intercostal 1.0% (venous)  | ropivacaine | 200 | 2.5 | 5.87 | 2.35 | 12 | 19.6 | [@behnke2002] |
| Bilateral intercostal (venous) | ropivacaine | 140 | 1.1 | 2.20 | 2.00 | 21 | 13.7 | [@kopacz1994] |
| Bilateral intercostal (venous) | bupivacaine | 140 | 0.9 | 1.28 | 1.42 | 30 | 15.7 | [@kopacz1994] |
| TAP block (arterial) | ropivacaine | 150 | 1.83 | 1.40 | 0.76 | 35 | 14.7 | [@murouchi2015] |
| Rectus sheath (arterial) | ropivacaine | 150 | 1.79 | 1.03 | 0.57 | 53 | 14.7 | [@murouchi2015] |
| Brachial plexus (venous) | ropivacaine | 190 | 1.3 | 1.30 | 1.00 | 53 | 18.6 | [@hickey1990] |
| Axillary plexus (venous) | ropivacaine | 175 | 1.28 | 1.21 | 0.95 | 52 | 17.2 | [@vainionpaa1995] |
| Axillary plexus (venous) | bupivacaine | 175 | 1.28 | 1.06 | 0.83 | 58 | 19.7 | [@vainionpaa1995] |
| Epidural 2% (venous) | lidocaine | 350 | 2.3 | 3.70 | 1.61 | 20 | 29.2 | [@inoue1985] |

Across the ten records, the geometric mean fold error of predicted versus observed $C_{max}$
was 1.51, with 9 of 10 predictions (90%) within two-fold of observation and a Pearson
correlation of $r = 0.81$ (\autoref{fig:validation_cmax}).

![External validation: observed vs predicted $C_{max}$ (depot model, $k_a$ calibrated to observed $T_{max}$). Solid line = identity; shaded band = two-fold. 90% of predictions lie within two-fold (geometric mean fold error 1.51; $r=0.81$). Marker shape distinguishes venous (circle) and arterial (triangle) sampling.\label{fig:validation_cmax}](figures/fig12_validation_cmax.png){ width=80% }

By contrast, the intravenous-input baseline predicted $C_{max}$ of 14--29 mg/L---roughly an
order of magnitude above the observed range of 0.9--2.5 mg/L---and predicted an instantaneous
peak ($T_{max}=0$) for every study, whereas observed peaks occurred 11--58 minutes after
injection (\autoref{fig:validation_tmax}).

![External validation: observed vs predicted $T_{max}$. The depot model reproduces the observed 11--58 min peaks (points near identity), whereas the intravenous-input baseline predicts $T_{max}=0$ for every study (red crosses along the horizontal axis).\label{fig:validation_tmax}](figures/fig13_validation_tmax.png){ width=80% }

Two patterns are worth stating plainly rather than obscuring. First, the model tended to
*overestimate* $C_{max}$ for the fastest-absorbing intercostal records sampled from venous
blood (fold errors up to 2.35), and to give its closest agreement for the slower peripheral
nerve and fascial plane blocks. This is the expected direction of error: the disposition
volumes are intravenous-derived, and venous samples underestimate the true arterial peak, so
a model calibrated only on timing will read slightly high against venous $C_{max}$. Second,
the two fascial plane records sampled from *arterial* blood were the only cases where the
model modestly *under*-predicted (fold 0.57--0.76), consistent with the same sampling-site
argument. We therefore interpret the validation as showing that the approach reproduces the
correct order of magnitude and the qualitative timing of systemic exposure across routes---a
substantial improvement over the intravenous-input assumption---while not being accurate
enough to support quantitative dosing decisions. This distinction motivates the framing of
yoshika as an exploratory and educational tool (§4).

Representative concentration-time curves for four administration routes are shown in
\autoref{fig:validation_curves}.

![Representative predicted concentration-time curves (yoshika depot, blue; intravenous-input baseline, red dashed) against observed peak $C_{max}\pm$SD (black squares) for intercostal, TAP, axillary plexus, and epidural cases. The intravenous-input curve peaks off-scale at $t=0$; the depot curve tracks the observed peak magnitude and timing.\label{fig:validation_curves}](figures/fig14_validation_curves.png){ width=95% }

# 4. Discussion

## 4.1 Nature of the contribution and relation to existing models

We want to be explicit about what is and is not novel here, since this was a central point
in review. yoshika does not introduce a new pharmacokinetic model. The equations are a
standard three-compartment mammillary model with an optional first-order depot input, and
placing the dose in a different compartment at $t=0$ is a mathematically trivial change of
initial conditions. Existing frameworks such as the Python Anesthesia Simulator
[@aubouinpairault2023] already solve compartmental PK systems, and the disposition
parameters we use are drawn from established clinical pharmacokinetic literature
[@tucker1979; @burm1989].

We also stress that the improved agreement in §3.3 is not, and should not be read as, a new
predictive capability unreachable by conventional tools. Any standard compartmental
simulator that adds a depot input and fits its absorption rate can reproduce exactly the same
curves and the same validation result; there is no mathematics here that a conventional model
cannot express. What the intravenous-input baseline gets wrong is therefore not a limitation
of compartmental modelling but a limitation of its *default use*---placing the entire dose in
plasma at $t=0$ regardless of the administration route. The value we claim is in making that
default choice explicit and easy to vary and compare, and in testing it, rather than in any
new equation.

Framed this way, the contribution is threefold and methodological. First, yoshika is, to our
knowledge, the first open-source tool that treats the *initial compartment* as a
first-class, user-selectable input for local anesthetics and makes systematic
scenario-to-scenario comparison under shared disposition parameters straightforward and
reproducible. Second, the paper draws attention to a consequence of this trivial change
that is easy to overlook in intravenous-oriented simulators and in routine mg/kg-based
practice: the choice of input compartment changes the predicted peak concentration by
about an order of magnitude and moves the predicted peak from $t=0$ to tens of minutes
later. Third---and this is what elevates the work above a mere software option---we
provide an external validation (§3.3) showing that, with a single route-specific
absorption parameter, the standard model reproduces observed $C_{max}$ within two-fold in
90% of ten published datasets, whereas the intravenous-input assumption is wrong by roughly
an order of magnitude in both magnitude and timing. The novelty is thus a validated
methodology and tool, not a new equation.

## 4.2 Potential applications

Framed as an exploratory and educational tool, yoshika may be useful across several domains.

**Route-aware exploration of systemic exposure.** The comparison in §3.2 and the validation
in §3.3 together suggest that the intravenous-input assumption substantially overstates
$C_{max}$ for fascial plane blocks and infiltration and mis-times the peak. A route-aware
simulation gives predictions closer to reported concentrations and points to a plausible
later monitoring window. We frame these as hypotheses for prospective testing rather than
dosing instructions.

**Block success as a real-time input to scenario selection.** A practical extension follows
from the observation that regional block success is accompanied by measurable local vascular
and sympathetic changes: a successful block produces sympathectomy-mediated vasodilation that
can be detected non-invasively, for example as an increase in the pulse-oximeter perfusion
index or in skin temperature [@kus2013; @ginosar2009]. In principle such a signal could be
used to inform the choice of input scenario in real time---if a block appears successful, the
slow-release (vessel-poor-tissue) scenario may describe systemic exposure better than the
intravenous-input assumption, implying a lower and later peak and hence a correspondingly
later window for vigilance against delayed LAST; if the block appears to have failed, a
faster-absorption scenario with earlier monitoring would be the more prudent default. We
present this as a hypothesis enabled by the tool, not a validated protocol: prospective
studies linking an objective block-success signal to measured plasma concentrations would be
required before any such use.

**Clinical pharmacology and toxicology.** By making explicit how the assumed input route
changes predicted peak concentration and timing, yoshika offers a computational aid for
reconsidering how intravenous-derived mg/kg limits are applied to regional anesthesia,
where absorption kinetics differ [@neal2018; @rosenberg2004]. The context-sensitive maximum
dose framework (\autoref{tab:context_dose}) is presented as a conceptual proposal to be
tested, not an established guideline.

**Anesthesia information management systems.** yoshika demonstrates that route-adaptive PKPD
simulation is computationally inexpensive with standard ODE solvers and could in principle
be integrated into AIMS infrastructure, motivating administration-route-specific predictions
in place of a single intravenous-input model.

**Education and training.** yoshika provides an interactive environment for trainees to
visualize how injection site and absorption assumptions affect drug disposition, reinforcing
the pharmacokinetic principles underlying regional anesthesia.

**Research.** Its modular design facilitates extension to new drug models, custom compartment
configurations, and population analyses. The bundled validation dataset and pipeline provide
a reproducible baseline for future comparison.

## 4.3 Limitations and future work

Several limitations temper the interpretation of these results.

**Lumped compartments and disposition provenance.** As emphasized in §1.2, V2 and V3 are
fitted lumped compartments, not anatomical spaces, and the disposition parameters are derived
from intravenous or systemic data. Transferring them to peripheral injection sites is an
approximation; the validation (§3.3) supports order-of-magnitude and timing fidelity but not
quantitative accuracy, and the model should not be used for dosing decisions.

**Calibration and sampling.** In the validation, the absorption rate $k_a$ was calibrated to
the observed $T_{max}$, so $T_{max}$ agreement is imposed rather than predicted; the
independent test is on $C_{max}$. Reported concentrations also depend on sampling site
(venous vs arterial) and assay, which contributes to the systematic over- and
under-prediction patterns we describe.

**Phenomenological description of absorption.** The model is a phenomenological
compartmental description. The ordinary differential equations are, at a mechanistic level,
an approximation to the underlying diffusion (Smoluchowski) processes that govern local
anesthetic transfer between tissue, membrane, and aqueous compartments [@smrkolj2023;
@smrkolj2025]. In particular, after injection a substantial fraction of local anesthetic is
stored in lipophilic compartments (Schwann cell and other membranes, adipose tissue) and
released slowly; more lipophilic agents have larger storage capacity and correspondingly
longer duration of action [@strichartz1990; @kavcic2021]. Local tissue acidosis increases
the protonated fraction and lowers affinity for these lipophilic compartments, reducing
storage capacity and shortening duration of action [@kavcic2021; @smrkolj2025]. yoshika's
single depot rate constant lumps all of these effects into one absorption term and does not
represent pH- or lipophilicity-dependent storage explicitly.

**Perfusion and drug interactions.** Local perfusion is a critical determinant of systemic
absorption and duration that the fixed rate constants do not capture. Co-administered
vasoconstrictors such as adrenaline can prolong duration of action severalfold (as exploited
in dental surgery), whereas alcohol-induced vasodilation can shorten it substantially; a
combination of local acidosis and vasodilation may in the extreme abolish the anesthetic
effect. Representing these perfusion- and pH-dependent effects, ideally by coupling the
compartmental model to a diffusion-based description of intraneural and peri-neural transport
[@smrkolj2023; @smrkolj2025], is an important direction for future work.

**Scope.** Spinal (intrathecal) administration is not modeled (§2.2.5), and only four
local anesthetics are parameterized by default. Prospective studies measuring plasma
concentration profiles after various block types, with documented block success and sampling
site, would be needed to parameterize site-specific absorption and to test the
context-sensitive maximum dose hypothesis directly.

# 5. Conclusion

yoshika is an open-source Python package that makes the initial compartment of drug
deposition a selectable input for local anesthetic PKPD simulation. Using a standard
three-compartment model, it lets users compare route-aware scenarios---vessel-poor-tissue
("successful block"), vessel-rich-tissue ("failed block"), intravascular (plasma), and
depot absorption (fascial plane/epidural)---under shared disposition parameters. Its
contribution is methodological and practical rather than a new equation: it provides a
reproducible tool for systematic comparison and draws attention, with external validation,
to how strongly the assumed input route affects predicted peak exposure and timing.

External validation against ten published datasets indicates that a standard model with a
single route-specific absorption parameter reproduces observed peak concentrations within
two-fold in 90% of cases, whereas the intravenous-input assumption overstates peak
concentration roughly tenfold and mis-times the peak. These findings support using
route-aware simulation to generate hypotheses about regional anesthesia systemic exposure
and monitoring, while further prospective validation is required before any clinical dosing
application. The software is freely available under the MIT license and can be installed via
pip.

# Declaration of competing interest

The authors declare that they have no known competing financial interests or personal
relationships that could have appeared to influence the work reported in this paper.

# CRediT authorship contribution statement

**Tatsuki Onishi:** Conceptualization, Methodology, Software, Validation, Writing -- Original Draft, Writing -- Review & Editing.

# Data availability

yoshika is openly available under the MIT license from its public source repository and from
the Python Package Index (`pip install yoshika`; version 0.1.0). All code, the built-in drug
parameters, the digitized validation dataset, and the scripts used to produce every figure
and table in this article are included in the repository. The validation data were digitized
from the cited published studies; no new patient data were generated.

# Funding

This research did not receive any specific grant from funding agencies in the public,
commercial, or not-for-profit sectors.

# Ethics approval

Not applicable. This study did not involve human participants, human data, or animals; it
uses only computational simulation and pharmacokinetic parameters and summary values already
published in the cited literature.

# Declaration of generative AI and AI-assisted technologies in the writing process

During the preparation of this work the author used generative AI and AI-assisted tools to
support software development and to improve the language and readability of the manuscript.
After using these tools, the author reviewed and edited the content as needed and takes full
responsibility for the content of the publication.

# Acknowledgements

The author thanks the reviewers for their constructive comments, which prompted the external
validation and the expanded discussion of diffusion-based and perfusion-dependent mechanisms.

# References
