#!/usr/bin/env python3
"""
P2: Serialize the precomputed analysis layer to stable, versioned API-ready files.

Reads from ANALYSIS_SRC (read-only) and systems_master.csv, then writes
structured JSON under data/api/v1/. Repackages existing JSON/CSV products;
does NOT recompute any analysis.

Output layout:
    data/api/v1/
        index.json                     master index with counts and coverage
        consensus/
            pockets_druggable.json     consensus druggable pockets + back-links
            pockets_orthosteric.json   consensus orthosteric pockets + back-links
            gateways.json              gateway atlas summary by pair/family/metric
            druggable_nominations.json druggable pocket nominations + caveats
            reorg_atlas.json           within-receptor reorganization table
            reorg_pockets.json         per-pocket reorganization (signed, by receptor)
        systems/
            {system_id}/
                pockets.json           per-system called pockets
                pockets_gpcrdb.json    pockets mapped to GPCRdb generics + zone
                gateways.json          gateway metrics (membrane_embedded only)

Usage:
    python3 scripts/p2_serialize.py [--dry-run] [--system SYSTEM_ID]

Options:
    --dry-run       Print coverage counts without writing files.
    --system SID    Process only one system (for testing).

Environment:
    ANALYSIS_SRC   Path to read-only analysis directory.
    DATA_ROOT      Project root.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

ANALYSIS_SRC = Path(os.environ.get("ANALYSIS_SRC", PROJECT_ROOT.parent / "a"))
DATA_ROOT = Path(os.environ.get("DATA_ROOT", PROJECT_ROOT))

MASTER_CSV = DATA_ROOT / "data" / "systems_master.csv"
API_OUT = DATA_ROOT / "data" / "api" / "v1"

POCKETS_ATLAS = ANALYSIS_SRC / "paper1_pockets" / "atlas"
GATEWAYS_ATLAS = ANALYSIS_SRC / "paper1_gateways" / "atlas"
POCKETS_DIR = ANALYSIS_SRC / "paper1_pockets"
GATEWAYS_DIR = ANALYSIS_SRC / "paper1_gateways"
SI_DIR = ANALYSIS_SRC / "paper1_si"

SCHEMA_VERSION = "1.0"
GENERATED_AT = datetime.now(timezone.utc).isoformat()

# Caveats appended to druggable nomination outputs (required by P2 spec).
DRUGGABILITY_CAVEATS = (
    "Druggability scores are proxy metrics derived from pocket size, occupancy, "
    "and lining composition, not experimentally validated druggability. "
    "Family selectivity status reflects differential pocket occupancy across "
    "G-protein families in this dataset and does not constitute a binding or "
    "modulation claim."
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def read_json(path: Path) -> dict | list:
    with open(path) as f:
        return json.load(f)


def write_json(path: Path, data, indent: int = 2):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(clean_nans(data), f, indent=indent, allow_nan=False)


def file_size(path: Path) -> int | None:
    return path.stat().st_size if path.exists() else None


def nan_safe(val):
    if isinstance(val, float) and (val != val):  # NaN
        return None
    return val


def clean_nans(obj):
    """Recursively replace NaN floats with None so JSON serialization doesn't fail."""
    if isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nans(v) for v in obj]
    if isinstance(obj, float) and obj != obj:  # NaN check
        return None
    return obj


# --------------------------------------------------------------------------- #
# Per-system serialization
# --------------------------------------------------------------------------- #

