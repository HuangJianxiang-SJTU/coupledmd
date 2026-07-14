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
  - Panel D uses the frozen real portal screenshot in
    scidata_figures/portal_screenshots/.

All numbers are read from frozen CSVs in tables/. No trajectory I/O.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-coupledmd")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

import figstyle

figstyle.apply_style()

HERE = Path(__file__).resolve().parent
V9 = HERE / "scidata_figures" / "v9_figure_inputs"
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT
FAM_COL = figstyle.FAMILY

# Compact double-column typography. The final figure is 183 mm wide.
FS_PANEL = 10          # panel letter (A–D)
FS_TITLE = 9           # subplot titles
FS_LABEL = 8           # axis labels / card headings
FS_TICK = 7            # tick labels
FS_ANNOT = 6.5         # in-panel annotations / small text

# Folder / layer accent colours for the schematic panels.
FOLDER_COL = "#2c6fb3"          # directory nodes
LEAF_COL = MUTED                 # file / leaf nodes
HIGHLIGHT_COL = ACCENT           # per-system subtree root
LAYER_COLS = [ACCENT, "#2c6fb3", "#586170"]   # archival → portal → API
PORTAL_SCREENSHOT_DIR = OUT / "portal_screenshots"


def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        path = OUT / f"{name}.{ext}"
        fig.savefig(path, bbox_inches="tight", pad_inches=0.03,
                    dpi=600 if ext == "png" else None)
        print(f"  saved {path}")
    plt.close(fig)


def panel(ax, letter: str, x=-0.10, y=1.03) -> None:
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
        t2=pd.read_csv(V9 / "scidata_T2_repository_structure_v9.csv"),
        t6=pd.read_csv(V9 / "scidata_T6_manifest_summary_v9.csv"),
    )


def find_snapshot(directory: Path) -> Path:
    """Return the most recently modified PNG snapshot in *directory*."""
    snapshots = sorted(directory.glob("*.png"))
    if not snapshots:
        raise FileNotFoundError(f"No PNG snapshot found in {directory}")
    return max(snapshots, key=lambda path: path.stat().st_mtime)


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
        ("systems.csv · unresolved_systems.csv", 1, False, LEAF_COL),
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
        "Keys: system_id · UniProt · GPCRdb · class · G-protein family\n"
        "ligand/source · replica IDs · paths · QC flags · checksums",
        transform=ax.transAxes, fontsize=FS_ANNOT, color=MUTED, va="top",
        linespacing=1.35,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Panel C — archive-first access model
# ──────────────────────────────────────────────────────────────────────────────
def draw_access(ax, t6) -> None:
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

    cohort = t6.loc[t6["manifest"] == "release_cohort_v9_final208"].iloc[0]
    arch = t6.loc[t6["manifest"] == "archive_source_inventory_v9"].iloc[0]
    port = t6.loc[t6["manifest"] == "portal_api_file_manifest_v9"].iloc[0]

    ax.text(
        0.015, 0.22,
        f"Release cohort: {int(cohort['systems'])} systems · "
        f"{int(cohort['records'])} trajectories (3 × 500 ns per system)",
        transform=ax.transAxes, fontsize=FS_ANNOT, color=INK,
    )
    ax.text(
        0.015, 0.14,
        f"Archive source inventory: {arch['status']}  ·  "
        f"portal/API file manifest: {port['status']} from current server evidence",
        transform=ax.transAxes, fontsize=FS_ANNOT, color=MUTED,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Panel D — frozen real portal screenshot
# ──────────────────────────────────────────────────────────────────────────────
def draw_portal_snapshot(ax) -> None:
    screenshot = find_snapshot(PORTAL_SCREENSHOT_DIR)
    image = plt.imread(screenshot)
    ax.imshow(image, aspect="equal", interpolation="lanczos")
    ax.axis("off")
    ax.add_patch(Rectangle(
        (0, 0), 1, 1, transform=ax.transAxes, fill=False,
        edgecolor=PALE, linewidth=0.7, clip_on=False,
    ))
    ax.text(
        0.995, 1.015, "Legacy 222-system interface snapshot; v9 files audited separately",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=FS_ANNOT,
        color=MUTED,
    )


def make_figure2() -> None:
    d = load_tables()
    t2, t6 = d["t2"], d["t6"]
    cohort = t6.loc[t6["manifest"] == "release_cohort_v9_final208"].iloc[0]
    assert int(cohort["systems"]) == 208
    assert int(cohort["records"]) == 624
    assert set(t6.loc[t6["manifest"].isin(
        ["archive_source_inventory_v9", "portal_api_file_manifest_v9"]), "status"]) == {"audited"}
    assert len(t2) == 12

    # 183 mm wide (Nature/Scientific Data double-column width). Panels C and D
    # span the page so the access model reads linearly and the real screenshot
    # remains legible after typesetting.
    fig = plt.figure(figsize=(7.20, 9.25))
    gs = fig.add_gridspec(
        3, 2, height_ratios=[1.05, 0.42, 1.18],
        hspace=0.32, wspace=0.26,
        left=0.065, right=0.985, top=0.975, bottom=0.035,
    )

    axA = fig.add_subplot(gs[0, 0])
    draw_tree(axA)
    panel(axA, "A", x=-0.10, y=1.02)
    axA.set_title("Archival repository hierarchy", fontsize=FS_TITLE,
                  loc="left", pad=6)

    axB = fig.add_subplot(gs[0, 1])
    draw_schema(axB)
    panel(axB, "B", x=-0.10, y=1.02)
    axB.set_title("Metadata schema (per system)", fontsize=FS_TITLE,
                  loc="left", pad=6)

    axC = fig.add_subplot(gs[1, :])
    draw_access(axC, t6)
    panel(axC, "C", x=-0.045, y=1.02)
    axC.set_title("Archive-first access model", fontsize=FS_TITLE,
                  loc="left", pad=6)

    axD = fig.add_subplot(gs[2, :])
    draw_portal_snapshot(axD)
    panel(axD, "D", x=-0.045, y=1.02)
    axD.set_title("Web portal interface snapshot", fontsize=FS_TITLE,
                  loc="left", pad=6)

    # No suptitle — caption lives in the manuscript text.
    save(fig, "v9_figure2_data_records")


if __name__ == "__main__":
    print("Figure 2 (data records) …")
    make_figure2()
