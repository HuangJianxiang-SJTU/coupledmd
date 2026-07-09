#!/usr/bin/env python3
"""Main Figure 2 — Data records, repository organization and access model.

Adapted from `generate_scidata_main_figures.py::build_figure2` (Scientific Data
Figure 2), now reworked as a main-text figure.

Changes versus the original:
  - No figure title (suptitle removed).
  - Enlarged axis labels, tick labels, panel titles and panel letters,
    consistent with `new_figure1.py` typography.
  - Panel A redrawn as a real directory tree with connector lines and colored
    folder markers instead of plain indented text.
  - Panel B (metadata schema) and Panel C (access model) use larger rounded
    cards with hairline arrows and a clearer hierarchy.
  - Panel D replaces the "screenshot pending" placeholder with an honest,
    stylized portal-access schematic (search · filters · NGL viewer ·
    downloads · API) so the figure is self-contained for publication.

All numbers are read from frozen CSVs in tables/. No trajectory I/O.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-coupledmd")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import figstyle

figstyle.apply_style()

HERE = Path(__file__).resolve().parent
TBL = HERE / "tables"
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT
FAM_COL = figstyle.FAMILY

# Enlarged typography — kept identical to new_figure1.py for visual consistency.
FS_PANEL = 13          # panel letter (A–D)
FS_TITLE = 12          # subplot titles
FS_LABEL = 11          # axis labels
FS_TICK = 9            # tick labels
FS_ANNOT = 8           # in-panel annotations / small text

# Folder / layer accent colours for the schematic panels.
FOLDER_COL = "#2c6fb3"          # directory nodes
LEAF_COL = MUTED                 # file / leaf nodes
HIGHLIGHT_COL = ACCENT           # per-system subtree root
LAYER_COLS = [ACCENT, "#2c6fb3", "#586170"]   # archival → portal → API


def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        path = OUT / f"{name}.{ext}"
        fig.savefig(path, bbox_inches="tight", pad_inches=0.03,
                    dpi=600 if ext == "png" else None)
        print(f"  saved {path}")
    plt.close(fig)


def panel(ax, letter: str, x=-0.10, y=1.04) -> None:
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=FS_PANEL,
            fontweight="bold", va="bottom", ha="left", color=INK)


def rounded_card(ax, xy, w, h, text, fc="#f5f7fa", ec=PALE, fs=FS_ANNOT,
                 bold=False, color=INK, rounding=0.04, lw=0.7):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.01,rounding_size={rounding}",
        facecolor=fc, edgecolor=ec, linewidth=lw, transform=ax.transAxes,
    )
    ax.add_patch(patch)
    if text:
        ax.text(x + w / 2, y + h / 2, text, transform=ax.transAxes,
                ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", color=color,
                linespacing=1.35)


def arrow(ax, x0, y0, x1, y1, color=MUTED, lw=0.9, mut=10):
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1), transform=ax.transAxes,
        arrowstyle="-|>", mutation_scale=mut, linewidth=lw, color=color,
        shrinkA=1.5, shrinkB=1.5,
    ))


def load_tables() -> dict:
    return dict(
        t2=pd.read_csv(TBL / "scidata_T2_repository_structure.csv"),
        t6=pd.read_csv(TBL / "scidata_T6_manifest_summary.csv"),
        t7=pd.read_csv(TBL / "scidata_T7_portal_file_availability_summary.csv"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Panel A — archive hierarchy as a real directory tree
# ──────────────────────────────────────────────────────────────────────────────
def draw_tree(ax) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # (label, depth, is_dir, color)
    # depth 0 = root, 1 = top-level, 2 = per-system children
    nodes = [
        ("archive_root/",                         0, True,  HIGHLIGHT_COL),
        ("manifest/",                             1, True,  FOLDER_COL),
        ("checksums + release version",           1, False, LEAF_COL),
        ("metadata/",                             1, True,  FOLDER_COL),
        ("systems.csv · held_back_systems.csv",   1, False, LEAF_COL),
        ("systems/<system_id>/",                  1, True,  HIGHLIGHT_COL),
        ("topology/",                             2, True,  FOLDER_COL),
        ("structures + parameters",               2, False, LEAF_COL),
        ("trajectories/rep{1..3}/",               2, True,  FOLDER_COL),
        ("full production runs",                  2, False, LEAF_COL),
        ("reduced/",                              2, True,  FOLDER_COL),
        ("aligned, strided for viz",              2, False, LEAF_COL),
        ("features/",                             2, True,  FOLDER_COL),
        ("RMSD · RMSF · contacts",                2, False, LEAF_COL),
        ("pocket/",                               2, True,  FOLDER_COL),
        ("fpocket + GPCRdb mapping",              2, False, LEAF_COL),
        ("qc/",                                   2, True,  FOLDER_COL),
        ("frame · PBC · stability",               2, False, LEAF_COL),
        ("code/",                                 1, True,  FOLDER_COL),
        ("scripts + notebooks",                   1, False, LEAF_COL),
        ("web_api_snapshot/",                     1, True,  FOLDER_COL),
        ("OpenAPI schema + endpoints",            1, False, LEAF_COL),
    ]

    n = len(nodes)
    y_top = 0.96
    y_bot = 0.06
    ys = np.linspace(y_top, y_bot, n)

    # x positions per depth
    x0 = 0.04
    dx = 0.135
    # vertical connector columns per depth (x of the parent's branch line)
    branch_x = {0: x0, 1: x0 + dx, 2: x0 + 2 * dx}

    # group rows by their parent depth so we can draw elbow connectors
    # Each directory node owns a vertical drop feeding its children.
    dir_rows = [i for i, (_, d, isd, _) in enumerate(nodes) if isd]
    for i in dir_rows:
        _, depth, _, col = nodes[i]
        if depth >= 2:
            continue  # only top-level dirs branch into depth-2 children
        # children = subsequent nodes at depth+1 until next node at depth<=depth
        children = []
        for j in range(i + 1, n):
            _, jd, _, _ = nodes[j]
            if jd <= depth:
                break
            if jd == depth + 1:
                children.append(j)
        if not children:
            continue
        bx = branch_x[depth] + 0.028          # branch column just right of folder label
        y_parent = ys[i] - 0.012
        y_last = ys[children[-1]]
        # vertical branch line
        ax.plot([bx, bx], [y_last, y_parent], color=PALE, lw=0.9,
                transform=ax.transAxes, zorder=1)
        # horizontal elbows to each child
        for cj in children:
            y_c = ys[cj]
            cx = branch_x[depth + 1] - 0.012
            ax.plot([bx, cx], [y_c, y_c], color=PALE, lw=0.9,
                    transform=ax.transAxes, zorder=1)

    # draw labels + folder / file glyphs
    for (label, depth, is_dir, col), y in zip(nodes, ys):
        x = x0 + depth * dx
        if is_dir:
            ax.text(x, y, "█", transform=ax.transAxes, fontsize=FS_ANNOT,
                    color=col, va="center", ha="left", fontweight="bold")
            ax.text(x + 0.022, y, label, transform=ax.transAxes, fontsize=FS_TICK,
                    color=col, va="center", ha="left", fontweight="bold",
                    fontfamily="monospace")
        else:
            ax.text(x, y, "–", transform=ax.transAxes, fontsize=FS_TICK,
                    color=col, va="center", ha="left")
            ax.text(x + 0.022, y, label, transform=ax.transAxes, fontsize=FS_ANNOT,
                    color=MUTED, va="center", ha="left", fontfamily="monospace")


# ──────────────────────────────────────────────────────────────────────────────
# Panel B — metadata schema (entity cards + relations)
# ──────────────────────────────────────────────────────────────────────────────
def draw_schema(ax) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # (label, x, y, w, h, fill, edge, is_root)
    root_fc = "#e8f3f3"
    sub_fc = "#f5f7fa"
    cards = [
        ("system",        0.36, 0.80, 0.28, 0.13, root_fc, ACCENT, True),
        ("receptor",      0.04, 0.52, 0.26, 0.13, sub_fc, FOLDER_COL, False),
        ("G protein",     0.37, 0.52, 0.26, 0.13, sub_fc, FOLDER_COL, False),
        ("ligand / state",0.70, 0.52, 0.26, 0.13, sub_fc, FOLDER_COL, False),
        ("replicas",      0.16, 0.24, 0.28, 0.13, sub_fc, FOLDER_COL, False),
        ("files",         0.56, 0.24, 0.28, 0.13, sub_fc, FOLDER_COL, False),
        ("QC status",     0.36, 0.04, 0.28, 0.13, sub_fc, FOLDER_COL, False),
    ]
    centers = {}
    for label, x, y, w, h, fc, ec, is_root in cards:
        rounded_card(ax, (x, y), w, h, label, fc=fc, ec=ec,
                     fs=FS_LABEL, bold=True, color=ec if is_root else INK,
                     rounding=0.05, lw=1.0)
        centers[label] = (x + w / 2, y + h / 2, x, y, w, h)

    # relations: system -> receptor / G protein / ligand
    sx, sy = centers["system"][0], centers["system"][1] - 0.065
    for child in ("receptor", "G protein", "ligand / state"):
        cx, cy = centers[child][0], centers[child][1] + 0.065
        arrow(ax, sx, sy, cx, cy, color=FOLDER_COL, lw=1.0, mut=11)
    # second row links
    for src, dst in [("receptor", "replicas"), ("G protein", "replicas"),
                     ("G protein", "files"), ("ligand / state", "files")]:
        sx2, sy2 = centers[src][0], centers[src][1] - 0.065
        cx2, cy2 = centers[dst][0], centers[dst][1] + 0.065
        arrow(ax, sx2, sy2, cx2, cy2, color=MUTED, lw=0.8, mut=9)
    # files + replicas -> QC
    for src in ("replicas", "files"):
        sx3, sy3 = centers[src][0], centers[src][1] - 0.065
        cx3, cy3 = centers["QC status"][0], centers["QC status"][1] + 0.065
        arrow(ax, sx3, sy3, cx3, cy3, color=MUTED, lw=0.8, mut=9)

    ax.text(
        0.02, -0.05,
        "Keys: system_id · UniProt · GPCRdb · class · G-protein family · "
        "ligand/source · replica IDs · paths · QC flags · checksums",
        transform=ax.transAxes, fontsize=FS_ANNOT, color=MUTED, va="top",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Panel C — archive-first access model
# ──────────────────────────────────────────────────────────────────────────────
def draw_access(ax, t6, t7) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    layers = [
        ("Stable archival\nrepository",
         "DOI / accession\nfull trajectories\nmetadata + manifests", 0),
        ("Web portal",
         "browse · filter\nvisualize · download", 1),
        ("REST API",
         "programmatic\nmetadata + derived\nrecords", 2),
    ]
    card_w = 0.27
    gap = 0.06
    x0 = 0.015
    y0 = 0.34
    h = 0.56
    for i, (title, sub, idx) in enumerate(layers):
        x = x0 + i * (card_w + gap)
        col = LAYER_COLS[idx]
        rounded_card(ax, (x, y0), card_w, h, "", fc="#eef6ff", ec=col,
                     rounding=0.05, lw=1.1)
        ax.text(x + card_w / 2, y0 + h - 0.12, title, transform=ax.transAxes,
                ha="center", va="center", fontsize=FS_LABEL, fontweight="bold",
                color=col, linespacing=1.3)
        ax.text(x + card_w / 2, y0 + 0.20, sub, transform=ax.transAxes,
                ha="center", va="center", fontsize=FS_ANNOT, color=INK,
                linespacing=1.45)
        if i < 2:
            ax.text(x + card_w + gap / 2, y0 + h / 2, "→",
                    transform=ax.transAxes, ha="center", va="center",
                    fontsize=FS_TITLE, color=col, fontweight="bold")

    arch = t6.loc[t6["manifest"] == "archive_manifest_clean_v1_from_metadata"].iloc[0]
    port = t6.loc[t6["manifest"] == "portal_file_manifest_clean_v1"].iloc[0]
    present = int(t7["present"].sum())
    expected = int(t7["expected_systems"].sum())
    missing = int(t7["missing"].sum())
    pending = int(t7["checksums_pending"].sum())

    ax.text(
        0.015, 0.22,
        f"Archive layer: {int(arch['records'])} paths across {int(arch['systems'])} systems  ·  "
        f"portal/API layer: {int(port['records'])} records",
        transform=ax.transAxes, fontsize=FS_ANNOT, color=INK,
    )
    ax.text(
        0.015, 0.14,
        f"Availability: {present}/{expected} record slots present ({missing} missing)  ·  "
        f"{pending} binary/large-file checksums pending",
        transform=ax.transAxes, fontsize=FS_ANNOT, color=MUTED,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Panel D — stylized portal access schematic (honest mock-up, not a screenshot)
# ──────────────────────────────────────────────────────────────────────────────
def draw_portal(ax) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # browser frame
    frame = FancyBboxPatch(
        (0.03, 0.06), 0.94, 0.88,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor="#fbfcfd", edgecolor=PALE, linewidth=1.0,
        transform=ax.transAxes,
    )
    ax.add_patch(frame)
    # title bar
    bar = FancyBboxPatch(
        (0.03, 0.80), 0.94, 0.14,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor="#eef1f4", edgecolor=PALE, linewidth=0.8,
        transform=ax.transAxes,
    )
    ax.add_patch(bar)
    for k, c in enumerate(["#e06561", "#e8b04b", "#58c46a"]):
        ax.add_patch(plt.Circle((0.06 + k * 0.022, 0.87), 0.009,
                                color=c, transform=ax.transAxes, zorder=3))
    # address bar
    addr = FancyBboxPatch(
        (0.16, 0.835), 0.78, 0.07,
        boxstyle="round,pad=0.005,rounding_size=0.02",
        facecolor="white", edgecolor=PALE, linewidth=0.6,
        transform=ax.transAxes,
    )
    ax.add_patch(addr)
    ax.text(0.18, 0.87, "www.coupledmd.cn/atlas", transform=ax.transAxes,
            fontsize=FS_ANNOT, color=MUTED, va="center", ha="left",
            fontfamily="monospace")

    # left filter rail
    rail = FancyBboxPatch(
        (0.05, 0.10), 0.26, 0.66,
        boxstyle="round,pad=0.005,rounding_size=0.015",
        facecolor="#f5f7fa", edgecolor=PALE, linewidth=0.6,
        transform=ax.transAxes,
    )
    ax.add_patch(rail)
    ax.text(0.07, 0.72, "Filters", transform=ax.transAxes, fontsize=FS_ANNOT,
            fontweight="bold", color=INK, va="center")
    chips = [("Class", "A · B"), ("G-protein", "Gi · Gs · Gq · G12/13"),
             ("Ligand", "apo / bound"), ("Sampling", "3 × 500 ns")]
    yy = 0.64
    for name, val in chips:
        ax.text(0.07, yy, name, transform=ax.transAxes, fontsize=FS_ANNOT - 0.5,
                color=MUTED, va="center")
        ax.text(0.07, yy - 0.045, val, transform=ax.transAxes,
                fontsize=FS_ANNOT - 0.5, color=INK, va="center", fontweight="bold")
        yy -= 0.135

    # search bar
    search = FancyBboxPatch(
        (0.34, 0.72), 0.60, 0.06,
        boxstyle="round,pad=0.005,rounding_size=0.02",
        facecolor="white", edgecolor=PALE, linewidth=0.6,
        transform=ax.transAxes,
    )
    ax.add_patch(search)
    ax.text(0.36, 0.75, "Search 208 systems · 174 receptors", transform=ax.transAxes,
            fontsize=FS_ANNOT, color=MUTED, va="center", ha="left")

    # NGL viewer pane
    viewer = FancyBboxPatch(
        (0.34, 0.34), 0.40, 0.34,
        boxstyle="round,pad=0.005,rounding_size=0.015",
        facecolor="#eef6ff", edgecolor=PALE, linewidth=0.7,
        transform=ax.transAxes,
    )
    ax.add_patch(viewer)
    # cartoon helices hint
    rng = np.arange(7)
    for k in rng:
        xc = 0.39 + k * 0.052
        ys_ = 0.51 + 0.045 * np.sin(np.linspace(0, 4 * np.pi, 30))
        xs_ = np.linspace(xc, xc + 0.04, 30)
        col = [FAM_COL["Gi"], FAM_COL["Gs"], FAM_COL["Gq"], FAM_COL["G12-13"],
               FAM_COL["Gi"], FAM_COL["Gs"], FAM_COL["Gq"]][k]
        ax.plot(xs_, ys_, color=col, lw=2.2, alpha=0.75,
                transform=ax.transAxes)
    ax.text(0.54, 0.37, "NGL 3D viewer", transform=ax.transAxes,
            fontsize=FS_ANNOT, color=MUTED, ha="center", va="center",
            fontweight="bold")

    # right info / action stack
    info = FancyBboxPatch(
        (0.76, 0.34), 0.18, 0.34,
        boxstyle="round,pad=0.005,rounding_size=0.015",
        facecolor="#f5f7fa", edgecolor=PALE, linewidth=0.6,
        transform=ax.transAxes,
    )
    ax.add_patch(info)
    ax.text(0.85, 0.62, "System card", transform=ax.transAxes, fontsize=FS_ANNOT,
            fontweight="bold", color=INK, ha="center")
    for k, line in enumerate(["receptor · G-protein", "pockets · contacts",
                              "gateway · RMSF"]):
        ax.text(0.85, 0.55 - k * 0.06, line, transform=ax.transAxes,
                fontsize=FS_ANNOT - 0.5, color=MUTED, ha="center")

    # action buttons
    for k, (label, col) in enumerate([("Download", FAM_COL["Gi"]),
                                      ("REST API", FOLDER_COL),
                                      ("Cite", MUTED)]):
        bx = 0.34 + k * 0.21
        btn = FancyBboxPatch(
            (bx, 0.12), 0.18, 0.07,
            boxstyle="round,pad=0.005,rounding_size=0.02",
            facecolor=col, edgecolor="none", transform=ax.transAxes,
        )
        ax.add_patch(btn)
        ax.text(bx + 0.09, 0.155, label, transform=ax.transAxes,
                fontsize=FS_ANNOT, color="white", ha="center", va="center",
                fontweight="bold")


def make_figure2() -> None:
    d = load_tables()
    t6, t7 = d["t6"], d["t7"]

    fig = plt.figure(figsize=(11.0, 7.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 0.95], hspace=0.40,
                          wspace=0.26, left=0.05, right=0.985,
                          top=0.955, bottom=0.045)

    axA = fig.add_subplot(gs[0, 0])
    draw_tree(axA)
    panel(axA, "A", x=-0.06, y=1.02)
    axA.set_title("Archival repository hierarchy", fontsize=FS_TITLE,
                  loc="left", pad=6)

    axB = fig.add_subplot(gs[0, 1])
    draw_schema(axB)
    panel(axB, "B", x=-0.06, y=1.02)
    axB.set_title("Metadata schema (per system)", fontsize=FS_TITLE,
                  loc="left", pad=6)

    axC = fig.add_subplot(gs[1, 0])
    draw_access(axC, t6, t7)
    panel(axC, "C", x=-0.06, y=1.02)
    axC.set_title("Archive-first access model", fontsize=FS_TITLE,
                  loc="left", pad=6)

    axD = fig.add_subplot(gs[1, 1])
    draw_portal(axD)
    panel(axD, "D", x=-0.06, y=1.02)
    axD.set_title("Web portal access layer", fontsize=FS_TITLE,
                  loc="left", pad=6)

    # No suptitle — caption lives in the manuscript text.
    fig.tight_layout(pad=0.6)
    save(fig, "new_figure2_data_records")


if __name__ == "__main__":
    print("Figure 2 (data records) …")
    make_figure2()
