#!/usr/bin/env python3
"""Additional data-rich Scientific Data figure candidates.

These are not replacements for the frozen four-figure draft. They are candidate
main/supplementary analyses that expose more of the GPCR/G-protein dataset:

  Fig 5  scidata_figure5_community_landscape
  Fig 6  scidata_figure6_drug_design_pocket_atlas
  Fig 7  scidata_figure7_gateway_atlas
  Fig 8  scidata_figure8_gprotein_barcode
  Fig 9  scidata_figure9_partner_switching_reuse
  Fig 10 scidata_figure10_portal_archive_coverage

All panels are generated from frozen CSVs plus the local API JSON layer used by
www.coupledmd.cn. No trajectory I/O is performed.
"""

from __future__ import annotations

import ast
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-coupledmd")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Wedge

import figstyle

figstyle.apply_style()

HERE = Path(__file__).resolve().parent
TBL = HERE / "tables"
API = HERE.parent / "data" / "api" / "v1"
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

FAM_ORDER = ["Gi", "Gs", "Gq", "G12-13"]
FAM_COL = figstyle.FAMILY
FAM_LABEL = figstyle.FAMILY_LABEL
INK = figstyle.INK
MUTED = figstyle.MUTED
PALE = figstyle.PALE
ACCENT = figstyle.ACCENT
WARN = "#c0741a"
RED = "#b23a48"
CLASS_COL = {"A": "#2c6fb3", "B": "#c0741a"}
ZONE_COL = {
    "orthosteric": "#b23a48",
    "tm_core_allosteric": "#155e63",
    "intracellular_allosteric": "#8a4aa0",
    "coupling_interface": "#586170",
    "other": "#aab2bd",
}


def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        path = OUT / f"{name}.{ext}"
        fig.savefig(path, bbox_inches="tight", pad_inches=0.02, dpi=600 if ext == "png" else None)
        print(f"  saved {path}")
    plt.close(fig)


def panel(ax, letter: str, x=-0.10, y=1.04) -> None:
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


