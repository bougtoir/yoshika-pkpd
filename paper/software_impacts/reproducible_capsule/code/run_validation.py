"""External validation of yoshika against published depot-route LA plasma data.

For each published study, the depot absorption rate constant (ka) is calibrated
so that the model reproduces the observed time-to-peak (Tmax); the resulting
predicted peak concentration (Cmax) is then compared with the observed value.
This isolates the question the reviewers raised: given the correct absorption
timing, does a three-compartment model built on intravenously-derived
disposition parameters predict the observed peak plasma concentration after
non-intravenous administration?

The intravenous-forced model (dose placed in the central compartment, the
assumption of conventional simulators) is included as a reference to show the
magnitude of the error that motivates the depot approach.

Outputs:
  paper/figures/fig12_validation_cmax.png   observed vs predicted Cmax
  paper/figures/fig13_validation_tmax.png   observed vs predicted Tmax
  paper/validation_results.csv              full numeric table
"""

from __future__ import annotations

import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from validation_data import VALIDATION_DATA

from yoshika.compartments import Compartment
from yoshika.drugs import DrugLibrary
from yoshika.model import PKModel

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE, "figures")


def _tmax_for_ka(params, dose_mg: float, ka: float) -> tuple[float, float]:
    res = PKModel(
        drug_params=params, dose_mg=dose_mg,
        initial_compartment=Compartment.DEPOT, ka_override=ka,
    ).solve(duration_min=600.0, dt=0.25)
    return res.time_to_peak, res.peak_plasma_concentration


def calibrate_ka(params, dose_mg: float, target_tmax: float) -> float:
    """Find ka (1/min) whose predicted Tmax matches the observed Tmax.

    Tmax is monotonically decreasing in ka, so a bisection search converges.
    """
    lo, hi = 0.005, 0.60
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        tmax, _ = _tmax_for_ka(params, dose_mg, mid)
        if tmax > target_tmax:  # too slow -> need larger ka
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def run() -> list[dict]:
    rows: list[dict] = []
    for rec in VALIDATION_DATA:
        params = DrugLibrary.get_by_name(rec.drug)
        ka = calibrate_ka(params, rec.dose_mg, rec.obs_tmax_min)
        pred_tmax, pred_cmax = _tmax_for_ka(params, rec.dose_mg, ka)

        iv = PKModel(
            drug_params=params, dose_mg=rec.dose_mg,
            initial_compartment=Compartment.PLASMA,
        ).solve(duration_min=600.0, dt=0.25)

        rows.append({
            "label": rec.label,
            "drug": rec.drug,
            "route": rec.route,
            "dose_mg": rec.dose_mg,
            "sampling": rec.sampling,
            "obs_cmax": rec.obs_cmax_mg_l,
            "obs_tmax": rec.obs_tmax_min,
            "ka_fit": round(ka, 4),
            "abs_halflife_min": round(np.log(2) / ka, 1),
            "pred_cmax": round(pred_cmax, 2),
            "pred_tmax": round(pred_tmax, 1),
            "cmax_fold_error": round(pred_cmax / rec.obs_cmax_mg_l, 2),
            "iv_forced_cmax": round(iv.peak_plasma_concentration, 1),
            "iv_forced_tmax": round(iv.time_to_peak, 1),
            "reference": rec.reference,
        })
    return rows


def _fmt_stats(rows: list[dict]) -> dict:
    fold = np.array([r["cmax_fold_error"] for r in rows])
    obs = np.array([r["obs_cmax"] for r in rows])
    pred = np.array([r["pred_cmax"] for r in rows])
    # geometric mean fold error and % within 2-fold
    gmfe = float(np.exp(np.mean(np.abs(np.log(fold)))))
    within2 = float(np.mean((fold >= 0.5) & (fold <= 2.0)) * 100.0)
    rmse = float(np.sqrt(np.mean((pred - obs) ** 2)))
    r = float(np.corrcoef(obs, pred)[0, 1])
    return {"gmfe": gmfe, "within2_pct": within2, "rmse": rmse, "pearson_r": r}


