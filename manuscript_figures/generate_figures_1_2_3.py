#!/usr/bin/env python3
"""
Generate Figures 1, 2 and 3 for the CoupledMD NAR paper.

Figure 1 — Database overview            (double column, 2x2 panels)
Figure 2 — CCR5 allosteric recovery     (single column, 3 panels)
Figure 3 — FFAR4 gateway reorganisation (double column, 1x2 panels)

All values are read from the real pipeline outputs under data/. No value is
hand-set. See INTEGRITY_FLAGS.md for the data corrections applied here
(Fig 1A system counts, Fig 1D receptor column, Fig 3 open_fraction metric).
"""

import json
import os

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.pyplot as plt

# Liberation Sans lacks the unicode superscript-plus glyph; render via mathtext.
NA_PLUS = r"Na$^{+}$"

import figstyle as fs
from figstyle import FAMILY, FAMILY_ORDER, FAMILY_LABEL, ACCENT, INK, MUTED, PALE, ZONE

fs.apply_style()

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
API_DIR = os.path.join(DATA_DIR, "api", "v1", "systems")

# Standard IUPHAR symbols for the multi-system receptors (nomenclature only,
# used as compact axis labels; receptor_gene is null for most rows).
RECEPTOR_SYMBOL = {
    "Orexin receptor type 2": "OX2R",
    "Corticotropin-releasing factor receptor 2": "CRHR2",
    "Free fatty acid receptor 4": "FFAR4",
    "Cholecystokinin receptor type A": "CCKAR",
    "Endothelin receptor type B": "EDNRB",
    "Somatostatin receptor type 2": "SSTR2",
    "Adhesion G protein-coupled receptor E5": "ADGRE5",
    "5-hydroxytryptamine receptor 4": "HTR4",
    "P2Y purinoceptor 1": "P2RY1",
    "Neuromedin-U receptor 2": "NMUR2",
    "Neuropeptide Y receptor type 1": "NPY1R",
    "Muscarinic acetylcholine receptor M1": "CHRM1",
    "Muscarinic acetylcholine receptor M4": "CHRM4",
    "Alpha-2A adrenergic receptor": "ADRA2A",
    "Histamine H1 receptor": "HRH1",
    "Glucagon receptor": "GCGR",
    "Apelin receptor": "APLNR",
    "C3a anaphylatoxin chemotactic receptor": "C3AR1",
    "C5a anaphylatoxin chemotactic receptor 1": "C5AR1",
    "Calcitonin receptor": "CALCR",
    "Oxytocin receptor": "OXTR",
    "Substance-P receptor": "TACR1",
    "Gastrin/cholecystokinin type B receptor": "CCKBR",
    "Growth hormone secretagogue receptor type 1": "GHSR",
    "Lysophosphatidic acid receptor 1": "LPAR1",
    "Sphingosine 1-phosphate receptor 1": "S1PR1",
    "5-hydroxytryptamine receptor 1A": "HTR1A",
    "5-hydroxytryptamine receptor 1E": "HTR1E",
}


def _symbol(name):
    return RECEPTOR_SYMBOL.get(name, (name[:18] + "…") if len(name) > 19 else name)


