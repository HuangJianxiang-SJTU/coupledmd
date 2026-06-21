#!/usr/bin/env python3
"""
Generate Figures 4 and 5 for the CoupledMD NAR paper.

Figure 4 — G-protein coupling interface  (double column, 2x2 panels)
Figure 5 — Partner-switching reorganisation (double column, 2x2 panels)

All values read from the real pipeline outputs. See INTEGRITY_FLAGS.md:
- Fig 4A plots the 25 CGN positions present in the pilot table (not 356).
- Fig 5D plots jaccard vs alpha5 tilt difference with NO trend line, because the
  resource's own Spearman stats show no significant association (n=13).
"""

import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.transforms
from matplotlib.patches import Ellipse, Polygon

import numpy as np
import pandas as pd

import figstyle as fs
from figstyle import FAMILY, FAMILY_LABEL, ACCENT, INK, MUTED, FLOCK

warnings.filterwarnings("ignore")
fs.apply_style()

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = Path("/MDdata/data02/jxhuang/gpcr_g")
PILOT_CSV    = BASE / "a" / "stage2_outputs" / "pilot_long.csv"
COUPLING_CSV = BASE / "a" / "paper1_coupling_table.csv"
REORG_JSON   = BASE / "gpcr_g_server" / "data" / "api" / "v1" / "consensus" / "reorg_atlas.json"
SYSTEMS_DIR  = BASE / "gpcr_g_server" / "data" / "api" / "v1" / "systems"

SEGMENT_ORDER = ["G.HN", "G.hns1", "G.S3", "G.s2s3", "G.h4s6",
                 "G.H2", "G.H5", "H.HD", "H.hdhe"]


