#!/usr/bin/env python3
"""
Generate Figure 4 and Figure 5 for the CoupledMD NAR paper.
Publication-quality matplotlib figures in Nature-family journal style.
"""

import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms
from matplotlib.patches import Ellipse
import matplotlib.ticker as mticker

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

# ── Global style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 7,
    "axes.labelsize": 7,
    "axes.titlesize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "legend.fontsize": 6,
    "legend.title_fontsize": 6,
    "axes.linewidth": 0.5,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.minor.width": 0.3,
    "ytick.minor.width": 0.3,
    "lines.linewidth": 1.0,
    "lines.markersize": 3,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "figure.dpi": 150,
})

# ── Colour palette ────────────────────────────────────────────────────────────
FAMILY_COLORS = {
    "Gi": "#2f8f6b",
    "Gs": "#2c6fb3",
    "Gq": "#c0741a",
    "G12-13": "#8a4aa0",
    "G12": "#8a4aa0",
}
FLOCK_COLORS = {
    "conserved": "#155e63",
    "selectivity-determining": "#c0741a",
    "paralog-specific": "#7b7b7b",
    "neutral": "#b0b0b0",
}

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = Path("/MDdata/data02/jxhuang/gpcr_g")
OUT  = BASE / "gpcr_g_server" / "manuscript_figures"
OUT.mkdir(parents=True, exist_ok=True)

PILOT_CSV       = BASE / "a" / "stage2_outputs" / "pilot_long.csv"
COUPLING_CSV    = BASE / "a" / "paper1_coupling_table.csv"
BARCODE_CSV     = BASE / "a" / "galpha_barcode_reference.csv"
REORG_JSON      = BASE / "gpcr_g_server" / "data" / "api" / "v1" / "consensus" / "reorg_atlas.json"
SYSTEMS_DIR     = BASE / "gpcr_g_server" / "data" / "api" / "v1" / "systems"

# ── Helper: panel label ──────────────────────────────────────────────────────
def add_panel_label(ax, label, x=-0.08, y=1.05):
    """Add bold uppercase panel label in top-left corner."""
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=8, fontweight="bold", va="top", ha="left")

