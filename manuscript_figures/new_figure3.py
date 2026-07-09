#!/usr/bin/env python3
"""Main Figure 3 — binding-site validation and dataset scope.

Adapted from `generate_scidata_main_figures.py::build_validation`
(Scientific Data Figure 3, "scidata_figure3_validation_ridgeline"), restyled to
match `new_figure1.py`.

Changes versus the original:
  - No per-subpanel titles (descriptive subtitles removed).
  - Enlarged panel letters, axis labels, tick labels and annotations
    (FS_* constants match new_figure1.py exactly).
  - Panel A: recovery-% and the 0.85-threshold callout moved into the
    headroom above the ridges so they no longer sit on top of the KDE curves.
  - tight_layout / bbox_inches="tight" for a compact, border-free composition.

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
TBL = HERE / "tables"
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

FAM_COL = figstyle.FAMILY
FAM_ORDER = ["Gi", "Gs", "Gq", "G12-13"]
FAM_LABEL = figstyle.FAMILY_LABEL
INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT

# Enlarged typography — matches new_figure1.py so the two figures read as one set.
FS_PANEL = 13          # panel letter (A–C)
FS_LABEL = 11          # axis labels
FS_TICK = 9            # tick labels
FS_ANNOT = 8           # in-panel annotations / small text


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
        "s1": pd.read_csv(TBL / "scidata_S1_included_systems_clean_v1.csv"),
        "t4": pd.read_csv(TBL / "scidata_T4_technical_validation_clean_v1.csv"),
        "t4a": pd.read_csv(TBL / "scidata_T4a_recovery_summary_clean_v1.csv"),
    }


def make_figure3() -> None:
    s1, t4, t4a = (load_tables()[k] for k in ("s1", "t4", "t4a"))
    sub2fam = {"Gi/o": "Gi", "Gs": "Gs", "Gq/11": "Gq", "G12/13": "G12-13"}
    t4m = t4.copy()
    t4m["fam"] = t4m["g_family"]

    fig = plt.figure(figsize=(7.4, 8.2))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.4, 1.0, 0.7],
                          hspace=0.55, left=0.17, right=0.96,
                          top=0.96, bottom=0.10)
    axA = fig.add_subplot(gs[0])
    axB = fig.add_subplot(gs[1])
    axC = fig.add_subplot(gs[2])

    # ── Panel A: ridgeline of best_ortho_freq by family ──────────────────────
    rows_for_kde = t4m.dropna(subset=["best_ortho_freq"])
    ybase = np.linspace(0, 1, 200)
    for i, f in enumerate(FAM_ORDER):
        vals = rows_for_kde.loc[rows_for_kde["fam"] == f, "best_ortho_freq"].values
        if len(vals) < 2 or np.allclose(vals.std(), 0):
            vals = np.r_[vals, vals + 1e-3, vals - 1e-3]
        kde = gaussian_kde(vals, bw_method=0.25)
        dens = kde(ybase)
        dens = dens / dens.max() * 0.8
        y0 = i
        axA.fill_between(ybase, y0, y0 + dens, color=FAM_COL[f], alpha=0.55, lw=0)
        axA.plot(ybase, y0 + dens, color=FAM_COL[f], lw=1.0)
        jit = np.random.RandomState(7 + i).uniform(-0.06, 0.06, size=len(vals))
        axA.plot(vals, y0 + 0.05 + jit * 0.5, "|", color=FAM_COL[f],
                 ms=4, alpha=0.5, mew=0.8)
        rr = t4a.loc[t4a["subset"].map(sub2fam) == f, "recovery_rate_percent"]
        rr = float(rr.iloc[0]) if len(rr) else 0.0
        # Place the recovery-% in the headroom directly above each ridge so it
        # never sits on top of the KDE curve.
        axA.text(0.992, y0 + 0.92, f"{FAM_LABEL[f]}  {rr:.1f}% recovered",
                 ha="right", va="center", fontsize=FS_ANNOT,
                 color=FAM_COL[f], fontweight="bold")
    axA.axvline(0.85, color=INK, lw=0.8, ls="--", alpha=0.7)
    # Threshold callout moved into the headroom above the top ridge.
    axA.text(0.853, len(FAM_ORDER) + 0.6, "0.85 recovery threshold",
             fontsize=FS_ANNOT, color=INK, va="center", ha="left")
    axA.set_yticks(range(len(FAM_ORDER)))
    axA.set_yticklabels([FAM_LABEL[f] for f in FAM_ORDER], fontsize=FS_TICK)
    axA.set_ylim(-0.2, len(FAM_ORDER) + 0.9)
    axA.set_xlim(0.80, 1.0)
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
    figstyle.despine(axB)
    panel(axB, "B")

    # ── Panel C: dataset scope (systems vs aggregate µs) ─────────────────────
    datasets = ["GPCRmd\n(single receptor)", "mdCATH\n(single domain)",
                "This work\n(complex)"]
    systems = [60, 5398, 208]
    sampling = [40, 320, 312]      # aggregate µs (order of magnitude)
    x = np.arange(len(datasets))
    w = 0.38
    axC.bar(x - w / 2, systems, w, color=PALE, edgecolor=INK, lw=0.5,
            label="systems")
    axC.bar(x + w / 2, sampling, w, color=[MUTED, MUTED, ACCENT],
            edgecolor=INK, lw=0.5, label="aggregate µs")
    axC.set_yscale("log")
    axC.set_xticks(x)
    axC.set_xticklabels(datasets, fontsize=FS_TICK)
    axC.tick_params(axis="y", labelsize=FS_TICK)
    axC.set_ylabel("count (log)", fontsize=FS_LABEL)
    axC.legend(frameon=False, fontsize=FS_ANNOT, loc="upper left", ncol=2)
    for xi, v in zip(x - w / 2, systems):
        axC.text(xi, v * 1.12, f"{v}", ha="center", fontsize=FS_ANNOT, color=INK)
    for xi, v in zip(x + w / 2, sampling):
        axC.text(xi, v * 1.12, f"{v}", ha="center", fontsize=FS_ANNOT, color=INK)
    figstyle.despine(axC)
    panel(axC, "C")

    # No suptitle / no per-subpanel titles; compact, border-free composition.
    fig.tight_layout(pad=0.5)
    save(fig, "new_figure3_validation_ridgeline")


if __name__ == "__main__":
    print("Figure 3 (validation ridgeline) …")
    make_figure3()