def confidence_ellipse(x, y, ax, n_std=2.0, facecolor="none", **kwargs):
    if len(x) < 3:
        return
    cov = np.cov(x, y)
    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    rx, ry = np.sqrt(1 + pearson), np.sqrt(1 - pearson)
    ell = Ellipse((0, 0), width=rx * 2, height=ry * 2, facecolor=facecolor, **kwargs)
    sx, sy = np.sqrt(cov[0, 0]) * n_std, np.sqrt(cov[1, 1]) * n_std
    tr = (matplotlib.transforms.Affine2D().rotate_deg(45)
          .scale(sx, sy).translate(np.mean(x), np.mean(y)))
    ell.set_transform(tr + ax.transData)
    ax.add_patch(ell)


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — G-protein coupling interface
# ══════════════════════════════════════════════════════════════════════════════
def make_figure4():
    pilot = pd.read_csv(PILOT_CSV)
    coupling = pd.read_csv(COUPLING_CSV)

    pilot["cgn_segment"] = pd.Categorical(pilot["cgn_segment"],
                                          categories=SEGMENT_ORDER, ordered=True)
    pilot = pilot.sort_values(["cgn_segment", "cgn_position"]).reset_index(drop=True)
    ordered_pos = pilot["cgn_position"].unique().tolist()

    fig, axes = plt.subplots(2, 2, figsize=(fs.COL2, 5.4))
    fig.subplots_adjust(hspace=0.55, wspace=0.30, left=0.08, right=0.96,
                        top=0.93, bottom=0.12)

    # ── A — contact-persistence barcode (pilot CGN positions) ─────────────────
    ax = axes[0, 0]
    agg = (pilot.groupby("cgn_position", sort=False)
           .agg(mean_cp=("contact_persistence_mean", "mean"),
                ci_lo=("contact_persistence_ci_low", "mean"),
                ci_hi=("contact_persistence_ci_high", "mean"),
                segment=("cgn_segment", "first"),
                flock=("flock_class", "first"))
           .reindex(ordered_pos))
    err_lo = (agg["mean_cp"] - agg["ci_lo"]).fillna(0).clip(lower=0)
    err_hi = (agg["ci_hi"] - agg["mean_cp"]).fillna(0).clip(lower=0)
    xp = np.arange(len(agg))
    colors = [FLOCK.get(fc, "#aab2bd") for fc in agg["flock"]]

    h5 = (agg["segment"] == "G.H5").values
    if h5.any():
        idx = np.where(h5)[0]
        ax.axvspan(idx[0] - 0.5, idx[-1] + 0.5, color="#f1f3f5", zorder=0)
        ax.text((idx[0] + idx[-1]) / 2, 1.02, "α5 (G.H5)", ha="center",
                va="bottom", fontsize=5.5, style="italic", color=MUTED,
                transform=ax.get_xaxis_transform())
    ax.bar(xp, agg["mean_cp"], color=colors, width=0.82, zorder=2)
    ax.errorbar(xp, agg["mean_cp"], yerr=[err_lo, err_hi], fmt="none",
                ecolor=INK, elinewidth=0.4, capsize=1.2, capthick=0.4, zorder=3)
    ax.set_xticks(xp)
    ax.set_xticklabels([p.replace("G.", "").replace("H.", "H") for p in agg.index],
                       rotation=90, fontsize=4.3)
    ax.set_ylabel("Contact persistence")
    ax.set_ylim(0, 1.08)
    ax.set_xlim(-0.6, len(agg) - 0.4)
    handles = [mpatches.Patch(color=FLOCK["conserved"], label="Conserved"),
               mpatches.Patch(color=FLOCK["selectivity-determining"],
                              label="Selectivity-det.")]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=5,
              handlelength=1.0, handletextpad=0.4, borderpad=0.2,
              bbox_to_anchor=(0.0, 0.62))
    fs.despine(ax)
    fs.panel_label(ax, "A", x=-0.11)

    # ── B — α5 tilt vs insertion depth ────────────────────────────────────────
    ax = axes[0, 1]
    for fam in ["Gi", "Gs", "Gq"]:
        sub = coupling[coupling["g_family"] == fam].dropna(subset=["f01_tilt", "f06_depth"])
        if not len(sub):
            continue
        ax.scatter(sub["f01_tilt"], sub["f06_depth"], c=FAMILY[fam], s=18,
                   edgecolors="white", linewidths=0.3, zorder=3,
                   label=FAMILY_LABEL[fam])
        if len(sub) >= 3:
            confidence_ellipse(sub["f01_tilt"].values, sub["f06_depth"].values,
                               ax, n_std=2.0, edgecolor=FAMILY[fam],
                               facecolor=FAMILY[fam], alpha=0.08,
                               linewidth=0.8, zorder=2)
    ox = coupling[(coupling["system"] == "7L1V")]
    if len(ox):
        r = ox.iloc[0]
        ax.scatter(r["f01_tilt"], r["f06_depth"], s=42, facecolors="none",
                   edgecolors=INK, linewidths=0.9, zorder=5)
        ax.annotate("OX2R\n(7L1V, Gs)", xy=(r["f01_tilt"], r["f06_depth"]),
                    xytext=(r["f01_tilt"] - 20, r["f06_depth"] + 3.5),
                    fontsize=5, color=INK, va="bottom",
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
    ax.set_xlabel("α5 tilt angle (°)")
    ax.set_ylabel("α5 insertion depth (Å)")
    ax.legend(loc="lower right", frameon=False, fontsize=5.5,
              handletextpad=0.3, borderpad=0.2, labelspacing=0.3)
    fs.despine(ax)
    fs.panel_label(ax, "B", x=-0.13)

    # ── C — selectivity-determining contact fingerprint heatmap ───────────────
    ax = axes[1, 0]
    sel = pilot[pilot["flock_class"] == "selectivity-determining"].copy()
    sel["cgn_segment"] = pd.Categorical(sel["cgn_segment"],
                                        categories=SEGMENT_ORDER, ordered=True)
    sel = sel.sort_values(["cgn_segment", "cgn_position"])
    sel_pos = sel["cgn_position"].unique().tolist()
    fams = ["Gi", "Gs", "Gq", "G12"]
    mat = np.full((len(fams), len(sel_pos)), np.nan)
    for i, fam in enumerate(fams):
        fd = sel[sel["g_alpha_family"] == fam]
        for j, pos in enumerate(sel_pos):
            v = fd[fd["cgn_position"] == pos]["contact_persistence_mean"]
            if len(v):
                mat[i, j] = v.mean()
    im = ax.imshow(mat, aspect="auto", cmap="cividis", vmin=0, vmax=1,
                   interpolation="nearest")
    ax.set_xticks(np.arange(len(sel_pos)))
    ax.set_xticklabels([p.replace("G.", "") for p in sel_pos], rotation=90, fontsize=4.3)
    ax.set_yticks(np.arange(len(fams)))
    ax.set_yticklabels([FAMILY_LABEL.get(f, f) for f in fams])
    ax.set_ylabel("G-protein family")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, shrink=0.9)
    cbar.set_label("Contact persistence", fontsize=6)
    cbar.ax.tick_params(labelsize=5)
    fs.panel_label(ax, "C", x=-0.11)

    # ── D — RMSF profile along G.H5 ───────────────────────────────────────────
    ax = axes[1, 1]
    h5d = pilot[pilot["cgn_segment"] == "G.H5"].copy()
    h5pos = sorted(h5d["cgn_position"].unique(), key=lambda x: int(x.split(".")[-1]))
    for fam in ["Gi", "Gs", "Gq", "G12"]:
        fd = h5d[h5d["g_alpha_family"] == fam]
        m, lo, hi = [], [], []
        for pos in h5pos:
            pd_ = fd[fd["cgn_position"] == pos]
            if len(pd_) and not np.isnan(pd_["rmsf_mean"].mean()):
                mm = pd_["rmsf_mean"].mean()
                m.append(mm)
                lo.append(mm - pd_["rmsf_ci_low"].mean())
                hi.append(pd_["rmsf_ci_high"].mean() - mm)
            else:
                m.append(np.nan); lo.append(0); hi.append(0)
        m = np.array(m); lo = np.array(lo); hi = np.array(hi)
        x = np.arange(len(h5pos)); valid = ~np.isnan(m)
        if valid.any():
            ax.plot(x[valid], m[valid], color=FAMILY[fam], marker="o",
                    markersize=2.5, linewidth=1.0, label=FAMILY_LABEL.get(fam, fam),
                    zorder=3)
            ax.fill_between(x[valid], (m - lo)[valid], (m + hi)[valid],
                            color=FAMILY[fam], alpha=0.12, zorder=2)
    ax.set_xticks(np.arange(len(h5pos)))
    ax.set_xticklabels([p.split(".")[-1] for p in h5pos], rotation=90, fontsize=5)
    ax.set_xlabel("G.H5 position")
    ax.set_ylabel("RMSF (Å)")
    ax.legend(loc="upper left", frameon=False, fontsize=5.5,
              handlelength=1.0, handletextpad=0.3, ncol=2, columnspacing=0.8)
    fs.despine(ax)
    fs.panel_label(ax, "D", x=-0.13)

    fs.save(fig, "figure4_gprotein_interface")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — Partner-switching reorganisation
