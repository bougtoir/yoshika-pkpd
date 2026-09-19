#!/usr/bin/env python3
"""Reproducible-capsule entrypoint for the yoshika external validation.

Runs the published-data validation pipeline and writes the numeric results
table and the validation figures to the Code Ocean results directory.

This script deliberately reproduces ONLY the scientific validation
(Cmax/Tmax comparison and figures). It does not build the manuscript,
highlights, or cover letter.
"""
from __future__ import annotations

import csv
import os

import run_validation as rv

# Code Ocean mounts an output directory at /results; fall back to ../results
# so the capsule can also be run locally for testing.
RESULTS_DIR = "/results" if os.path.isdir("/results") else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "results"
)
RESULTS_DIR = os.path.abspath(RESULTS_DIR)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Redirect the pipeline's figure output into the results directory.
rv.FIG_DIR = RESULTS_DIR


def main() -> None:
    rows = rv.run()

    csv_path = os.path.join(RESULTS_DIR, "validation_results.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    rv.make_figures(rows)
    rv.make_overlay_figure(rows)

    stats = rv._fmt_stats(rows)
    summary = (
        f"n={len(rows)}  "
        f"geometric-mean fold error (Cmax)={stats['gmfe']:.2f}  "
        f"within 2-fold={stats['within2_pct']:.0f}%  "
        f"Pearson r={stats['pearson_r']:.2f}\n"
        "IV-forced model predicts Tmax=0 for every study "
        "(observed range 11-58 min).\n"
    )
    with open(os.path.join(RESULTS_DIR, "summary.txt"), "w") as f:
        f.write(summary)
    print(summary, end="")
    print(f"Wrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