def serialize_system(sid: str, meta: dict, dry_run: bool) -> dict:
    """
    Package per-system pocket and gateway files.
    Returns a coverage dict for the master index.
    """
    out_dir = API_OUT / "systems" / sid
    coverage = {"system_id": sid, "has_pockets": False, "has_pockets_gpcrdb": False,
                 "has_gateways": False}

    # pockets.json
    src_pockets = POCKETS_ATLAS / f"{sid}_pockets.json"
    if src_pockets.exists():
        if not dry_run:
            data = read_json(src_pockets)
            data["_schema_version"] = SCHEMA_VERSION
            write_json(out_dir / "pockets.json", data)
        coverage["has_pockets"] = True

    # pockets_gpcrdb.json
    src_gpcrdb = POCKETS_ATLAS / f"{sid}_pockets_gpcrdb.json"
    if src_gpcrdb.exists():
        if not dry_run:
            data = read_json(src_gpcrdb)
            data["_schema_version"] = SCHEMA_VERSION
            write_json(out_dir / "pockets_gpcrdb.json", data)
        coverage["has_pockets_gpcrdb"] = True

    # gateways.json — only for membrane_embedded systems
    if meta.get("trajectory_type") == "membrane_embedded":
        src_gw = GATEWAYS_ATLAS / f"{sid}_gateways.json"
        if src_gw.exists():
            if not dry_run:
                data = read_json(src_gw)
                # data is a list of records; wrap with metadata
                wrapped = {
                    "_schema_version": SCHEMA_VERSION,
                    "system_id": sid,
                    "records": data,
                }
                write_json(out_dir / "gateways.json", wrapped)
            coverage["has_gateways"] = True

    # per-system index.json — metadata + analysis file pointers
    if not dry_run:
        index = {
            "_schema_version": SCHEMA_VERSION,
            "_generated_at": GENERATED_AT,
            "system_id": sid,
            "metadata": meta,
            "analysis_files": {
                "pockets": f"systems/{sid}/pockets.json" if coverage["has_pockets"] else None,
                "pockets_gpcrdb": f"systems/{sid}/pockets_gpcrdb.json" if coverage["has_pockets_gpcrdb"] else None,
                "gateways": f"systems/{sid}/gateways.json" if coverage["has_gateways"] else None,
            },
            "notes": {
                "pocketgrid_npz": f"systems/{sid}/pocketgrid.npz (not serialized to JSON; "
                                   "served as binary from ANALYSIS_SRC)",
                "alpha5_geometry": "No per-system alpha5 geometry files in analysis layer. "
                                   "Summary-level alpha5-reorganization correlations are in "
                                   "consensus/reorg_atlas.json.",
            },
        }
        write_json(out_dir / "index.json", index)

    return coverage


# --------------------------------------------------------------------------- #
# Consensus-level serialization
# --------------------------------------------------------------------------- #