# ══════════════════════════════════════════════════════════════════════════════
def make_figure5():
    """
    INTEGRITY NOTE (F11): The 'jaccard' column in reorg_atlas.json equals
    1 - Jaccard_similarity (i.e. Jaccard DISTANCE). We plot Jaccard SIMILARITY
    (= 1 - jaccard_dist) so that 0.0 = no shared pockets and 1.0 = identical.
    OX2R Gq-Gs: Jaccard_sim = 1.0 (identical pocket profiles, both in orthosteric
    cluster O1 only). The Gi complex uniquely opens a druggable pocket (D18).
    """
    reorg = json.load(open(REORG_JSON))
    comp = pd.DataFrame(reorg["comparisons"])

    # Convert Jaccard distance to similarity (F11 fix)
    comp["jaccard_sim"] = (1.0 - comp["jaccard"]).clip(0.0, 1.0)

    ox2r = {"Gi": "Gi_7SQO", "Gq": "Gq_7SR8", "Gs": "Gs_7L1V"}
    gateways = {}
    for fam, sid in ox2r.items():
        gp = SYSTEMS_DIR / sid / "gateways.json"
        if gp.exists():
            gateways[fam] = json.load(open(gp))

    # contrast colour = colour of the destination family
    contrast_color = {"Gi-Gq": FAMILY["Gq"], "Gi-Gs": FAMILY["Gs"],
                      "Gq-Gs": FAMILY["Gs"]}

    fig, axes = plt.subplots(2, 2, figsize=(fs.COL2, 5.4))
    fig.subplots_adjust(hspace=0.42, wspace=0.32, left=0.09, right=0.96,
                        top=0.93, bottom=0.10)

    # ── A — jaccard similarity vs gateway divergence ──────────────────────────
    ax = axes[0, 0]
    for _, r in comp.iterrows():
        is_ox = r["receptor"] == "OX2R"
        ax.scatter(r["jaccard_sim"], r["gateway_dist"],
                   c=contrast_color.get(r["contrast"], MUTED),
                   s=46 if is_ox else 26,
                   edgecolors=INK if is_ox else "white",
                   linewidths=0.9 if is_ox else 0.3, zorder=5 if is_ox else 3)
    # OX2R Gq-Gs: identical pockets (sim=1.0) but notable gateway divergence
    ext = comp[(comp.receptor == "OX2R") & (comp.contrast == "Gq-Gs")].iloc[0]
    ax.annotate("OX2R Gq→Gs\n(gateway shift;\nidentical pockets)",
                xy=(ext["jaccard_sim"], ext["gateway_dist"]),
                xytext=(ext["jaccard_sim"] - 0.45, ext["gateway_dist"] + 0.005),
                fontsize=4.8, color=INK, va="center",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
    ax.axvline(0.5, color="#cccccc", lw=0.5, ls="--", zorder=1)
    ax.set_xlabel("Pocket Jaccard similarity")
    ax.set_ylabel("Gateway divergence (mean |Δ open fraction|)")
    ax.set_xlim(-0.06, 1.12)
    handles = [mpatches.Patch(color=FAMILY["Gq"], label="→ Gq/11"),
               mpatches.Patch(color=FAMILY["Gs"], label="→ Gs")]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=5.5,
              handlelength=1.0, handletextpad=0.4, ncol=2, columnspacing=1.0)
    fs.despine(ax)
    fs.panel_label(ax, "A", x=-0.13)

    # ── B — OX2R pairwise pocket Jaccard SIMILARITY ───────────────────────────
    # Gi has a unique druggable pocket (cluster D18) absent in Gq and Gs.
    # Gq and Gs have identical pocket profiles (both in orthosteric cluster O1).
    ax = axes[0, 1]
    ox_j = (comp[comp.receptor == "OX2R"].set_index("contrast")
            .reindex(["Gi-Gq", "Gi-Gs", "Gq-Gs"]))
    labels = ["Gi↔Gq", "Gi↔Gs", "Gq↔Gs"]
    jvals = ox_j["jaccard_sim"].values
    xb = np.arange(len(labels))
    # Gi contrasts show intermediate similarity (Gi has unique druggable pocket)
    # Gq-Gs shows identical (sim=1.0)
    bar_colors = [FAMILY["Gi"], FAMILY["Gi"], ACCENT]
    bars = ax.bar(xb, jvals, width=0.58, color=bar_colors, zorder=3)
    for xi, v in zip(xb, jvals):
        ax.text(xi, v + 0.03, f"{v:.2f}", ha="center", va="bottom",
                fontsize=6, fontweight="bold", color=INK)
    ax.annotate("Gi-unique\ndruggable pocket", xy=(0, jvals[0]),
                xytext=(0.5, jvals[0] - 0.30),
                ha="center", va="top", fontsize=4.8, color=FAMILY["Gi"],
                fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=FAMILY["Gi"], lw=0.6,
                                connectionstyle="arc3,rad=0.2"))
    ax.annotate("identical\npocket profiles", xy=(2, jvals[2]),
                xytext=(2, jvals[2] - 0.28),
                ha="center", va="top", fontsize=4.8, color=ACCENT,
                fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=0.6))
    ax.set_xticks(xb)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Pocket Jaccard similarity")
    ax.set_ylim(0, 1.18)
    ax.set_title("OX2R partner-specific pockets", fontsize=7.5, pad=3)
    fs.despine(ax)
    fs.panel_label(ax, "B", x=-0.13)

    # ── C — OX2R gateway open-fraction heatmap ────────────────────────────────
    ax = axes[1, 0]
    pairs = sorted(set(rec["pair"] for fam in gateways
                       for rec in gateways[fam]["records"]
                       if rec["metric"] == "open_fraction"))
    fam_order = ["Gi", "Gq", "Gs"]
    mat = np.zeros((len(pairs), len(fam_order)))
    for j, fam in enumerate(fam_order):
        if fam not in gateways:
            continue
        of = {r["pair"]: r["mean"] for r in gateways[fam]["records"]
              if r["metric"] == "open_fraction"}
        for i, p in enumerate(pairs):
            mat[i, j] = of.get(p, 0.0)
    im = ax.imshow(mat, aspect="auto", cmap="cividis", vmin=0, vmax=1,
                   interpolation="nearest")
    ax.set_xticks(np.arange(len(fam_order)))
    ax.set_xticklabels([FAMILY_LABEL[f] for f in fam_order])
    ax.set_yticks(np.arange(len(pairs)))
    ax.set_yticklabels(pairs, fontsize=5.5)
    ax.set_ylabel("Portal pair")
    for i in range(len(pairs)):
        for j in range(len(fam_order)):
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center",
                    fontsize=4.8, color="white" if mat[i, j] < 0.55 else INK)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, shrink=0.9)
    cbar.set_label("Open fraction", fontsize=6)
    cbar.ax.tick_params(labelsize=5)
    fs.panel_label(ax, "C", x=-0.18)

    # ── D — jaccard similarity vs α5 tilt difference (NO trend: see F10) ──────
    ax = axes[1, 1]
    cd = comp.dropna(subset=["dtilt"])
    for _, r in cd.iterrows():
        is_ox = r["receptor"] == "OX2R"
        ax.scatter(r["jaccard_sim"], r["dtilt"],
                   c=contrast_color.get(r["contrast"], MUTED),
                   s=46 if is_ox else 26, marker="D" if is_ox else "o",
                   edgecolors=INK if is_ox else "white",
                   linewidths=0.8 if is_ox else 0.3, zorder=5 if is_ox else 3)
    for _, r in cd[cd.receptor == "OX2R"].iterrows():
        ax.annotate(f"OX2R {r['contrast'].replace('-', '→')}",
                    xy=(r["jaccard_sim"], r["dtilt"]),
                    xytext=(r["jaccard_sim"] - 0.10, r["dtilt"] + 2.0),
                    fontsize=4.6, color=INK)
    ax.set_xlabel("Pocket Jaccard similarity")
    ax.set_ylabel("α5 tilt difference (°)")
    ax.set_xlim(-0.06, 1.12)
    ax.text(0.5, 0.97, "no significant association (n=13)", transform=ax.transAxes,
            ha="center", va="top", fontsize=4.8, color=MUTED, style="italic")
    fs.despine(ax)
    fs.panel_label(ax, "D", x=-0.13)

    fs.save(fig, "figure5_partner_switching")
    plt.close(fig)


if __name__ == "__main__":
    print("Figure 4 — coupling interface …")
    make_figure4()
    print("Figure 5 — partner switching …")
    make_figure5()
    print("Done.")