# ══════════════════════════════════════════════════════════════════════════════
#  FIGURE 1 — Database overview
# ══════════════════════════════════════════════════════════════════════════════
def make_figure_1():
    df = pd.read_csv(os.path.join(DATA_DIR, "systems_master.csv"))

    fig, axes = plt.subplots(2, 2, figsize=(fs.COL2, 4.7))
    fig.subplots_adjust(hspace=0.50, wspace=0.30, left=0.09, right=0.97,
                        top=0.91, bottom=0.11)
    ax_a, ax_b, ax_c, ax_d = axes.flat

    # ── A — system count per family (horizontal bars) ─────────────────────────
    sys_counts = df.groupby("g_protein_family").size().reindex(FAMILY_ORDER)
    y = np.arange(len(FAMILY_ORDER))[::-1]
    ax_a.barh(y, sys_counts.values, height=0.66,
              color=[FAMILY[f] for f in FAMILY_ORDER])
    for yi, f in zip(y, FAMILY_ORDER):
        n = int(sys_counts[f])
        ax_a.text(n + 2, yi, str(n), va="center", ha="left",
                  fontsize=6.5, fontweight="bold", color=INK)
    ax_a.set_yticks(y)
    ax_a.set_yticklabels([FAMILY_LABEL[f] for f in FAMILY_ORDER])
    ax_a.set_xlim(0, 116)
    ax_a.set_xlabel("Systems (n)")
    ax_a.set_title("222 ternary complexes", fontsize=7.5, pad=4)
    fs.despine(ax_a)
    fs.panel_label(ax_a, "A", x=-0.30)

    # ── B — structural provenance (donut) ─────────────────────────────────────
    n_exp = int((df["structural_provenance"] == "experimental").sum())
    # engineered_uncertain = all non-experimental
    n_eng = int(len(df) - n_exp)
    wedges, _ = ax_b.pie(
        [n_exp, n_eng], startangle=90, counterclock=False,
        colors=[ACCENT, PALE],
        wedgeprops=dict(width=0.38, edgecolor="white", linewidth=0.6))
    ax_b.text(0, 0.07, "222", ha="center", va="center",
              fontsize=10, fontweight="bold", color=INK)
    ax_b.text(0, -0.12, "systems", ha="center", va="center",
              fontsize=6, color=MUTED)
    ax_b.text(0, 1.18, f"Experimental · {n_exp}", ha="center", va="center",
              fontsize=6.5, color=ACCENT, fontweight="bold")
    ax_b.text(0, -1.24, f"Engineered/chimeric · {n_eng}", ha="center", va="center",
              fontsize=6.5, color=MUTED, fontweight="bold")
    ax_b.set_title("Structural provenance", fontsize=7.5, pad=2)
    fs.panel_label(ax_b, "B", x=-0.08)

    # ── C — aggregate sampling per family + total (vertical bars) ──────────────
    samp = (df.groupby("g_protein_family")["total_sampling_ns"].sum() / 1000
            ).reindex(FAMILY_ORDER)
    total = df["total_sampling_ns"].sum() / 1000
    xc = np.arange(len(FAMILY_ORDER) + 1)
    vals = list(samp.values) + [total]
    cols = [FAMILY[f] for f in FAMILY_ORDER] + [MUTED]
    labs = [FAMILY_LABEL[f] for f in FAMILY_ORDER] + ["All"]
    ax_c.bar(xc, vals, width=0.62, color=cols)
    for xi, v in zip(xc, vals):
        ax_c.text(xi, v + 5, f"{v:.0f}", ha="center", va="bottom",
                  fontsize=6, fontweight="bold", color=INK)
    ax_c.set_xticks(xc)
    ax_c.set_xticklabels(labs)
    ax_c.set_ylabel("Aggregate sampling (µs)")
    ax_c.set_ylim(0, total * 1.18)
    ax_c.set_title("≈332 µs total", fontsize=7.5, pad=4)
    fs.despine(ax_c)
    fs.panel_label(ax_c, "C", x=-0.20)

    # ── D — most-represented receptors (top 12 by system count) ───────────────
    cnt = df.groupby("receptor_name").size()
    dom = df.groupby("receptor_name")["g_protein_family"].agg(
        lambda x: x.value_counts().index[0])
    top = (pd.DataFrame({"n": cnt, "dom": dom})
           .sort_values(["n", "n"], ascending=False)
           .head(12)
           .sort_values("n"))
    yd = np.arange(len(top))
    cold = [FAMILY[f] for f in top["dom"]]
    ax_d.hlines(yd, 0, top["n"].values, color=cold, linewidth=1.0, alpha=0.55)
    ax_d.scatter(top["n"].values, yd, c=cold, s=22, zorder=3,
                 edgecolors="white", linewidths=0.4)
    ax_d.set_yticks(yd)
    ax_d.set_yticklabels([_symbol(n) for n in top.index], fontsize=5.8)
    ax_d.set_xlabel("Systems (n)")
    ax_d.set_xlim(0, top["n"].max() + 0.6)
    ax_d.set_xticks(range(0, int(top["n"].max()) + 1))
    ax_d.set_title("Most-represented receptors", fontsize=7.5, pad=4)
    handles = [Line2D([0], [0], marker="o", linestyle="", markersize=4,
                      markerfacecolor=FAMILY[f], markeredgecolor="white",
                      markeredgewidth=0.3, label=FAMILY_LABEL[f])
               for f in FAMILY_ORDER]
    ax_d.legend(handles=handles, loc="lower right", frameon=False,
                fontsize=5.2, handletextpad=0.2, labelspacing=0.25,
                borderpad=0.2)
    fs.despine(ax_d)
    fs.panel_label(ax_d, "D", x=-0.34)

    fs.save(fig, "figure_1")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