def read_json(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def load_tables() -> dict[str, pd.DataFrame]:
    return {
        "s1": pd.read_csv(TBL / "scidata_S1_included_systems_clean_v1.csv"),
        "s2": pd.read_csv(TBL / "scidata_S2_held_back_systems.csv"),
        "s4": pd.read_csv(TBL / "scidata_S4_per_system_pockets_clean_v1.csv"),
        "s5": pd.read_csv(TBL / "scidata_S5_gateway_per_system_clean_v1.csv"),
        "s6": pd.read_csv(TBL / "scidata_S6_portal_api_endpoints.csv"),
        "s8": pd.read_csv(TBL / "scidata_S8_archive_manifest_clean_v1_from_metadata.csv"),
        "s9": pd.read_csv(TBL / "scidata_S9_portal_file_manifest_clean_v1.csv"),
        "t4": pd.read_csv(TBL / "scidata_T4_technical_validation_clean_v1.csv"),
        "t4a": pd.read_csv(TBL / "scidata_T4a_recovery_summary_clean_v1.csv"),
        "t5": pd.read_csv(TBL / "scidata_T5_qc_summary_clean_v1.csv"),
        "t6": pd.read_csv(TBL / "scidata_T6_manifest_summary.csv"),
        "t7": pd.read_csv(TBL / "scidata_T7_portal_file_availability_summary.csv"),
        "t8": pd.read_csv(TBL / "scidata_T8_viz_pbc_full_audit_clean_v1.csv"),
    }


def clean_family(value: str) -> str:
    if value == "G12":
        return "G12-13"
    return value


def ordered_families(values) -> list[str]:
    present = set(values)
    return [f for f in FAM_ORDER if f in present]


def fig5_community_landscape(d: dict[str, pd.DataFrame]) -> None:
    s1, s2 = d["s1"].copy(), d["s2"].copy()
    s1["g_protein_family"] = s1["g_protein_family"].map(clean_family)

    fig = plt.figure(figsize=(10.8, 7.4))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.1, 1.15, 1.0], height_ratios=[1.0, 1.0],
                          wspace=0.38, hspace=0.42)
    ax_hm = fig.add_subplot(gs[0, 0])
    ax_prom = fig.add_subplot(gs[0, 1])
    ax_lig = fig.add_subplot(gs[0, 2])
    ax_reuse = fig.add_subplot(gs[1, :2])
    ax_hold = fig.add_subplot(gs[1, 2])

    # A: class x family matrix.
    ct = pd.crosstab(s1["gpcr_class"], s1["g_protein_family"]).reindex(columns=ordered_families(s1["g_protein_family"]), fill_value=0)
    im = ax_hm.imshow(ct.values, cmap="YlGnBu", aspect="auto")
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            ax_hm.text(j, i, int(ct.iloc[i, j]), ha="center", va="center",
                       color="white" if ct.iloc[i, j] > ct.values.max() * 0.45 else INK,
                       fontweight="bold")
    ax_hm.set_xticks(range(ct.shape[1]), ct.columns)
    ax_hm.set_yticks(range(ct.shape[0]), [f"Class {c}" for c in ct.index])
    ax_hm.set_title("Clean-v1 coupling coverage")
    ax_hm.set_xlabel("G-protein family")
    ax_hm.set_ylabel("GPCR class")
    panel(ax_hm, "A")
    fig.colorbar(im, ax=ax_hm, fraction=0.046, pad=0.02, label="systems")

    # B: receptors represented by more than one family.
    recfam = s1.groupby(["receptor_gene", "receptor_name"])["g_protein_family"].agg(lambda x: sorted(set(x))).reset_index()
    recfam["n_families"] = recfam["g_protein_family"].map(len)
    recsys = s1.groupby("receptor_gene")["system_id"].count()
    recfam["n_systems"] = recfam["receptor_gene"].map(recsys)
    top = recfam.sort_values(["n_families", "n_systems"], ascending=False).head(16).iloc[::-1]
    colors = [FAM_COL.get(fams[0], MUTED) if len(fams) == 1 else ACCENT for fams in top["g_protein_family"]]
    ax_prom.barh(np.arange(len(top)), top["n_systems"], color=colors, edgecolor="white", lw=0.5)
    ax_prom.set_yticks(np.arange(len(top)), top["receptor_gene"].fillna("NA"))
    ax_prom.set_xlabel("systems")
    ax_prom.set_title("Receptors with reusable multi-family coverage")
    for y, (_, row) in enumerate(top.iterrows()):
        label = "/".join(row["g_protein_family"])
        ax_prom.text(row["n_systems"] + 0.2, y, label, va="center", fontsize=6.2, color=MUTED)
    ax_prom.set_xlim(0, max(top["n_systems"]) + 4)
    panel(ax_prom, "B")

    # C: ligand annotation by family.
    ligand = s1.copy()
    ligand["ligand_bucket"] = np.where(ligand["ligand_name"].isna() | (ligand["ligand_name"].astype(str).str.lower() == "nan"),
                                       "apo/none", "ligand present")
    lig_ct = pd.crosstab(ligand["g_protein_family"], ligand["ligand_bucket"]).reindex(FAM_ORDER).dropna(how="all")
    bottoms = np.zeros(len(lig_ct))
    for bucket, color in [("ligand present", RED), ("apo/none", PALE)]:
        vals = lig_ct.get(bucket, pd.Series(0, index=lig_ct.index)).values
        ax_lig.bar(lig_ct.index, vals, bottom=bottoms, color=color, edgecolor="white", lw=0.5, label=bucket)
        bottoms += vals
    ax_lig.set_ylabel("systems")
    ax_lig.set_title("Ligand-bearing complexes")
    ax_lig.legend(frameon=False, loc="upper right")
    panel(ax_lig, "C")

    # D: drug-design target space: receptors sorted by system count, colored by family diversity.
    counts = recfam.sort_values(["n_systems", "n_families"], ascending=False).head(42)
    x = np.arange(len(counts))
    ax_reuse.scatter(x, counts["n_systems"], s=26 + 34 * counts["n_families"],
                     c=[ACCENT if n > 1 else MUTED for n in counts["n_families"]],
                     edgecolor="white", lw=0.4)
    ax_reuse.set_xticks(x, counts["receptor_gene"].fillna("NA"), rotation=75, ha="right", fontsize=5.8)
    ax_reuse.set_ylabel("systems per receptor")
    ax_reuse.set_title("Dense receptor-level sampling supports benchmarking and reuse")
    ax_reuse.grid(axis="y", color=PALE, lw=0.4)
    ax_reuse.text(0.99, 0.92, "bubble size = number of G-family contexts", transform=ax_reuse.transAxes,
                  ha="right", fontsize=7, color=MUTED)
    panel(ax_reuse, "D")

    # E: clean vs held-back transparency.
    reason = s2["hold_reason"].fillna("").map(lambda x: "nonstandard length" if "nonstandard" in x.lower()
                                               else "missing/incomplete files")
    h = reason.value_counts()
    ax_hold.bar(["included", "held back"], [len(s1), len(s2)], color=[FAM_COL["Gi"], WARN], edgecolor="white")
    ax_hold.set_title("Release boundary")
    ax_hold.set_ylabel("systems")
    ax_hold.text(0, len(s1) + 3, f"{len(s1)} clean", ha="center", fontweight="bold")
    ax_hold.text(1, len(s2) + 3, f"{len(s2)} held", ha="center", fontweight="bold")
    ypos = 0.72
    for key, val in h.items():
        ax_hold.text(0.55, ypos, f"{val} {key}", transform=ax_hold.transAxes, fontsize=7, color=MUTED)
        ypos -= 0.08
    panel(ax_hold, "E")

    fig.suptitle("Figure 5 candidate: GPCR community and drug-target landscape", x=0.02, ha="left",
                 fontsize=12, fontweight="bold")
    save(fig, "scidata_figure5_community_landscape")


