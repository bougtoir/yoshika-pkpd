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
