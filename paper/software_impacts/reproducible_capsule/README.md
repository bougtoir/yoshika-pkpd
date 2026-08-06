# yoshika — reproducible capsule

This capsule reproduces the **external-validation results and figures** of the
`yoshika` local-anesthetic PKPD package (the scientific results reported in the
Software Impacts article). It does **not** build the manuscript, highlights, or
cover letter.

The full source archive (this capsule plus the package, tests, and paper) is
archived on Zenodo: concept DOI `10.5281/zenodo.21816213` (latest version),
v0.1.0 `10.5281/zenodo.21816214`.

## What it does

Running the capsule executes `code/run.py`, which:

1. installs `yoshika==0.1.0` (from PyPI) and its dependencies (see
   `environment/requirements.txt`);
2. runs the published-data validation pipeline (`code/run_validation.py`) using
   the digitized clinical reference values in `code/validation_data.py`;
3. writes the following to the results directory:
   - `validation_results.csv` — full numeric table (observed vs predicted
     Cmax/Tmax, fold errors, calibrated `ka`);
   - `fig12_validation_cmax.png`, `fig13_validation_tmax.png`,
     `fig14_validation_curves.png` — validation figures;
   - `summary.txt` — geometric-mean fold error, % within two-fold, Pearson r.

## Reproducibility design

- Summary statistics are computed from source; none are hard-coded.
- Disposition parameters are held fixed; only the depot absorption rate `ka`
  is calibrated per study to the observed Tmax (one degree of freedom/study).
- No external raw data files are required; see `data/README.md`.

## Run locally (equivalent to Code Ocean)

```bash
pip install -r environment/requirements.txt
cd code && ./run          # results written to ../results
```

## On Code Ocean

Upload this folder as a capsule (Python), set the run command to `code/run`,
and add `environment/requirements.txt` to the environment. Results appear in
`/results`.
