#!/usr/bin/env python3
"""Main Figure 5 — drug-design pocket atlas.

Adapted from `generate_scidata_extra_figures.py::fig6_pocket_atlas`
(Scientific Data Figure 6 candidate, "scidata_figure6_drug_design_pocket_atlas"),
restyled to match `new_figure1.py`.

Changes versus the original:
  - No figure title (suptitle removed).
  - Enlarged panel letters, subpanel titles, axis labels, tick labels and
    annotations (FS_* constants match new_figure1.py exactly).
  - Panel A is a blank, axis-off slot reserved for a portal snapshot to be
    composed in by hand. The former data panels are shifted one letter on:
    A→B (clusters), B→C (zones), C→D (anchors), D→E (validation),
    E→F (nominations). All six cells of the 2×3 grid are now occupied.

All panels are generated from frozen CSVs plus the local API JSON consensus
layer used by www.coupledmd.cn. No trajectory I/O is performed.
"""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-coupledmd")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import figstyle

figstyle.apply_style()

HERE = Path(__file__).resolve().parent
V9 = HERE / "scidata_figures" / "v9_figure_inputs"
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

FAM_COL = figstyle.FAMILY
FAM_LABEL = figstyle.FAMILY_LABEL
INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT
ZONE_COL = {
    "orthosteric": "#b23a48",
    "tm_core_allosteric": "#155e63",
    "intracellular_allosteric": "#8a4aa0",
    "coupling_interface": "#586170",
    "other": "#aab2bd",
}
ZONE_LABEL = {
    "orthosteric": "Orthosteric",
    "tm_core_allosteric": "TM-core allosteric",
    "intracellular_allosteric": "Intracellular allosteric",
    "coupling_interface": "Coupling interface",
    "extracellular_vestibule": "Extracellular vestibule",
    "other": "Other",
}

# Enlarged typography — matches new_figure1.py so the figures read as one set.
FS_PANEL = 13          # panel letter (A–E)
FS_TITLE = 12          # subpanel titles
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


def load_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return (
        pd.read_csv(V9 / "scidata_S4_per_pocket_v9.csv"),
        pd.read_csv(V9 / "scidata_S4a_pocket_source_status_v9.csv"),
        pd.read_csv(V9 / "scidata_T4a_recovery_summary_v9.csv"),
    )


