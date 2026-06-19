#!/usr/bin/env python3
"""
P0: Freeze the cohort and produce data/systems_master.{csv,parquet}.

Reads the canonical inventory from ANALYSIS_SRC (read-only), applies the
force-field correction, derives trajectory_type / bilayer_status /
structural_provenance, records file existence and sizes, and writes the frozen
master table to data/ in the project root.

Usage:
    python3 scripts/p0_freeze_cohort.py [--checksum] [--dry-run]

Options:
    --checksum   Compute SHA-256 of every trajectory + topology file.
                 WARNING: ~23 GB per system x 222 = multi-TB read; expect 2+ hours.
    --dry-run    Print a summary without writing output files.

Environment (from .env or shell):
    ANALYSIS_SRC   Path to the read-only analysis directory (default: ../a relative to project root).
    DATA_ROOT      Project root (default: directory containing this script's parent).
"""

import argparse
import hashlib
import os
import sys
import time
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Allow overrides from environment (set in .env or shell).
ANALYSIS_SRC = Path(os.environ.get("ANALYSIS_SRC", PROJECT_ROOT.parent / "a"))
DATA_ROOT = Path(os.environ.get("DATA_ROOT", PROJECT_ROOT))

INVENTORY_PATH = ANALYSIS_SRC / "inventory_v3_extended.csv"
OUT_DIR = DATA_ROOT / "data"

# Force-field correction mapping.
# Key: current label in inventory. Value: corrected label for the master table.
FF_MAP = {
    "AMBER (FF unresolved — check mdout)": "CHARMM36 (chamber, AMBER pmemd)",
    # The 10 GROMACS TRR protein-only systems already say "CHARMM36" but need a
    # more specific label so the engine distinction is clear.
    "CHARMM36": "CHARMM36 (protein-only, GROMACS)",
    # Class-B systems from CHARMM-GUI: label is already correct, confirm only.
    "CHARMM36 (via AMBER CHARMM-GUI)": "CHARMM36 (via AMBER CHARMM-GUI)",
}