def load_consensus(name: str) -> dict:
    return read_json(API / "consensus" / name)


def fig6_pocket_atlas(d: dict[str, pd.DataFrame]) -> None:
    drug = load_consensus("pockets_druggable.json")["clusters"]
    ortho = load_consensus("pockets_orthosteric.json")["clusters"]
    nom = load_consensus("druggable_nominations.json")["nominations"]
    t4a = d["t4a"].copy()

    rows = []
    for cl in drug:
        zone = max(cl.get("zones", {"other": 1}), key=cl.get("zones", {"other": 1}).get)
        rows.append({
            "cid": cl["consensus_id"],
            "n_receptors": cl.get("n_receptors", 0),
            "n_systems": cl.get("n_systems", 0),
            "mean_freq": cl.get("mean_freq", np.nan),
            "n_voxels": cl.get("n_voxels", np.nan),
            "zone": zone,
            "n_core": len(cl.get("core_generic_numbers", [])),
        })
    df = pd.DataFrame(rows)

    fig = plt.figure(figsize=(10.8, 7.2))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.2, 1.0, 1.1], wspace=0.36, hspace=0.42)
    ax_sc = fig.add_subplot(gs[:, 0])
    ax_zone = fig.add_subplot(gs[0, 1])
    ax_gn = fig.add_subplot(gs[0, 2])
    ax_rec = fig.add_subplot(gs[1, 1])
    ax_nom = fig.add_subplot(gs[1, 2])

    for zone, sub in df.groupby("zone"):
        ax_sc.scatter(sub["n_receptors"], sub["mean_freq"],
                      s=18 + 0.10 * sub["n_voxels"].fillna(0),
                      color=ZONE_COL.get(zone, MUTED), alpha=0.78, edgecolor="white", lw=0.35, label=zone)
    ax_sc.set_xlabel("receptors represented by cluster")
    ax_sc.set_ylabel("mean pocket occupancy")
    ax_sc.set_title("Consensus druggable pocket clusters")
    ax_sc.set_ylim(0.45, 1.02)
    ax_sc.grid(color=PALE, lw=0.4)
    ax_sc.legend(frameon=False, loc="lower right", fontsize=6)
    panel(ax_sc, "A")

    zone_counts = Counter()
    for cl in drug:
        for z, n in cl.get("zones", {}).items():
            zone_counts[z] += n
    zitems = sorted(zone_counts.items(), key=lambda kv: kv[1], reverse=True)
    ax_zone.barh([z for z, _ in zitems][::-1], [v for _, v in zitems][::-1],
                 color=[ZONE_COL.get(z, MUTED) for z, _ in zitems][::-1])
    ax_zone.set_xlabel("cluster members")
    ax_zone.set_title("Pocket zones")
    panel(ax_zone, "B")

    gn = Counter()
    for cl in drug + ortho:
        gn.update(cl.get("core_generic_numbers", [])[:12])
    top_gn = gn.most_common(18)[::-1]
    ax_gn.barh([k for k, _ in top_gn], [v for _, v in top_gn], color=ACCENT)
    ax_gn.set_xlabel("clusters")
    ax_gn.set_title("Reusable GPCRdb-position anchors")
    panel(ax_gn, "C")

    rec = t4a[t4a["subset"] != "All clean-v1"].copy()
    rec["family"] = rec["subset"].replace({"Gi/o": "Gi", "Gq/11": "Gq", "G12/13": "G12-13"})
    ax_rec.bar(rec["family"], rec["recovery_rate_percent"], color=[FAM_COL.get(f, MUTED) for f in rec["family"]])
    ax_rec.set_ylim(0, 100)
    ax_rec.set_ylabel("orthosteric recovery (%)")
    ax_rec.set_title("Binding-site validation")
    for x, row in enumerate(rec.itertuples()):
        ax_rec.text(x, row.recovery_rate_percent + 2, f"{row.orthosteric_recovered}/{row.systems_with_pockets}",
                    ha="center", fontsize=7)
    panel(ax_rec, "D")

    nom_df = pd.DataFrame(nom).sort_values("drug_proxy", ascending=False).head(9).iloc[::-1]
    ax_nom.barh(nom_df["cid"].astype(str), nom_df["drug_proxy"], color=[ZONE_COL.get(z, MUTED) for z in nom_df["zone"]])
    ax_nom.set_xlabel("proxy score")
    ax_nom.set_ylabel("cluster id")
    ax_nom.set_title("Drug-design nomination examples")
    for y, (_, row) in enumerate(nom_df.iterrows()):
        txt = str(row.get("example_receptors", "")).split(",")[0]
        ax_nom.text(row["drug_proxy"] + 0.1, y, txt[:16], va="center", fontsize=6.4, color=MUTED)
    panel(ax_nom, "E")

    fig.suptitle("Figure 6 candidate: drug-design pocket atlas", x=0.02, ha="left",
                 fontsize=12, fontweight="bold")
    save(fig, "scidata_figure6_drug_design_pocket_atlas")


