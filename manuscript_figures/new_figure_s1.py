#!/usr/bin/env python3
"""Generate Supplementary Figure S1 — circular dendrogram of receptors.

Hierarchical-cluster the 174 receptors by their G-protein-family coupling
profile (Jaccard distance, average linkage) and draw the tree bent into a
circle (circlize::circlize_dendrogram style): branches merge inward to a
central hub; each leaf on the rim is a coloured tick (by family; teal for
receptors coupling to >1 family) labelled with its representative 4-letter
PDB ID. Minimal annotation: one center line + a small family legend.

Receptor -> representative PDB: the PDB of the receptor's family that comes
first in family order (deterministic; for single-family receptors that is
simply their PDB).

All numbers read from the frozen clean-v1 CSV (no trajectory I/O).
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-coupledmd")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle

import figstyle  # noqa: E402  (local module)
from scipy.cluster.hierarchy import linkage, leaves_list, to_tree

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
ACCENT = figstyle.ACCENT  # multi-family receptors


def load_s1() -> pd.DataFrame:
    return pd.read_csv(V9 / "scidata_S1_included_systems_v9.csv")


def _rep_pdb(sub: pd.DataFrame) -> str:
    """Representative 4-letter PDB for one receptor (primary family, then PDB id)."""
    fams_present = [f for f in FAM_ORDER
                    if (sub["g_protein_family"].values == f).any()]
    prim = fams_present[0]
    rows = sub[sub["g_protein_family"] == prim].sort_values("pdb_id")
    return str(rows["pdb_id"].iloc[0])


def _polar(r, th):
    return r * np.cos(th), r * np.sin(th)


def _arc_xy(r, th0, th1, n=48):
    t = np.linspace(th0, th1, n)
    return r * np.cos(t), r * np.sin(t)


def build_figure(s1: pd.DataFrame) -> None:
    assert len(s1) == 208
    assert s1["receptor_name"].nunique(dropna=True) == 174
    assert s1["receptor_uniprot"].nunique(dropna=True) == 173
    missing_uniprot = s1.loc[s1["receptor_uniprot"].isna(), "system_id"].tolist()
    assert missing_uniprot == ["Gs_8HTI"]
    unnamed = s1.loc[s1["receptor_name"].isna(), "system_id"].tolist()
    assert unnamed == []
    # Identifier definition: one leaf per distinct non-null receptor_name.
    # Gs_8HTI is an explicit consensus-model exception: it has no canonical
    # UniProt accession and is never silently dropped from receptor grouping.
    named = s1.dropna(subset=["receptor_name"]).copy()
    # receptor -> set of families, in FAM_ORDER
    prof = named.groupby("receptor_name")["g_protein_family"].agg(
        lambda s: sorted(set(s)))
    rep_pdb = named.groupby("receptor_name").apply(_rep_pdb, include_groups=False)
    ids = list(prof.index)
    fams = list(prof.values)

    X = np.array([[1 if f in fs else 0 for f in FAM_ORDER] for fs in fams],
                 dtype=float)
    Z = linkage(X, method="average", metric="jaccard")
    order = leaves_list(Z)  # receptor indices in leaf order
    n = len(order)

    # leaf angles: start at top (pi/2), go clockwise
    leaf_ang = np.empty(n)
    for pos, idx in enumerate(order):
        leaf_ang[idx] = (np.pi / 2) - 2 * np.pi * pos / n

    root = to_tree(Z)
    Hmax = float(root.dist) if root.dist > 0 else 1.0
    R_LEAF = 1.00
    R_CENTER = 0.17

    def radius_of(h: float) -> float:
        return R_LEAF - (h / Hmax) * (R_LEAF - R_CENTER)

    info = {}

    def walk(node):
        if node.is_leaf():
            a = leaf_ang[node.id]
            info[id(node)] = (a, a, a, R_LEAF)
            return a, a
        la_min, la_max = walk(node.left)
        ra_min, ra_max = walk(node.right)
        amin = min(la_min, ra_min)
        amax = max(la_max, ra_max)
        amid = 0.5 * (amin + amax)
        r = radius_of(node.dist)
        info[id(node)] = (amin, amax, amid, r)
        return amin, amax

    walk(root)

    # 183 mm wide: render at the intended publication size so text is not
    # subsequently reduced by typesetting.
    fig = plt.figure(figsize=(7.20, 7.35), facecolor="white")
    ax = fig.add_axes([0.025, 0.025, 0.95, 0.95])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.34, 1.24)

    # faint outer guide ring
    th = np.linspace(0, 2 * np.pi, 240)
    ax.plot(R_LEAF * np.cos(th), R_LEAF * np.sin(th),
            color=PALE, lw=0.45, ls=(0, (1, 2)), zorder=0)

    # draw merges recursively
    def draw_node(node):
        if node.is_leaf():
            return
        l, r = node.left, node.right
        li = info[id(l)]; ri = info[id(r)]; ni = info[id(node)]
        # radial line for each child at its own angle, child r -> node r
        x0, y0 = _polar(li[3], li[2]); x1, y1 = _polar(ni[3], li[2])
        ax.plot([x0, x1], [y0, y1], color=MUTED, lw=0.55, zorder=2)
        x0, y0 = _polar(ri[3], ri[2]); x1, y1 = _polar(ni[3], ri[2])
        ax.plot([x0, x1], [y0, y1], color=MUTED, lw=0.55, zorder=2)
        # connecting arc at node radius between the two child angles
        xa, ya = _arc_xy(ni[3], li[2], ri[2], n=24)
        ax.plot(xa, ya, color=MUTED, lw=0.55, zorder=2)
        draw_node(l); draw_node(r)

    draw_node(root)

    # leaf ticks + PDB labels
    for idx in range(n):
        a = leaf_ang[idx]
        fset = fams[idx]
        col = FAM_COL[fset[0]] if len(fset) == 1 else ACCENT
        # coloured radial tick just outside the ring
        x0, y0 = _polar(R_LEAF - 0.012, a)
        x1, y1 = _polar(R_LEAF + 0.040, a)
        ax.plot([x0, x1], [y0, y1], color=col, lw=1.25,
                solid_capstyle="round", zorder=3)
        # PDB label further out, radial, upright-corrected on the left half
        ang = np.degrees(a) % 360
        if 90 < ang < 270:
            rot = ang - 180
            ha = "right"
        else:
            rot = ang
            ha = "left"
        lr = R_LEAF + 0.060
        xt, yt = _polar(lr, a)
        ax.text(xt, yt, rep_pdb.iloc[idx], ha=ha, va="center",
                fontsize=6.2, color=col, rotation=rot,
                fontfamily="monospace",
                rotation_mode="anchor", zorder=4)

    # center hub + minimal summary
    ax.add_patch(Circle((0, 0), R_CENTER, facecolor="white",
                        edgecolor=INK, lw=0.65, zorder=5))
    ax.text(0, 0.050, "CoupledMD", ha="center", va="center",
            fontsize=8.5, fontweight="bold", color=INK, zorder=6)
    ax.text(0, -0.005, f"{n} named receptors", ha="center", va="center",
            fontsize=6.4, color=MUTED, zorder=6)
    ax.text(0, -0.052, "173 mapped UniProt", ha="center", va="center",
            fontsize=5.2, color=MUTED, zorder=6)
    ax.text(0, -0.092, "1 consensus model lacks canonical UniProt", ha="center", va="center",
            fontsize=4.8, color=MUTED, zorder=6)

    # family legend
    handles = [
        Line2D([0], [0], color=FAM_COL[f], lw=2.2,
               solid_capstyle="round", label=FAM_LABEL[f])
        for f in FAM_ORDER
    ]
    handles.append(Line2D([0], [0], color=ACCENT, lw=2.2,
                          solid_capstyle="round", label="≥2 families"))
    leg = ax.legend(handles=handles, loc="lower center",
                    bbox_to_anchor=(0.5, 0.002), frameon=False, fontsize=7.5,
                    handlelength=1.25, handletextpad=0.5, columnspacing=1.5,
                    ncol=5, borderpad=0.2)
    for t in leg.get_texts():
        t.set_color(MUTED)

    _save(fig, "v9_figureS1_dendrogram")


def _save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        p = OUT / f"{name}.{ext}"
        fig.savefig(p, dpi=600 if ext == "png" else None,
                    facecolor="white")
        print(f"  saved {p}")
    plt.close(fig)


def main() -> None:
    build_figure(load_s1())
    print("[S1] done.")


if __name__ == "__main__":
    main()
