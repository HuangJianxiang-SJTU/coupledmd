#!/usr/bin/env python3
"""
Shared publication style for the CoupledMD NAR figures.

One visual system across all five figures: a single sans-serif with a clear
size hierarchy (panel letters > axis titles > tick labels), hairline axes,
no top/right spines, and one colour-blind-safe palette in which the same
entity carries the same colour in every figure.

Imported by generate_figures_1_2_3.py and generate_figures_4_5.py.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# ── Canonical, colour-blind-safe palette ──────────────────────────────────────
# Same G-protein family → same colour in every figure.
FAMILY = {
    "Gi":     "#2f8f6b",   # Gi/o   green
    "Gq":     "#c0741a",   # Gq/11  orange
    "Gs":     "#2c6fb3",   # Gs     blue
    "G12-13": "#8a4aa0",   # G12/13 purple
    "G12":    "#8a4aa0",   # alias
}
FAMILY_ORDER = ["Gi", "Gs", "Gq", "G12-13"]
FAMILY_LABEL = {"Gi": "Gi/o", "Gs": "Gs", "Gq": "Gq/11", "G12-13": "G12/13"}

ACCENT = "#155e63"   # teal neutral accent
INK    = "#171b22"   # near-black ink for text / hairlines
MUTED  = "#586170"   # muted grey for secondary marks / annotations
PALE   = "#d8dde3"   # pale fill (e.g. protein-only, background shading)

# Flock CGN functional classes (Fig 4)
FLOCK = {
    "conserved":               ACCENT,
    "selectivity-determining": FAMILY["Gq"],
    "paralog-specific":        MUTED,
    "neutral":                 "#aab2bd",
}

# Pocket zones (Figs 2, 5)
ZONE = {
    "orthosteric": "#b23a48",   # restrained red, reserved for orthosteric site
    "allosteric":  ACCENT,
    "interface":   MUTED,
}

# ── Column widths (Nucleic Acids Research) ────────────────────────────────────
COL1 = 3.42   # single column  (~87 mm)
COL2 = 7.00   # double column  (~180 mm)

# ── Output location ───────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
FIGDIR = HERE / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)


def apply_style():
    """Install the global rcParams. Call once at import time."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Liberation Sans", "Helvetica", "DejaVu Sans"],
        "font.size": 7,
        "axes.labelsize": 7.5,
        "axes.titlesize": 8,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6,
        "legend.title_fontsize": 6.5,
        "axes.labelcolor": INK,
        "text.color": INK,
        "axes.edgecolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.linewidth": 0.5,
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "xtick.minor.width": 0.3,
        "ytick.minor.width": 0.3,
        "lines.linewidth": 1.0,
        "lines.markersize": 3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "figure.dpi": 150,
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42,   # embed TrueType (editable text)
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def panel_label(ax, letter, x=-0.13, y=1.06):
    """Bold uppercase panel letter at the top-left of an axes."""
    ax.text(x, y, letter, transform=ax.transAxes,
            fontsize=9, fontweight="bold", va="bottom", ha="left", color=INK)


def despine(ax, left=True, bottom=True):
    """Keep only the requested spines; matches the global no-top/right rule."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)


def save(fig, name):
    """Save a figure as vector PDF + 600-dpi PNG into figures/."""
    for ext in ("pdf", "png"):
        path = FIGDIR / f"{name}.{ext}"
        fig.savefig(path)
        print(f"  saved {path}")