def fig7_gateway_atlas(d: dict[str, pd.DataFrame]) -> None:
    cons = pd.DataFrame(load_consensus("gateways.json")["records"])
    s5 = d["s5"].copy()
    open_cols = [c for c in s5.columns if c.endswith("open_fraction")]
    pairs = [c.replace(" open_fraction", "") for c in open_cols]

    fam_hm = cons[(cons["metric"] == "open_fraction") & (cons["group"].isin(FAM_ORDER))]
    mat = fam_hm.pivot(index="group", columns="pair", values="mean").reindex(FAM_ORDER).reindex(columns=pairs)

    fig = plt.figure(figsize=(10.8, 7.0))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.1, 1.25, 1.1], wspace=0.38, hspace=0.40)
    ax_rad = fig.add_subplot(gs[:, 0])
    ax_hm = fig.add_subplot(gs[:, 1])
    ax_dist = fig.add_subplot(gs[0, 2])
    ax_rep = fig.add_subplot(gs[1, 2])

    # A: radial receptor-gateway glyph, ALL mean.
    all_df = cons[(cons["metric"] == "open_fraction") & (cons["group"] == "ALL")].set_index("pair")
    ax_rad.set_aspect("equal")
    ax_rad.axis("off")
    n = 7
    angles = np.linspace(np.pi / 2, np.pi / 2 - 2 * np.pi, n, endpoint=False)
    tm_xy = np.column_stack([np.cos(angles), np.sin(angles)])
    for i, (x, y) in enumerate(tm_xy, 1):
        ax_rad.add_patch(Circle((x, y), 0.12, facecolor="white", edgecolor=INK, lw=0.7))
        ax_rad.text(x, y, f"TM{i}", ha="center", va="center", fontsize=7, fontweight="bold")
    for pair in pairs:
        i, j = [int(tok.replace("TM", "")) - 1 for tok in pair.split("-")]
        val = float(all_df.loc[pair, "mean"]) if pair in all_df.index else 0
        x0, y0 = tm_xy[i]
        x1, y1 = tm_xy[j]
        ax_rad.plot([x0, x1], [y0, y1], color=ACCENT, lw=0.5 + 8 * val, alpha=0.78)
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        ax_rad.text(xm * 1.08, ym * 1.08, f"{val:.2f}", ha="center", va="center", fontsize=6.3)
    ax_rad.set_xlim(-1.45, 1.45)
    ax_rad.set_ylim(-1.35, 1.35)
    ax_rad.set_title("Global TM-gateway openness")
    panel(ax_rad, "A", x=-0.02)

    im = ax_hm.imshow(mat.values, cmap="viridis", vmin=0, vmax=max(0.65, np.nanmax(mat.values)))
    ax_hm.set_yticks(range(len(mat.index)), mat.index)
    ax_hm.set_xticks(range(len(mat.columns)), mat.columns, rotation=55, ha="right")
    ax_hm.set_title("Family-resolved open fraction")
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            if np.isfinite(mat.iloc[i, j]):
                ax_hm.text(j, i, f"{mat.iloc[i, j]:.2f}", ha="center", va="center", fontsize=6,
                           color="white" if mat.iloc[i, j] > 0.35 else INK)
    fig.colorbar(im, ax=ax_hm, fraction=0.046, pad=0.02)
    panel(ax_hm, "B")

    vals = s5[open_cols].to_numpy().ravel()
    vals = vals[np.isfinite(vals)]
    ax_dist.hist(vals, bins=np.linspace(0, 1, 26), color=ACCENT, edgecolor="white", lw=0.4)
    ax_dist.set_xlabel("open fraction")
    ax_dist.set_ylabel("system x gateway")
    ax_dist.set_title("Per-system gateway distribution")
    panel(ax_dist, "C")

    # D: replicate spread from JSON gateway records.
    spreads = []
    for sid in d["s1"]["system_id"]:
        p = API / "systems" / sid / "gateways.json"
        if not p.exists():
            continue
        for rec in read_json(p).get("records", []):
            if rec.get("metric") == "open_fraction" and rec.get("replica_values"):
                spreads.append(max(rec["replica_values"]) - min(rec["replica_values"]))
    ax_rep.hist(spreads, bins=np.linspace(0, max(spreads) if spreads else 1, 24),
                color=FAM_COL["Gi"], edgecolor="white", lw=0.4)
    ax_rep.set_xlabel("max-min among replicas")
    ax_rep.set_ylabel("gateway metrics")
    ax_rep.set_title("Replica spread")
    panel(ax_rep, "D")

    fig.suptitle("Figure 7 candidate: TM-gateway atlas for membrane-accessible pockets", x=0.02,
                 ha="left", fontsize=12, fontweight="bold")
    save(fig, "scidata_figure7_gateway_atlas")