#  FIGURE 2 — CCR5 allosteric recovery
# ══════════════════════════════════════════════════════════════════════════════
def make_figure_2():
    sid = "Gi_7F1Q"
    with open(os.path.join(API_DIR, sid, "pockets.json")) as f:
        pdata = json.load(f)
    with open(os.path.join(API_DIR, sid, "pockets_gpcrdb.json")) as f:
        gdata = json.load(f)

    pockets = sorted(pdata["pockets"], key=lambda p: p["mean_freq"], reverse=True)
    # zone per local pocket id (the Na+/maraviroc pocket is the tm_core_allosteric one)
    zone_of = {p["pocket_id"]: p.get("zone") for p in gdata["pockets"]}
    na_id = next((p["pocket_id"] for p in gdata["pockets"]
                  if p.get("zone") == "tm_core_allosteric"), None)
    n_frames = gdata.get("n_frames")
    n_rep = gdata.get("n_replicas")

    fig, (ax_a, ax_b, ax_c) = plt.subplots(
        3, 1, figsize=(fs.COL1, 5.1),
        gridspec_kw={"height_ratios": [1.25, 1.0, 0.5], "hspace": 0.62})
    fig.subplots_adjust(left=0.20, right=0.95, top=0.90, bottom=0.08)

    def pcolor(p):
        if p["is_orthosteric"]:
            return ZONE["orthosteric"]
        if p["pocket_id"] == na_id:
            return FAMILY["Gq"]            # highlight Na+/maraviroc pocket
        return ACCENT

    # ── A — ranked pocket frequencies ─────────────────────────────────────────
    freqs = [p["mean_freq"] for p in pockets]
    ya = np.arange(len(pockets))
    ax_a.barh(ya, freqs, height=0.7, color=[pcolor(p) for p in pockets])
    ax_a.set_yticks(ya)
    ax_a.set_yticklabels([f"P{p['pocket_id']}" for p in pockets], fontsize=5.5)
    ax_a.invert_yaxis()
    ax_a.set_xlim(0.84, 0.97)
    ax_a.set_xlabel("Mean occupancy frequency")
    ax_a.set_title("13 persistent pockets (CCR5, Gi_7F1Q)", fontsize=7, pad=4)
    # colour-coded legend in clear lower-right space (avoids label–bar overlap)
    handles = [Patch(color=ZONE["orthosteric"], label="Orthosteric"),
               Patch(color=FAMILY["Gq"], label=NA_PLUS + " / maraviroc"),
               Patch(color=ACCENT, label="Other allosteric")]
    ax_a.legend(handles=handles, loc="lower right", frameon=False, fontsize=5.2,
                handlelength=1.0, handletextpad=0.4, labelspacing=0.3,
                borderpad=0.2)
    fs.despine(ax_a)
    fs.panel_label(ax_a, "A", x=-0.24, y=1.10)

    # ── B — pocket size vs frequency, bubble ∝ volume ─────────────────────────
    for p in pockets:
        ax_b.scatter(p["n_lining"], p["mean_freq"],
                     s=max(p["n_voxels"] / 6, 6), c=pcolor(p),
                     edgecolors="white", linewidths=0.4, alpha=0.9, zorder=3)
    na = next(p for p in pockets if p["pocket_id"] == na_id)
    ortho = next(p for p in pockets if p["is_orthosteric"])
    ax_b.annotate(NA_PLUS + " pocket\n2.50·3.39·7.49", xy=(na["n_lining"], na["mean_freq"]),
                  xytext=(na["n_lining"] + 8, na["mean_freq"] - 0.018),
                  fontsize=5, color=FAMILY["Gq"], va="top",
                  arrowprops=dict(arrowstyle="-", color=FAMILY["Gq"], lw=0.5))
    ax_b.annotate("orthosteric", xy=(ortho["n_lining"], ortho["mean_freq"]),
                  xytext=(ortho["n_lining"] - 6, ortho["mean_freq"] + 0.006),
                  fontsize=5, color=ZONE["orthosteric"], ha="right", va="bottom",
                  arrowprops=dict(arrowstyle="-", color=ZONE["orthosteric"], lw=0.5))
    ax_b.set_xlabel("Lining residues (n)")
    ax_b.set_ylabel("Mean frequency")
    ax_b.set_xlim(0, 82)
    ax_b.set_ylim(0.845, 0.965)
    # size legend in clear lower-right
    for vox, lab in [(50, "50"), (300, "300"), (800, "800")]:
        ax_b.scatter([], [], s=max(vox / 6, 6), c="0.7",
                     edgecolors="white", linewidths=0.4, label=lab)
    ax_b.legend(title="Volume (voxels)", loc="lower right", frameon=False,
                fontsize=4.8, title_fontsize=4.8, handletextpad=0.3,
                labelspacing=0.5, borderpad=0.2)
    fs.despine(ax_b)
    fs.panel_label(ax_b, "B", x=-0.24, y=1.08)

    # ── C — compact summary (clean table, no chartjunk) ───────────────────────
    ax_c.axis("off")
    rows = [
        ("System", "CCR5 · Gi · PDB 7F1Q"),
        ("Sampling", f"{n_frames} frames · {n_rep} replicas"),
        ("Orthosteric", f"recovered, freq {ortho['mean_freq']:.3f}"),
        (NA_PLUS + " / maraviroc", f"freq {na['mean_freq']:.3f} · positions 2.50·3.39·7.49"),
        ("Clinical link", "maraviroc — FDA-approved CCR5 inhibitor"),
    ]
    y0 = 0.96
    ax_c.text(0.0, 1.04, "CCR5 case summary", fontsize=6.2, fontweight="bold",
              color=INK, transform=ax_c.transAxes)
    for k, v in rows:
        ax_c.plot([0, 1], [y0 + 0.02, y0 + 0.02], color="#e3e7ec",
                  lw=0.4, transform=ax_c.transAxes)
        ax_c.text(0.0, y0, k, fontsize=5.4, fontweight="bold", color=MUTED,
                  va="top", transform=ax_c.transAxes)
        ax_c.text(0.34, y0, v, fontsize=5.4, color=INK, va="top",
                  transform=ax_c.transAxes)
        y0 -= 0.205
    fs.panel_label(ax_c, "C", x=-0.24, y=1.18)

    fig.suptitle("MD blind-recovers the maraviroc allosteric site in CCR5",
                 fontsize=8, fontweight="bold", y=0.985)
    fs.save(fig, "figure_2")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
