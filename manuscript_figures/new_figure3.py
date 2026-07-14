#!/usr/bin/env python3
"""Main Figure 3 — technical validation of pocket-derived records.

Adapted from `generate_scidata_main_figures.py::build_validation`
(Scientific Data Figure 3, "scidata_figure3_validation_ridgeline"), restyled to
match `new_figure1.py`.

Changes versus the original:
  - The external database scale comparison was removed.
  - Panels A and B form a compact double-column validation figure.
  - Recovery fractions occupy a dedicated annotation column outside the KDE
    region, preventing overlap with curves, ticks and axes.

All panels are generated from frozen CSVs. No trajectory I/O is performed.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-coupledmd")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

import figstyle

figstyle.apply_style()

HERE = Path(__file__).resolve().parent
V9 = HERE / "scidata_figures" / "v9_figure_inputs"
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

FAM_COL = figstyle.FAMILY
FAM_ORDER = ["Gi", "Gs", "Gq", "G12-13"]
FAM_LABEL = figstyle.FAMILY_LABEL
INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT

# Compact double-column typography, consistent with the revised Figure 2.
FS_PANEL = 10          # panel letter (A–B)
FS_LABEL = 8           # axis labels
FS_TICK = 7            # tick labels
FS_ANNOT = 6.5         # in-panel annotations / small text


def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        path = OUT / f"{name}.{ext}"
        fig.savefig(path, bbox_inches="tight", pad_inches=0.02,
                    dpi=600 if ext == "png" else None)
        print(f"  saved {path}")
    plt.close(fig)


def panel(ax, letter: str, x=-0.10, y=1.04) -> None:
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=FS_PANEL,
            fontweight="bold", va="bottom")


def load_tables() -> dict[str, pd.DataFrame]:
    return {
        "t4": pd.read_csv(V9 / "scidata_T4_technical_validation_v9.csv"),
        "t4a": pd.read_csv(V9 / "scidata_T4a_recovery_summary_v9.csv"),
    }


def make_figure3() -> None:
    tables = load_tables()
    t4, t4a = tables["t4"], tables["t4a"]
    assert len(t4) == 208 and t4["system_id"].is_unique
    assert t4["g_family"].value_counts().to_dict() == {
        "Gi": 95, "Gs": 65, "Gq": 42, "G12-13": 6}
    assert int(t4a.loc[t4a["subset"].eq("All v9"), "systems_n"].iloc[0]) == 208
    sub2fam = {"Gi/o": "Gi", "Gs": "Gs", "Gq/11": "Gq", "G12/13": "G12-13"}
    t4m = t4.copy()
    t4m["fam"] = t4m["g_family"]

    fig = plt.figure(figsize=(7.2, 3.45))
    gs = fig.add_gridspec(
        1, 2, width_ratios=[1.55, 1.0], wspace=0.34,
        left=0.09, right=0.985, top=0.90, bottom=0.18,
    )
    axA = fig.add_subplot(gs[0, 0])
    axB = fig.add_subplot(gs[0, 1])

    # ── Panel A: ridgeline of best_ortho_freq by family ──────────────────────
    rows_for_kde = t4m.dropna(subset=["best_ortho_freq"])
    ybase = np.linspace(0, 1, 200)
    for i, f in enumerate(FAM_ORDER):
        vals = rows_for_kde.loc[rows_for_kde["fam"] == f, "best_ortho_freq"].values
        if len(vals) == 1:
            vals = np.r_[vals, vals + 1e-3, vals - 1e-3]
        y0 = i
        if len(vals) >= 2:
            kde = gaussian_kde(vals, bw_method=0.25)
            dens = kde(ybase)
            dens = dens / dens.max() * 0.8
            axA.fill_between(ybase, y0, y0 + dens, color=FAM_COL[f], alpha=0.55, lw=0)
            axA.plot(ybase, y0 + dens, color=FAM_COL[f], lw=1.0)
            jit = np.random.RandomState(7 + i).uniform(-0.06, 0.06, size=len(vals))
            axA.plot(vals, y0 + 0.05 + jit * 0.5, "|", color=FAM_COL[f],
                     ms=4, alpha=0.5, mew=0.8)
        else:
            axA.text(0.825, y0 + 0.25, "no recovered pocket",
                     fontsize=FS_ANNOT, color=MUTED, va="center")
        rec = t4a.loc[t4a["subset"].map(sub2fam) == f]
        if len(rec):
            rec = rec.iloc[0]
            recovered = int(rec["orthosteric_recovered"])
            total = int(rec["systems_with_pockets"])
            rate = float(rec["recovery_rate_percent"])
            axA.text(
                1.058, y0 + 0.40, f"{recovered}/{total} ({rate:.1f}%)",
                ha="right", va="center", fontsize=FS_ANNOT,
                color=FAM_COL[f], fontweight="bold", clip_on=False,
            )
    axA.axvline(0.85, color=INK, lw=0.8, ls="--", alpha=0.7)
    axA.axvline(1.008, color=PALE, lw=0.7)
    axA.text(0.852, 4.12, "threshold = 0.85", fontsize=FS_ANNOT,
             color=INK, va="center", ha="left")
    axA.text(1.058, 4.12, "Proportion recovered", fontsize=FS_ANNOT,
             color=MUTED, va="center", ha="right", fontweight="bold")
    axA.set_yticks(range(len(FAM_ORDER)))
    axA.set_yticklabels([FAM_LABEL[f] for f in FAM_ORDER], fontsize=FS_TICK)
    axA.set_ylim(-0.15, 4.28)
    axA.set_xlim(0.80, 1.065)
    axA.set_xticks([0.80, 0.85, 0.90, 0.95, 1.00])
    axA.set_xlabel("best orthosteric-pocket frequency (per system)",
                   fontsize=FS_LABEL)
    axA.tick_params(axis="x", labelsize=FS_TICK)
    figstyle.despine(axA)
    panel(axA, "A")

    # ── Panel B: n_pockets lollipop by family (median ± IQR) ─────────────────
    grp = t4m.groupby("fam")["n_pockets"]
    med = grp.median().reindex(FAM_ORDER)
    q1 = grp.quantile(0.25).reindex(FAM_ORDER)
    q3 = grp.quantile(0.75).reindex(FAM_ORDER)
    xs = np.arange(len(FAM_ORDER))
    for x, f in zip(xs, FAM_ORDER):
        axB.plot([x, x], [q1[f], q3[f]], color=FAM_COL[f], lw=3, alpha=0.5,
                 solid_capstyle="round")
        axB.plot(x, med[f], "o", color=FAM_COL[f], ms=7, zorder=3)
        vals = t4m.loc[t4m["fam"] == f, "n_pockets"].values
        jit = np.random.RandomState(11 + x).uniform(-0.12, 0.12, size=len(vals))
        axB.plot(x + jit, vals, ".", color=FAM_COL[f], alpha=0.35, ms=2.5)
    axB.set_xticks(xs)
    axB.set_xticklabels([FAM_LABEL[f] for f in FAM_ORDER], fontsize=FS_TICK)
    axB.tick_params(axis="y", labelsize=FS_TICK)
    axB.set_ylabel("pockets / system", fontsize=FS_LABEL)
    axB.set_ylim(0, 22)
    axB.text(0.98, 0.97, "median ± IQR", transform=axB.transAxes,
             ha="right", va="top", fontsize=FS_ANNOT, color=MUTED)
    figstyle.despine(axB)
    panel(axB, "B")

    # No suptitle / no per-subpanel titles; caption carries interpretation.
    save(fig, "v9_figure3_validation_ridgeline")


if __name__ == "__main__":
    print("Figure 3 (validation ridgeline) …")
    make_figure3()