def aggregate_gprotein_metrics(s1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    clean_ids = set(s1["system_id"])
    for sid in clean_ids:
        p = API / "systems" / sid / "gprotein_metrics.json"
        if not p.exists():
            continue
        fam = clean_family(str(s1.loc[s1["system_id"] == sid, "g_protein_family"].iloc[0]))
        for pos in read_json(p).get("positions", []):
            rows.append({
                "system_id": sid,
                "family": fam,
                "segment": pos.get("cgn_segment"),
                "position": pos.get("cgn_position"),
                "flock": pos.get("flock_class"),
                "rmsf": pos.get("rmsf_mean"),
                "contact": pos.get("contact_persistence_mean"),
                "s2": pos.get("s2_mean"),
                "chi1": pos.get("chi1_entropy_mean"),
            })
    return pd.DataFrame(rows)


def fig8_gprotein_barcode(d: dict[str, pd.DataFrame]) -> None:
    gp = aggregate_gprotein_metrics(d["s1"])
    if gp.empty:
        print("  skipped Fig 8: no gprotein_metrics.json files found")
        return
    seg_order = [s for s in gp["segment"].dropna().drop_duplicates()]
    key_segments = [s for s in seg_order if s in {"G.HN", "G.hns1", "G.S1", "G.s1h1", "G.H1", "G.H5"}]
    if len(key_segments) < 4:
        key_segments = seg_order[:10]

    fig = plt.figure(figsize=(10.8, 7.0))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.2, 1.2, 1.0], wspace=0.40, hspace=0.42)
    ax_rmsf = fig.add_subplot(gs[0, 0])
    ax_contact = fig.add_subplot(gs[0, 1])
    ax_flock = fig.add_subplot(gs[0, 2])
    ax_s2 = fig.add_subplot(gs[1, :2])
    ax_cov = fig.add_subplot(gs[1, 2])

    def heat(metric, ax, title, cmap):
        piv = gp[gp["segment"].isin(key_segments)].pivot_table(index="family", columns="segment", values=metric,
                                                               aggfunc="mean").reindex(FAM_ORDER)
        piv = piv[[c for c in key_segments if c in piv.columns]]
        im = ax.imshow(piv.values, aspect="auto", cmap=cmap)
        ax.set_yticks(range(len(piv.index)), piv.index)
        ax.set_xticks(range(len(piv.columns)), piv.columns, rotation=45, ha="right")
        ax.set_title(title)
        for i in range(piv.shape[0]):
            for j in range(piv.shape[1]):
                if np.isfinite(piv.iloc[i, j]):
                    ax.text(j, i, f"{piv.iloc[i, j]:.2g}", ha="center", va="center", fontsize=6,
                            color="white" if piv.iloc[i, j] > np.nanmean(piv.values) else INK)
        return im

    im1 = heat("rmsf", ax_rmsf, "G-alpha mobility by CGN segment", "magma")
    fig.colorbar(im1, ax=ax_rmsf, fraction=0.046, pad=0.02, label="RMSF")
    panel(ax_rmsf, "A")

    im2 = heat("contact", ax_contact, "Receptor-contact persistence", "YlGnBu")
    fig.colorbar(im2, ax=ax_contact, fraction=0.046, pad=0.02, label="mean")
    panel(ax_contact, "B")

    flock_counts = gp.drop_duplicates(["family", "position"]).groupby(["family", "flock"]).size().unstack(fill_value=0).reindex(FAM_ORDER)
    left = np.zeros(len(flock_counts))
    flock_cols = {"conserved": ACCENT, "selectivity-determining": WARN, "paralog-specific": MUTED, "neutral": PALE}
    for fl in flock_counts.columns:
        ax_flock.barh(flock_counts.index, flock_counts[fl], left=left, label=fl, color=flock_cols.get(fl, PALE),
                      edgecolor="white", lw=0.4)
        left += flock_counts[fl].values
    ax_flock.set_xlabel("CGN positions")
    ax_flock.set_title("Barcode annotation coverage")
    ax_flock.legend(frameon=False, fontsize=5.8, loc="upper center",
                    bbox_to_anchor=(0.50, -0.12), ncol=2, borderaxespad=0.0)
    panel(ax_flock, "C")

    s2 = gp.dropna(subset=["contact", "s2"])
    rng = np.random.default_rng(3)
    sample = s2.sample(min(3500, len(s2)), random_state=3) if len(s2) else s2
    ax_s2.scatter(sample["contact"], sample["s2"], s=6, alpha=0.20,
                  c=[FAM_COL.get(f, MUTED) for f in sample["family"]], edgecolors="none")
    ax_s2.set_xlabel("contact persistence")
    ax_s2.set_ylabel("side-chain order parameter proxy (S2)")
    ax_s2.set_title("Per-position dynamic annotation layer")
    ax_s2.text(0.02, 0.92, f"{len(s2):,} position records with contact + S2", transform=ax_s2.transAxes,
               ha="left", color=MUTED, fontsize=7,
               bbox=dict(facecolor="white", edgecolor="none", alpha=0.80, pad=1.5))
    panel(ax_s2, "D")

    cov = gp.groupby("system_id")["position"].nunique()
    ax_cov.hist(cov, bins=24, color=ACCENT, edgecolor="white", lw=0.4)
    ax_cov.set_xlabel("CGN positions per system")
    ax_cov.set_ylabel("systems")
    ax_cov.set_title("Per-system metric coverage")
    ax_cov.axvline(cov.median(), color=INK, lw=1)
    ax_cov.text(cov.median(), ax_cov.get_ylim()[1] * 0.92, f"median {cov.median():.0f}", ha="right",
                va="top", fontsize=7)
    panel(ax_cov, "E")

    fig.suptitle("Figure 8 candidate: G-protein CGN barcode and dynamics annotation", x=0.02,
                 ha="left", fontsize=12, fontweight="bold")
    save(fig, "scidata_figure8_gprotein_barcode")


