#!/usr/bin/env python3
"""Generate 6 candidate representations for Supplementary Figure S1.

Three fundamentally different geometries × two annotation levels = 6 variants,
each saved to its own file so one can be selected.

  V1  Circular dendrogram of receptors (clustered by coupling profile)
  V2  Radial tree of class -> family (branch thickness = system count)
  V3  Sunburst / icicle hierarchy (class -> family -> count wedges)

  a = minimal annotation (family colors + one center line + tiny legend)
  b = stripped annotation (no in-figure text; color only)

All numbers read from frozen clean-v1 CSVs (no trajectory I/O).
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-coupledmd")

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Wedge, Circle, PathPatch
from matplotlib.path import Path as MplPath

import figstyle  # noqa: E402  (local module)
from scipy.cluster.hierarchy import linkage, leaves_list, to_tree
from scipy.spatial.distance import pdist

figstyle.apply_style()

HERE = Path(__file__).resolve().parent
TBL = HERE / "tables"
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

FAM_COL = figstyle.FAMILY
FAM_ORDER = ["Gi", "Gs", "Gq", "G12-13"]
FAM_LABEL = figstyle.FAMILY_LABEL
CLASS_COL = {"A": "#2c6fb3", "B": "#c0741a"}
INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT  # for multi-family receptors


def load_s1() -> pd.DataFrame:
    return pd.read_csv(TBL / "scidata_S1_included_systems_clean_v1.csv")


def _polar(r, th):
    return r * np.cos(th), r * np.sin(th)


def _arc_xy(r, th0, th1, n=48):
    t = np.linspace(th0, th1, n)
    return r * np.cos(t), r * np.sin(t)


def _variant_tag(fig, code: str) -> None:
    """Tiny corner tag so the user can identify which file is which."""
    fig.text(0.99, 0.01, code, ha="right", va="bottom",
             fontsize=6, color=MUTED, alpha=0.8)


# ──────────────────────────────────────────────────────────────────────────────
# V1 — Circular dendrogram of receptors
# ──────────────────────────────────────────────────────────────────────────────
def _circular_dendro_axes(s1: pd.DataFrame, minimal: bool, code: str):
    # receptor -> set of families
    prof = s1.groupby("receptor_uniprot")["g_protein_family"].agg(
        lambda s: sorted(set(s)))
    ids = list(prof.index)
    fams = list(prof.values)

    # binary feature matrix over FAM_ORDER, Jaccard distance
    X = np.array([[1 if f in fs else 0 for f in FAM_ORDER] for fs in fams],
                 dtype=float)
    Z = linkage(X, method="average", metric="jaccard")
    order = leaves_list(Z)  # receptor indices in leaf order

    n = len(order)
    # assign each leaf an angle evenly around the circle
    leaf_ang = np.empty(n)
    for pos, idx in enumerate(order):
        leaf_ang[idx] = (np.pi / 2) - 2 * np.pi * pos / n  # start at top, CW

    # walk tree -> assign each node (leaf & internal) angle-mid + radius
    root = to_tree(Z)
    Hmax = float(root.dist) if root.dist > 0 else 1.0
    R_LEAF = 1.00
    R_CENTER = 0.16

    def radius_of(h: float) -> float:
        return R_LEAF - (h / Hmax) * (R_LEAF - R_CENTER)

    # node id -> (amin, amax, amid, radius)
    info = {}

    def walk(node):
        if node.is_leaf():
            a = leaf_ang[node.id]
            info[id(node)] = (a, a, a, R_LEAF)
            return a, a
        la_min, la_max = walk(node.left)
        ra_min, ra_max = walk(node.right)
        # children are contiguous in leaf order; span union
        amin = min(la_min, ra_min)
        amax = max(la_max, ra_max)
        amid = 0.5 * (amin + amax)
        r = radius_of(node.dist)
        info[id(node)] = (amin, amax, amid, r)
        return amin, amax

    walk(root)

    fig = plt.figure(figsize=(7.0, 7.0))
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-1.18, 1.18); ax.set_ylim(-1.18, 1.18)

    # faint outer guide ring
    th = np.linspace(0, 2 * np.pi, 200)
    ax.plot(R_LEAF * np.cos(th), R_LEAF * np.sin(th),
            color=PALE, lw=0.4, ls=(0, (1, 2)), zorder=0)

    # draw merges (internal nodes): two radial lines + connecting arc
    def draw_node(node):
        if node.is_leaf():
            return
        l, r = node.left, node.right
        li = info[id(l)]; ri = info[id(r)]; ni = info[id(node)]
        # radial line for left child at its angle, from child r to node r
        x0, y0 = _polar(li[3], li[2])
        x1, y1 = _polar(ni[3], li[2])
        ax.plot([x0, x1], [y0, y1], color=INK, lw=0.7, zorder=2)
        # radial line for right child
        x0, y0 = _polar(ri[3], ri[2])
        x1, y1 = _polar(ni[3], ri[2])
        ax.plot([x0, x1], [y0, y1], color=INK, lw=0.7, zorder=2)
        # connecting arc at node radius between the two child angles
        a0, a1 = li[2], ri[2]
        xa, ya = _arc_xy(ni[3], a0, a1, n=24)
        ax.plot(xa, ya, color=INK, lw=0.7, zorder=2)
        draw_node(l); draw_node(r)

    draw_node(root)

    # leaf ticks colored by family (multi-family -> ACCENT)
    for idx, fid in enumerate(ids):
        a = leaf_ang[idx]
        fset = fams[idx]
        if len(fset) == 1:
            col = FAM_COL[fset[0]]
        else:
            col = ACCENT
        x0, y0 = _polar(R_LEAF - 0.015, a)
        x1, y1 = _polar(R_LEAF + 0.045, a)
        ax.plot([x0, x1], [y0, y1], color=col, lw=1.2, solid_capstyle="round",
                zorder=3)

    if minimal:
        ax.add_patch(Circle((0, 0), R_CENTER, facecolor="white",
                            edgecolor=INK, lw=0.6, zorder=5))
        ax.text(0, 0.045, "CoupledMD", ha="center", va="center",
                fontsize=9, fontweight="bold", color=INK, zorder=6)
        ax.text(0, -0.02, f"{len(prof)} receptors", ha="center", va="center",
                fontsize=7, color=MUTED, zorder=6)
        # tiny family legend
        from matplotlib.patches import Patch
        handles = [Patch(facecolor=FAM_COL[f], label=FAM_LABEL[f]) for f in FAM_ORDER]
        handles.append(Patch(facecolor=ACCENT, label="≥2 families"))
        leg = ax.legend(handles=handles, loc="lower center",
                        bbox_to_anchor=(0.5, -0.02), frameon=False,
                        fontsize=6.4, handlelength=1.1, ncol=5,
                        borderpad=0.3)
        for t in leg.get_texts():
            t.set_color(MUTED)
    # stripped: center left blank (just a thin hub ring)
    else:
        ax.add_patch(Circle((0, 0), R_CENTER, facecolor="white",
                            edgecolor=PALE, lw=0.4, zorder=5))

    _variant_tag(fig, code)
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# V2 — Radial tree of class -> family
# ──────────────────────────────────────────────────────────────────────────────
def _radial_tree_axes(s1: pd.DataFrame, minimal: bool, code: str):
    ct = pd.crosstab(s1["gpcr_class"], s1["g_protein_family"])
    classes = list(ct.index)
    fams_all = [f for f in FAM_ORDER if f in ct.columns]
    total = int(ct.values.sum())
    max_count = int(ct.values.max())

    fig = plt.figure(figsize=(7.0, 7.0))
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2)

    R_ROOT = 0.0
    R_CLASS = 0.45
    R_FAM = 1.0

    # class nodes spread on upper arc; leaves (families) on outer arc
    # distribute classes at angles around the circle, families nested
    # Layout: each class gets an angular sector sized by system count
    class_counts = {c: int(ct.loc[c].sum()) for c in classes}
    grand = sum(class_counts.values())
    # compute sector boundaries
    boundaries = []
    a = np.pi / 2  # start at top
    for c in classes:
        w = 2 * np.pi * class_counts[c] / grand
        boundaries.append((c, a - w / 2, a + w / 2))
        a -= w

    # draw root -> class branches
    for c, lo, hi in boundaries:
        ca = 0.5 * (lo + hi)
        # root point
        # branch thickness scaled by count
        lw = 0.8 + 6.0 * class_counts[c] / max_count
        xr, yr = _polar(R_ROOT, ca)
        xc, yc = _polar(R_CLASS, ca)
        ax.plot([xr, xc], [yr, yc], color=CLASS_COL[c], lw=lw,
                solid_capstyle="round", zorder=2)
        ax.scatter([xc], [yc], s=22, color=CLASS_COL[c], zorder=3)
        # class -> family leaves within this class's sector
        sub = [(f, int(ct.loc[c, f])) for f in fams_all if int(ct.loc[c, f]) > 0]
        if sub:
            # spread family leaves across [lo+pad, hi-pad]
            pad = (hi - lo) * 0.06
            n = len(sub)
            if n == 1:
                angs = [0.5 * (lo + hi)]
            else:
                angs = np.linspace(lo + pad, hi - pad, n)
            for (f, cnt), fa in zip(sub, angs):
                lwl = 0.6 + 4.0 * cnt / max_count
                xf, yf = _polar(R_FAM, fa)
                ax.plot([xc, xf], [yc, yf], color=FAM_COL[f], lw=lwl,
                        solid_capstyle="round", zorder=2)
                size = 18 + 90 * cnt / max_count
                ax.scatter([xf], [yf], s=size, color=FAM_COL[f],
                           edgecolor="white", lw=0.6, zorder=4)
                if minimal:
                    ax.text(xf * 1.08, yf * 1.08, f"{cnt}",
                            ha="center", va="center", fontsize=6.5,
                            color=FAM_COL[f], fontweight="bold", zorder=5)

    # sector boundary arcs (faint) at R_FAM
    for c, lo, hi in boundaries:
        xa, ya = _arc_xy(R_FAM, lo, hi, n=48)
        ax.plot(xa, ya, color=CLASS_COL[c], lw=0.6, alpha=0.25, zorder=0)

    if minimal:
        ax.add_patch(Circle((0, 0), 0.02, color=INK, zorder=3))
        ax.text(0, -0.06, "class × family", ha="center", va="top",
                fontsize=7, color=MUTED)
        # legend
        from matplotlib.patches import Patch
        handles = [Patch(facecolor=FAM_COL[f], label=FAM_LABEL[f]) for f in FAM_ORDER]
        handles += [Patch(facecolor=CLASS_COL[c], label=f"Class {c}") for c in classes]
        leg = ax.legend(handles=handles, loc="lower center",
                        bbox_to_anchor=(0.5, -0.04), frameon=False,
                        fontsize=6.2, handlelength=1.1, ncol=3,
                        borderpad=0.3)
        for t in leg.get_texts():
            t.set_color(MUTED)

    _variant_tag(fig, code)
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# V3 — Sunburst / icicle hierarchy
# ──────────────────────────────────────────────────────────────────────────────
def _sunburst_axes(s1: pd.DataFrame, minimal: bool, code: str):
    ct = pd.crosstab(s1["gpcr_class"], s1["g_protein_family"])
    classes = list(ct.index)
    fams_all = [f for f in FAM_ORDER if f in ct.columns]
    grand = int(ct.values.sum())

    R_OUT = 1.00   # class ring outer
    R_MID = 0.78   # family ring outer / class ring inner
    R_IN = 0.52    # count ring outer / family ring inner
    R_HUB = 0.42

    fig = plt.figure(figsize=(7.0, 7.0))
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-1.12, 1.12); ax.set_ylim(-1.12, 1.12)

    a = np.pi / 2  # start at top, go clockwise (decreasing angle)
    class_segs = []
    for c in classes:
        w = 2 * np.pi * int(ct.loc[c].sum()) / grand
        lo = a - w
        hi = a
        class_segs.append((c, lo, hi))
        # class ring (outermost): colored by class, light shade
        ax.add_patch(Wedge((0, 0), R_OUT, np.degrees(lo), np.degrees(hi),
                           width=R_OUT - R_MID,
                           facecolor=CLASS_COL[c], alpha=0.35,
                           edgecolor="white", lw=0.8, zorder=2))
        a = lo

    # family ring (middle): within each class sector, sub-wedges per family
    for c, clo, chi in class_segs:
        sub = [(f, int(ct.loc[c, f])) for f in fams_all if int(ct.loc[c, f]) > 0]
        ccw = chi
        for f, cnt in sub:
            fw = (chi - clo) * cnt / int(ct.loc[c].sum())
            flo = ccw - fw
            fhi = ccw
            ax.add_patch(Wedge((0, 0), R_MID, np.degrees(flo), np.degrees(fhi),
                               width=R_MID - R_IN,
                               facecolor=FAM_COL[f], alpha=0.9,
                               edgecolor="white", lw=0.6, zorder=3))
            ccw = flo

    # count ring (innermost): solid family-colored wedge filling, depth ∝ count
    # (single inner ring repeating family color at full saturation, thin)
    for c, clo, chi in class_segs:
        sub = [(f, int(ct.loc[c, f])) for f in fams_all if int(ct.loc[c, f]) > 0]
        ccw = chi
        for f, cnt in sub:
            fw = (chi - clo) * cnt / int(ct.loc[c].sum())
            flo = ccw - fw
            fhi = ccw
            ax.add_patch(Wedge((0, 0), R_IN, np.degrees(flo), np.degrees(fhi),
                               width=R_IN - R_HUB,
                               facecolor=FAM_COL[f], alpha=0.55,
                               edgecolor="none", zorder=2))
            ccw = flo

    if minimal:
        ax.add_patch(Circle((0, 0), R_HUB, facecolor="white", edgecolor=PALE,
                            lw=0.4, zorder=5))
        ax.text(0, 0.04, "CoupledMD", ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=INK, zorder=6)
        ax.text(0, -0.03, f"{grand} systems", ha="center", va="center",
                fontsize=6.8, color=MUTED, zorder=6)
        from matplotlib.patches import Patch
        handles = [Patch(facecolor=FAM_COL[f], label=FAM_LABEL[f]) for f in FAM_ORDER]
        handles += [Patch(facecolor=CLASS_COL[c], alpha=0.35, label=f"Class {c}")
                    for c in classes]
        leg = ax.legend(handles=handles, loc="lower center",
                        bbox_to_anchor=(0.5, -0.02), frameon=False,
                        fontsize=6.2, handlelength=1.1, ncol=3,
                        borderpad=0.3)
        for t in leg.get_texts():
            t.set_color(MUTED)
    else:
        ax.add_patch(Circle((0, 0), R_HUB, facecolor="white", edgecolor=PALE,
                            lw=0.4, zorder=5))

    _variant_tag(fig, code)
    return fig


def _save(fig, name: str) -> None:
    for ext in ("png",):
        p = OUT / f"{name}.{ext}"
        fig.savefig(p, dpi=220 if ext == "png" else None)
        print(f"  saved {p}")
    plt.close(fig)


def main() -> None:
    s1 = load_s1()
    specs = [
        ("V1a_dendro_min", "V1a", "minimal"),
        ("V1b_dendro_stripped", "V1b", "stripped"),
        ("V2a_radialtree_min", "V2a", "minimal"),
        ("V2b_radialtree_stripped", "V2b", "stripped"),
        ("V3a_sunburst_min", "V3a", "minimal"),
        ("V3b_sunburst_stripped", "V3b", "stripped"),
    ]
    for fname, code, level in specs:
        minimal = (level == "minimal")
        if code.startswith("V1"):
            fig = _circular_dendro_axes(s1, minimal, code)
        elif code.startswith("V2"):
            fig = _radial_tree_axes(s1, minimal, code)
        else:
            fig = _sunburst_axes(s1, minimal, code)
        _save(fig, f"new_figureS1_{fname}")
    print("[variants] done.")


if __name__ == "__main__":
    main()
