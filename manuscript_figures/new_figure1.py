#!/usr/bin/env python3
"""Main Figure 1 — GPCR community and drug-target landscape.

Adapted from `generate_scidata_extra_figures.py::fig5_community_landscape`
(Scientific Data Figure 5 candidate), now promoted to main Figure 1.

Changes versus the original:
  - No figure title (suptitle removed).
  - tight_layout used for a compact, border-free composition.
  - Removed the "bubble size = number of G-family contexts" annotation.
  - Enlarged axis labels, tick labels, titles and panel letters for clarity.

All panels are generated from frozen CSVs. No trajectory I/O is performed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-coupledmd")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import figstyle

figstyle.apply_style()

HERE = Path(__file__).resolve().parent
TBL = HERE / "tables"
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

FAM_ORDER = ["Gi", "Gs", "Gq", "G12-13"]
FAM_COL = figstyle.FAMILY
INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT
WARN = "#c0741a"
RED = "#b23a48"

# Enlarged typography so the figure reads clearly as a main-text figure.
FS_PANEL = 13          # panel letter (A–E)
FS_TITLE = 12          # subplot titles
FS_LABEL = 11          # axis labels
FS_TICK = 9            # tick labels
FS_ANNOT = 8           # in-panel annotations / small text


def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        path = OUT / f"{name}.{ext}"
        fig.savefig(path, bbox_inches="tight", pad_inches=0.02, dpi=600 if ext == "png" else None)
        print(f"  saved {path}")
    plt.close(fig)


def panel(ax, letter: str, x=-0.10, y=1.04) -> None:
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=FS_PANEL,
            fontweight="bold", va="bottom")


def read_json(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def load_tables() -> dict[str, pd.DataFrame]:
    return {
        "s1": pd.read_csv(TBL / "scidata_S1_included_systems_clean_v1.csv"),
        "s2": pd.read_csv(TBL / "scidata_S2_held_back_systems.csv"),
    }


def clean_family(value: str) -> str:
    if value == "G12":
        return "G12-13"
    return value


def ordered_families(values) -> list[str]:
    present = set(values)
    return [f for f in FAM_ORDER if f in present]


def make_figure1() -> None:
    s1, s2 = load_tables()["s1"].copy(), load_tables()["s2"].copy()
    s1["g_protein_family"] = s1["g_protein_family"].map(clean_family)

    fig = plt.figure(figsize=(10.8, 7.4))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.1, 1.15, 1.0], height_ratios=[1.0, 1.0],
                          wspace=0.38, hspace=0.42)
    ax_hm = fig.add_subplot(gs[0, 0])
    ax_prom = fig.add_subplot(gs[0, 1])
    ax_lig = fig.add_subplot(gs[0, 2])
    ax_reuse = fig.add_subplot(gs[1, :2])
    ax_hold = fig.add_subplot(gs[1, 2])

    # A: class x family matrix.
    ct = pd.crosstab(s1["gpcr_class"], s1["g_protein_family"]).reindex(
        columns=ordered_families(s1["g_protein_family"]), fill_value=0)
    im = ax_hm.imshow(ct.values, cmap="YlGnBu", aspect="auto")
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            ax_hm.text(j, i, int(ct.iloc[i, j]), ha="center", va="center",
                       color="white" if ct.iloc[i, j] > ct.values.max() * 0.45 else INK,
                       fontweight="bold", fontsize=FS_TICK)
    ax_hm.set_xticks(range(ct.shape[1]), ct.columns, fontsize=FS_TICK)
    ax_hm.set_yticks(range(ct.shape[0]), [f"Class {c}" for c in ct.index], fontsize=FS_TICK)
    ax_hm.set_xlabel("G-protein family", fontsize=FS_LABEL)
    ax_hm.set_ylabel("GPCR class", fontsize=FS_LABEL)
    panel(ax_hm, "A")
    # Colorbar kept for the count scale, but its "systems" label is omitted: it sat
    # between A and B and collided with B's receptor-gene y-axis labels.
    cbar = fig.colorbar(im, ax=ax_hm, fraction=0.046, pad=0.02)
    cbar.ax.tick_params(labelsize=FS_TICK)

    # B: receptors represented by more than one family.
    recfam = s1.groupby(["receptor_gene", "receptor_name"])["g_protein_family"].agg(
        lambda x: sorted(set(x))).reset_index()
    recfam["n_families"] = recfam["g_protein_family"].map(len)
    recsys = s1.groupby("receptor_gene")["system_id"].count()
    recfam["n_systems"] = recfam["receptor_gene"].map(recsys)
    top = recfam.sort_values(["n_families", "n_systems"], ascending=False).head(16).iloc[::-1]
    colors = [FAM_COL.get(fams[0], MUTED) if len(fams) == 1 else ACCENT
              for fams in top["g_protein_family"]]
    ax_prom.barh(np.arange(len(top)), top["n_systems"], color=colors, edgecolor="white", lw=0.5)
    ax_prom.set_yticks(np.arange(len(top)), top["receptor_gene"].fillna("NA"), fontsize=FS_TICK)
    ax_prom.tick_params(axis="x", labelsize=FS_TICK)
    ax_prom.set_xlabel("systems", fontsize=FS_LABEL)
    for y, (_, row) in enumerate(top.iterrows()):
        label = "/".join(row["g_protein_family"])
        ax_prom.text(row["n_systems"] + 0.2, y, label, va="center",
                     fontsize=FS_ANNOT, color=MUTED)
    ax_prom.set_xlim(0, max(top["n_systems"]) + 4)
    panel(ax_prom, "B")

    # C: ligand annotation by family.
    ligand = s1.copy()
    ligand["ligand_bucket"] = np.where(
        ligand["ligand_name"].isna() | (ligand["ligand_name"].astype(str).str.lower() == "nan"),
        "apo/none", "ligand present")
    lig_ct = pd.crosstab(ligand["g_protein_family"], ligand["ligand_bucket"]).reindex(FAM_ORDER).dropna(how="all")
    bottoms = np.zeros(len(lig_ct))
    for bucket, color in [("ligand present", RED), ("apo/none", PALE)]:
        vals = lig_ct.get(bucket, pd.Series(0, index=lig_ct.index)).values
        ax_lig.bar(lig_ct.index, vals, bottom=bottoms, color=color, edgecolor="white",
                   lw=0.5, label=bucket)
        bottoms += vals
    ax_lig.set_ylabel("systems", fontsize=FS_LABEL)
    ax_lig.tick_params(axis="both", labelsize=FS_TICK)
    ax_lig.legend(frameon=False, loc="upper right", fontsize=FS_ANNOT)
    panel(ax_lig, "C")

    # D: drug-design target space: receptors sorted by system count, colored by family diversity.
    counts = recfam.sort_values(["n_systems", "n_families"], ascending=False).head(42)
    x = np.arange(len(counts))
    ax_reuse.scatter(x, counts["n_systems"], s=26 + 34 * counts["n_families"],
                     c=[ACCENT if n > 1 else MUTED for n in counts["n_families"]],
                     edgecolor="white", lw=0.4)
    ax_reuse.set_xticks(x, counts["receptor_gene"].fillna("NA"), rotation=75, ha="right",
                        fontsize=FS_TICK)
    ax_reuse.tick_params(axis="y", labelsize=FS_TICK)
    ax_reuse.set_ylabel("systems per receptor", fontsize=FS_LABEL)
    ax_reuse.grid(axis="y", color=PALE, lw=0.4)
    panel(ax_reuse, "D")

    # E: clean vs held-back transparency.
    reason = s2["hold_reason"].fillna("").map(
        lambda x: "nonstandard length" if "nonstandard" in x.lower()
        else "missing/incomplete files")
    h = reason.value_counts()
    ax_hold.bar(["included", "held back"], [len(s1), len(s2)], color=[FAM_COL["Gi"], WARN],
                edgecolor="white")
    ax_hold.set_ylabel("systems", fontsize=FS_LABEL)
    ax_hold.tick_params(axis="both", labelsize=FS_TICK)
    ax_hold.text(0, len(s1) + 3, f"{len(s1)} clean", ha="center", fontweight="bold",
                 fontsize=FS_ANNOT)
    ax_hold.text(1, len(s2) + 3, f"{len(s2)} held", ha="center", fontweight="bold",
                 fontsize=FS_ANNOT)
    ypos = 0.72
    for key, val in h.items():
        ax_hold.text(0.55, ypos, f"{val} {key}", transform=ax_hold.transAxes,
                     fontsize=FS_ANNOT, color=MUTED)
        ypos -= 0.08
    panel(ax_hold, "E")

    # No suptitle; tight layout for a compact, border-free composition.
    fig.tight_layout(pad=0.5)
    # Shift panel B right (narrowing it slightly, right edge unchanged) so its
    # receptor-gene y-axis labels clear panel A's colorbar, while keeping A and C fixed.
    bbox = ax_prom.get_position()
    _shift = 0.030
    ax_prom.set_position([bbox.x0 + _shift, bbox.y0, bbox.width - _shift, bbox.height])
    save(fig, "new_figure1_community_landscape")


if __name__ == "__main__":
    print("Figure 1 (community landscape) …")
    make_figure1()
