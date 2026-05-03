# yoshika

**Y**ielding **O**pen **S**imulation of **H**ybrid **I**nter-disciplinary **K**inetic **A**bsorption

A Python PKPD (pharmacokinetic/pharmacodynamic) package for local anesthetics with **selectable initial compartment**.

## Motivation

Traditional 3-compartment PK models (Marsh, Schnider, Eleveld, etc.) assume intravenous administration where drug enters plasma (V1) first. However, in regional anesthesia:

- **Successful block** → drug starts in vessel-poor tissue (bpt/V3)
- **Failed block** → drug starts in vessel-rich tissue (brt/V2) or plasma

yoshika allows selecting the initial compartment to simulate these clinically distinct scenarios and compare their pharmacokinetic profiles.

## Installation

```bash
pip install yoshika
```

Or install from source:

```bash
git clone https://github.com/bougtoir/yoshika-pkpd.git
cd yoshika-pkpd
pip install -e ".[dev]"
```

## Quick Start

```python
from yoshika import Simulator, Drug, Compartment

# Create a simulator for bupivacaine 150mg in a 70kg patient
sim = Simulator(drug=Drug.BUPIVACAINE, dose_mg=150, weight_kg=70)

# Simulate with drug starting in vessel-poor tissue (successful block)
result = sim.run(initial_compartment=Compartment.BPT)

print(f"Peak plasma concentration: {result.pk.peak_plasma_concentration:.2f} mg/L")
print(f"Time to peak: {result.pk.time_to_peak:.1f} min")
```

## Compare Scenarios

Compare IV administration vs. successful vs. failed block:

```python
from yoshika import Simulator, Drug
from yoshika.plotting import plot_comparison
from yoshika.drugs import DrugLibrary

sim = Simulator(drug=Drug.BUPIVACAINE, dose_mg=150, weight_kg=70)
results = sim.compare()  # Runs plasma, brt, bpt scenarios

# Summary table
table = Simulator.summary_table(results)
print(table)

# Plot plasma concentration comparison with toxicity thresholds
params = DrugLibrary.get(Drug.BUPIVACAINE)
fig, ax = plot_comparison(results, drug_params=params)
fig.savefig("comparison.png", dpi=150)
```

## Supported Drugs

| Drug | V1 (L) | V2 (L) | V3 (L) | CNS Toxicity (mg/L) | CV Toxicity (mg/L) |
|------|---------|--------|--------|---------------------|-------------------|
| Lidocaine | 12.0 | 33.0 | 60.0 | 5.0 | 10.0 |
| Bupivacaine | 9.8 | 23.0 | 62.0 | 2.0 | 4.0 |
| Ropivacaine | 10.5 | 25.0 | 58.0 | 2.2 | 4.4 |
| Levobupivacaine | 10.0 | 24.0 | 60.0 | 2.5 | 5.0 |

## Compartment Model

```
                    ┌──────────────┐
                    │   PLASMA     │
                    │   (V1)       │◄──── k10 (elimination)
                    └──────┬───────┘
                     ▲     │     ▲
                k12/k21    │   k13/k31
                     │     │     │
              ┌──────┴──┐  │  ┌──┴──────┐
              │  BRT     │  │  │  BPT    │
              │  (V2)    │  │  │  (V3)   │
              │ vessel-  │  │  │ vessel- │
              │ rich     │  │  │ poor    │
              └──────────┘  │  └─────────┘
                            │
                    ┌───────┴──────┐
                    │   DEPOT      │
                    │ (injection)  │───── ka (absorption)
                    └──────────────┘
```

**Initial compartment options:**
- `Compartment.PLASMA` — IV administration (traditional model)
- `Compartment.BRT` — Failed block / intravascular injection
- `Compartment.BPT` — Successful peripheral block
- `Compartment.DEPOT` — Depot absorption (fascial plane blocks, **epidural administration**)

### Epidural Administration

Epidural administration can be approximated using the **Depot compartment** (`Compartment.DEPOT`). In epidural anesthesia, the drug is injected into the epidural space and is absorbed into the systemic circulation primarily through epidural venous plexus uptake, with concurrent diffusion across the dura into the CSF. This absorption process follows approximately first-order kinetics, which is modeled by the depot compartment's absorption rate constant (ka). While the actual epidural pharmacokinetics involves parallel pathways (vascular absorption, dural penetration, and epidural fat sequestration), the depot model provides a reasonable first-order approximation of the systemic absorption phase.

Users can adjust the `ka` parameter to match published epidural absorption rates for specific local anesthetics.

### Spinal (Intrathecal) Administration

Spinal (subarachnoid) administration is **not modeled** in the current version. Intrathecal injection delivers drug directly into the cerebrospinal fluid (CSF), involving unique pharmacokinetics (CSF spread, direct spinal cord uptake, and subsequent systemic absorption) that differ fundamentally from the peripheral compartment model. Additionally, spinal anesthesia is predominantly a single-shot technique with relatively small doses (e.g., bupivacaine 10–15 mg), making systemic toxicity modeling less clinically relevant compared to larger-dose peripheral nerve blocks and epidural techniques.

## Clinical Scenario Mapping

| Clinical Scenario | Initial Compartment | Rationale |
|---|---|---|
| IV injection | `Compartment.PLASMA` | Drug enters central circulation directly |
| Failed nerve block (intravascular) | `Compartment.BRT` | Accidental injection into vessel-rich tissue |
| Successful peripheral nerve block | `Compartment.BPT` | Drug deposited in vessel-poor tissue around nerves |
| Fascial plane block | `Compartment.DEPOT` | Absorption from tissue plane via first-order kinetics |
| Epidural administration | `Compartment.DEPOT` | Approximate: absorption from epidural space via first-order kinetics |
| Spinal (intrathecal) | *Not supported* | Requires CSF compartment (not implemented) |

## API Reference

### Core Classes

- **`Simulator`** — High-level simulation engine
- **`PKModel`** — 3-compartment PK ODE model
- **`Drug`** — Drug enum (LIDOCAINE, BUPIVACAINE, ROPIVACAINE, LEVOBUPIVACAINE)
- **`Compartment`** — Compartment enum (PLASMA, BRT, BPT, DEPOT)
- **`DrugLibrary`** — Drug parameter database
- **`EffectSiteModel`** — Effect-site equilibration (ke0)
- **`SigmoidEmaxModel`** — Sigmoid Emax PD model

### Plotting Functions

- **`plot_concentration(result)`** — Concentration-time curves for all compartments
- **`plot_comparison(results)`** — Multi-scenario plasma concentration comparison
- **`plot_effect(results)`** — PD effect comparison

### Utility Functions

- **`auc_trapezoidal(time, conc)`** — AUC calculation
- **`half_life_terminal(time, conc)`** — Terminal half-life estimation
- **`time_above_threshold(time, conc, threshold)`** — Duration above toxic threshold
- **`compartment_from_string(name)`** — String-to-Compartment conversion

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check yoshika/ tests/

# Type check
mypy yoshika/
```

## License

MIT License

## Citation

If you use yoshika in your research, please cite:

```bibtex
@article{yoshika2026,
  title={yoshika: A Python Package for Pharmacokinetic-Pharmacodynamic Simulation of Local Anesthetics with Selectable Initial Compartment},
  author={Onishi, Tatsuki},
  year={2026},
  journal={Computer Methods and Programs in Biomedicine Update}
}
```
