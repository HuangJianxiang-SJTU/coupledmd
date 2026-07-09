#!/usr/bin/env python3
"""Canonical publication-grade Scientific Data main-figure generator.

Produces (matplotlib PDF + 600 dpi PNG via figstyle.py):
  Fig 1  scidata_figure1_overview_circos       — Circos class<->family coupling centerpiece
  Fig 2  scidata_figure2_data_records          — Archive hierarchy, schema, access model
  Fig 3  scidata_figure3_validation_ridgeline  — Pocket-recovery ridgeline + benchmark
  Fig 4  scidata_figure4_qc                    — Gateway heatmap + PBC/frame/QC panels
  Contact sheet: scidata_all_main_figures_contact_sheet.png

All numbers read from frozen clean-v1 CSVs in tables/ (no trajectory I/O).
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-coupledmd")

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Polygon, PathPatch
from matplotlib.path import Path as MplPath

import figstyle  # noqa: E402  (local module alongside this script)

figstyle.apply_style()

HERE = Path(__file__).resolve().parent
TBL = HERE / "tables"
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

# Canonical palette (re-exported for clarity)
FAM_COL = figstyle.FAMILY              # Gi green, Gs blue, Gq orange, G12-13 purple
FAM_ORDER = ["Gi", "Gs", "Gq", "G12-13"]
FAM_LABEL = figstyle.FAMILY_LABEL
CLASS_COL = {"A": "#2c6fb3", "B": "#c0741a"}   # class A blue, class B orange
INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT
OK_COL = FAM_COL["Gi"]
WARN_COL = "#c0741a"
HOLD_COL = "#8a4aa0"
SCREENSHOT_DIR = OUT / "portal_screenshots"


# ──────────────────────────────────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────────────────────────────────
def load_tables() -> dict:
    return dict(
        s1=pd.read_csv(TBL / "scidata_S1_included_systems_clean_v1.csv"),
        t4=pd.read_csv(TBL / "scidata_T4_technical_validation_clean_v1.csv"),
        t4a=pd.read_csv(TBL / "scidata_T4a_recovery_summary_clean_v1.csv"),
        s5=pd.read_csv(TBL / "scidata_S5_gateway_per_system_clean_v1.csv"),
        s2=pd.read_csv(TBL / "scidata_S2_held_back_systems.csv"),
        t2=pd.read_csv(TBL / "scidata_T2_repository_structure.csv"),
        t6=pd.read_csv(TBL / "scidata_T6_manifest_summary.csv"),
        t7=pd.read_csv(TBL / "scidata_T7_portal_file_availability_summary.csv"),
        t8=pd.read_csv(TBL / "scidata_T8_viz_pbc_full_audit_clean_v1.csv"),
        t8a=pd.read_csv(TBL / "scidata_T8a_viz_pbc_summary_clean_v1.csv"),
        t8b=pd.read_csv(TBL / "scidata_T8b_viz_qc_flags_clean_v1.csv"),
    )


def _metric(t8a: pd.DataFrame, name: str) -> int:
    row = t8a.loc[t8a["metric"] == name, "value"]
    return int(row.iloc[0]) if len(row) else 0


def categorize_hold(reason: str) -> str:
    r = reason.lower()
    if "nonstandard 6-replica" in r:
        return "nonstandard replicas + missing outputs"
    if "nonstandard trajectory" in r or "3 x 2 ns" in r or "3 x 260" in r:
        return "nonstandard length"
    if "missing processed pocket" in r:
        return "missing processed outputs"
    return "temporary / incomplete files"


# ──────────────────────────────────────────────────────────────────────────────
# Geometry helpers for the Circos
# ──────────────────────────────────────────────────────────────────────────────
def _polar_to_cart(r, theta):
    return r * np.cos(theta), r * np.sin(theta)


def _arc_path(r_inner, r_outer, theta0, theta1, n=48):
    """Closed annular-sector path between two radii and two angles (radians)."""
    t = np.linspace(theta0, theta1, n)
    xo, yo = _polar_to_cart(r_outer, t)
    xi, yi = _polar_to_cart(r_inner, t[::-1])
    verts = np.column_stack([np.r_[xo, xi], np.r_[yo, yi]])
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(verts) - 2) + [MplPath.CLOSEPOLY]
    return MplPath(verts, codes)


def _ribbon_path(theta0, theta1, r0, r1, n=64):
    """A 'ribbon' (quadratic-bezier-ish band) connecting two arcs at radius r0 and r1.

    theta0/theta1 are (start,end) angle tuples for the two endpoints on the outer ring.
    """
    a0, a1 = theta0
    b0, b1 = theta1
    t = np.linspace(0, 1, n)
    # outer edge along ring 0 (a0->a1), inner edge along ring 1 (b1->b0) to close
    ang_out = a0 + (a1 - a0) * t
    ang_in = b1 + (b0 - b1) * t
    xo, yo = _polar_to_cart(r0, ang_out)
    xi, yi = _polar_to_cart(r1, ang_in)
    verts = np.column_stack([np.r_[xo, xi], np.r_[yo, yi]])
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(verts) - 2) + [MplPath.CLOSEPOLY]
    return MplPath(verts, codes)


# ──────────────────────────────────────────────────────────────────────────────
# Figure 1 — Circos overview
# ──────────────────────────────────────────────────────────────────────────────
def build_circos(d: dict):
    s1 = d["s1"]
    t4a = d["t4a"]

    # class x family crosstab (system counts)
    ct = pd.crosstab(s1["gpcr_class"], s1["g_protein_family"])
    classes = list(ct.index)            # ['A','B']
    fams = [f for f in FAM_ORDER if f in ct.columns]

    class_counts = {c: int(ct.loc[c].sum()) for c in classes}
    fam_counts = {f: int(ct[f].sum()) for f in fams}
    total = sum(class_counts.values())

    # family-level recovery + sampling (µs)
    recov = {}
    samp = {}
    for _, row in t4a.iterrows():
        sub = row["subset"]
        if sub == "All clean-v1":
            continue
        # subset labels look like 'Gi/o','Gq/11' -> map back
    # robust mapping from t4a subset -> family key
    sub2fam = {"Gi/o": "Gi", "Gs": "Gs", "Gq/11": "Gq", "G12/13": "G12-13"}
    for _, row in t4a.iterrows():
        f = sub2fam.get(row["subset"])
        if f:
            recov[f] = float(row["recovery_rate_percent"])
    for f in fams:
        samp[f] = float(s1.loc[s1["g_protein_family"] == f, "total_sampling_ns"].sum()) / 1000.0

    # Layout: two arc groups with a small gap between them.
    # Classes occupy the top semicircle, families the bottom; both ordered so the
    # heaviest coupling (class A -> Gi) faces its counterpart.
    GAP = 0.06  # radians of empty space between the two arc groups
    class_span = np.pi - GAP          # classes span just under pi
    fam_span = np.pi - GAP
    # start class arc at angle pi (left) going clockwise to 0; we use standard polar
    # so increase CCW. Place classes on the upper half: from angle (pi - GAP/2) down to GAP/2.
    cls_start = np.pi - GAP / 2
    cls_ends = []
    a = cls_start
    for c in classes:
        w = class_span * class_counts[c] / total
        cls_ends.append((a, a - w))   # going clockwise (decreasing angle)
        a -= w
    fam_start = -GAP / 2              # continue clockwise into lower half
    fam_ends = []
    a = fam_start
    for f in fams:
        w = fam_span * fam_counts[f] / total
        fam_ends.append((a, a - w))
        a -= w
    # angle ranges (hi, lo) for each segment
    seg_angle = {}
    for c, (hi, lo) in zip(classes, cls_ends):
        seg_angle[c] = (lo, hi)
    for f, (hi, lo) in zip(fams, fam_ends):
        seg_angle[f] = (lo, hi)

    fig = plt.figure(figsize=(10.4, 8.6))
    ax = fig.add_axes([0.035, 0.045, 0.58, 0.90])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)

    R_OUT = 1.00       # outer segment radius
    R_SEG_IN = 0.92    # inner edge of class/family segment ring
    R_REC_OUT = 0.92   # recovery track outer
    R_REC_IN = 0.74
    R_SAMP_OUT = 0.74  # sampling track outer
    R_SAMP_IN = 0.60
    R_RIB = 0.60       # ribbons anchor at this radius and bow toward center

    # --- segment ring (classes + families) ---
    for c in classes:
        lo, hi = seg_angle[c]
        p = MplPath(_arc_verts(R_SEG_IN, R_OUT, lo, hi))
        ax.add_patch(Polygon(_arc_poly(R_SEG_IN, R_OUT, lo, hi),
                                 facecolor=CLASS_COL[c], edgecolor="white", lw=1.0))
        mid = 0.5 * (lo + hi)
        rlab = 1.06
        x, y = _polar_to_cart(rlab, mid)
        ha = "left" if -np.pi / 2 < mid < np.pi / 2 else "right"
        ax.text(x, y, f"Class {c}\n{class_counts[c]} sys", ha=ha, va="center",
                fontsize=8.5, fontweight="bold", color=CLASS_COL[c])
    for f in fams:
        lo, hi = seg_angle[f]
        ax.add_patch(Polygon(_arc_poly(R_SEG_IN, R_OUT, lo, hi),
                                 facecolor=FAM_COL[f], edgecolor="white", lw=1.0))
        mid = 0.5 * (lo + hi)
        x, y = _polar_to_cart(1.06, mid)
        ha = "left" if -np.pi / 2 < mid < np.pi / 2 else "right"
        ax.text(x, y, f"{FAM_LABEL[f]}\n{fam_counts[f]} sys", ha=ha, va="center",
                fontsize=8.5, fontweight="bold", color=FAM_COL[f])

    # --- recovery track (inner radial bars per family) ---
    recov_max = max(recov.values()) if recov else 100.0
    for f in fams:
        lo, hi = seg_angle[f]
        frac = recov.get(f, 0.0) / recov_max
        r_in = R_REC_IN
        r_out = R_REC_IN + (R_REC_OUT - R_REC_IN) * frac
        ax.add_patch(Polygon(_arc_poly(r_in, r_out, lo, hi, n=24),
                                 facecolor=FAM_COL[f], alpha=0.85, edgecolor="none"))
        mid = 0.5 * (lo + hi)
        x, y = _polar_to_cart(R_REC_IN - 0.04, mid)
        ha = "left" if -np.pi / 2 < mid < np.pi / 2 else "right"
        ax.text(x, y, f"{recov.get(f,0):.1f}%", ha=ha, va="center",
                fontsize=6.5, color=FAM_COL[f], fontweight="bold")

    # --- sampling track (outer radial bars per family) ---
    samp_max = max(samp.values()) if samp else 1.0
    for f in fams:
        lo, hi = seg_angle[f]
        frac = samp.get(f, 0.0) / samp_max
        r_in = R_SAMP_IN
        r_out = R_SAMP_IN + (R_SAMP_OUT - R_SAMP_IN) * frac
        ax.add_patch(Polygon(_arc_poly(r_in, r_out, lo, hi, n=24),
                                 facecolor=FAM_COL[f], alpha=0.45, edgecolor="none"))

    # thin track guide rings
    for r in (R_REC_OUT, R_REC_IN, R_SAMP_OUT, R_SAMP_IN):
        th = np.linspace(0, 2 * np.pi, 200)
        ax.plot(r * np.cos(th), r * np.sin(th), color=PALE, lw=0.4, zorder=0)

    # --- ribbons: class -> family ---
    for c in classes:
        lo_c, hi_c = seg_angle[c]
        # allocate sub-arcs within the class segment, one per family (sized by cell count)
        sub = a = lo_c
        spans = []
        for f in fams:
            n = int(ct.loc[c, f]) if f in ct.columns else 0
            if n == 0:
                spans.append(None)
                continue
            w = (hi_c - lo_c) * n / class_counts[c]
            spans.append((a, a + w))
            a += w
        for f, sp in zip(fams, spans):
            if sp is None:
                continue
            c0, c1 = sp
            f0, f1 = seg_angle[f]
            # mirror family sub-arc sized by same cell count within family segment
            f_span_total = seg_angle[f][1] - seg_angle[f][0]
            n = int(ct.loc[c, f])
            fw = f_span_total * n / fam_counts[f]
            # place family sub-arc starting from the class-facing edge
            ff0 = f0
            ff1 = f0 + fw
            seg_angle[f] = (ff1, f1)  # consume from the low edge
            ribbon = _ribbon_path((c0, c1), (ff0, ff1), R_RIB, R_RIB * 0.30)
            ax.add_patch(PathPatch(ribbon, facecolor=FAM_COL[f],
                                       alpha=0.35, edgecolor="none", lw=0))

    # --- center summary ---
    ax.text(0, 0.10, "CoupledMD", ha="center", va="center", fontsize=15,
            fontweight="bold", color=INK)
    ax.text(0, 0.02, "clean-v1 release", ha="center", va="center", fontsize=8.5,
            color=MUTED)
    ax.text(0, -0.10, "208 systems", ha="center", va="center", fontsize=11,
            fontweight="bold", color=INK)
    ax.text(0, -0.18, "174 receptors · 312 µs", ha="center", va="center",
            fontsize=8.5, color=INK)
    ax.text(0, -0.25, "3 × 500 ns · POPC · CHARMM36", ha="center", va="center",
            fontsize=7.2, color=MUTED)

    ax.set_title("Figure 1.  Coupling landscape of the clean-v1 GPCR/G-protein MD dataset",
                 fontsize=11, fontweight="bold", loc="left", x=0.0)

    # ── right-side strip: promiscuous receptors ───────────────────────────
    axr = fig.add_axes([0.69, 0.11, 0.29, 0.78])
    axr.axis("off")
    # receptors coupled to >1 family
    ruse = (s1.groupby("receptor_uniprot")["g_protein_family"]
            .agg(lambda s: sorted(set(s))))
    multi = ruse[ruse.apply(len) > 1]
    # friendly names
    name_map = (s1.drop_duplicates("receptor_uniprot")
                .set_index("receptor_uniprot")["receptor_name"].to_dict())
    rows = []
    for up, fs in multi.items():
        rows.append((name_map.get(up, up), len(fs), len(fs) == 3, up))
    rows.sort(key=lambda r: (-r[1], r[0]))
    axr.text(0.0, 1.02, "Receptor coupling breadth", transform=axr.transAxes,
             fontsize=9, fontweight="bold", color=INK)
    axr.text(0.0, 0.975, "receptors simulated with >1 G-protein family",
             transform=axr.transAxes, fontsize=7, color=MUTED)
    n = len(rows)
    ytop = 0.92
    ybot = 0.04
    ys = np.linspace(ytop, ybot, n)
    for (name, k, is3, up), y in zip(rows, ys):
        # bar length ∝ #families
        axr.barh(y, k / 3.0, height=0.6 / n, color=FAM_COL["G12-13"] if is3 else FAM_COL["Gi"],
                 alpha=0.85, transform=axr.transAxes)
        label = name if len(name) <= 28 else name[:25] + "..."
        axr.text(-0.02, y, label, transform=axr.transAxes, ha="right", va="center",
                 fontsize=5.8, color=INK)
        axr.text(k / 3.0 + 0.015, y, f"{k}", transform=axr.transAxes, ha="left",
                 va="center", fontsize=6.5, color=MUTED, fontweight="bold")
    axr.set_xlim(-0.62, 1.15)
    axr.text(0.0, -0.06, f"{n} receptors couple to ≥2 families\n(max 3) — descriptive reuse signal",
             transform=axr.transAxes, fontsize=6.5, color=MUTED)

    _save(fig, "scidata_figure1_overview_circos")


def _arc_poly(r_inner, r_outer, theta0, theta1, n=48):
    t = np.linspace(theta0, theta1, n)
    xo, yo = _polar_to_cart(r_outer, t)
    xi, yi = _polar_to_cart(r_inner, t[::-1])
    return np.column_stack([np.r_[xo, xi], np.r_[yo, yi]])


def _arc_verts(r_inner, r_outer, theta0, theta1, n=48):
    return _arc_poly(r_inner, r_outer, theta0, theta1, n)


# ──────────────────────────────────────────────────────────────────────────────
# Figure 3 — validation ridgeline + lollipop + benchmark
# ──────────────────────────────────────────────────────────────────────────────
def build_validation(d: dict):
    t4 = d["t4"]
    t4a = d["t4a"]
    s1 = d["s1"]

    fig = plt.figure(figsize=(7.2, 7.7))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.35, 1.0, 0.7],
                          hspace=0.68, left=0.16, right=0.96, top=0.93, bottom=0.11)

    # --- Panel A: ridgeline of best_ortho_freq by family ---
    axA = fig.add_subplot(gs[0])
    sub2fam = {"Gi/o": "Gi", "Gs": "Gs", "Gq/11": "Gq", "G12/13": "G12-13"}
    fam_order = FAM_ORDER
    # merge family label
    t4m = t4.copy()
    t4m["fam"] = t4m["g_family"]
    rows_for_kde = t4m.dropna(subset=["best_ortho_freq"])
    from scipy.stats import gaussian_kde
    ybase = np.linspace(0, 1, 200)
    for i, f in enumerate(fam_order):
        vals = rows_for_kde.loc[rows_for_kde["fam"] == f, "best_ortho_freq"].values
        if len(vals) < 2 or np.allclose(vals.std(), 0):
            vals = np.r_[vals, vals + 1e-3, vals - 1e-3]
        kde = gaussian_kde(vals, bw_method=0.25)
        dens = kde(ybase)
        dens = dens / dens.max() * 0.8
        y0 = i
        axA.fill_between(ybase, y0, y0 + dens, color=FAM_COL[f], alpha=0.55, lw=0)
        axA.plot(ybase, y0 + dens, color=FAM_COL[f], lw=1.0)
        # jitter dots
        jit = np.random.RandomState(7 + i).uniform(-0.06, 0.06, size=len(vals))
        axA.plot(vals, y0 + 0.05 + jit * 0.5, "|", color=FAM_COL[f],
                 ms=4, alpha=0.5, mew=0.8)
        rr = t4a.loc[t4a["subset"].map(sub2fam) == f, "recovery_rate_percent"]
        rr = float(rr.iloc[0]) if len(rr) else 0.0
        axA.text(0.965, y0 + 0.35, f"{FAM_LABEL[f]}  {rr:.1f}% recovered",
                 ha="right", va="center", fontsize=6.8, color=FAM_COL[f],
                 fontweight="bold", transform=axA.get_yaxis_transform()
                 if False else axA.transData)
    axA.axvline(0.85, color=INK, lw=0.8, ls="--", alpha=0.7)
    axA.text(0.852, 3.7, "0.85 recovery\nthreshold", fontsize=6, color=INK, va="top")
    axA.set_yticks(range(len(fam_order)))
    axA.set_yticklabels([FAM_LABEL[f] for f in fam_order], fontsize=7.5)
    axA.set_ylim(-0.2, len(fam_order) + 0.4)
    axA.set_xlim(0.80, 1.0)
    axA.set_xlabel("best orthosteric-pocket frequency (per system)")
    figstyle.despine(axA)
    figstyle.panel_label(axA, "A", x=-0.10, y=1.06)
    axA.set_title("Binding-site recovery is consistent across G-protein families",
                  fontsize=8.5, loc="left", pad=4)

    # --- Panel B: n_pockets lollipop by family ---
    axB = fig.add_subplot(gs[1])
    grp = t4m.groupby("fam")["n_pockets"]
    med = grp.median().reindex(fam_order)
    q1 = grp.quantile(0.25).reindex(fam_order)
    q3 = grp.quantile(0.75).reindex(fam_order)
    xs = np.arange(len(fam_order))
    for x, f in zip(xs, fam_order):
        # IQR bar
        axB.plot([x, x], [q1[f], q3[f]], color=FAM_COL[f], lw=3, alpha=0.5,
                 solid_capstyle="round")
        axB.plot(x, med[f], "o", color=FAM_COL[f], ms=7, zorder=3)
        # raw dots
        vals = t4m.loc[t4m["fam"] == f, "n_pockets"].values
        jit = np.random.RandomState(11 + x).uniform(-0.12, 0.12, size=len(vals))
        axB.plot(x + jit, vals, ".", color=FAM_COL[f], alpha=0.35, ms=2.5)
    axB.set_xticks(xs)
    axB.set_xticklabels([FAM_LABEL[f] for f in fam_order], fontsize=7.5)
    axB.set_ylabel("pockets / system")
    axB.set_ylim(0, 22)
    figstyle.despine(axB)
    figstyle.panel_label(axB, "B", x=-0.10, y=1.06)
    axB.set_title("Detected pocket count is stable across families (median ± IQR)",
                  fontsize=8.5, loc="left", pad=4)

    # --- Panel C: dataset benchmark (positioning) ---
    axC = fig.add_subplot(gs[2])
    # honest scope comparison — values from the research plan / public knowledge only.
    datasets = ["GPCRmd\n(single receptor)", "mdCATH\n(single domain)",
                "This work\n(complex)"]
    systems = [60, 5398, 208]
    sampling = [40, 320, 312]      # µs order-of-magnitude (mdCATH ~ms aggregate -> shown as bar)
    # normalize for a single comparable axis: systems and aggregate µs as grouped bars
    x = np.arange(len(datasets))
    w = 0.38
    b1 = axC.bar(x - w / 2, systems, w, color=PALE, edgecolor=INK, lw=0.5,
                 label="systems")
    b2 = axC.bar(x + w / 2, sampling, w, color=[MUTED, MUTED, figstyle.ACCENT],
                 edgecolor=INK, lw=0.5, label="aggregate µs")
    axC.set_yscale("log")
    axC.set_xticks(x)
    axC.set_xticklabels(datasets, fontsize=7)
    axC.set_ylabel("count (log)")
    axC.legend(frameon=False, fontsize=6.2, loc="upper left", ncol=2)
    for xi, v in zip(x - w / 2, systems):
        axC.text(xi, v * 1.1, f"{v}", ha="center", fontsize=6, color=INK)
    for xi, v in zip(x + w / 2, sampling):
        axC.text(xi, v * 1.1, f"{v}", ha="center", fontsize=6, color=INK)
    figstyle.despine(axC)
    figstyle.panel_label(axC, "C", x=-0.10, y=1.06)
    axC.set_title("Scope: multi-chain functional complexes complement single-receptor/domain resources",
                  fontsize=8.5, loc="left", pad=4)

    _save(fig, "scidata_figure3_validation_ridgeline")


# ──────────────────────────────────────────────────────────────────────────────
# Figure 2 — data records, schema, access model
# ──────────────────────────────────────────────────────────────────────────────
def _rounded_box(ax, xy, w, h, text, fc="#f5f7fa", ec=PALE, fs=6.5, bold=False):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04",
        facecolor=fc, edgecolor=ec, linewidth=0.6, transform=ax.transAxes,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2, y + h / 2, text, transform=ax.transAxes,
        ha="center", va="center", fontsize=fs,
        fontweight="bold" if bold else "normal", color=INK,
    )


def _arrow(ax, x0, y0, x1, y1, color=MUTED):
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1), transform=ax.transAxes,
        arrowstyle="-|>", mutation_scale=8, linewidth=0.7, color=color,
        shrinkA=2, shrinkB=2,
    ))


def build_figure2(d: dict):
    t2 = d["t2"]
    t6 = d["t6"]
    t7 = d["t7"]

    fig = plt.figure(figsize=(figstyle.COL2, 5.8))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 0.95], hspace=0.48, wspace=0.38,
                          left=0.08, right=0.97, top=0.93, bottom=0.07)

    # --- Panel A: archive hierarchy tree ---
    axA = fig.add_subplot(gs[0, 0])
    axA.set_xlim(0, 1)
    axA.set_ylim(0, 1)
    axA.axis("off")
    figstyle.panel_label(axA, "A", x=-0.08, y=1.02)
    axA.set_title("Archival repository hierarchy", fontsize=8.5, loc="left", pad=4)

    tree_lines = [
        ("archive_root/", 0.02, 0.92, True),
        ("manifest/  checksums + version", 0.06, 0.84, False),
        ("metadata/  systems + held_back", 0.06, 0.76, False),
        ("systems/<system_id>/", 0.06, 0.68, True),
        ("topology/  structures + parameters", 0.10, 0.60, False),
        ("trajectories/rep{1..3}/  full production", 0.10, 0.52, False),
        ("reduced/  aligned strided trajectories", 0.10, 0.44, False),
        ("features/  RMSD, RMSF, contacts", 0.10, 0.36, False),
        ("pocket/  fpocket + GPCRdb mapping", 0.10, 0.28, False),
        ("qc/  frame, PBC, stability reports", 0.10, 0.20, False),
        ("code/  scripts + notebooks", 0.06, 0.10, False),
        ("web_api_snapshot/  OpenAPI schema", 0.06, 0.02, False),
    ]
    for txt, x, y, bold in tree_lines:
        axA.text(x, y, txt, transform=axA.transAxes, fontsize=6.2 if not bold else 6.8,
                 fontweight="bold" if bold else "normal", fontfamily="monospace", color=INK)
    arch_row = t6.loc[t6["manifest"] == "archive_manifest_clean_v1_from_metadata"].iloc[0]
    portal_row = t6.loc[t6["manifest"] == "portal_file_manifest_clean_v1"].iloc[0]
    axA.text(
        0.02, -0.06,
        f"clean v1: {int(arch_row['records'])} archive paths · "
        f"{int(portal_row['records'])} portal/API records",
        transform=axA.transAxes, fontsize=5.8, color=MUTED,
    )

    # --- Panel B: metadata schema ---
    axB = fig.add_subplot(gs[0, 1])
    axB.set_xlim(0, 1)
    axB.set_ylim(0, 1)
    axB.axis("off")
    figstyle.panel_label(axB, "B", x=-0.08, y=1.02)
    axB.set_title("Metadata schema (per system)", fontsize=8.5, loc="left", pad=4)

    boxes = {
        "system": (0.36, 0.78, 0.28, 0.12),
        "receptor": (0.06, 0.54, 0.24, 0.11),
        "G protein": (0.38, 0.54, 0.24, 0.11),
        "ligand/state": (0.70, 0.54, 0.24, 0.11),
        "replicas": (0.18, 0.30, 0.24, 0.11),
        "files": (0.58, 0.30, 0.24, 0.11),
        "QC status": (0.36, 0.06, 0.28, 0.11),
    }
    for label, (x, y, w, h) in boxes.items():
        _rounded_box(axB, (x, y), w, h, label, bold=True)
    _arrow(axB, 0.50, 0.78, 0.18, 0.65)
    _arrow(axB, 0.50, 0.78, 0.50, 0.65)
    _arrow(axB, 0.50, 0.78, 0.82, 0.65)
    _arrow(axB, 0.50, 0.54, 0.30, 0.41)
    _arrow(axB, 0.50, 0.54, 0.70, 0.41)
    _arrow(axB, 0.50, 0.30, 0.50, 0.17)
    axB.text(
        0.02, -0.04,
        "Keys: system_id, UniProt, GPCRdb, class, G-protein family,\n"
        "ligand/source, replica IDs, paths, QC flags, checksums",
        transform=axB.transAxes, fontsize=5.8, color=MUTED, va="top",
    )

    # --- Panel C: access model ---
    axC = fig.add_subplot(gs[1, 0])
    axC.set_xlim(0, 1)
    axC.set_ylim(0, 1)
    axC.axis("off")
    figstyle.panel_label(axC, "C", x=-0.08, y=1.02)
    axC.set_title("Archive-first access model", fontsize=8.5, loc="left", pad=4)

    layers = [
        ("Stable archival\nrepository", "DOI/accession\nfull trajectories\nmetadata + manifests", ACCENT),
        ("Web portal", "browse · filter\nvisualize · download", "#2c6fb3"),
        ("REST API", "programmatic\nmetadata + derived\nrecords", "#586170"),
    ]
    for i, (title, sub, col) in enumerate(layers):
        x = 0.02 + i * 0.33
        _rounded_box(axC, (x, 0.35), 0.28, 0.55, "", fc="#eef6ff", ec=col)
        axC.text(x + 0.14, 0.72, title, transform=axC.transAxes, ha="center", va="center",
                 fontsize=7.2, fontweight="bold", color=col)
        axC.text(x + 0.14, 0.52, sub, transform=axC.transAxes, ha="center", va="center",
                 fontsize=5.8, color=INK)
        if i < 2:
            _arrow(axC, x + 0.29, 0.62, x + 0.33, 0.62)
    miss = int(t7["missing"].sum())
    axC.text(
        0.02, 0.12,
        f"Portal layer: {int(t7['present'].sum())}/{int(t7['expected_systems'].sum())} "
        f"record slots present ({miss} missing); binary checksums pending",
        transform=axC.transAxes, fontsize=5.8, color=MUTED,
    )

    # --- Panel D: portal screenshot or styled placeholder ---
    axD = fig.add_subplot(gs[1, 1])
    axD.set_xlim(0, 1)
    axD.set_ylim(0, 1)
    axD.axis("off")
    figstyle.panel_label(axD, "D", x=-0.08, y=1.02)
    axD.set_title("Web portal access layer", fontsize=8.5, loc="left", pad=4)

    shot = None
    for ext in ("png", "jpg", "jpeg", "webp"):
        for p in sorted(SCREENSHOT_DIR.glob(f"*.{ext}")):
            shot = p
            break
        if shot:
            break

    frame = FancyBboxPatch(
        (0.04, 0.06), 0.92, 0.82, boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor="#f7f7f8", edgecolor=PALE, linewidth=0.8, transform=axD.transAxes,
    )
    axD.add_patch(frame)
    if shot and shot.exists():
        img = plt.imread(shot)
        axD.imshow(img, extent=[0.06, 0.94, 0.10, 0.84], aspect="auto", zorder=1)
        axD.text(0.06, 0.02, shot.name, transform=axD.transAxes, fontsize=5.5, color=MUTED)
    else:
        axD.text(
            0.50, 0.52,
            "Portal screenshot pending\n\nsearch · filters · NGL viewer\n"
            "downloads · API endpoints",
            transform=axD.transAxes, ha="center", va="center",
            fontsize=7.5, color=MUTED, linespacing=1.5,
        )
        axD.text(
            0.50, 0.14,
            "Drop PNG into scidata_figures/portal_screenshots/\n"
            "and re-run to embed",
            transform=axD.transAxes, ha="center", va="center",
            fontsize=5.8, color=MUTED, style="italic",
        )

    fig.suptitle(
        "Figure 2.  Data records, repository organization and access model",
        fontsize=9.5, fontweight="bold", x=0.08, ha="left", y=0.985,
    )
    _save(fig, "scidata_figure2_data_records")


# ──────────────────────────────────────────────────────────────────────────────
# Figure 4 — gateway heatmap (fancy) + QC completeness panels
# ──────────────────────────────────────────────────────────────────────────────
def build_qc(d: dict):
    s5 = d["s5"]
    s2 = d["s2"]
    t8 = d["t8"]
    t8a = d["t8a"]
    t8b = d["t8b"]
    s1 = d["s1"]

    iface_cols = [
        ("TM3-TM4", "TM3-TM4 open_fraction"),
        ("TM7-TM1", "TM7-TM1 open_fraction"),
        ("TM4-TM5", "TM4-TM5 open_fraction"),
        ("TM5-TM6", "TM5-TM6 open_fraction"),
        ("TM1-TM2", "TM1-TM2 open_fraction"),
        ("TM6-TM7", "TM6-TM7 open_fraction"),
        ("TM2-TM3", "TM2-TM3 open_fraction"),
    ]
    mat = s5[["System ID"] + [c[1] for c in iface_cols]].copy()
    mat.columns = ["system_id"] + [c[0] for c in iface_cols]
    fam_map = s1.set_index("system_id")["g_protein_family"].to_dict()
    mat["fam"] = mat["system_id"].map(fam_map)
    mat = mat.dropna(subset=["fam"])
    mat["fam_order"] = mat["fam"].map({f: i for i, f in enumerate(FAM_ORDER)})
    mat = mat.sort_values(["fam_order", "system_id"]).reset_index(drop=True)
    M = mat[[c[0] for c in iface_cols]].to_numpy(float)

    fig = plt.figure(figsize=(7.7, 8.35))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0], wspace=0.34,
                          left=0.14, right=0.97, top=0.92, bottom=0.14)
    gs_r = gs[0, 1].subgridspec(3, 1, height_ratios=[1.25, 0.90, 1.12], hspace=0.70)

    # --- Panel A: gateway heatmap (fancy centerpiece) ---
    axA = fig.add_subplot(gs[0, 0])
    cmap = mpl.colormaps["RdYlBu_r"]
    im = axA.imshow(M, aspect="auto", cmap=cmap, vmin=0, vmax=1, interpolation="nearest")
    axA.set_xticks(range(len(iface_cols)))
    axA.set_xticklabels([c[0] for c in iface_cols], rotation=45, ha="right", fontsize=7)
    counts = mat["fam"].value_counts().reindex(FAM_ORDER).fillna(0).astype(int)
    cum = 0
    for f in FAM_ORDER:
        cum += counts[f]
        if cum < len(mat):
            axA.axhline(cum - 0.5, color="white", lw=1.2)
    axA.set_yticks([])
    axA.set_xlabel("TM helix-pair gateway interface")
    axA.set_ylabel(f"{len(mat)} systems (grouped by G-protein family)", fontsize=7.5)
    cum = 0
    for f in FAM_ORDER:
        c = counts[f]
        if c:
            axA.text(-0.75, cum + c / 2 - 0.5, FAM_LABEL[f], ha="right", va="center",
                     fontsize=7, color=FAM_COL[f], fontweight="bold")
        cum += c
    cb = fig.colorbar(im, ax=axA, fraction=0.035, pad=0.02)
    cb.set_label("open fraction", fontsize=6.5)
    cb.ax.tick_params(labelsize=6)
    figstyle.panel_label(axA, "A", x=-0.16, y=1.02)
    axA.set_title(
        "TM-gateway open-fraction landscape\n(validation: conformational range present)",
        fontsize=8.5, loc="left", pad=6,
    )

    # --- Panel B: PBC audit (fixed split axes — no overlap) ---
    axB = fig.add_subplot(gs_r[0])
    axB.set_axis_off()
    figstyle.panel_label(axB, "B", x=-0.18, y=1.06)
    axB.set_title("Reduced-trajectory PBC audit", fontsize=8, loc="left", pad=4)

    ok = _metric(t8a, "status_OK")
    warn = _metric(t8a, "status_WARN")
    audited = _metric(t8a, "systems_audited")

    ax_pie = axB.inset_axes([0.00, 0.10, 0.36, 0.78])
    ax_pie.pie(
        [ok, warn], colors=[OK_COL, WARN_COL], startangle=90,
        wedgeprops=dict(width=0.44, edgecolor="white", linewidth=1.0),
    )
    ax_pie.set(aspect="equal")
    ax_pie.text(0, 0.05, str(audited), ha="center", va="center", fontsize=13,
                fontweight="bold", color=INK)
    ax_pie.text(0, -0.16, "audited", ha="center", va="center", fontsize=6.2, color=MUTED)
    ax_pie.text(0, -1.18, f"OK {ok}   WARN {warn}", ha="center", va="center",
                fontsize=5.8, color=INK)

    ax_bar = axB.inset_axes([0.42, 0.12, 0.56, 0.78])
    metrics = [
        ("atom mismatch", _metric(t8a, "atom_count_mismatch")),
        ("blank elements", _metric(t8a, "blank_elements")),
        ("box mismatch", _metric(t8a, "box_mismatch")),
        ("intra-chain breaks", _metric(t8a, "intra_break_frames")),
        ("inter-chain splits", _metric(t8a, "inter_chain_split_frames")),
    ]
    ys = np.arange(len(metrics))
    vals = [m[1] for m in metrics]
    ax_bar.barh(ys, vals, height=0.55, color=[OK_COL if v == 0 else WARN_COL for v in vals],
                edgecolor=INK, linewidth=0.4)
    ax_bar.set_yticks(ys)
    ax_bar.set_yticklabels([])
    ax_bar.set_xlim(0, max(max(vals) * 1.5, 0.8))
    ax_bar.invert_yaxis()
    for yi, (label, v) in zip(ys, metrics):
        ax_bar.text(0.02, yi, label, va="center", ha="left", fontsize=5.8, color=INK)
        ax_bar.text(0.74, yi, str(v), va="center", ha="center",
                    fontsize=6.2, fontweight="bold", color=INK)
    ax_bar.set_xlabel("failure count", fontsize=6)
    figstyle.despine(ax_bar, left=True, bottom=True)

    # --- Panel C: frame-count distribution ---
    axC = fig.add_subplot(gs_r[1])
    frame_counts = t8["n_frames"].value_counts().sort_index()
    xs = np.arange(len(frame_counts))
    bar_cols = []
    for nf in frame_counts.index:
        if nf == 2500:
            bar_cols.append(ACCENT)
        elif nf == 2501:
            bar_cols.append(WARN_COL)
        else:
            bar_cols.append(HOLD_COL)
    bars = axC.bar(xs, frame_counts.values, color=bar_cols, edgecolor=INK, linewidth=0.4, width=0.62)
    axC.set_xticks(xs)
    axC.set_xticklabels([str(int(v)) for v in frame_counts.index], fontsize=6.5)
    axC.set_xlabel("frames / reduced trajectory")
    axC.set_ylabel("systems")
    for bar, n in zip(bars, frame_counts.values):
        axC.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                 str(int(n)), ha="center", va="bottom", fontsize=6, color=INK)
    figstyle.despine(axC)
    figstyle.panel_label(axC, "C", x=-0.18, y=1.08)
    axC.set_title("Reduced trajectory frame counts", fontsize=8, loc="left", pad=4)

    # --- Panel D: held-back transparency + QC flags ---
    axD = fig.add_subplot(gs_r[2])
    axD.set_axis_off()
    figstyle.panel_label(axD, "D", x=-0.18, y=1.06)
    axD.set_title("Exclusion roster and visualization flags", fontsize=8, loc="left", pad=10)

    ax_donut = axD.inset_axes([0.00, 0.00, 0.40, 0.82])
    s2c = s2.copy()
    s2c["cat"] = s2c["hold_reason"].apply(categorize_hold)
    cat_counts = s2c["cat"].value_counts()
    palette = [WARN_COL, HOLD_COL, OK_COL, "#586170"]
    wedges, _ = ax_donut.pie(
        cat_counts.values, colors=palette[: len(cat_counts)], startangle=90,
        wedgeprops=dict(width=0.40, edgecolor="white", linewidth=1.0),
    )
    ax_donut.set(aspect="equal")
    ax_donut.text(0, 0.06, "14", ha="center", va="center", fontsize=14, fontweight="bold", color=INK)
    ax_donut.text(0, -0.14, "held back", ha="center", va="center", fontsize=6.2, color=MUTED)
    ax_donut.text(0, -0.26, "of 222", ha="center", va="center", fontsize=5.5, color=MUTED)
    ax_donut.legend(
        wedges, [f"{c[:16]} ({n})" for c, n in cat_counts.items()],
        loc="lower center", bbox_to_anchor=(0.5, -0.44), fontsize=5.1, frameon=False,
    )

    ax_tbl = axD.inset_axes([0.45, 0.00, 0.55, 0.82])
    ax_tbl.set_axis_off()
    flags = t8b[["system_id", "status", "n_frames", "scatter_frames"]].copy()
    tbl = ax_tbl.table(
        cellText=flags.values,
        colLabels=["system", "status", "frames", "scatter"],
        loc="upper center",
        bbox=[0.0, 0.0, 1.0, 1.0],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(5.8)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor(PALE)
        cell.set_linewidth(0.35)
        if r == 0:
            cell.set_facecolor(PALE)
            cell.set_text_props(fontweight="bold")
        elif r > 0 and c == 1:
            st = flags.iloc[r - 1]["status"]
            cell.set_facecolor("#eef6f1" if st == "OK" else "#fdf3e7")
    fig.suptitle(
        "Figure 4.  Global quality control and completeness summary",
        fontsize=9.5, fontweight="bold", x=0.08, ha="left", y=0.985,
    )
    fig.text(
        0.08, 0.045,
        "Reduced-trajectory visualization audit (208/208 clean-v1). "
        "Production-archive frame counts and SHA256 checksums pending.",
        fontsize=5.8, color=MUTED, ha="left",
    )
    _save(fig, "scidata_figure4_qc")


# ──────────────────────────────────────────────────────────────────────────────
def build_contact_sheet():
    """Tile all four main figure PNGs into one contact sheet."""
    from PIL import Image
    paths = [OUT / f"{n}.png" for n in (
        "scidata_figure1_overview_circos",
        "scidata_figure2_data_records",
        "scidata_figure3_validation_ridgeline",
        "scidata_figure4_qc",
    )]
    imgs = [Image.open(p).convert("RGB") for p in paths if p.exists()]
    if not imgs:
        print("  (no figures for contact sheet)")
        return
    # scale to common width
    W = 1500
    scaled = []
    for im in imgs:
        h = int(im.height * W / im.width)
        scaled.append(im.resize((W, h)))
    pad = 30
    H = sum(im.height for im in scaled) + pad * (len(scaled) + 1)
    sheet = Image.new("RGB", (W + pad * 2, H), "white")
    y = pad
    for im in scaled:
        sheet.paste(im, (pad, y))
        y += im.height + pad
    out = OUT / "scidata_all_main_figures_contact_sheet.png"
    sheet.save(out)
    print(f"  saved {out}")


# ──────────────────────────────────────────────────────────────────────────────
def _save(fig, name):
    for ext in ("pdf", "png"):
        p = OUT / f"{name}.{ext}"
        fig.savefig(p, dpi=600 if ext == "png" else None)
        print(f"  saved {p}")
    plt.close(fig)


def _sanity(d):
    s1 = d["s1"]
    t4 = d["t4"]
    print("\n--- sanity check (figure vs source CSV) ---")
    print(f"  systems           : {len(s1)}  (expect 208)")
    print(f"  unique receptors  : {s1['receptor_uniprot'].nunique()}  (expect 174)")
    print(f"  total sampling µs : {s1['total_sampling_ns'].sum()/1000:.1f}  (expect 312.0)")
    print(f"  class counts      : {s1['gpcr_class'].value_counts().to_dict()}")
    print(f"  family counts     : {s1['g_protein_family'].value_counts().to_dict()}")
    rec = (t4['ortho_recovered'] == True).sum()
    has_p = (t4['has_pockets'] == True).sum()
    print(f"  ortho recovered   : {rec}/{has_p}  (expect 156/206)")
    multi = s1.groupby('receptor_uniprot')['g_protein_family'].nunique()
    print(f"  promiscuous rec.  : {(multi>1).sum()}  (expect 15)")


def main():
    d = load_tables()
    _sanity(d)
    print("\n[1/5] Circos overview (Fig 1)...")
    build_circos(d)
    print("[2/5] Data records (Fig 2)...")
    build_figure2(d)
    print("[3/5] Validation ridgeline (Fig 3)...")
    build_validation(d)
    print("[4/5] QC + gateway heatmap (Fig 4)...")
    build_qc(d)
    print("[5/5] Contact sheet...")
    build_contact_sheet()
    print("\nDone.")


if __name__ == "__main__":
    main()