def serialize_consensus(dry_run: bool) -> dict:
    sizes = {}

    # consensus_druggable
    src = POCKETS_DIR / "consensus_druggable.json"
    if src.exists():
        if not dry_run:
            data = read_json(src)
            out = {
                "_schema_version": SCHEMA_VERSION,
                "_generated_at": GENERATED_AT,
                "_source": "paper1_pockets/consensus_druggable.json",
                "n_clusters": len(data),
                "clusters": data,
            }
            p = API_OUT / "consensus" / "pockets_druggable.json"
            write_json(p, out)
            sizes["pockets_druggable"] = file_size(p)

    # consensus_orthosteric
    src = POCKETS_DIR / "consensus_orthosteric.json"
    if src.exists():
        if not dry_run:
            data = read_json(src)
            out = {
                "_schema_version": SCHEMA_VERSION,
                "_generated_at": GENERATED_AT,
                "_source": "paper1_pockets/consensus_orthosteric.json",
                "n_clusters": len(data),
                "clusters": data,
            }
            p = API_OUT / "consensus" / "pockets_orthosteric.json"
            write_json(p, out)
            sizes["pockets_orthosteric"] = file_size(p)

    # gateway atlas summary
    src_csv = GATEWAYS_DIR / "gateway_atlas_summary.csv"
    if src_csv.exists():
        if not dry_run:
            df = pd.read_csv(src_csv)
            records = df.where(pd.notna(df), None).to_dict(orient="records")
            out = {
                "_schema_version": SCHEMA_VERSION,
                "_generated_at": GENERATED_AT,
                "_source": "paper1_gateways/gateway_atlas_summary.csv",
                "n_records": len(records),
                "columns": list(df.columns),
                "records": records,
            }
            p = API_OUT / "consensus" / "gateways.json"
            write_json(p, out)
            sizes["gateways"] = file_size(p)

    # druggable nominations (t6)
    src_nom = POCKETS_DIR / "t6_nomination_table.csv"
    src_held = POCKETS_DIR / "t6_heldout_recovery.csv"
    if src_nom.exists():
        if not dry_run:
            df_nom = pd.read_csv(src_nom)
            records = df_nom.where(pd.notna(df_nom), None).to_dict(orient="records")
            out = {
                "_schema_version": SCHEMA_VERSION,
                "_generated_at": GENERATED_AT,
                "_source": "paper1_pockets/t6_nomination_table.csv",
                "_caveat": DRUGGABILITY_CAVEATS,
                "n_nominations": len(records),
                "columns": list(df_nom.columns),
                "nominations": records,
            }
            if src_held.exists():
                df_held = pd.read_csv(src_held)
                out["heldout_recovery"] = {
                    "_source": "paper1_pockets/t6_heldout_recovery.csv",
                    "n_records": len(df_held),
                    "records": df_held.where(pd.notna(df_held), None).to_dict(orient="records"),
                }
            p = API_OUT / "consensus" / "druggable_nominations.json"
            write_json(p, out)
            sizes["druggable_nominations"] = file_size(p)

    # within-receptor reorganization
    src_reorg = POCKETS_DIR / "reorg_table.csv"
    src_signed = POCKETS_DIR / "reorg_pocket_signed.csv"
    if src_reorg.exists():
        if not dry_run:
            df_reorg = pd.read_csv(src_reorg)
            out = {
                "_schema_version": SCHEMA_VERSION,
                "_generated_at": GENERATED_AT,
                "_source": "paper1_pockets/reorg_table.csv",
                "n_comparisons": len(df_reorg),
                "columns": list(df_reorg.columns),
                "comparisons": df_reorg.where(pd.notna(df_reorg), None).to_dict(orient="records"),
            }
            if src_signed.exists():
                df_signed = pd.read_csv(src_signed)
                out["pocket_level"] = {
                    "_source": "paper1_pockets/reorg_pocket_signed.csv",
                    "n_records": len(df_signed),
                    "columns": list(df_signed.columns),
                    "records": df_signed.where(pd.notna(df_signed), None).to_dict(orient="records"),
                }
            # also include alpha5 correlation summary
            src_a5 = SI_DIR / "t8_alpha5_reorg_correlations.csv"
            if src_a5.exists():
                df_a5 = pd.read_csv(src_a5)
                out["alpha5_reorg_correlations"] = {
                    "_source": "paper1_si/t8_alpha5_reorg_correlations.csv",
                    "_note": "Summary-level Spearman correlations between alpha5 engagement "
                             "geometry and gateway/pocket reorganization. No per-system "
                             "alpha5 geometry files exist in the current analysis layer.",
                    "n_records": len(df_a5),
                    "records": df_a5.where(pd.notna(df_a5), None).to_dict(orient="records"),
                }
            p = API_OUT / "consensus" / "reorg_atlas.json"
            write_json(p, out)
            sizes["reorg_atlas"] = file_size(p)

    return sizes


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main(args):
    t0 = time.time()

    if not MASTER_CSV.exists():
        sys.exit(f"ERROR: systems_master.csv not found. Run p0 first.")

    df = pd.read_csv(MASTER_CSV)
    print(f"Loaded {len(df)} systems from {MASTER_CSV}")

    if args.system:
        sids = [args.system]
        df = df[df["system_id"].isin(sids)]
        if df.empty:
            sys.exit(f"ERROR: system_id '{args.system}' not found in master table.")
    else:
        sids = list(df["system_id"])

    # Build per-system metadata dicts (subset of master columns for the index).
    META_COLS = [
        "system_id", "pdb_id", "receptor_name", "receptor_uniprot", "receptor_gene",
        "g_protein_family", "g_alpha_subtype", "ligand_name", "ligand_chem_id",
        "n_replicas", "length_per_replica_ns", "total_sampling_ns",
        "force_field", "lipid_composition", "has_velocities", "has_forces",
        "trajectory_type", "has_bilayer", "structural_provenance",
        "traj_size_bytes", "topo_size_bytes", "master_schema_version",
    ]
    # Build meta dict per system, converting NaN to None.
    meta_by_sid = {}
    for _, row in df.iterrows():
        meta = {}
        for col in META_COLS:
            v = row.get(col, None)
            if isinstance(v, float) and pd.isna(v):
                meta[col] = None
            else:
                meta[col] = nan_safe(v)
            if isinstance(meta[col], bool):
                meta[col] = bool(meta[col])
        meta_by_sid[row["system_id"]] = meta

    if args.dry_run:
        print("\n[DRY RUN] Would serialize:")
        print(f"  {len(sids)} per-system directories under data/api/v1/systems/")
        # Count coverage
        n_pockets = sum(1 for s in sids if (POCKETS_ATLAS / f"{s}_pockets.json").exists())
        n_gpcrdb = sum(1 for s in sids if (POCKETS_ATLAS / f"{s}_pockets_gpcrdb.json").exists())
        n_gw = sum(1 for s in sids
                   if (GATEWAYS_ATLAS / f"{s}_gateways.json").exists()
                   and meta_by_sid.get(s, {}).get("trajectory_type") == "membrane_embedded")
        print(f"    pockets.json:          {n_pockets}/{len(sids)}")
        print(f"    pockets_gpcrdb.json:   {n_gpcrdb}/{len(sids)}")
        print(f"    gateways.json:         {n_gw}/{len(sids)}")
        print(f"\n  Consensus files under data/api/v1/consensus/:")
        for f in ["consensus_druggable.json", "consensus_orthosteric.json",
                  "gateway_atlas_summary.csv", "t6_nomination_table.csv", "reorg_table.csv"]:
            src = (POCKETS_DIR if "gateway" not in f else GATEWAYS_DIR) / f
            print(f"    {f}: {'exists' if src.exists() else 'MISSING'}")
        return

    # -- Consensus files --
    print("\nSerializing consensus files ...")
    consensus_sizes = serialize_consensus(dry_run=False)
    for name, sz in consensus_sizes.items():
        kb = sz / 1024 if sz else 0
        print(f"  consensus/{name}.json  {kb:.1f} KB")

    # -- Per-system files --
    print(f"\nSerializing {len(sids)} systems ...")
    coverage_rows = []
    for i, sid in enumerate(sids):
        meta = meta_by_sid.get(sid, {})
        row = serialize_system(sid, meta, dry_run=False)
        coverage_rows.append(row)
        if (i + 1) % 50 == 0:
            print(f"  ... {i+1}/{len(sids)}")

    # -- Master index --
    cov_df = pd.DataFrame(coverage_rows)
    index = {
        "_schema_version": SCHEMA_VERSION,
        "_generated_at": GENERATED_AT,
        "n_systems": len(sids),
        "coverage": {
            "has_pockets": int(cov_df["has_pockets"].sum()),
            "has_pockets_gpcrdb": int(cov_df["has_pockets_gpcrdb"].sum()),
            "has_gateways": int(cov_df["has_gateways"].sum()),
        },
        "systems": [
            {
                "system_id": r["system_id"],
                "has_pockets": r["has_pockets"],
                "has_pockets_gpcrdb": r["has_pockets_gpcrdb"],
                "has_gateways": r["has_gateways"],
            }
            for r in coverage_rows
        ],
        "consensus_files": [
            "consensus/pockets_druggable.json",
            "consensus/pockets_orthosteric.json",
            "consensus/gateways.json",
            "consensus/druggable_nominations.json",
            "consensus/reorg_atlas.json",
        ],
    }
    write_json(API_OUT / "index.json", index)

    elapsed = time.time() - t0

    # File size summary
    print(f"\n=== P2 SERIALIZATION SUMMARY ===")
    print(f"Output directory: {API_OUT}")
    print(f"\nCoverage (out of {len(sids)} systems):")
    print(f"  pockets.json:         {cov_df['has_pockets'].sum()}")
    print(f"  pockets_gpcrdb.json:  {cov_df['has_pockets_gpcrdb'].sum()}")
    print(f"  gateways.json:        {cov_df['has_gateways'].sum()}")

    # Disk usage
    import subprocess
    result = subprocess.run(["du", "-sh", str(API_OUT)], capture_output=True, text=True)
    print(f"\nTotal API output size: {result.stdout.strip()}")
    print(f"Done in {elapsed:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview coverage without writing files")
    parser.add_argument("--system", metavar="SYSTEM_ID",
                        help="Process only one system (for testing)")
    main(parser.parse_args())