def make_figures(rows: list[dict]) -> None:
    os.makedirs(FIG_DIR, exist_ok=True)
    routes = sorted({r["route"] for r in rows})
    cmap = plt.get_cmap("tab10")
    color = {rt: cmap(i) for i, rt in enumerate(routes)}

    # ---- Cmax observed vs predicted ----
    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    for r in rows:
        m = "o" if r["sampling"] == "venous" else "^"
        ax.scatter(r["obs_cmax"], r["pred_cmax"], s=70, color=color[r["route"]],
                   marker=m, edgecolor="k", linewidth=0.5, zorder=3)
    hi = max(max(r["obs_cmax"] for r in rows), max(r["pred_cmax"] for r in rows)) * 1.15
    ax.plot([0, hi], [0, hi], "k-", lw=1, label="line of identity")
    ax.plot([0, hi], [0, 2 * hi], "k--", lw=0.7, alpha=0.6, label="2-fold")
    ax.plot([0, hi], [0, 0.5 * hi], "k--", lw=0.7, alpha=0.6)
    ax.set_xlim(0, hi)
    ax.set_ylim(0, hi)
    ax.set_xlabel("Observed Cmax (mg/L)")
    ax.set_ylabel("Predicted Cmax (mg/L), ka calibrated to Tmax")
    ax.set_title("External validation: peak plasma concentration")
    handles = [plt.Line2D([], [], marker="o", ls="", color=color[rt],
                          markeredgecolor="k", label=rt) for rt in routes]
    handles += [
        plt.Line2D([], [], marker="o", ls="", color="grey", label="venous sample"),
        plt.Line2D([], [], marker="^", ls="", color="grey", label="arterial sample"),
        plt.Line2D([], [], ls="-", color="k", label="identity"),
        plt.Line2D([], [], ls="--", color="k", label="2-fold interval"),
    ]
    ax.legend(handles=handles, fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig12_validation_cmax.png"), dpi=300)
    plt.close(fig)

    # ---- Tmax observed vs predicted (+ IV-forced reference at 0) ----
    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    for r in rows:
        ax.scatter(r["obs_tmax"], r["pred_tmax"], s=70, color=color[r["route"]],
                   marker="o", edgecolor="k", linewidth=0.5, zorder=3)
        ax.scatter(r["obs_tmax"], r["iv_forced_tmax"], s=45, color="red",
                   marker="x", zorder=2)
    hi = max(r["obs_tmax"] for r in rows) * 1.2
    ax.plot([0, hi], [0, hi], "k-", lw=1)
    ax.set_xlim(0, hi)
    ax.set_ylim(-3, hi)
    ax.set_xlabel("Observed Tmax (min)")
    ax.set_ylabel("Predicted Tmax (min)")
    ax.set_title("External validation: time to peak")
    handles = [plt.Line2D([], [], marker="o", ls="", color=color[rt],
                          markeredgecolor="k", label=rt) for rt in routes]
    handles.append(plt.Line2D([], [], marker="x", ls="", color="red",
                              label="IV-forced model (Tmax=0)"))
    ax.legend(handles=handles, fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig13_validation_tmax.png"), dpi=300)
    plt.close(fig)


def make_overlay_figure(rows: list[dict]) -> None:
    """Predicted concentration-time curves with the observed (Cmax, Tmax) point.

    Only summary parameters (Cmax, Tmax +/- SD) were available from the primary
    sources, so the observed data are shown as a single marker with error bars
    rather than a digitized curve.
    """
    picks = [
        "Intercostal 1.0% (200 mg)",
        "TAP block (arterial, 150 mg)",
        "Axillary plexus ropiv (~175 mg)",
        "Epidural lidocaine 2% (~350 mg)",
    ]
    by_label = {r["label"]: r for r in rows}
    obs = {r.label: r for r in VALIDATION_DATA}
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5))
    for ax, label in zip(axes.ravel(), picks):
        r = by_label[label]
        rec = obs[label]
        params = DrugLibrary.get_by_name(r["drug"])
        res = PKModel(
            drug_params=params, dose_mg=r["dose_mg"],
            initial_compartment=Compartment.DEPOT, ka_override=r["ka_fit"],
        ).solve(duration_min=240.0, dt=0.25)
        ax.plot(res.time, res.plasma_concentration, "b-", lw=1.8,
                label="yoshika (depot)")
        iv = PKModel(drug_params=params, dose_mg=r["dose_mg"],
                     initial_compartment=Compartment.PLASMA).solve(
            duration_min=240.0, dt=0.25)
        ax.plot(iv.time, iv.plasma_concentration, "r--", lw=1.0, alpha=0.7,
                label="IV-forced")
        ax.errorbar(rec.obs_tmax_min, rec.obs_cmax_mg_l,
                    xerr=rec.obs_tmax_sd, yerr=rec.obs_cmax_sd, fmt="ks",
                    ms=7, capsize=3, zorder=5, label="observed Cmax/Tmax")
        ax.set_title(f"{label}\n[{rec.reference}]", fontsize=9)
        ax.set_xlabel("Time (min)")
        ax.set_ylabel("Plasma conc. (mg/L)")
        ax.set_xlim(0, 240)
        top = max(rec.obs_cmax_mg_l + rec.obs_cmax_sd, r["pred_cmax"]) * 1.6
        ax.set_ylim(0, top)
        ax.legend(fontsize=7, loc="upper right")
    fig.suptitle("Predicted concentration-time profiles vs observed peaks",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(FIG_DIR, "fig14_validation_curves.png"), dpi=300)
    plt.close(fig)


def main() -> None:
    rows = run()
    stats = _fmt_stats(rows)
    fields = list(rows[0].keys())
    with open(os.path.join(HERE, "validation_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    make_figures(rows)
    make_overlay_figure(rows)

    print(f"{'Study':<38}{'obs Cmax':>9}{'pred':>7}{'fold':>6}"
          f"{'obs Tmax':>9}{'IV Cmax':>9}")
    for r in rows:
        print(f"{r['label']:<38}{r['obs_cmax']:>9}{r['pred_cmax']:>7}"
              f"{r['cmax_fold_error']:>6}{r['obs_tmax']:>9}{r['iv_forced_cmax']:>9}")
    print("-" * 88)
    print(f"n={len(rows)}  geometric-mean fold error (Cmax)={stats['gmfe']:.2f}  "
          f"within 2-fold={stats['within2_pct']:.0f}%  "
          f"Pearson r={stats['pearson_r']:.2f}")
    print("IV-forced model predicts Tmax=0 for every study "
          "(observed range "
          f"{min(r['obs_tmax'] for r in rows):.0f}-{max(r['obs_tmax'] for r in rows):.0f} min).")


if __name__ == "__main__":
    main()
