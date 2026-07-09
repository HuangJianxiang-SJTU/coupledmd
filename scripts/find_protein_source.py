#!/usr/bin/env python3
"""
Locate the pre-extracted protein-only source for a viz system.

The viz tier (scripts/p5_build_viz_tier.py) was built from the PRE-EXTRACTED
protein-only database at /MDdata/data04/gpcr_g_database/<sub>/<pdb>/, which has
  protein.pdb   (protein+ligand, atom-order identical to data/viz/<sys>/structure.pdb)
  traj1.nc      (protein-only, full-resolution, 10001 frames @ 50 ps)
NOT the raw solvated runs in systems_master.csv.trajectory_path (those have
water/ions and a different atom count and will silently corrupt the overlay).

Usage:
    python3 scripts/find_protein_source.py <system_id> [<system_id> ...]
    python3 scripts/find_protein_source.py --all-broken
Prints: <system_id> <protein_pdb> <traj1.nc> [frames]   (or MISSING)
"""
import argparse
import csv
import os
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_DB = Path("/MDdata/data04/gpcr_g_database")
MASTER = PROJECT_ROOT / "data" / "systems_master.csv"
AUDIT_CSV = PROJECT_ROOT / "scripts" / "audit_output" / "VIZ_PBC_FULL_AUDIT.csv"

# family -> candidate subdirs (searched in order), mirrors p5_build_viz_tier.FAM_DIRS
FAM_DIRS = {
    "G12-13": ["a/a_g12", "b/b2_g12"],
    "Gi":     ["a/a_gi",  "b/b1_gi", "b/b2_gi"],
    "Gq":     ["a/a_gq",  "b/b1_gq", "b/b2_gq"],
    "Gs":     ["a/a_gs",  "b/b1_gs", "b/b2_gs"],
}


def find_source(system_id, df=None):
    """Return (protein_pdb, traj1_nc) or (None, None) if not found.

    Prefers a per-PDB subdir (<db>/<sub>/<pdb_id>/). The family-dir-level
    fallback (files directly under <db>/<sub>/) is only used when NO per-PDB
    subdir exists in ANY candidate subdir — otherwise stray sibling files in
    the family dir get mis-attributed (e.g. b/b1_gq/protein.pdb belongs to
    7TRY, not 7YDM).
    """
    if df is None:
        df = pd.read_csv(MASTER).set_index("system_id")
    if system_id not in df.index:
        return None, None
    row = df.loc[system_id]
    pdb_id = str(row["pdb_id"])
    fam = str(row["g_protein_family"])
    subs = FAM_DIRS.get(fam, [])
    # 1. per-PDB subdir in any candidate
    for sub in subs:
        d = EXTRACTED_DB / sub / pdb_id
        pp = d / "protein.pdb"
        for tname in ("traj1.nc", "traj2.nc", "traj3.nc"):
            tp = d / tname
            if pp.is_file() and tp.is_file():
                return str(pp), str(tp)
    # 2. family-dir-level fallback ONLY if no per-PDB subdir exists anywhere
    if not any((EXTRACTED_DB / sub / pdb_id).is_dir() for sub in subs):
        for sub in subs:
            pp = EXTRACTED_DB / sub / "protein.pdb"
            for tname in ("traj1.nc", "traj2.nc", "traj3.nc"):
                tp = EXTRACTED_DB / sub / tname
                if pp.is_file() and tp.is_file():
                    return str(pp), str(tp)
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("systems", nargs="*")
    ap.add_argument("--all-broken", action="store_true", help="resolve every BROKEN/BROKEN_NGL system in the audit CSV")
    ap.add_argument("--verify", action="store_true", help="load with MDAnalysis to confirm atom count/order matches viz PDB")
    args = ap.parse_args()

    if args.all_broken:
        rows = list(csv.DictReader(open(AUDIT_CSV)))
        systems = [r["system_id"] for r in rows if r["status"] in ("BROKEN", "BROKEN_NGL")]
    else:
        systems = args.systems
    if not systems:
        ap.error("give system_ids or --all-broken")

    df = pd.read_csv(MASTER).set_index("system_id")
    missing = []
    for sid in systems:
        pp, tp = find_source(sid, df)
        if not pp:
            print(f"{sid:12s} MISSING (family={df.loc[sid,'g_protein_family'] if sid in df.index else '?'}, pdb={df.loc[sid,'pdb_id'] if sid in df.index else '?'})")
            missing.append(sid)
            continue
        extra = ""
        if args.verify:
            import warnings; warnings.filterwarnings("ignore")
            import MDAnalysis as mda
            us = mda.Universe(pp, tp)
            uv = mda.Universe(str(PROJECT_ROOT / "data" / "viz" / sid / "structure.pdb"))
            ok = (us.atoms.n_atoms == uv.atoms.n_atoms and (us.atoms.names == uv.atoms.names).all())
            extra = f" atoms={us.atoms.n_atoms} frames={len(us.trajectory)} order_ok={ok}"
        print(f"{sid:12s} {pp}  {tp}{extra}")
    if missing:
        print(f"\n{len(missing)} MISSING: {missing}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