# Systems flagged as engineered constructs or identity-uncertain.
# Derived from cleanup_notes in the inventory; cross-checked manually.
ENGINEERED_SYSTEMS = {
    "Gi_6CMO",   # chimera construct (BRIL + Rhodopsin)
    "Gi_6D9H",   # chimera of CHRM4 and Adenosine receptor A1
    "Gi_7D77",
    "Gi_8IRU",   # DRD4 recovered from entity description
    "Gi_8ZQE",
    "Gq_7DWC",
    "Gq_7EZM",
    "Gq_7F6G",
    "Gq_8HCQ",
    "Gq_8HCX",
    "Gs_8I2G",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def sha256_file(path: Path, chunk_mb: int = 64) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_mb * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def file_info(path_str: str) -> dict:
    p = Path(path_str) if path_str and not pd.isna(path_str) else None
    if p is None or not p.exists():
        return {"exists": False, "size_bytes": None}
    return {"exists": True, "size_bytes": p.stat().st_size}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main(args):
    t0 = time.time()

    if not INVENTORY_PATH.exists():
        sys.exit(f"ERROR: inventory not found at {INVENTORY_PATH}")

    print(f"Reading inventory: {INVENTORY_PATH}")
    df = pd.read_csv(INVENTORY_PATH)
    print(f"  {len(df)} rows x {len(df.columns)} columns")

    # ------------------------------------------------------------------ #
    # 1. Force-field correction
    # ------------------------------------------------------------------ #
    orig_ff = df["force_field"].copy()
    df["force_field_orig"] = orig_ff  # keep original for audit

    unmapped = set(orig_ff.unique()) - set(FF_MAP)
    if unmapped:
        print(f"WARNING: unrecognized force_field values (will be left unchanged): {unmapped}")

    df["force_field"] = orig_ff.map(FF_MAP).fillna(orig_ff)

    ff_counts = df.groupby(["force_field_orig", "force_field"]).size().reset_index(name="n")
    print("\nForce-field correction summary:")
    for _, row in ff_counts.iterrows():
        arrow = " -> " if row["force_field_orig"] != row["force_field"] else " == "
        print(f"  {row['n']:3d}  {row['force_field_orig']!r}{arrow}{row['force_field']!r}")

    # ------------------------------------------------------------------ #
    # 2. Trajectory type and bilayer status
    # ------------------------------------------------------------------ #
    traj = df["trajectory_path"].fillna("")
    df["trajectory_type"] = traj.apply(
        lambda p: "protein_only" if p.endswith(".trr") else "membrane_embedded"
    )
    df["has_bilayer"] = df["trajectory_type"] == "membrane_embedded"

    print(f"\nTrajectory type: membrane_embedded={df['has_bilayer'].sum()}, "
          f"protein_only={(~df['has_bilayer']).sum()}")

    # ------------------------------------------------------------------ #
    # 3. Structural provenance
    # ------------------------------------------------------------------ #
    df["structural_provenance"] = df["system_id"].apply(
        lambda sid: "engineered_uncertain" if sid in ENGINEERED_SYSTEMS else "experimental"
    )
    n_eng = (df["structural_provenance"] == "engineered_uncertain").sum()
    print(f"Structural provenance: experimental={len(df)-n_eng}, engineered_uncertain={n_eng}")

    # ------------------------------------------------------------------ #
    # 4. File existence and sizes
    # ------------------------------------------------------------------ #
    print("\nChecking trajectory and topology file existence ...")
    traj_info = df["trajectory_path"].apply(file_info)
    topo_info = df["topology_path"].apply(file_info)

    df["traj_exists"] = [r["exists"] for r in traj_info]
    df["traj_size_bytes"] = [r["size_bytes"] for r in traj_info]
    df["topo_exists"] = [r["exists"] for r in topo_info]
    df["topo_size_bytes"] = [r["size_bytes"] for r in topo_info]

    n_traj_missing = (~df["traj_exists"]).sum()
    n_topo_missing = (~df["topo_exists"]).sum()
    total_traj_gb = df["traj_size_bytes"].dropna().sum() / 1e9
    total_topo_gb = df["topo_size_bytes"].dropna().sum() / 1e9
    print(f"  Trajectories: {df['traj_exists'].sum()} found, {n_traj_missing} missing, "
          f"{total_traj_gb:.1f} GB total")
    print(f"  Topologies:   {df['topo_exists'].sum()} found, {n_topo_missing} missing, "
          f"{total_topo_gb:.1f} GB total")

    # ------------------------------------------------------------------ #
    # 5. Optional SHA-256 checksums
    # ------------------------------------------------------------------ #
    if args.checksum:
        print(f"\nComputing SHA-256 checksums ({len(df)} traj + {len(df)} topo) ...")
        print("  This will read all trajectory data. Estimated time: 2-4 hours.")
        traj_sha = []
        topo_sha = []
        for i, row in df.iterrows():
            for col, lst in [("trajectory_path", traj_sha), ("topology_path", topo_sha)]:
                p = Path(row[col]) if row[col] and not pd.isna(row[col]) else None
                if p and p.exists():
                    lst.append(sha256_file(p))
                else:
                    lst.append(None)
            if (i + 1) % 10 == 0:
                print(f"  ... {i+1}/{len(df)}")
        df["traj_sha256"] = traj_sha
        df["topo_sha256"] = topo_sha
    else:
        df["traj_sha256"] = None
        df["topo_sha256"] = None

    # ------------------------------------------------------------------ #
    # 6. Add schema version
    # ------------------------------------------------------------------ #
    df["master_schema_version"] = "1.0"

    # ------------------------------------------------------------------ #
    # 7. Column order: put new cols right after existing ones
    # ------------------------------------------------------------------ #
    original_cols = list(pd.read_csv(INVENTORY_PATH, nrows=0).columns)
    new_cols = [
        "force_field_orig", "trajectory_type", "has_bilayer",
        "structural_provenance",
        "traj_exists", "traj_size_bytes", "traj_sha256",
        "topo_exists", "topo_size_bytes", "topo_sha256",
        "master_schema_version",
    ]
    df = df[original_cols + new_cols]

    # ------------------------------------------------------------------ #
    # 8. Emit output
    # ------------------------------------------------------------------ #
    if args.dry_run:
        print("\n[DRY RUN] Would write:")
        print(f"  {OUT_DIR}/systems_master.csv   ({len(df)} rows, {len(df.columns)} cols)")
        print(f"  {OUT_DIR}/systems_master.parquet")
        print("\nFirst 3 rows of key new columns:")
        print(df[["system_id", "force_field", "trajectory_type", "has_bilayer",
                   "structural_provenance", "traj_size_bytes"]].head(3).to_string())
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_out = OUT_DIR / "systems_master.csv"
    parquet_out = OUT_DIR / "systems_master.parquet"

    df.to_csv(csv_out, index=False)
    df.to_parquet(parquet_out, index=False)

    csv_mb = csv_out.stat().st_size / 1e6
    parquet_mb = parquet_out.stat().st_size / 1e6
    elapsed = time.time() - t0

    print(f"\nWrote:")
    print(f"  {csv_out}  ({csv_mb:.2f} MB)")
    print(f"  {parquet_out}  ({parquet_mb:.2f} MB)")
    print(f"\nDone in {elapsed:.1f}s")

    # Summary table
    print("\n=== FROZEN MASTER TABLE SUMMARY ===")
    print(f"Total systems: {len(df)}")
    print(f"\nForce field (corrected):")
    for ff, n in df["force_field"].value_counts().items():
        print(f"  {n:3d}  {ff}")
    print(f"\nTrajectory type:")
    for tt, n in df["trajectory_type"].value_counts().items():
        print(f"  {n:3d}  {tt}")
    print(f"\nG-protein family:")
    for fam, n in df["g_protein_family"].value_counts().items():
        print(f"  {n:3d}  {fam}")
    print(f"\nStructural provenance:")
    for prov, n in df["structural_provenance"].value_counts().items():
        print(f"  {n:3d}  {prov}")
    print(f"\nFile sizes (trajectory tier, sampled):")
    print(f"  Min: {df['traj_size_bytes'].min()/1e9:.2f} GB")
    print(f"  Max: {df['traj_size_bytes'].max()/1e9:.2f} GB")
    print(f"  Total: {df['traj_size_bytes'].sum()/1e9:.1f} GB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checksum", action="store_true",
                        help="Compute SHA-256 checksums (slow; 2+ hours)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing output files")
    main(parser.parse_args())