def make_figure5() -> None:
    pockets, sources, t4a = load_tables()
    assert len(sources) == 208
    assert sources["pocket_record_status"].value_counts().to_dict() == {"available": 208}
    assert len(pockets) == 2168
    per_system = pockets.groupby(["system_id", "receptor_name", "g_family"]).agg(
        n_pockets=("pocket_id", "count"),
        mean_freq=("mean_freq", "mean"),
        mean_voxels=("n_voxels", "mean"),
    ).reset_index()

    fig = plt.figure(figsize=(10.8, 7.0))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.15, 1.0, 1.1],
                          wspace=0.48, hspace=0.55,
                          left=0.07, right=0.97, top=0.90, bottom=0.09)
    ax_snap = fig.add_subplot(gs[0, 0])  # A — snapshot slot (blank, added by hand)
    ax_snap.set_axis_off()
    ax_sc = fig.add_subplot(gs[0, 1])    # B
    ax_zone = fig.add_subplot(gs[0, 2])  # C
    ax_gn = fig.add_subplot(gs[1, 0])    # D
    ax_rec = fig.add_subplot(gs[1, 1])   # E
    ax_nom = fig.add_subplot(gs[1, 2])   # F

    # ── B: per-system pocket landscape, recalculated for v9 ─────────────────
    for family, sub in per_system.groupby("g_family"):
        ax_sc.scatter(sub["n_pockets"], sub["mean_freq"],
                      s=18 + 0.10 * sub["mean_voxels"].fillna(0),
                      color=FAM_COL.get(family, MUTED), alpha=0.65,
                      edgecolor="white", lw=0.35,
                      label=FAM_LABEL.get(family, family))
    ax_sc.set_xlabel("pockets per system", fontsize=FS_LABEL)
    ax_sc.set_ylabel("mean pocket occupancy", fontsize=FS_LABEL)
    ax_sc.set_title("Per-system pocket landscape",
                    fontsize=FS_TITLE, loc="left", pad=4)
    ax_sc.set_ylim(0.45, 1.02)
    ax_sc.tick_params(axis="both", labelsize=FS_TICK)
    ax_sc.grid(color=PALE, lw=0.4)
    ax_sc.legend(frameon=False, loc="lower right", fontsize=FS_ANNOT,
                 handletextpad=0.45, labelspacing=0.35, borderaxespad=0.35)
    panel(ax_sc, "B")

    # ── A: snapshot slot (blank, to be composed in by hand) ───────────────────
    panel(ax_snap, "A")

    # ── B: pocket zones ──────────────────────────────────────────────────────
    zone_counts = Counter()
    zone_counts.update(pockets["zone"].fillna("other"))
    zitems = sorted(zone_counts.items(), key=lambda kv: kv[1], reverse=True)
    zkeys = [z for z, _ in zitems][::-1]
    zvals = [v for _, v in zitems][::-1]
    ypos = np.arange(len(zkeys))
    ax_zone.barh(ypos, zvals,
                 color=[ZONE_COL.get(z, MUTED) for z in zkeys])
    zone_ticklabels = {
        "tm_core_allosteric": "TM-core\nallosteric",
        "intracellular_allosteric": "Intracellular\nallosteric",
        "extracellular_vestibule": "Extracellular\nvestibule",
    }
    ax_zone.set_yticks(ypos)
    ax_zone.set_yticklabels(
        [zone_ticklabels.get(z, ZONE_LABEL.get(z, z.replace("_", " ")))
         for z in zkeys],
        fontsize=FS_TICK, linespacing=1.15,
    )
    ax_zone.set_xlabel("pockets", fontsize=FS_LABEL)
    ax_zone.set_title("Pocket zones", fontsize=FS_TITLE, loc="left", pad=4)
    ax_zone.tick_params(axis="both", labelsize=FS_TICK)
    panel(ax_zone, "C")

    # ── C: reusable GPCRdb-position anchors ──────────────────────────────────
    gn = Counter()
    for value in pockets["receptor_generic_numbers"].dropna():
        gn.update([item for item in str(value).split(";") if item])
    top_gn = gn.most_common(18)[::-1]
    ax_gn.barh([k for k, _ in top_gn], [v for _, v in top_gn], color=ACCENT)
    ax_gn.set_xlabel("pockets containing position", fontsize=FS_LABEL)
    ax_gn.set_title("Reusable GPCRdb-position anchors",
                    fontsize=FS_TITLE, loc="left", pad=4)
    ax_gn.tick_params(axis="both", labelsize=FS_TICK)
    panel(ax_gn, "D")

    # ── D: binding-site validation (orthosteric recovery) ────────────────────
    rec = t4a[t4a["subset"] != "All v9"].copy()
    rec["family"] = rec["subset"].replace(
        {"Gi/o": "Gi", "Gq/11": "Gq", "G12/13": "G12-13"})
    rec_x = np.arange(len(rec))
    ax_rec.bar(rec_x, rec["recovery_rate_percent"],
               color=[FAM_COL.get(f, MUTED) for f in rec["family"]])
    ax_rec.set_xticks(rec_x)
    ax_rec.set_xticklabels(
        [FAM_LABEL.get(f, f) for f in rec["family"]], fontsize=FS_TICK,
    )
    ax_rec.set_ylim(0, 100)
    ax_rec.set_ylabel("orthosteric recovery (%)", fontsize=FS_LABEL)
    ax_rec.set_title("Binding-site validation", fontsize=FS_TITLE, loc="left", pad=4)
    ax_rec.tick_params(axis="both", labelsize=FS_TICK)
    for x, row in enumerate(rec.itertuples()):
        ax_rec.text(
            x, row.recovery_rate_percent + 1.8,
            f"{row.orthosteric_recovered}/{row.systems_with_pockets}\n"
            f"({row.recovery_rate_percent:.1f}%)",
            ha="center", va="bottom", fontsize=FS_ANNOT, linespacing=1.05,
        )
    panel(ax_rec, "E")

    # ── F: systems with the largest recalculated pocket counts ───────────────
    top = per_system.sort_values("n_pockets", ascending=False).head(9).iloc[::-1]
    ax_nom.barh(top["system_id"], top["n_pockets"],
                color=[FAM_COL.get(f, MUTED) for f in top["g_family"]])
    ax_nom.set_xlabel("pockets", fontsize=FS_LABEL)
    ax_nom.set_ylabel("system", fontsize=FS_LABEL)
    ax_nom.set_title("Highest per-system pocket counts",
                     fontsize=FS_TITLE, loc="left", pad=4)
    ax_nom.tick_params(axis="both", labelsize=FS_TICK)
    ax_nom.set_xlim(0, float(top["n_pockets"].max()) * 1.45)
    for y, (_, row) in enumerate(top.iterrows()):
        txt = str(row.get("receptor_name", ""))
        ax_nom.annotate(
            txt[:12], xy=(row["n_pockets"], y), xytext=(5, 0),
            textcoords="offset points", ha="left", va="center",
            fontsize=FS_ANNOT, color=MUTED, clip_on=False,
        )
    panel(ax_nom, "F")

    # No suptitle; spacing is controlled explicitly by the GridSpec above.
    save(fig, "v9_figure5_pocket_atlas")


if __name__ == "__main__":
    print("Figure 5 (drug-design pocket atlas) …")
    make_figure5()