# ── Helper: confidence ellipse ───────────────────────────────────────────────
def confidence_ellipse(x, y, ax, n_std=2.0, facecolor="none", **kwargs):
    """Draw a n_std confidence ellipse based on covariance."""
    if len(x) < 3:
        return
    cov = np.cov(x, y)
    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2,
                       facecolor=facecolor, **kwargs)
    scale_x = np.sqrt(cov[0, 0]) * n_std
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_x, mean_y = np.mean(x), np.mean(y)
    transf = (matplotlib.transforms.Affine2D()
              .rotate_deg(45)
              .scale(scale_x, scale_y)
              .translate(mean_x, mean_y))
    ellipse.set_transform(transf + ax.transData)
    ax.add_patch(ellipse)


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — G-protein coupling interface
# ══════════════════════════════════════════════════════════════════════════════
def make_figure4():
    pilot    = pd.read_csv(PILOT_CSV)
    coupling = pd.read_csv(COUPLING_CSV)
    barcode  = pd.read_csv(BARCODE_CSV)

    # Merge flock_class from barcode reference onto pilot data
    # (pilot already has flock_class, but let's ensure consistency)
    # pilot already has: cgn_position, cgn_segment, flock_class

    # ── Segment ordering ──────────────────────────────────────────────────
    segment_order = ["G.HN", "G.hns1", "G.S3", "G.s2s3", "G.h4s6",
                     "G.H2", "G.H5", "H.HD", "H.hdhe"]
    pilot["cgn_segment"] = pd.Categorical(pilot["cgn_segment"], categories=segment_order, ordered=True)

    # Sort positions by segment then by position name
    pilot = pilot.sort_values(["cgn_segment", "cgn_position"]).reset_index(drop=True)
    ordered_positions = pilot["cgn_position"].unique().tolist()

    # ── Panel A: Contact persistence barcode ──────────────────────────────
    # Aggregate across all systems: mean of contact_persistence_mean per CGN position
    agg = (pilot.groupby("cgn_position", sort=False)
           .agg(
               mean_cp=("contact_persistence_mean", "mean"),
               ci_lo=("contact_persistence_ci_low", "mean"),
               ci_hi=("contact_persistence_ci_high", "mean"),
               segment=("cgn_segment", "first"),
               flock=("flock_class", "first"),
           )
           .reindex(ordered_positions))

    # Error = distance from mean to CI bounds (use the larger of the two)
    agg["err_lo"] = agg["mean_cp"] - agg["ci_lo"]
    agg["err_hi"] = agg["ci_hi"] - agg["mean_cp"]
    agg["err_lo"] = agg["err_lo"].fillna(0).clip(lower=0)
    agg["err_hi"] = agg["err_hi"].fillna(0).clip(lower=0)

    fig, axes = plt.subplots(2, 2, figsize=(7.09, 5.5))
    fig.subplots_adjust(hspace=0.45, wspace=0.40)

    # ── A ─────────────────────────────────────────────────────────────────
    ax = axes[0, 0]
    add_panel_label(ax, "A")

    x_pos = np.arange(len(agg))
    bar_colors = [FLOCK_COLORS.get(fc, "#b0b0b0") for fc in agg["flock"]]

    # Highlight G.H5 segment with background shading
    h5_mask = agg["segment"] == "G.H5"
    if h5_mask.any():
        h5_indices = np.where(h5_mask)[0]
        ax.axvspan(h5_indices[0] - 0.5, h5_indices[-1] + 0.5,
                   color="#f0f0f0", zorder=0)
        # Add label for G.H5
        mid = (h5_indices[0] + h5_indices[-1]) / 2
        ax.text(mid, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 1.0,
                "α5", ha="center", va="bottom", fontsize=5, fontstyle="italic",
                color="#555555", zorder=5)

    bars = ax.bar(x_pos, agg["mean_cp"], color=bar_colors, width=0.8,
                  edgecolor="none", zorder=2)
    ax.errorbar(x_pos, agg["mean_cp"],
                yerr=[agg["err_lo"], agg["err_hi"]],
                fmt="none", ecolor="#333333", elinewidth=0.5, capsize=1.5,
                capthick=0.5, zorder=3)

    ax.set_xticks(x_pos)
    ax.set_xticklabels([p.replace("G.", "").replace("H.", "H") for p in agg.index],
                       rotation=90, fontsize=4.5)
    ax.set_ylabel("Contact persistence")
    ax.set_ylim(0, 1.05)
    ax.set_xlim(-0.6, len(agg) - 0.4)

    # Add segment separators
    prev_seg = None
    for i, seg in enumerate(agg["segment"]):
        if prev_seg is not None and seg != prev_seg:
            ax.axvline(i - 0.5, color="#cccccc", linewidth=0.3, zorder=1)
        prev_seg = seg

    # Legend for flock_class
    legend_handles = [
        mpatches.Patch(color=FLOCK_COLORS["conserved"], label="Conserved"),
        mpatches.Patch(color=FLOCK_COLORS["selectivity-determining"], label="Selectivity-det."),
        mpatches.Patch(color="#b0b0b0", label="Other"),
    ]
    ax.legend(handles=legend_handles, loc="upper right", frameon=False,
              fontsize=5, handlelength=1.2, handletextpad=0.3)

    # Re-add α5 label after ylim is set
    if h5_mask.any():
        h5_indices = np.where(h5_mask)[0]
        mid = (h5_indices[0] + h5_indices[-1]) / 2
        ax.text(mid, 1.01, "α5", ha="center", va="bottom", fontsize=5,
                fontstyle="italic", color="#555555", zorder=5,
                transform=ax.get_xaxis_transform())

    # ── B: Alpha5 coupling geometry scatter ───────────────────────────────
    ax = axes[0, 1]
    add_panel_label(ax, "B")

    for fam in ["Gi", "Gs", "Gq"]:
        sub = coupling[coupling["g_family"] == fam].dropna(subset=["f01_tilt", "f06_depth"])
        if len(sub) == 0:
            continue
        color = FAMILY_COLORS[fam]
        ax.scatter(sub["f01_tilt"], sub["f06_depth"], c=color, s=18,
                   edgecolors="white", linewidths=0.3, zorder=3, label=fam)
        # 95% confidence ellipse — use n_std=2.447 (97% CI) to accommodate
        # the bimodal deep/shallow insertion distribution
        if len(sub) >= 3:
            confidence_ellipse(sub["f01_tilt"].values, sub["f06_depth"].values,
                               ax, n_std=2.447, edgecolor=color,
                               facecolor=color, alpha=0.10, linewidth=1.0, zorder=2)

    ax.set_xlabel("α5 tilt angle (°)")
    ax.set_ylabel("α5 insertion depth (Å)")
    ax.legend(loc="upper left", frameon=False, fontsize=5.5,
              handlelength=0.8, handletextpad=0.3, borderpad=0.3)
    # Annotate the two clusters
    ax.annotate("deep insertion", xy=(65, 49), fontsize=5, color="#586170",
                ha="center", style="italic")
    ax.annotate("shallow insertion", xy=(45, 21), fontsize=5, color="#586170",
                ha="center", style="italic")

    # ── C: Family-specific contact fingerprint heatmap ────────────────────
    ax = axes[1, 0]
    add_panel_label(ax, "C")

    # Filter to selectivity-determining positions only
    sel_positions = pilot[pilot["flock_class"] == "selectivity-determining"]["cgn_position"].unique().tolist()
    # Order by segment
    sel_pilot = pilot[pilot["cgn_position"].isin(sel_positions)].copy()
    sel_pilot["cgn_segment"] = pd.Categorical(sel_pilot["cgn_segment"], categories=segment_order, ordered=True)
    sel_pilot = sel_pilot.sort_values(["cgn_segment", "cgn_position"])
    sel_positions_ordered = sel_pilot["cgn_position"].unique().tolist()

    families = ["Gi", "Gs", "Gq", "G12"]
    heatmap_data = np.full((len(families), len(sel_positions_ordered)), np.nan)

    for i, fam in enumerate(families):
        fam_data = sel_pilot[sel_pilot["g_alpha_family"] == fam]
        for j, pos in enumerate(sel_positions_ordered):
            vals = fam_data[fam_data["cgn_position"] == pos]["contact_persistence_mean"]
            if len(vals) > 0:
                heatmap_data[i, j] = vals.mean()

    im = ax.imshow(heatmap_data, aspect="auto", cmap="bwr", vmin=0, vmax=1,
                   interpolation="nearest")

    ax.set_xticks(np.arange(len(sel_positions_ordered)))
    ax.set_xticklabels([p.replace("G.", "") for p in sel_positions_ordered],
                       rotation=90, fontsize=4.5)
    ax.set_yticks(np.arange(len(families)))
    ax.set_yticklabels(families)
    ax.set_ylabel("G-protein family")

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, shrink=0.9)
    cbar.set_label("Contact persistence", fontsize=6)
    cbar.ax.tick_params(labelsize=5)

    # ── D: RMSF profile along G.H5 ───────────────────────────────────────
    ax = axes[1, 1]
    add_panel_label(ax, "D")

    h5_data = pilot[pilot["cgn_segment"] == "G.H5"].copy()
    h5_positions = sorted(h5_data["cgn_position"].unique(),
                          key=lambda x: int(x.split(".")[-1]))

    for fam in ["Gi", "Gs", "Gq", "G12"]:
        fam_h5 = h5_data[h5_data["g_alpha_family"] == fam]
        color = FAMILY_COLORS[fam]
        means = []
        ci_los = []
        ci_his = []
        valid_pos = []
        for pos in h5_positions:
            pos_data = fam_h5[fam_h5["cgn_position"] == pos]
            if len(pos_data) > 0:
                m = pos_data["rmsf_mean"].mean()
                lo = pos_data["rmsf_ci_low"].mean()
                hi = pos_data["rmsf_ci_high"].mean()
                if not np.isnan(m):
                    means.append(m)
                    ci_los.append(m - lo if not np.isnan(lo) else 0)
                    ci_his.append(hi - m if not np.isnan(hi) else 0)
                    valid_pos.append(pos)
                else:
                    means.append(np.nan)
                    ci_los.append(0)
                    ci_his.append(0)
                    valid_pos.append(pos)
            else:
                means.append(np.nan)
                ci_los.append(0)
                ci_his.append(0)
                valid_pos.append(pos)

        x = np.arange(len(valid_pos))
        means = np.array(means)
        ci_los = np.array(ci_los)
        ci_his = np.array(ci_his)

        # Plot line
        valid_mask = ~np.isnan(means)
        if valid_mask.any():
            ax.plot(x[valid_mask], means[valid_mask], color=color, marker="o",
                    markersize=2.5, linewidth=1.0, label=fam, zorder=3)
            # Shaded CI band
            ax.fill_between(x[valid_mask],
                            (means - ci_los)[valid_mask],
                            (means + ci_his)[valid_mask],
                            color=color, alpha=0.15, zorder=2)

    ax.set_xticks(np.arange(len(h5_positions)))
    ax.set_xticklabels([p.split(".")[-1] for p in h5_positions],
                       rotation=90, fontsize=5)
    ax.set_xlabel("G.H5 position")
    ax.set_ylabel("RMSF (Å)")
    ax.legend(loc="upper left", frameon=False, fontsize=5.5,
              handlelength=1.0, handletextpad=0.3, borderpad=0.3)

    # ── Save ──────────────────────────────────────────────────────────────
    for ext in ["pdf", "png"]:
        fig.savefig(OUT / f"figure4_gprotein_interface.{ext}", dpi=300)
    plt.close(fig)
    print(f"✓ Figure 4 saved to {OUT}/figure4_gprotein_interface.{{pdf,png}}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — Partner-switching reorganization
# ══════════════════════════════════════════════════════════════════════════════
def make_figure5():
    with open(REORG_JSON) as f:
        reorg = json.load(f)

    comparisons = pd.DataFrame(reorg["comparisons"])

    # OX2R system IDs
    ox2r_systems = {
        "Gi": "Gi_7SQO",
        "Gq": "Gq_7SR8",
        "Gs": "Gs_7L1V",
    }

    # ── Load OX2R pocket data ─────────────────────────────────────────────
    ox2r_pockets = {}
    for fam, sid in ox2r_systems.items():
        ppath = SYSTEMS_DIR / sid / "pockets_gpcrdb.json"
        if ppath.exists():
            with open(ppath) as f:
                ox2r_pockets[fam] = json.load(f)
        else:
            print(f"  Warning: {ppath} not found")

    # ── Load OX2R gateway data ────────────────────────────────────────────
    ox2r_gateways = {}
    for fam, sid in ox2r_systems.items():
        gpath = SYSTEMS_DIR / sid / "gateways.json"
        if gpath.exists():
            with open(gpath) as f:
                ox2r_gateways[fam] = json.load(f)
        else:
            print(f"  Warning: {gpath} not found")

    fig, axes = plt.subplots(2, 2, figsize=(7.09, 5.5))
    fig.subplots_adjust(hspace=0.45, wspace=0.40)

    # ── A: Overview dot plot ──────────────────────────────────────────────
    ax = axes[0, 0]
    add_panel_label(ax, "A")

    # Color by famA→famB transition
    transition_colors = {
        "Gi-Gq": FAMILY_COLORS["Gq"],
        "Gi-Gs": FAMILY_COLORS["Gs"],
        "Gq-Gs": FAMILY_COLORS["Gs"],
    }

    for _, row in comparisons.iterrows():
        contrast = row["contrast"]
        color = transition_colors.get(contrast, "#888888")
        is_ox2r = row["receptor"] == "OX2R"
        ec = "black" if is_ox2r else "white"
        ew = 1.0 if is_ox2r else 0.3
        sz = 50 if is_ox2r else 30
        zorder = 5 if is_ox2r else 3
        ax.scatter(row["jaccard"], row["gateway_dist"], c=color, s=sz,
                   edgecolors=ec, linewidths=ew, zorder=zorder)
        if is_ox2r:
            ax.annotate("OX2R", (row["jaccard"], row["gateway_dist"]),
                        textcoords="offset points", xytext=(5, 5),
                        fontsize=5.5, fontweight="bold", color="#333333", zorder=6)

    # Reference lines
    ax.axvline(0.5, color="#999999", linewidth=0.5, linestyle="--", zorder=1)
    ax.axhline(0.08, color="#999999", linewidth=0.5, linestyle="--", zorder=1)

    ax.set_xlabel("Pocket Jaccard similarity")
    ax.set_ylabel("Gateway dissimilarity")
    ax.set_xlim(-0.05, 1.1)
    ax.set_ylim(0, None)

    # Legend for transition types
    legend_handles = [
        mpatches.Patch(color=FAMILY_COLORS["Gq"], label="Gi → Gq"),
        mpatches.Patch(color=FAMILY_COLORS["Gs"], label="Gi → Gs / Gq → Gs"),
    ]
    ax.legend(handles=legend_handles, loc="upper right", frameon=False,
              fontsize=5.5, handlelength=1.2, handletextpad=0.3)

    # ── B: OX2R pocket comparison (grouped bar) ──────────────────────────
    ax = axes[0, 1]
    add_panel_label(ax, "B")

    # Map zones to 3 categories for the bar chart
    zone_map = {
        "orthosteric": "Orthosteric",
        "intracellular_allosteric": "Allosteric",
        "tm_core_allosteric": "Allosteric",
        "extracellular_vestibule": "Allosteric",
        "coupling_interface": "Intracellular",
        "other": "Intracellular",
    }
    zone_order = ["Orthosteric", "Allosteric", "Intracellular"]

    pocket_summary = {}
    for fam in ["Gi", "Gq", "Gs"]:
        if fam not in ox2r_pockets:
            continue
        zone_freqs = {z: [] for z in zone_order}
        for p in ox2r_pockets[fam]["pockets"]:
            mapped = zone_map.get(p["zone"], "Intracellular")
            if mapped in zone_freqs:
                zone_freqs[mapped].append(p["mean_freq"])
        pocket_summary[fam] = {z: np.mean(v) if v else 0 for z, v in zone_freqs.items()}

    n_zones = len(zone_order)
    n_fams = len(pocket_summary)
    bar_width = 0.22
    x_base = np.arange(n_zones)

    for i, fam in enumerate(["Gi", "Gq", "Gs"]):
        if fam not in pocket_summary:
            continue
        vals = [pocket_summary[fam].get(z, 0) for z in zone_order]
        offset = (i - (n_fams - 1) / 2) * bar_width
        ax.bar(x_base + offset, vals, bar_width, color=FAMILY_COLORS[fam],
               label=fam, edgecolor="none", zorder=2)

    ax.set_xticks(x_base)
    ax.set_xticklabels(zone_order)
    ax.set_ylabel("Mean pocket frequency")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right", frameon=False, fontsize=5.5,
              handlelength=1.0, handletextpad=0.3, borderpad=0.3)

    # ── C: OX2R gateway heatmap ──────────────────────────────────────────
    ax = axes[1, 0]
    add_panel_label(ax, "C")

    # Build heatmap: rows = portal pairs, columns = Gi/Gq/Gs
    all_pairs = sorted(set(
        r["pair"]
        for fam in ox2r_gateways
        for r in ox2r_gateways[fam]["records"]
        if r["metric"] == "open_fraction"
    ))
    fam_order = ["Gi", "Gq", "Gs"]
    gw_matrix = np.zeros((len(all_pairs), len(fam_order)))

    for j, fam in enumerate(fam_order):
        if fam not in ox2r_gateways:
            continue
        of_dict = {r["pair"]: r["mean"]
                   for r in ox2r_gateways[fam]["records"]
                   if r["metric"] == "open_fraction"}
        for i, pair in enumerate(all_pairs):
            gw_matrix[i, j] = of_dict.get(pair, 0.0)

    im = ax.imshow(gw_matrix, aspect="auto", cmap="coolwarm", vmin=0, vmax=1,
                   interpolation="nearest")
    ax.set_xticks(np.arange(len(fam_order)))
    ax.set_xticklabels(fam_order)
    ax.set_yticks(np.arange(len(all_pairs)))
    ax.set_yticklabels(all_pairs, fontsize=5.5)
    ax.set_ylabel("Portal pair")

    # Annotate cells
    for i in range(len(all_pairs)):
        for j in range(len(fam_order)):
            val = gw_matrix[i, j]
            text_color = "white" if val > 0.6 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=5, color=text_color, zorder=5)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, shrink=0.9)
    cbar.set_label("Open fraction", fontsize=6)
    cbar.ax.tick_params(labelsize=5)

    # ── D: Scatter with OX2R triangle overlay ────────────────────────────
    ax = axes[1, 1]
    add_panel_label(ax, "D")

    # Plot all 16 pairs as dots
    for _, row in comparisons.iterrows():
        contrast = row["contrast"]
        color = transition_colors.get(contrast, "#888888")
        is_ox2r = row["receptor"] == "OX2R"
        if is_ox2r:
            continue  # will plot OX2R separately
        ax.scatter(row["jaccard"], row["gateway_dist"], c=color, s=25,
                   edgecolors="white", linewidths=0.3, zorder=3, alpha=0.8)

    # OX2R triangle: connect the 3 OX2R contrasts
    ox2r_rows = comparisons[comparisons["receptor"] == "OX2R"]
    ox2r_points = ox2r_rows[["jaccard", "gateway_dist"]].values
    if len(ox2r_points) >= 2:
        # Plot OX2R points
        for _, row in ox2r_rows.iterrows():
            ax.scatter(row["jaccard"], row["gateway_dist"], c="#e74c3c", s=45,
                       edgecolors="black", linewidths=0.6, zorder=5, marker="D")

        # Connect with lines to form triangle
        from matplotlib.patches import Polygon
        if len(ox2r_points) == 3:
            triangle = Polygon(ox2r_points, closed=True, fill=False,
                               edgecolor="#e74c3c", linewidth=1.2, linestyle="-",
                               zorder=4)
            ax.add_patch(triangle)
        elif len(ox2r_points) == 2:
            ax.plot(ox2r_points[:, 0], ox2r_points[:, 1],
                    color="#e74c3c", linewidth=1.2, zorder=4)

        # Label OX2R contrasts
        for _, row in ox2r_rows.iterrows():
            label = f"OX2R\n{row['contrast']}"
            ax.annotate(label, (row["jaccard"], row["gateway_dist"]),
                        textcoords="offset points", xytext=(6, 4),
                        fontsize=4.5, color="#e74c3c", zorder=6)

    # Annotate top 5 most divergent (by gateway_dist)
    comparisons_sorted = comparisons.sort_values("gateway_dist", ascending=False)
    annotated = 0
    for _, row in comparisons_sorted.iterrows():
        if row["receptor"] == "OX2R":
            continue  # already annotated
        if annotated >= 5:
            break
        ax.annotate(row["receptor"], (row["jaccard"], row["gateway_dist"]),
                    textcoords="offset points", xytext=(4, 4),
                    fontsize=4.5, color="#555555", zorder=6)
        annotated += 1

    ax.set_xlabel("Pocket Jaccard similarity")
    ax.set_ylabel("Gateway dissimilarity")
    ax.set_xlim(-0.05, 1.1)
    ax.set_ylim(0, None)

    # ── Save ──────────────────────────────────────────────────────────────
    for ext in ["pdf", "png"]:
        fig.savefig(OUT / f"figure5_partner_switching.{ext}", dpi=300)
    plt.close(fig)
    print(f"✓ Figure 5 saved to {OUT}/figure5_partner_switching.{{pdf,png}}")


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating Figure 4 …")
    make_figure4()
    print("Generating Figure 5 …")
    make_figure5()
    print("Done.")
