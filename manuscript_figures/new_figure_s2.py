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
  A  Portal file completeness (percentage available per record type)
  B  Two-tier data product (production archive vs portal/API layer, relative scale)
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
V9 = HERE / "scidata_figures" / "v9_figure_inputs"
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
        "t6": pd.read_csv(V9 / "scidata_T6_manifest_summary_v9.csv"),
        "t7": pd.read_csv(V9 / "scidata_T7_portal_api_availability_summary_v9.csv"),
        "s8": pd.read_csv(V9 / "scidata_S8_archive_source_inventory_v9.csv"),
        "s9": pd.read_csv(V9 / "scidata_S9_portal_api_file_manifest_v9.csv"),
    }


def make_figure_s2() -> None:
    d = load_tables()
    t6, t7, s8, s9 = d["t6"], d["t7"], d["s8"], d["s9"]
    cohort = t6.loc[t6["manifest"].eq("release_cohort_v9_final208")].iloc[0]
    archive = t6.loc[t6["manifest"].eq("archive_source_inventory_v9")].iloc[0]
    portal = t6.loc[t6["manifest"].eq("portal_api_file_manifest_v9")].iloc[0]
    api = t6.loc[t6["manifest"].eq("openapi_snapshot")].iloc[0]
    assert int(cohort["systems"]) == 208 and int(cohort["records"]) == 624
    assert archive["status"] == portal["status"] == "audited"
    assert len(s8) == 416 and s8["exists"].all()
    assert len(s9) == 2080 and len(t7) == 10

    fig = plt.figure(figsize=(10.8, 3.8))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.15, 1.15],
                          wspace=0.40,
                          left=0.07, right=0.97, top=0.88, bottom=0.18)
    ax_files = fig.add_subplot(gs[0, 0])
    ax_size = fig.add_subplot(gs[0, 1])
    ax_api = fig.add_subplot(gs[0, 2])

    # ── A: measured portal/API record coverage ───────────────────────────────
    short = t7.copy()
    short["label"] = (short["record_type"].str.replace("api_", "", regex=False)
                      .str.replace("viz_", "viz ", regex=False))
    short["applicable_systems"] = short["expected_systems"] - short["records_not_applicable"]
    short["coverage_pct"] = 100 * short["records_available"] / short["applicable_systems"]
    short = short.sort_values(["coverage_pct", "record_type"], ascending=[True, True])
    colors = np.where(short["records_missing"].add(short["records_unpopulated"]).eq(0),
                      FAM_COL["Gi"], WARN)
    y = np.arange(len(short))
    ax_files.barh(y, short["coverage_pct"], color=colors, edgecolor="white")
    ax_files.set_yticks(y, short["label"], fontsize=FS_TICK)
    ax_files.set_xlim(97.5, 100.15)
    ax_files.set_xticks([98, 99, 100])
    ax_files.set_xlabel("scientifically populated (%)", fontsize=FS_LABEL)
    for yi, row in enumerate(short.itertuples()):
        gap = int(row.records_missing + row.records_unpopulated)
        if gap:
            ax_files.text(row.coverage_pct + 0.05, yi, f"−{gap}", va="center",
                          fontsize=FS_ANNOT, color=WARN)
    ax_files.set_title("Portal/API record coverage", fontsize=FS_TITLE,
                       loc="left", pad=4)
    panel(ax_files, "A")

    # ── B: two-tier data product (archive vs portal, log10 bytes) ─────────────
    archive_counts = s8.groupby("record_type")["exists"].sum().reindex(
        ["production_trajectory", "topology"])
    ax_size.barh(["production trajectory", "topology"], archive_counts.values,
                 color=[ACCENT, FAM_COL["Gs"]], edgecolor="white")
    ax_size.set_xlim(0, 225)
    ax_size.set_xlabel("systems with source record", fontsize=FS_LABEL)
    for yv, val in enumerate(archive_counts.values):
        ax_size.text(val + 2, yv, f"{int(val)}/208", va="center",
                     fontsize=FS_ANNOT, fontweight="bold")
    ax_size.text(0.02, 0.05, "624 selected replicas · 312.0 µs",
                 transform=ax_size.transAxes, fontsize=FS_ANNOT, color=MUTED)
    ax_size.set_title("Archive source inventory", fontsize=FS_TITLE,
                      loc="left", pad=4)
    panel(ax_size, "B")

    # ── C: documented REST surface ───────────────────────────────────────────
    gaps = t7.loc[(t7["records_missing"] + t7["records_unpopulated"]).gt(0)].copy()
    gaps["gap_n"] = gaps["records_missing"] + gaps["records_unpopulated"]
    gaps["label"] = gaps["record_type"].str.replace("api_", "", regex=False)
    gaps = gaps.sort_values("gap_n")
    if gaps.empty:
        ax_api.axis("off")
        ax_api.text(0.5, 0.56, "No populated-record gaps", ha="center", va="center",
                    transform=ax_api.transAxes, fontsize=FS_LABEL, fontweight="bold",
                    color=FAM_COL["Gi"])
        ax_api.text(0.5, 0.43, "All applicable portal/API records: 208/208",
                    ha="center", va="center", transform=ax_api.transAxes,
                    fontsize=FS_ANNOT, color=MUTED)
    else:
        ax_api.barh(gaps["label"], gaps["gap_n"], color=WARN, edgecolor="white")
        ax_api.set_xlim(0, 3.8)
        ax_api.set_xticks([0, 1, 2, 3])
        ax_api.set_xlabel("systems lacking populated record", fontsize=FS_LABEL)
        for yv, row in enumerate(gaps.itertuples()):
            ax_api.text(row.gap_n + 0.08, yv, str(row.affected_system_ids),
                        va="center", fontsize=FS_ANNOT, color=MUTED)
    ax_api.text(0.98, 0.03, f"OpenAPI snapshot: {int(api['records'])} endpoints",
                transform=ax_api.transAxes, ha="right", fontsize=FS_ANNOT,
                color=ACCENT)
    ax_api.set_title("Measured coverage gaps", fontsize=FS_TITLE,
                     loc="left", pad=4)
    panel(ax_api, "C")

    # No suptitle; compact, border-free composition.
    fig.tight_layout(pad=0.5)
    save(fig, "v9_figureS2_portal_archive_coverage")


if __name__ == "__main__":
    print("Supplementary Figure S2 (portal/archive coverage) …")
    make_figure_s2()