def fig9_partner_switching_reuse(d: dict[str, pd.DataFrame]) -> None:
    reorg = load_consensus("reorg_atlas.json")
    comp = pd.DataFrame(reorg["comparisons"])
    geom = pd.DataFrame(load_consensus("coupling_geometry.json")["records"])

    fig = plt.figure(figsize=(10.8, 7.0))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.15, 1.15, 1.05], wspace=0.38, hspace=0.42)
    ax_sc = fig.add_subplot(gs[:, 0])
    ax_bar = fig.add_subplot(gs[0, 1])
    ax_rank = fig.add_subplot(gs[1, 1])
    ax_flow = fig.add_subplot(gs[:, 2])

    comp["contrast"] = comp["contrast"].astype(str)
    ax_sc.scatter(comp["gateway_dist"], comp["dtilt"], s=40 + 28 * comp["n_portals"],
                  c=comp["jaccard"], cmap="viridis", edgecolor="white", lw=0.5)
    for _, row in comp.sort_values("dtilt", ascending=False).head(6).iterrows():
        ax_sc.text(row["gateway_dist"] + 0.002, row["dtilt"], row["receptor"], fontsize=6.3)
    ax_sc.set_xlabel("gateway-vector distance")
    ax_sc.set_ylabel("absolute alpha5 tilt difference")
    ax_sc.set_title("Partner-switching reuse comparisons")
    ax_sc.grid(color=PALE, lw=0.4)
    panel(ax_sc, "A")

    c = comp["contrast"].value_counts().sort_index()
    ax_bar.bar(c.index, c.values, color=ACCENT, edgecolor="white")
    ax_bar.set_ylabel("receptor comparisons")
    ax_bar.set_title("Multi-family receptor contrasts")
    panel(ax_bar, "B")

    if not geom.empty:
        metrics = ["f01_tilt", "f06_depth", "f04_sasa", "f02_hook"]
        means = geom.groupby("g_family")[metrics].mean().reindex(ordered_families(geom["g_family"]))
        z = (means - means.mean()) / means.std(ddof=0).replace(0, np.nan)
        im = ax_rank.imshow(z.values, cmap="coolwarm", vmin=-1.8, vmax=1.8, aspect="auto")
        ax_rank.set_yticks(range(len(z.index)), z.index)
        ax_rank.set_xticks(range(len(metrics)), ["tilt", "depth", "SASA", "hook"], rotation=35, ha="right")
        ax_rank.set_title("Coupling-geometry feature layer")
        fig.colorbar(im, ax=ax_rank, fraction=0.046, pad=0.02, label="z")
    panel(ax_rank, "C")

    ax_flow.axis("off")
    steps = [
        ("filter", "same receptor\nmultiple G families"),
        ("compare", "pocket sets\nand gateway vectors"),
        ("measure", "alpha5/coupling\ngeometry features"),
        ("reuse", "hypothesis-ready\nPaper 2 input"),
    ]
    ys = np.linspace(0.86, 0.16, len(steps))
    for i, ((title, text), y) in enumerate(zip(steps, ys)):
        box = FancyBboxPatch((0.10, y - 0.07), 0.80, 0.12, boxstyle="round,pad=0.012,rounding_size=0.018",
                             facecolor="white", edgecolor=ACCENT if i < 3 else WARN, lw=0.9,
                             transform=ax_flow.transAxes)
        ax_flow.add_patch(box)
        ax_flow.text(0.50, y + 0.017, title.upper(), ha="center", va="center",
                     transform=ax_flow.transAxes, fontsize=6.5, fontweight="bold", color=ACCENT if i < 3 else WARN)
        ax_flow.text(0.50, y - 0.025, text, ha="center", va="center", transform=ax_flow.transAxes, fontsize=7.2)
        if i < len(steps) - 1:
            ax_flow.add_patch(FancyArrowPatch((0.50, y - 0.08), (0.50, ys[i + 1] + 0.07),
                                              arrowstyle="-|>", mutation_scale=9, lw=0.8, color=MUTED,
                                              transform=ax_flow.transAxes))
    ax_flow.set_title("Usage-note workflow")
    panel(ax_flow, "D", x=0.02)

    fig.suptitle("Figure 9 candidate: partner-switching as a restrained reuse vignette", x=0.02,
                 ha="left", fontsize=12, fontweight="bold")
    save(fig, "scidata_figure9_partner_switching_reuse")


