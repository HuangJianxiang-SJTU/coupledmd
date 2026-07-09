#!/usr/bin/env python3
"""Supplementary Figure S2 — portal, archive and server coverage.

Adapted from `generate_scidata_extra_figures.py::fig10_portal_archive_coverage`
(Scientific Data Figure 10 candidate,
"scidata_figure10_portal_archive_coverage"), restyled to match the
`new_figure1.py` typography.

Changes versus the original:
  - No figure title (suptitle removed).
  - Enlarged panel letters, subpanel titles, axis labels, tick labels and
    annotations (FS_* constants match new_figure1.py exactly).
  - Single 1x3 row: panels A-C only (the access-model schematic that was
    panel D is covered by main-text Figure 2, so it is dropped here).

Panels:
  A  Portal file availability (present vs missing, per record type)
  B  Two-tier data product (production archive vs portal/API layer, log10 bytes)
  C  Documented REST surface (endpoints grouped by manuscript use)

All panels are generated from frozen CSVs. No trajectory I/O is performed.
"""

from __future__ import annotations

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

FAM_COL = figstyle.FAMILY
INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT
WARN = "#c0741a"

# Enlarged typography — matches new_figure1.py so the figures read as one set.
FS_PANEL = 13          # panel letter (A–D)
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


def load_tables() -> dict[str, pd.DataFrame]:
    return {
        "t6": pd.read_csv(TBL / "scidata_T6_manifest_summary.csv"),
        "t7": pd.read_csv(TBL / "scidata_T7_portal_file_availability_summary.csv"),
        "s6": pd.read_csv(TBL / "scidata_S6_portal_api_endpoints.csv"),
        "s8": pd.read_csv(TBL / "scidata_S8_archive_manifest_clean_v1_from_metadata.csv"),
        "s9": pd.read_csv(TBL / "scidata_S9_portal_file_manifest_clean_v1.csv"),
    }


def make_figure_s2() -> None:
    d = load_tables()
    t7, s8, s9, s6 = d["t7"], d["s8"], d["s9"], d["s6"]

    fig = plt.figure(figsize=(10.8, 3.8))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.15, 1.15],
                          wspace=0.40,
                          left=0.07, right=0.97, top=0.88, bottom=0.18)
    ax_files = fig.add_subplot(gs[0, 0])
    ax_size = fig.add_subplot(gs[0, 1])
    ax_api = fig.add_subplot(gs[0, 2])

    # ── A: portal file availability (present vs missing) ─────────────────────
    short = t7.copy()
    short["label"] = (short["record_type"]
                      .str.replace("api_", "", regex=False)
                      .str.replace("viz_", "viz ", regex=False))
    y = np.arange(len(short))[::-1]
    ax_files.barh(y, short["present"], color=FAM_COL["Gi"], label="present")
    ax_files.barh(y, short["missing"], left=short["present"], color=WARN,
                  label="missing")
    ax_files.set_yticks(y, short["label"], fontsize=FS_TICK)
    ax_files.tick_params(axis="x", labelsize=FS_TICK)
    ax_files.set_xlabel("systems", fontsize=FS_LABEL)
    ax_files.set_title("Portal file availability", fontsize=FS_TITLE,
                       loc="left", pad=4)
    ax_files.legend(frameon=False, fontsize=FS_ANNOT)
    panel(ax_files, "A")

    # ── B: two-tier data product (archive vs portal, log10 bytes) ─────────────
    archive_bytes = float(s8["size_bytes"].sum())
    portal_bytes = float(s9["size_bytes"].sum())
    ax_size.barh(["production archive", "portal/API layer"],
                 np.log10([archive_bytes, portal_bytes]),
                 color=[ACCENT, WARN], edgecolor="white")
    ax_size.set_xlabel("total size (log$_{10}$ bytes)", fontsize=FS_LABEL)
    ax_size.set_title("Two-tier data product", fontsize=FS_TITLE,
                      loc="left", pad=4)
    ax_size.tick_params(axis="both", labelsize=FS_TICK)
    ax_size.text(np.log10(archive_bytes), 0, f" {archive_bytes/1e12:.1f} TB",
                 va="center", fontsize=FS_ANNOT)
    ax_size.text(np.log10(portal_bytes), 1, f" {portal_bytes/1e9:.1f} GB",
                 va="center", fontsize=FS_ANNOT)
    panel(ax_size, "B")

    # ── C: documented REST surface ───────────────────────────────────────────
    tags = (s6["manuscript_use"].fillna("other")
            .str.extract(r"(portal|download|open access|API|citation|account)",
                         expand=False)
            .fillna("API/data"))
    tag_counts = tags.value_counts().sort_values()
    ax_api.barh(tag_counts.index, tag_counts.values, color=ACCENT,
                edgecolor="white")
    ax_api.set_xlabel("endpoints", fontsize=FS_LABEL)
    ax_api.set_title("Documented REST surface", fontsize=FS_TITLE,
                     loc="left", pad=4)
    ax_api.tick_params(axis="both", labelsize=FS_TICK)
    ax_api.text(0.98, 0.05, "www.coupledmd.cn/api/docs",
                transform=ax_api.transAxes, ha="right", color=MUTED,
                fontsize=FS_ANNOT)
    panel(ax_api, "C")

    # No suptitle; compact, border-free composition.
    fig.tight_layout(pad=0.5)
    save(fig, "new_figure_s2_portal_archive_coverage")


if __name__ == "__main__":
    print("Supplementary Figure S2 (portal/archive coverage) …")
    make_figure_s2()
