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
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Patch

import figstyle  # noqa: E402  (local module)
from scipy.cluster.hierarchy import linkage, leaves_list, to_tree

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
ACCENT = figstyle.ACCENT  # multi-family receptors


def load_s1() -> pd.DataFrame:
    return pd.read_csv(TBL / "scidata_S1_included_systems_clean_v1.csv")


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
    # receptor -> set of families, in FAM_ORDER
    prof = s1.groupby("receptor_uniprot")["g_protein_family"].agg(
        lambda s: sorted(set(s)))
    rep_pdb = s1.groupby("receptor_uniprot").apply(_rep_pdb, include_groups=False)
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
    R_CENTER = 0.16

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

    fig = plt.figure(figsize=(9.6, 9.6))
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.95])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.42, 1.42)
    ax.set_ylim(-1.42, 1.42)

    # faint outer guide ring
    th = np.linspace(0, 2 * np.pi, 240)
    ax.plot(R_LEAF * np.cos(th), R_LEAF * np.sin(th),
            color=PALE, lw=0.4, ls=(0, (1, 2)), zorder=0)

    # draw merges recursively
    def draw_node(node):
        if node.is_leaf():
            return
        l, r = node.left, node.right
        li = info[id(l)]; ri = info[id(r)]; ni = info[id(node)]
        # radial line for each child at its own angle, child r -> node r
        x0, y0 = _polar(li[3], li[2]); x1, y1 = _polar(ni[3], li[2])
        ax.plot([x0, x1], [y0, y1], color=INK, lw=0.7, zorder=2)
        x0, y0 = _polar(ri[3], ri[2]); x1, y1 = _polar(ni[3], ri[2])
        ax.plot([x0, x1], [y0, y1], color=INK, lw=0.7, zorder=2)
        # connecting arc at node radius between the two child angles
        xa, ya = _arc_xy(ni[3], li[2], ri[2], n=24)
        ax.plot(xa, ya, color=INK, lw=0.7, zorder=2)
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
        ax.plot([x0, x1], [y0, y1], color=col, lw=1.1,
                solid_capstyle="round", zorder=3)
        # PDB label further out, radial, upright-corrected on the left half
        ang = np.degrees(a) % 360
        if 90 < ang < 270:
            rot = ang - 180
            ha = "right"
        else:
            rot = ang
            ha = "left"
        lr = R_LEAF + 0.052
        xt, yt = _polar(lr, a)
        ax.text(xt, yt, rep_pdb.iloc[idx], ha=ha, va="center",
                fontsize=6.5, color=col, rotation=rot,
                rotation_mode="anchor", zorder=4)

    # center hub + minimal summary
    ax.add_patch(Circle((0, 0), R_CENTER, facecolor="white",
                        edgecolor=INK, lw=0.6, zorder=5))
    ax.text(0, 0.045, "CoupledMD", ha="center", va="center",
            fontsize=9.5, fontweight="bold", color=INK, zorder=6)
    ax.text(0, -0.02, f"{n} receptors", ha="center", va="center",
            fontsize=7.2, color=MUTED, zorder=6)

    # family legend
    handles = [Patch(facecolor=FAM_COL[f], label=FAM_LABEL[f]) for f in FAM_ORDER]
    handles.append(Patch(facecolor=ACCENT, label="≥2 families"))
    leg = ax.legend(handles=handles, loc="lower center",
                    bbox_to_anchor=(0.5, 0.0), frameon=False, fontsize=10,
                    handlelength=1.1, ncol=5, borderpad=0.4)
    for t in leg.get_texts():
        t.set_color(MUTED)

    _save(fig, "new_figureS1_dendrogram")


def _save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        p = OUT / f"{name}.{ext}"
        fig.savefig(p, dpi=600 if ext == "png" else None)
        print(f"  saved {p}")
    plt.close(fig)


def main() -> None:
    build_figure(load_s1())
    print("[S1] done.")


if __name__ == "__main__":
    main()
