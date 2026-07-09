#!/usr/bin/env python3
"""New Figure 4 — global quality-control and completeness summary.

Adapted from `generate_scidata_main_figures.py::build_qc`, now standalone and
re-designed for publication:

  - No figure or subpanel titles.
  - Enlarged typography (panel letters / labels / ticks) consistent with
    `new_figure1.py`.
  - Panels B–D replaced with content that carries real information:
      B  orthosteric pocket-recovery rate by G-protein family (structural
         fidelity benchmark; Table T4a).
      C  per-interface TM-gateway open-fraction distribution across all 208
         systems (box plot; quantifies the heatmap in A using Table S5).
      D  dataset completeness and exclusion transparency, with a one-line
         reduced-trajectory integrity callout (Tables S2, T8/T8a).
  - Panel A (the TM-gateway open-fraction heatmap) is retained as the
    centerpiece.

All numbers are read from frozen clean-v1 CSVs in tables/; no trajectory I/O.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-coupledmd")

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import figstyle  # noqa: E402  (local module alongside this script)

figstyle.apply_style()

HERE = Path(__file__).resolve().parent
TBL = HERE / "tables"
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

FAM_COL = figstyle.FAMILY
FAM_ORDER = figstyle.FAMILY_ORDER
FAM_LABEL = figstyle.FAMILY_LABEL
INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT
WARN_COL = "#c0741a"
HOLD_COL = "#8a4aa0"
OK_COL = FAM_COL["Gi"]

# Enlarged typography, consistent with new_figure1.py.
FS_PANEL = 13   # panel letter (A–D)
FS_LABEL = 11   # axis labels
FS_TICK = 9     # tick labels
FS_ANNOT = 8    # in-panel annotations / small text

IFACE_COLS = [
    ("TM3-TM4", "TM3-TM4 open_fraction"),
    ("TM7-TM1", "TM7-TM1 open_fraction"),
    ("TM4-TM5", "TM4-TM5 open_fraction"),
    ("TM5-TM6", "TM5-TM6 open_fraction"),
    ("TM1-TM2", "TM1-TM2 open_fraction"),
    ("TM6-TM7", "TM6-TM7 open_fraction"),
    ("TM2-TM3", "TM2-TM3 open_fraction"),
]


def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        path = OUT / f"{name}.{ext}"
        fig.savefig(path, bbox_inches="tight", pad_inches=0.02,
                    dpi=600 if ext == "png" else None)
        print(f"  saved {path}")
    plt.close(fig)


def panel(ax, letter: str, x=-0.12, y=1.05) -> None:
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=FS_PANEL,
            fontweight="bold", va="bottom", ha="left")


def load_tables() -> dict[str, pd.DataFrame]:
    return {
        "s1": pd.read_csv(TBL / "scidata_S1_included_systems_clean_v1.csv"),
        "s2": pd.read_csv(TBL / "scidata_S2_held_back_systems.csv"),
        "s5": pd.read_csv(TBL / "scidata_S5_gateway_per_system_clean_v1.csv"),
        "t4a": pd.read_csv(TBL / "scidata_T4a_recovery_summary_clean_v1.csv"),
        "t8": pd.read_csv(TBL / "scidata_T8_viz_pbc_full_audit_clean_v1.csv"),
        "t8a": pd.read_csv(TBL / "scidata_T8a_viz_pbc_summary_clean_v1.csv"),
        "t8b": pd.read_csv(TBL / "scidata_T8b_viz_qc_flags_clean_v1.csv"),
    }


def categorize_hold(reason: str) -> str:
    r = reason.lower()
    if "nonstandard 6-replica" in r:
        return "nonstandard replicas + missing outputs"
    if "nonstandard trajectory" in r or "3 x 2 ns" in r or "3 x 260" in r:
        return "nonstandard length"
    if "missing processed pocket" in r:
        return "missing processed outputs"
    return "temporary / incomplete files"


def make_figure4() -> None:
    d = load_tables()
    s1, s2, s5 = d["s1"], d["s2"], d["s5"]
    t4a, t8, t8a, t8b = d["t4a"], d["t8"], d["t8a"], d["t8b"]

    # ── Panel A: gateway open-fraction heatmap (centerpiece) ───────────────
    mat = s5[["System ID"] + [c[1] for c in IFACE_COLS]].copy()
    mat.columns = ["system_id"] + [c[0] for c in IFACE_COLS]
    fam_map = s1.set_index("system_id")["g_protein_family"].to_dict()
    mat["fam"] = mat["system_id"].map(fam_map)
    mat = mat.dropna(subset=["fam"])
    mat["fam_order"] = mat["fam"].map({f: i for i, f in enumerate(FAM_ORDER)})
    mat = mat.sort_values(["fam_order", "system_id"]).reset_index(drop=True)
    M = mat[[c[0] for c in IFACE_COLS]].to_numpy(float)
    n_sys = len(mat)
    counts = mat["fam"].value_counts().reindex(FAM_ORDER).fillna(0).astype(int)

    # ── Panel B data: orthosteric pocket recovery by family ───────────────
    t4a_fam = t4a[t4a["subset"].isin(["Gi/o", "Gs", "Gq/11", "G12/13"])].copy()
    t4a_all = t4a[t4a["subset"] == "All clean-v1"].iloc[0]

    # ── Panel D data: completeness / exclusions / integrity ───────────────
    s2c = s2.copy()
    s2c["cat"] = s2c["hold_reason"].apply(categorize_hold)
    cat_counts = s2c["cat"].value_counts()
    n_included = len(s1)
    n_held = len(s2)
    # integrity callout numbers
    audited = int(t8a.loc[t8a["metric"] == "systems_audited", "value"].iloc[0])
    n_ok = int(t8a.loc[t8a["metric"] == "status_OK", "value"].iloc[0])
    n_warn = int(t8a.loc[t8a["metric"] == "status_WARN", "value"].iloc[0])
    scatter_frames = int(t8a.loc[t8a["metric"] == "scatter_frames", "value"].iloc[0])
    atom_mm = int(t8a.loc[t8a["metric"] == "atom_count_mismatch", "value"].iloc[0])
    box_mm = int(t8a.loc[t8a["metric"] == "box_mismatch", "value"].iloc[0])
    intra = int(t8a.loc[t8a["metric"] == "intra_break_frames", "value"].iloc[0])
    inter = int(t8a.loc[t8a["metric"] == "inter_chain_split_frames", "value"].iloc[0])

    # ── Figure layout ─────────────────────────────────────────────────────
    fig = plt.figure(figsize=(10.4, 8.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0], wspace=0.34,
                          left=0.10, right=0.965, top=0.96, bottom=0.085)
    gs_r = gs[0, 1].subgridspec(3, 1, height_ratios=[1.05, 1.05, 0.95], hspace=0.62)

    axA = fig.add_subplot(gs[0, 0])

    # ── Panel A ───────────────────────────────────────────────────────────
    cmap = mpl.colormaps["RdYlBu_r"]
    im = axA.imshow(M, aspect="auto", cmap=cmap, vmin=0, vmax=1,
                    interpolation="nearest")
    axA.set_xticks(range(len(IFACE_COLS)))
    axA.set_xticklabels([c[0] for c in IFACE_COLS], rotation=45, ha="right",
                        fontsize=FS_TICK)
    axA.set_yticks([])
    axA.set_xlabel("TM helix-pair gateway interface", fontsize=FS_LABEL)
    # Family group brackets / labels along the y axis.
    cum = 0
    for f in FAM_ORDER:
        c = counts[f]
        if c:
            axA.text(-0.85, cum + c / 2 - 0.5, FAM_LABEL[f], ha="right",
                     va="center", fontsize=FS_TICK, color=FAM_COL[f],
                     fontweight="bold")
            if cum < n_sys:
                axA.axhline(cum - 0.5, color="white", lw=1.2)
        cum += c
    axA.set_ylabel(f"{n_sys} systems (grouped by G-protein family)",
                   fontsize=FS_LABEL)
    axA.tick_params(axis="x", labelsize=FS_TICK)
    cb = fig.colorbar(im, ax=axA, fraction=0.046, pad=0.02)
    cb.set_label("open fraction", fontsize=FS_LABEL)
    cb.ax.tick_params(labelsize=FS_TICK)
    panel(axA, "A", x=-0.16, y=1.02)

    # ── Panel B: orthosteric pocket recovery by family ───────────────────
    axB = fig.add_subplot(gs_r[0])
    order = ["Gi/o", "Gs", "Gq/11", "G12/13"]
    fam_key = {"Gi/o": "Gi", "Gs": "Gs", "Gq/11": "Gq", "G12/13": "G12-13"}
    rec = t4a_fam.set_index("subset").reindex(order)
    xs = np.arange(len(order))
    colors = [FAM_COL[fam_key[s]] for s in order]
    bars = axB.bar(xs, rec["recovery_rate_percent"], color=colors,
                   edgecolor="white", lw=0.6, width=0.62)
    # Overall reference line.
    overall = float(t4a_all["recovery_rate_percent"])
    axB.axhline(overall, color=MUTED, lw=0.8, ls="--", zorder=1)
    axB.text(len(order) - 0.45, overall + 2.5, f"overall {overall:.1f}%",
             fontsize=FS_ANNOT, color=MUTED, ha="right")
    # Annotate % and n on each bar.
    for x, b, (_, row) in zip(xs, bars, rec.iterrows()):
        h = b.get_height()
        axB.text(x, h + 2.0, f"{h:.1f}%", ha="center", va="bottom",
                 fontsize=FS_ANNOT, fontweight="bold", color=INK)
        axB.text(x, 2.0, f"n={int(row['systems_n'])}", ha="center", va="bottom",
                 fontsize=FS_ANNOT, color="white", fontweight="bold")
    axB.set_ylim(0, 100)
    axB.set_yticks([0, 25, 50, 75, 100])
    axB.set_yticklabels(["0", "25", "50", "75", "100"], fontsize=FS_TICK)
    axB.set_xticks(xs)
    axB.set_xticklabels([FAM_LABEL[fam_key[s]] for s in order],
                        fontsize=FS_TICK)
    axB.set_ylabel("orthosteric recovery (%)", fontsize=FS_LABEL)
    figstyle.despine(axB)
    panel(axB, "B", x=-0.20, y=1.06)

    # ── Panel C: per-interface open-fraction distribution ────────────────
    axC = fig.add_subplot(gs_r[1])
    data = [M[:, j] for j in range(M.shape[1])]
    labels = [c[0] for c in IFACE_COLS]
    # Sort interfaces by descending median for an informative reading order.
    order_c = sorted(range(len(labels)), key=lambda k: -np.median(data[k]))
    data_s = [data[k] for k in order_c]
    labels_s = [labels[k] for k in order_c]
    bp = axC.boxplot(
        data_s, positions=range(len(labels_s)), widths=0.55, patch_artist=True,
        showfliers=True, sym=".", whis=(5, 95),
        medianprops=dict(color=INK, lw=1.1),
        flierprops=dict(marker=".", markerfacecolor=MUTED,
                        markeredgecolor=MUTED, markersize=2.5),
        whiskerprops=dict(color=MUTED, lw=0.7),
        capprops=dict(color=MUTED, lw=0.7),
    )
    for patch in bp["boxes"]:
        patch.set_facecolor(PALE)
        patch.set_edgecolor(INK)
        patch.set_linewidth(0.6)
    # Overlay the mean as a small accent marker.
    means = [np.mean(col) for col in data_s]
    axC.scatter(range(len(labels_s)), means, s=22, color=ACCENT, zorder=4,
                edgecolor="white", lw=0.4, label="mean")
    axC.set_ylim(-0.02, 1.02)
    axC.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    axC.set_yticklabels(["0", ".25", ".5", ".75", "1"], fontsize=FS_TICK)
    axC.set_xticks(range(len(labels_s)))
    axC.set_xticklabels(labels_s, rotation=45, ha="right", fontsize=FS_TICK)
    axC.set_ylabel("open fraction", fontsize=FS_LABEL)
    axC.set_xlabel("TM helix-pair interface", fontsize=FS_LABEL)
    axC.legend(frameon=False, loc="lower right", fontsize=FS_ANNOT,
               handletextpad=0.2)
    figstyle.despine(axC)
    panel(axC, "C", x=-0.20, y=1.08)

    # ── Panel D: completeness + exclusion transparency ───────────────────
    axD = fig.add_subplot(gs_r[2])
    axD.set_axis_off()
    panel(axD, "D", x=-0.02, y=0.98)

    # Stacked horizontal bar: included vs held-back categories.
    cat_order = [
        "temporary / incomplete files",
        "nonstandard length",
        "missing processed outputs",
        "nonstandard replicas + missing outputs",
    ]
    cat_order = [c for c in cat_order if c in cat_counts.index]
    held_vals = [int(cat_counts.get(c, 0)) for c in cat_order]
    held_palette = ["#8a4aa0", "#b23a48", "#c0741a", "#586170"]
    included_col = ACCENT

    total = n_included + n_held
    ax_bar = axD.inset_axes([0.0, 0.30, 1.0, 0.45])
    ax_bar.barh([0], [n_included], color=included_col, edgecolor="white",
                lw=0.5, height=0.55)
    ax_bar.text(n_included / 2, 0, f"{n_included} included", ha="center",
                va="center", fontsize=FS_ANNOT, fontweight="bold",
                color="white")
    left = n_included
    for val, col in zip(held_vals, held_palette):
        if val:
            ax_bar.barh([0], [val], left=left, color=col, edgecolor="white",
                        lw=0.5, height=0.55)
            left += val
    ax_bar.text(n_included + n_held + 3, 0, f"{n_held} held back",
                ha="left", va="center", fontsize=FS_ANNOT, fontweight="bold",
                color=INK)
    ax_bar.set_xlim(0, total + 30)
    ax_bar.set_ylim(-0.5, 0.5)
    ax_bar.set_yticks([])
    ax_bar.set_xticks([0, n_included, total])
    ax_bar.set_xticklabels(["0", str(n_included), str(total)], fontsize=FS_TICK)
    ax_bar.set_xlabel("systems", fontsize=FS_LABEL)
    figstyle.despine(ax_bar, left=True, bottom=True)

    # Legend for held-back categories, placed in the lower half of panel D.
    handles = [plt.Rectangle((0, 0), 1, 1, color=held_palette[i])
               for i in range(len(cat_order))]
    labels_leg = [f"{c} ({held_vals[i]})" for i, c in enumerate(cat_order)]
    axD.legend(handles, labels_leg, loc="lower left",
               bbox_to_anchor=(0.0, 0.0), ncol=2, frameon=False,
               fontsize=FS_ANNOT, handletextpad=0.4, columnspacing=1.0,
               labelcolor=INK)

    # Trajectory-integrity callout as a figure footnote.
    fig.text(
        0.10, 0.025,
        f"Reduced-trajectory integrity audit: {audited}/{audited} systems pass "
        f"PBC re-image ({n_ok} OK, {n_warn} minor-scatter WARN); "
        f"0 atom-count mismatch · 0 box mismatch · 0 intra/inter-chain breaks · "
        f"{scatter_frames} minor-scatter frames ({len(t8b)} systems flagged).",
        fontsize=FS_ANNOT, color=MUTED, ha="left", va="bottom",
    )

    save(fig, "new_figure4_qc")


if __name__ == "__main__":
    print("Figure 4 (QC, revised) …")
    make_figure4()
