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

import json
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
TBL = HERE / "tables"
API = HERE.parent / "data" / "api" / "v1"
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


def read_json(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def load_consensus(name: str) -> dict:
    return read_json(API / "consensus" / name)


def load_t4a() -> pd.DataFrame:
    return pd.read_csv(TBL / "scidata_T4a_recovery_summary_clean_v1.csv")


def make_figure5() -> None:
    drug = load_consensus("pockets_druggable.json")["clusters"]
    ortho = load_consensus("pockets_orthosteric.json")["clusters"]
    nom = load_consensus("druggable_nominations.json")["nominations"]
    t4a = load_t4a()

    rows = []
    for cl in drug:
        zones = cl.get("zones", {"other": 1})
        zone = max(zones, key=zones.get)
        rows.append({
            "cid": cl["consensus_id"],
            "n_receptors": cl.get("n_receptors", 0),
            "n_systems": cl.get("n_systems", 0),
            "mean_freq": cl.get("mean_freq", np.nan),
            "n_voxels": cl.get("n_voxels", np.nan),
            "zone": zone,
            "n_core": len(cl.get("core_generic_numbers", [])),
        })
    df = pd.DataFrame(rows)

    fig = plt.figure(figsize=(10.8, 7.0))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.15, 1.0, 1.1],
                          wspace=0.40, hspace=0.55,
                          left=0.07, right=0.97, top=0.90, bottom=0.09)
    ax_snap = fig.add_subplot(gs[0, 0])  # A — snapshot slot (blank, added by hand)
    ax_snap.set_axis_off()
    ax_sc = fig.add_subplot(gs[0, 1])    # B
    ax_zone = fig.add_subplot(gs[0, 2])  # C
    ax_gn = fig.add_subplot(gs[1, 0])    # D
    ax_rec = fig.add_subplot(gs[1, 1])   # E
    ax_nom = fig.add_subplot(gs[1, 2])   # F

    # ── A: consensus druggable pocket clusters ───────────────────────────────
    for zone, sub in df.groupby("zone"):
        ax_sc.scatter(sub["n_receptors"], sub["mean_freq"],
                      s=18 + 0.10 * sub["n_voxels"].fillna(0),
                      color=ZONE_COL.get(zone, MUTED), alpha=0.78,
                      edgecolor="white", lw=0.35, label=zone)
    ax_sc.set_xlabel("receptors represented by cluster", fontsize=FS_LABEL)
    ax_sc.set_ylabel("mean pocket occupancy", fontsize=FS_LABEL)
    ax_sc.set_title("Consensus druggable pocket clusters",
                    fontsize=FS_TITLE, loc="left", pad=4)
    ax_sc.set_ylim(0.45, 1.02)
    ax_sc.tick_params(axis="both", labelsize=FS_TICK)
    ax_sc.grid(color=PALE, lw=0.4)
    ax_sc.legend(frameon=False, loc="lower right", fontsize=FS_ANNOT)
    panel(ax_sc, "B")

    # ── A: snapshot slot (blank, to be composed in by hand) ───────────────────
    panel(ax_snap, "A")

    # ── B: pocket zones ──────────────────────────────────────────────────────
    zone_counts = Counter()
    for cl in drug:
        for z, n in cl.get("zones", {}).items():
            zone_counts[z] += n
    zitems = sorted(zone_counts.items(), key=lambda kv: kv[1], reverse=True)
    zlabels = [z for z, _ in zitems][::-1]
    zvals = [v for _, v in zitems][::-1]
    ax_zone.barh(zlabels, zvals,
                 color=[ZONE_COL.get(z, MUTED) for z in zlabels])
    ax_zone.set_xlabel("cluster members", fontsize=FS_LABEL)
    ax_zone.set_title("Pocket zones", fontsize=FS_TITLE, loc="left", pad=4)
    ax_zone.tick_params(axis="both", labelsize=FS_TICK)
    panel(ax_zone, "C")

    # ── C: reusable GPCRdb-position anchors ──────────────────────────────────
    gn = Counter()
    for cl in drug + ortho:
        gn.update(cl.get("core_generic_numbers", [])[:12])
    top_gn = gn.most_common(18)[::-1]
    ax_gn.barh([k for k, _ in top_gn], [v for _, v in top_gn], color=ACCENT)
    ax_gn.set_xlabel("clusters", fontsize=FS_LABEL)
    ax_gn.set_title("Reusable GPCRdb-position anchors",
                    fontsize=FS_TITLE, loc="left", pad=4)
    ax_gn.tick_params(axis="both", labelsize=FS_TICK)
    panel(ax_gn, "D")

    # ── D: binding-site validation (orthosteric recovery) ────────────────────
    rec = t4a[t4a["subset"] != "All clean-v1"].copy()
    rec["family"] = rec["subset"].replace(
        {"Gi/o": "Gi", "Gq/11": "Gq", "G12/13": "G12-13"})
    ax_rec.bar(rec["family"], rec["recovery_rate_percent"],
               color=[FAM_COL.get(f, MUTED) for f in rec["family"]])
    ax_rec.set_ylim(0, 100)
    ax_rec.set_ylabel("orthosteric recovery (%)", fontsize=FS_LABEL)
    ax_rec.set_title("Binding-site validation", fontsize=FS_TITLE, loc="left", pad=4)
    ax_rec.tick_params(axis="both", labelsize=FS_TICK)
    for x, row in enumerate(rec.itertuples()):
        ax_rec.text(x, row.recovery_rate_percent + 2,
                    f"{row.orthosteric_recovered}/{row.systems_with_pockets}",
                    ha="center", fontsize=FS_ANNOT)
    panel(ax_rec, "E")

    # ── E: drug-design nomination examples ───────────────────────────────────
    nom_df = pd.DataFrame(nom).sort_values("drug_proxy", ascending=False).head(9).iloc[::-1]
    ax_nom.barh(nom_df["cid"].astype(str), nom_df["drug_proxy"],
                color=[ZONE_COL.get(z, MUTED) for z in nom_df["zone"]])
    ax_nom.set_xlabel("proxy score", fontsize=FS_LABEL)
    ax_nom.set_ylabel("cluster id", fontsize=FS_LABEL)
    ax_nom.set_title("Drug-design nomination examples",
                     fontsize=FS_TITLE, loc="left", pad=4)
    ax_nom.tick_params(axis="both", labelsize=FS_TICK)
    for y, (_, row) in enumerate(nom_df.iterrows()):
        txt = str(row.get("example_receptors", "")).split(",")[0]
        ax_nom.text(row["drug_proxy"] + 0.1, y, txt[:16], va="center",
                    fontsize=FS_ANNOT, color=MUTED)
    panel(ax_nom, "F")

    # No suptitle; compact, border-free composition.
    fig.tight_layout(pad=0.5)
    save(fig, "new_figure5_drug_design_pocket_atlas")


if __name__ == "__main__":
    print("Figure 5 (drug-design pocket atlas) …")
    make_figure5()
