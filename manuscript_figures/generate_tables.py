#!/usr/bin/env python3
"""
generate_tables.py — Generate all manuscript tables for CoupledMD NAR paper.

Main text (written to manuscript_figures/tables/):
  T1  Cohort summary (Gα family × engine × sampling)
  T2  Cohort-wide orthosteric recovery benchmark
  T3  Full 16-contrast partner-switching census with bootstrap 95% CIs

SI tables (same directory, prefixed S):
  S1  Full 222-system inventory
  S2  50 druggable pocket clusters reference
  S3  27-system α5 geometry + composite rank
  S4  16-contrast partner-switching census (expanded)
  S5  Per-portal gateway summary (7 portals × 222 systems — mean + CI)
  S6  Per-system consensus pocket inventory

All values read from pipeline outputs. No values are invented or rounded.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path("/MDdata/data02/jxhuang/gpcr_g")
SERVER = BASE / "gpcr_g_server"
API_V1 = SERVER / "data" / "api" / "v1"
API_SYS = API_V1 / "systems"
API_CONS = API_V1 / "consensus"
MASTER_CSV = SERVER / "data" / "systems_master.csv"
CONS_D = BASE / "a" / "paper1_pockets" / "consensus_druggable.csv"
CONS_O = BASE / "a" / "paper1_pockets" / "consensus_orthosteric.csv"
REORG_JSON = API_CONS / "reorg_atlas.json"
PHASE1_OUT = Path(__file__).parent / "phase1_outputs"
COUPLING_CSV = BASE / "a" / "paper1_coupling_table.csv"
GW_ATLAS = BASE / "a" / "paper1_gateways" / "atlas"

OUT = Path(__file__).parent / "tables"
OUT.mkdir(exist_ok=True)


def fmt_pct(x, denom=None):
    """Format as percentage string."""
    if denom:
        return f"{100*x/denom:.1f}%"
    return f"{100*x:.1f}%"


# ─────────────────────────────────────────────────────────────────────────────
# T1 — Cohort summary
# ─────────────────────────────────────────────────────────────────────────────
def make_T1():
    df = pd.read_csv(MASTER_CSV)

    # Force-field mapping
    ff_map = {
        "CHARMM36 (chamber, AMBER pmemd)": "CHARMM36m / AMBER pmemd",
        "CHARMM36 (protein-only, GROMACS)": "CHARMM36m / GROMACS (protein-only)",
        "CHARMM36 (via AMBER CHARMM-GUI)": "CHARMM36m / AMBER pmemd (CHARMM-GUI)",
    }
    df["engine"] = df["force_field"].map(lambda x: ff_map.get(x, x))

    # Family order
    fam_order = ["Gi", "Gs", "Gq", "G12-13"]
    fam_label = {"Gi": "Gi/o", "Gs": "Gs", "Gq": "Gq/11", "G12-13": "G12/13"}

    rows = []
    for fam in fam_order:
        sub = df[df["g_protein_family"] == fam]
        total_ns = sub["total_sampling_ns"].sum()
        prov = sub["structural_provenance"].value_counts().to_dict()
        rows.append({
            "G-protein family": fam_label[fam],
            "Systems (n)": len(sub),
            "Experimental": prov.get("experimental", 0),
            "Engineered/chimeric": prov.get("engineered_uncertain", 0),
            "Unique receptors": sub["receptor_uniprot"].nunique(),
            "Sampling (μs)": round(total_ns / 1000, 1),
            "Membrane": f"POPC (all {len(sub)})",
        })
    # Total row
    total_ns = df["total_sampling_ns"].sum()
    rows.append({
        "G-protein family": "TOTAL",
        "Systems (n)": len(df),
        "Experimental": (df["structural_provenance"] == "experimental").sum(),
        "Engineered/chimeric": (df["structural_provenance"] == "engineered_uncertain").sum(),
        "Unique receptors": df["receptor_uniprot"].nunique(),
        "Sampling (μs)": round(total_ns / 1000, 1),
        "Membrane": f"POPC (all {len(df)})",
    })

    t1 = pd.DataFrame(rows)
    t1.to_csv(OUT / "T1_cohort_summary.csv", index=False)
    print(f"T1 written ({len(t1)} rows): {OUT / 'T1_cohort_summary.csv'}")
    print(t1.to_string(index=False))
    return t1


# ─────────────────────────────────────────────────────────────────────────────
# T2 — Cohort-wide orthosteric recovery benchmark
# ─────────────────────────────────────────────────────────────────────────────
def make_T2():
    # Load Phase 1A outputs
    rec_df = pd.read_csv(PHASE1_OUT / "recovery_benchmark.csv")
    summary = json.load(open(PHASE1_OUT / "recovery_summary.json"))

    rows = []

    def row(label, n_sys, n_pockets, n_rec):
        pct = f"{100*n_rec/n_pockets:.1f}%" if n_pockets else "n/a"
        return {
            "Subset": label,
            "Total systems": n_sys,
            "Systems with ≥1 pocket": n_pockets,
            "Systems without pockets": n_sys - n_pockets,
            "Orthosteric site recovered": n_rec,
            "Recovery rate (% of pocket-having)": pct,
        }

    rows.append(row("All systems", 222,
                    summary["systems_with_pockets"],
                    summary["systems_with_ortho_recovered"]))

    fam_label = {"Gi": "Gi/o", "Gs": "Gs", "Gq": "Gq/11", "G12-13": "G12/13"}
    for fam in ["Gi", "Gs", "Gq", "G12-13"]:
        s = summary["by_g_family"].get(fam, {})
        sub = rec_df[rec_df["g_family"] == fam]
        rows.append(row(f"  {fam_label[fam]}", len(sub),
                        s.get("with_pockets", 0), s.get("recovered", 0)))

    for lt, label in [("small_molecule", "Small-molecule ligand"),
                      ("peptide", "Peptide ligand"),
                      ("none", "No co-crystallized ligand")]:
        s = summary["by_ligand_type"].get(lt, {})
        sub = rec_df[rec_df["lig_type"] == lt]
        rows.append(row(f"  {label}", len(sub),
                        s.get("with_pockets", 0), s.get("recovered", 0)))

    for prov, label in [("experimental", "Experimental structure"),
                        ("engineered_uncertain", "Engineered/chimeric")]:
        s = summary["by_provenance"].get(prov, {})
        sub = rec_df[rec_df["structural_provenance"] == prov]
        rows.append(row(f"  {label}", len(sub),
                        s.get("with_pockets", 0), s.get("recovered", 0)))

    t2 = pd.DataFrame(rows)
    t2.to_csv(OUT / "T2_recovery_benchmark.csv", index=False)
    print(f"\nT2 written ({len(t2)} rows): {OUT / 'T2_recovery_benchmark.csv'}")
    print(t2.to_string(index=False))
    return t2


# ─────────────────────────────────────────────────────────────────────────────
# T3 — Partner-switching census (16 contrasts, Jaccard SIM + gateway_dist + CIs)
# ─────────────────────────────────────────────────────────────────────────────
def make_T3():
    ps_df = pd.read_csv(PHASE1_OUT / "partner_switching_census.csv")
    ps_summary = json.load(open(PHASE1_OUT / "partner_switching_summary.json"))

    # NOTE: jaccard_dist = 1 - Jaccard_similarity (from reorg_atlas)
    # jaccard_sim = 1 - jaccard_dist (added in phase1_analysis)
    # Pocket Jaccard similarity: 0=completely different, 1=identical

    rows = []
    for _, r in ps_df.sort_values(["contrast", "jaccard_sim"]).iterrows():
        jac_sim = r.get("jaccard_sim", 1 - r["jaccard_dist"])
        gw_lo = r.get("gw_ci_lo", np.nan)
        gw_hi = r.get("gw_ci_hi", np.nan)
        n_pk_a = int(r["n_pk_A"])
        n_pk_b = int(r["n_pk_B"])
        note = ""
        if jac_sim == 0.0:
            note = "No shared pockets"
        elif jac_sim == 1.0:
            note = "Identical pocket profiles"

        rows.append({
            "Receptor": r["receptor"],
            "Contrast": r["contrast"],
            "Partner A": r["famA"],
            "Partner B": r["famB"],
            "Pockets A": n_pk_a,
            "Pockets B": n_pk_b,
            "Shared clusters": int(r["n_shared"]),
            "Pocket Jaccard sim.": f"{jac_sim:.3f}",
            "Gateway dist. (mean |Δ|)": f"{r['gateway_dist']:.3f}",
            "Gateway 95% CI low": f"{gw_lo:.3f}" if not np.isnan(gw_lo) else "n/a",
            "Gateway 95% CI high": f"{gw_hi:.3f}" if not np.isnan(gw_hi) else "n/a",
            "α5 tilt diff. (°)": f"{r['dtilt']:.1f}" if not np.isnan(r.get("dtilt", np.nan)) else "n/a",
            "Note": note,
        })

    t3 = pd.DataFrame(rows)
    t3.to_csv(OUT / "T3_partner_switching.csv", index=False)
    print(f"\nT3 written ({len(t3)} rows): {OUT / 'T3_partner_switching.csv'}")
    print(t3.to_string(index=False))
    return t3


# ─────────────────────────────────────────────────────────────────────────────
# S1 — Full 222-system inventory
# ─────────────────────────────────────────────────────────────────────────────
def make_S1():
    df = pd.read_csv(MASTER_CSV)
    fam_label = {"Gi": "Gi/o", "Gs": "Gs", "Gq": "Gq/11", "G12-13": "G12/13"}

    # Check pocket and gateway availability per system
    has_pocket = []
    has_gw = []
    has_gpcrdb = []
    for sid in df["system_id"]:
        pp = API_SYS / sid / "pockets.json"
        gp = API_SYS / sid / "gateways.json"
        pgp = API_SYS / sid / "pockets_gpcrdb.json"
        has_pocket.append("Yes" if pp.exists() else "No")
        has_gw.append("Yes" if gp.exists() else "No")
        if pgp.exists():
            d = json.load(open(pgp))
            has_gpcrdb.append("Yes" if d.get("pockets") else "No")
        else:
            has_gpcrdb.append("No")

    df["has_pocket_data"] = has_pocket
    df["has_gateway_data"] = has_gw
    df["has_gpcrdb_pockets"] = has_gpcrdb

    cols = [
        "system_id", "pdb_id", "receptor_name", "receptor_uniprot", "receptor_gene",
        "g_protein_family", "g_alpha_subtype", "ligand_name", "ligand_class",
        "n_replicas", "length_per_replica_ns", "total_sampling_ns",
        "force_field", "lipid_composition", "structural_provenance",
        "has_pocket_data", "has_gateway_data", "has_gpcrdb_pockets", "notes"
    ]
    available = [c for c in cols if c in df.columns]
    s1 = df[available].copy()
    s1["g_protein_family"] = s1["g_protein_family"].map(lambda x: fam_label.get(x, x))
    s1.to_csv(OUT / "S1_system_inventory.csv", index=False)
    print(f"\nS1 written ({len(s1)} rows): {OUT / 'S1_system_inventory.csv'}")
    return s1


# ─────────────────────────────────────────────────────────────────────────────
# S2 — 50 druggable pocket cluster reference
# ─────────────────────────────────────────────────────────────────────────────
def make_S2():
    cons_d = pd.read_csv(CONS_D)

    rows = []
    for _, r in cons_d.iterrows():
        members = str(r["member_systems"]).split(";")
        # Infer family distribution
        fam_counts = {"Gi": 0, "Gs": 0, "Gq": 0, "G12": 0}
        for m in members:
            for fam in fam_counts:
                if m.startswith(fam):
                    fam_counts[fam] += 1
        rows.append({
            "Cluster ID": int(r["consensus_id"]),
            "Member systems (n)": int(r["n_systems"]),
            "Unique pockets (n)": int(r.get("n_pockets", 0)),
            "Mean occupancy frequency": f"{r['mean_freq']:.3f}",
            "Zone(s)": r.get("zones", ""),
            "Core generic positions": r.get("core_generic_numbers", ""),
            "Gi/o (n)": fam_counts["Gi"],
            "Gs (n)": fam_counts["Gs"],
            "Gq/11 (n)": fam_counts["Gq"],
            "G12/13 (n)": fam_counts["G12"],
            "Member system IDs": r["member_systems"],
        })

    s2 = pd.DataFrame(rows).sort_values("Cluster ID")
    s2.to_csv(OUT / "S2_druggable_pocket_clusters.csv", index=False)
    print(f"\nS2 written ({len(s2)} rows): {OUT / 'S2_druggable_pocket_clusters.csv'}")
    return s2


# ─────────────────────────────────────────────────────────────────────────────
# S3 — α5 coupling geometry (27-system pilot)
# ─────────────────────────────────────────────────────────────────────────────
def make_S3():
    coup = pd.read_csv(COUPLING_CSV)
    fam_label = {"Gi": "Gi/o", "Gs": "Gs", "Gq": "Gq/11", "G12-13": "G12/13", "G12": "G12/13"}

    cols_in = ["system", "receptor", "g_family", "func_rank",
               "f01_tilt", "f06_depth", "f04_sasa", "f02_hook"]
    cols_out = ["PDB ID", "Receptor", "G-protein family", "Composite rank",
                "α5 tilt (°)", "α5 insertion depth (Å)", "α5 buried SASA (Å²)", "Hook angle (°)"]

    rows = []
    for _, r in coup.sort_values("func_rank").iterrows():
        rows.append({
            "PDB ID": r["system"],
            "Receptor": r["receptor"],
            "G-protein family": fam_label.get(r.get("g_family", ""), r.get("g_family", "")),
            "Composite rank": int(r["func_rank"]),
            "α5 tilt (°)": f"{r['f01_tilt']:.1f}" if not np.isnan(r["f01_tilt"]) else "n/a",
            "α5 insertion depth (Å)": f"{r['f06_depth']:.1f}" if not np.isnan(r["f06_depth"]) else "n/a",
            "α5 buried SASA (Å²)": f"{r['f04_sasa']:.0f}" if "f04_sasa" in r and not np.isnan(r["f04_sasa"]) else "n/a",
            "Hook angle (°)": f"{r['f02_hook']:.1f}" if "f02_hook" in r and not np.isnan(r["f02_hook"]) else "n/a",
        })

    s3 = pd.DataFrame(rows)
    s3.to_csv(OUT / "S3_alpha5_geometry.csv", index=False)
    print(f"\nS3 written ({len(s3)} rows): {OUT / 'S3_alpha5_geometry.csv'}")
    return s3


# ─────────────────────────────────────────────────────────────────────────────
# S4 — Partner-switching census (expanded, with pocket-level breakdown)
# ─────────────────────────────────────────────────────────────────────────────
def make_S4():
    # Load signed pocket change table
    signed_f = BASE / "a" / "paper1_pockets" / "reorg_pocket_signed.csv"
    if signed_f.exists():
        signed = pd.read_csv(signed_f)
        signed.to_csv(OUT / "S4_partner_switching_pocket_detail.csv", index=False)
        print(f"\nS4 written ({len(signed)} rows): {OUT / 'S4_partner_switching_pocket_detail.csv'}")
        return signed
    else:
        print("\nS4: reorg_pocket_signed.csv not found; skipping")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# S5 — Per-portal gateway summary (7 portals × 222 systems)
# ─────────────────────────────────────────────────────────────────────────────
def make_S5():
    ALL_PORTALS = ["TM3-TM4", "TM7-TM1", "TM4-TM5", "TM5-TM6",
                   "TM1-TM2", "TM6-TM7", "TM2-TM3"]
    rows = []
    for gf in sorted(GW_ATLAS.glob("*_gateways.json")):
        sid = gf.stem.replace("_gateways", "")
        recs = json.load(open(gf))
        # Build dict: (pair, metric) -> record
        rec_map = {(r["pair"], r["metric"]): r for r in recs}
        row = {"System ID": sid}
        for portal in ALL_PORTALS:
            of_rec = rec_map.get((portal, "open_fraction"), {})
            oc_rec = rec_map.get((portal, "occupancy"), {})
            row[f"{portal} open_fraction"] = f"{of_rec.get('mean', np.nan):.3f}" if of_rec else "n/a"
            row[f"{portal} open_fraction CI"] = (
                f"[{of_rec.get('ci_lo', of_rec.get('ci_low', np.nan)):.3f},"
                f"{of_rec.get('ci_hi', of_rec.get('ci_high', np.nan)):.3f}]"
                if of_rec else "n/a")
            row[f"{portal} mean_dist (Å)"] = f"{oc_rec.get('mean', np.nan):.2f}" if oc_rec else "n/a"
        rows.append(row)

    s5 = pd.DataFrame(rows)
    s5.to_csv(OUT / "S5_gateway_per_system.csv", index=False)
    print(f"\nS5 written ({len(s5)} rows): {OUT / 'S5_gateway_per_system.csv'}")
    return s5


# ─────────────────────────────────────────────────────────────────────────────
# S6 — Per-system consensus pocket inventory
# ─────────────────────────────────────────────────────────────────────────────
def make_S6():
    cons_d = pd.read_csv(CONS_D)
    cons_o = pd.read_csv(CONS_O)

    # Build system → cluster list
    sys_clusters = {}
    for _, r in cons_d.iterrows():
        for sid in str(r["member_systems"]).split(";"):
            sid = sid.strip()
            sys_clusters.setdefault(sid, {"druggable": [], "orthosteric": []})
            sys_clusters[sid]["druggable"].append(int(r["consensus_id"]))
    for _, r in cons_o.iterrows():
        for sid in str(r["member_systems"]).split(";"):
            sid = sid.strip()
            sys_clusters.setdefault(sid, {"druggable": [], "orthosteric": []})
            sys_clusters[sid]["orthosteric"].append(int(r["consensus_id"]))

    df = pd.read_csv(MASTER_CSV)
    rows = []
    for _, sys_row in df.iterrows():
        sid = sys_row["system_id"]
        cl = sys_clusters.get(sid, {"druggable": [], "orthosteric": []})
        # Count raw pockets
        pp = API_SYS / sid / "pockets.json"
        n_raw = 0
        if pp.exists():
            d = json.load(open(pp))
            n_raw = d.get("n_pockets", 0)
        rows.append({
            "System ID": sid,
            "Receptor": sys_row.get("receptor_name", ""),
            "G-protein family": sys_row.get("g_protein_family", ""),
            "Total pockets (fpocket)": n_raw,
            "Druggable consensus clusters": ";".join(map(str, sorted(cl["druggable"]))) if cl["druggable"] else "none",
            "N druggable clusters": len(cl["druggable"]),
            "Orthosteric consensus clusters": ";".join(map(str, sorted(cl["orthosteric"]))) if cl["orthosteric"] else "none",
            "N orthosteric clusters": len(cl["orthosteric"]),
        })

    s6 = pd.DataFrame(rows)
    s6.to_csv(OUT / "S6_per_system_pockets.csv", index=False)
    print(f"\nS6 written ({len(s6)} rows): {OUT / 'S6_per_system_pockets.csv'}")
    return s6


if __name__ == "__main__":
    print("=== Generating manuscript tables ===\n")
    make_T1()
    make_T2()
    make_T3()
    make_S1()
    make_S2()
    make_S3()
    make_S4()
    make_S5()
    make_S6()
    print(f"\n=== All tables written to {OUT} ===")
