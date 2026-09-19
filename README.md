# yoshika

**Y**ielding **O**pen **S**imulation of **H**ybrid **I**nter-disciplinary **K**inetic **A**bsorption — a Python package for pharmacokinetic–pharmacodynamic (PK/PD) simulation of local anesthetics with a **selectable initial compartment**.

Traditional compartmental PK models (Marsh, Schnider, Eleveld, …) assume intravenous administration, where drug first enters the central plasma compartment. In regional anesthesia the drug is instead deposited in tissue and reaches plasma by absorption. `yoshika` makes the initial site of drug placement an explicit, selectable input so that different administration-route scenarios can be simulated and compared under shared disposition parameters.

Selectable initial compartments:

- `PLASMA` — intravenous / central compartment
- `BRT` — vessel-rich tissue
- `BPT` — vessel-poor tissue
- `DEPOT` — depot / fascial-plane approximation (first-order absorption; also used to approximate epidural administration)

> **Scope.** `yoshika` is a research and educational simulation tool. It is **not** a clinical dosing calculator and does not provide clinically validated dosing guidance.

## Installation

```bash
pip install yoshika
```

Requires Python ≥ 3.9 (NumPy, SciPy, Matplotlib, pandas).

## Quick start

```python
from yoshika.model import PKModel
from yoshika.drugs import Drug
from yoshika.compartments import Compartment

# Depot (fascial-plane) administration of bupivacaine
model = PKModel(
    drug=Drug.BUPIVACAINE,
    dose_mg=150,
    initial_compartment=Compartment.DEPOT,
)
result = model.solve(duration_min=600, dt=0.25)

print(result.peak_plasma_concentration)  # Cmax (mg/L)
print(result.time_to_peak)               # Tmax (min)
```

Switch `initial_compartment` to `Compartment.PLASMA`, `Compartment.BRT`, or `Compartment.BPT` to compare route/input scenarios for the same drug and dose.

## Custom drugs and simulation scenarios

The built-in library covers lidocaine, bupivacaine, ropivacaine and
levobupivacaine. To simulate another agent (or an alternative parameter set for
an existing one), build a `DrugParameters` object and pass it directly to
`Simulator` / `PKModel`, or register it in the library under a string key:

```python
from dataclasses import replace

from yoshika.drugs import DrugParameters, DrugLibrary, Drug
from yoshika.compartments import Compartment
from yoshika.simulator import Simulator
from yoshika.model import PKModel

# 1) Define a drug from scratch (units: L, L/min, 1/min, mg/L).
#    The numbers below are placeholders to show the required fields; replace
#    them with values from the literature for the agent you are modelling.
mepivacaine = DrugParameters(
    name="Mepivacaine",
    v1=15.0, v2=30.0, v3=45.0,      # compartment volumes (L)
    cl=0.78, q2=0.90, q3=0.30,      # clearance and inter-compartmental flows (L/min)
    ke0=0.12,                       # effect-site equilibration (1/min)
    ka_depot=0.05,                  # default depot absorption rate (1/min)
    ec50=3.0, gamma=2.0,            # sigmoid-Emax effect model
    toxic_cns=5.0, toxic_cv=10.0,   # reference toxicity thresholds (mg/L)
    protein_binding=0.77, pka=7.6, molecular_weight=246.35,
    reference="<literature source for these values>",  # placeholder values
)

# 2) Or derive a variant from a built-in drug and change a few fields.
slow_absorption_lidocaine = replace(
    DrugLibrary.get(Drug.LIDOCAINE), name="Lidocaine (slow depot)", ka_depot=0.02
)

# 3a) Use the custom parameters directly ...
sim = Simulator(drug_params=mepivacaine, dose_mg=300, weight_kg=70)
results = sim.compare()                     # plasma / BRT / BPT scenarios
print(Simulator.summary_table(results))

# 3b) ... or register them so they can be looked up by name later.
DrugLibrary.add_custom_drug("mepivacaine", mepivacaine)
params = DrugLibrary.get_by_name("mepivacaine")

# 4) Any drug can be run with an explicit initial compartment and an
#    absorption rate override for a specific block type.
model = PKModel(
    drug_params=params,
    dose_mg=300,
    initial_compartment=Compartment.DEPOT,
    ka_override=0.03,               # e.g. a slowly absorbing fascial-plane block
)
result = model.solve(duration_min=600, dt=0.25)
print(result.peak_plasma_concentration, result.time_to_peak)
```

`DrugLibrary.get_absorption_rates()` returns the suggested depot absorption
rates by block type that ship with the package, which can be used as starting
values for `ka_override`. Every `DrugParameters` field is documented in
`yoshika/drugs.py`; please record the literature source of any custom values in
the `reference` field so that simulations remain traceable.

## External validation

The repository includes a reproducible external-validation pipeline
(`paper/run_validation.py`) that compares model predictions against ten
published clinical pharmacokinetic datasets (intercostal, fascial-plane and
peripheral-nerve blocks, and epidural administration; ropivacaine, bupivacaine,
lidocaine). Disposition parameters are held fixed and only the depot absorption
rate `ka` is calibrated per study to the reported time-to-peak:

- geometric-mean fold error (Cmax) = 1.51
- 90% of predicted Cmax within two-fold of observation
- Pearson r = 0.81 (observed vs predicted Cmax)

An intravenous-input baseline over-predicts Cmax by roughly an order of
magnitude and predicts Tmax = 0, illustrating why the initial-compartment
choice matters.

## Reproduce

```bash
pip install -e .
pip install pytest
python -m pytest -q                 # test suite
python paper/run_validation.py      # regenerate validation table + figures
```

All quantitative results and figures are regenerated from source; nothing is
hard-coded.

## Citation

If you use `yoshika`, please cite the accompanying peer-reviewed article:

> Onishi T. yoshika: a Python package for pharmacokinetic-pharmacodynamic
> simulation of local anesthetics with selectable initial compartment.
> *Array* 2026;31:101106. https://doi.org/10.1016/j.array.2026.101106

Archived source (Zenodo): concept DOI
[10.5281/zenodo.21816213](https://doi.org/10.5281/zenodo.21816213)
(latest version; v0.1.0 is
[10.5281/zenodo.21816214](https://doi.org/10.5281/zenodo.21816214)).

## License

MIT — see [LICENSE](LICENSE).