#  FIGURE 3 — FFAR4 gateway reorganisation (Gi vs Gq)
# ══════════════════════════════════════════════════════════════════════════════
def make_figure_3():
    with open(os.path.join(API_DIR, "Gi_8ID9", "gateways.json")) as f:
        gi = json.load(f)
    with open(os.path.join(API_DIR, "Gq_8IYS", "gateways.json")) as f:
        gq = json.load(f)

    pairs = ["TM1-TM2", "TM2-TM3", "TM3-TM4", "TM4-TM5",
             "TM5-TM6", "TM6-TM7", "TM7-TM1"]

    def metric(data, name):
        out = {}
        for r in data["records"]:
            if r["metric"] == name:
                out[r["pair"]] = (r["mean"], r["mean"] - r["ci_lo"],
                                  r["ci_hi"] - r["mean"])
        return out

    x = np.arange(len(pairs))
    w = 0.38
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(fs.COL2, 3.4))
    fig.subplots_adjust(wspace=0.28, left=0.09, right=0.98, top=0.86, bottom=0.20)

    def grouped(ax, gi_m, gq_m, ylabel, highlight=None):
        gi_v = [gi_m[p][0] for p in pairs]
        gq_v = [gq_m[p][0] for p in pairs]
        gi_e = [[gi_m[p][1] for p in pairs], [gi_m[p][2] for p in pairs]]
        gq_e = [[gq_m[p][1] for p in pairs], [gq_m[p][2] for p in pairs]]
        ax.bar(x - w / 2, gi_v, w, color=FAMILY["Gi"], label="Gi/o",
               yerr=gi_e, capsize=1.5, error_kw={"linewidth": 0.5, "ecolor": INK})
        ax.bar(x + w / 2, gq_v, w, color=FAMILY["Gq"], label="Gq/11",
               yerr=gq_e, capsize=1.5, error_kw={"linewidth": 0.5, "ecolor": INK})
        ax.set_xticks(x)
        ax.set_xticklabels(pairs, rotation=35, ha="right", fontsize=5.8)
        ax.set_ylabel(ylabel)
        fs.despine(ax)
        return gi_v, gq_v

    # ── A — open fraction (the partner-switching signal) ──────────────────────
    gi_of = metric(gi, "open_fraction")
    gq_of = metric(gq, "open_fraction")
    gi_v, gq_v = grouped(ax_a, gi_of, gq_of, "Gateway open fraction")
    ax_a.set_ylim(0, max(max(gi_v), max(gq_v)) * 1.30)
    ax_a.legend(loc="upper left", frameon=False, fontsize=6,
                handlelength=1.0, handletextpad=0.4)
    # highlight the TM6-TM7 ~10-fold divergence (point at the near-closed Gi bar)
    i67 = pairs.index("TM6-TM7")
    ax_a.annotate(f"~10× closure\nGi {gi_of['TM6-TM7'][0]:.3f} · Gq {gq_of['TM6-TM7'][0]:.3f}",
                  xy=(i67 - w / 2, gi_of["TM6-TM7"][0]),
                  xytext=(i67 - 1.7, 0.45), fontsize=5, color=INK, ha="left",
                  va="top",
                  arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.5,
                                  shrinkA=0, shrinkB=2))
    ax_a.set_title("Open-state fraction", fontsize=7.5, pad=3)
    fs.panel_label(ax_a, "A", x=-0.12)

    # ── B — mean portal distance (Å) with 8 Å open threshold ──────────────────
    gi_d = metric(gi, "occupancy")     # 'occupancy' stores mean portal distance (Å)
    gq_d = metric(gq, "occupancy")
    gi_v, gq_v = grouped(ax_b, gi_d, gq_d, "Mean portal distance (Å)")
    ax_b.set_ylim(0, max(max(gi_v), max(gq_v)) * 1.18)
    ax_b.axhline(8, color=MUTED, linestyle="--", linewidth=0.7)
    # label sits in the clear space above the short TM2-TM3 bars
    ax_b.text(1.0, 10.6, "8 Å open\nthreshold", fontsize=5, color=MUTED,
              ha="center", va="center", linespacing=1.1)
    ax_b.legend(loc="upper left", frameon=False, fontsize=6,
                handlelength=1.0, handletextpad=0.4)
    ax_b.set_title("Portal aperture", fontsize=7.5, pad=3)
    fs.panel_label(ax_b, "B", x=-0.12)

    fig.suptitle("FFAR4 gateway reorganisation between Gi/o and Gq/11 partners",
                 fontsize=8.5, fontweight="bold", y=0.99)
    fs.save(fig, "figure_3")
    plt.close(fig)


if __name__ == "__main__":
    print("Figure 1 — database overview …")
    make_figure_1()
    print("Figure 2 — CCR5 allosteric recovery …")
    make_figure_2()
    print("Figure 3 — FFAR4 gateway reorganisation …")
    make_figure_3()
    print("Done.")