def fig10_portal_archive_coverage(d: dict[str, pd.DataFrame]) -> None:
    t7, s8, s9, s6, t6 = d["t7"], d["s8"], d["s9"], d["s6"], d["t6"]

    fig = plt.figure(figsize=(10.8, 7.0))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.05, 1.15, 1.15], wspace=0.38, hspace=0.42)
    ax_files = fig.add_subplot(gs[0, 0])
    ax_size = fig.add_subplot(gs[1, 0])
    ax_api = fig.add_subplot(gs[:, 1])
    ax_route = fig.add_subplot(gs[:, 2])

    short = t7.copy()
    short["label"] = short["record_type"].str.replace("api_", "", regex=False).str.replace("viz_", "viz ", regex=False)
    y = np.arange(len(short))[::-1]
    ax_files.barh(y, short["present"], color=FAM_COL["Gi"], label="present")
    ax_files.barh(y, short["missing"], left=short["present"], color=WARN, label="missing")
    ax_files.set_yticks(y, short["label"])
    ax_files.set_xlabel("systems")
    ax_files.set_title("Portal file availability")
    ax_files.legend(frameon=False, fontsize=6)
    panel(ax_files, "A")

    archive_bytes = float(s8["size_bytes"].sum())
    portal_bytes = float(s9["size_bytes"].sum())
    ax_size.barh(["production archive", "portal/API layer"],
                 np.log10([archive_bytes, portal_bytes]),
                 color=[ACCENT, WARN], edgecolor="white")
    ax_size.set_xlabel("total size (log10 bytes)")
    ax_size.set_title("Two-tier data product")
    ax_size.text(np.log10(archive_bytes), 0, f" {archive_bytes/1e12:.1f} TB", va="center", fontsize=7)
    ax_size.text(np.log10(portal_bytes), 1, f" {portal_bytes/1e9:.1f} GB", va="center", fontsize=7)
    panel(ax_size, "B")

    tags = s6["manuscript_use"].fillna("other").str.extract(r"(portal|download|open access|API|citation|account)", expand=False).fillna("API/data")
    tag_counts = tags.value_counts().sort_values()
    ax_api.barh(tag_counts.index, tag_counts.values, color=ACCENT, edgecolor="white")
    ax_api.set_xlabel("endpoints")
    ax_api.set_title("Documented REST surface")
    ax_api.text(0.98, 0.05, "www.coupledmd.cn/api/docs", transform=ax_api.transAxes,
                ha="right", color=MUTED, fontsize=7)
    panel(ax_api, "C")

    ax_route.axis("off")
    ax_route.set_title("Archive-first access model")
    nodes = [
        ("Stable archive", "DOI/accession\nfull trajectories\nchecksums", (0.50, 0.82), ACCENT),
        ("CoupledMD portal", "www.coupledmd.cn\nbrowse/filter/view", (0.50, 0.55), FAM_COL["Gi"]),
        ("Programmatic API", "JSON, NPZ,\nPDB/XTC routes", (0.25, 0.25), WARN),
        ("Reuse notebooks", "download + cite\nworkflow scripts", (0.75, 0.25), MUTED),
    ]
    for title, text, (x, y0), col in nodes:
        box = FancyBboxPatch((x - 0.18, y0 - 0.07), 0.36, 0.13, boxstyle="round,pad=0.014,rounding_size=0.018",
                             transform=ax_route.transAxes, facecolor="white", edgecolor=col, lw=1.0)
        ax_route.add_patch(box)
        ax_route.text(x, y0 + 0.026, title, ha="center", va="center", transform=ax_route.transAxes,
                      fontsize=7.2, fontweight="bold", color=col)
        ax_route.text(x, y0 - 0.026, text, ha="center", va="center", transform=ax_route.transAxes, fontsize=6.5)
    arrows = [((0.50, 0.75), (0.50, 0.63)), ((0.42, 0.49), (0.28, 0.33)), ((0.58, 0.49), (0.72, 0.33))]
    for start, end in arrows:
        ax_route.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=9, lw=0.8,
                                           color=MUTED, transform=ax_route.transAxes))
    notes = [
        f"{int(t6['checksums_present'].sum())} checksums computed",
        f"{int(t6['checksums_pending'].sum())} pending final archive/binary checksums",
        "open access; API key optional for higher-rate use",
    ]
    ax_route.text(0.5, 0.04, "\n".join(notes), transform=ax_route.transAxes,
                  ha="center", va="bottom", fontsize=7, color=MUTED)
    panel(ax_route, "D", x=0.02)

    fig.suptitle("Figure 10 candidate: portal, archive and server coverage", x=0.02,
                 ha="left", fontsize=12, fontweight="bold")
    save(fig, "scidata_figure10_portal_archive_coverage")


def main() -> None:
    d = load_tables()
    print("Generating additional Scientific Data figure candidates...")
    fig5_community_landscape(d)
    fig6_pocket_atlas(d)
    fig7_gateway_atlas(d)
    fig8_gprotein_barcode(d)
    fig9_partner_switching_reuse(d)
    fig10_portal_archive_coverage(d)
    print("Done.")


if __name__ == "__main__":
    main()
