#!/usr/bin/env python3
"""
P2: Serialize the precomputed analysis layer to stable, versioned API-ready files.

Reads from ANALYSIS_SRC (read-only) and systems_master.csv, then writes
structured JSON under data/api/v1/. Repackages existing JSON/CSV products;
does NOT recompute any analysis.

Also registers every produced file in the SQLite database tables
system_pocket_files and system_gateway_files (created by p1_ingest.py).

Output layout:
    data/api/v1/
        index.json
        consensus/
            pockets_druggable.json
            pockets_orthosteric.json
            gateways.json
            druggable_nominations.json
            reorg_atlas.json
        systems/{sid}/
            index.json
            pockets.json
            pockets_gpcrdb.json
            pocketgrid.npz         (copied only with --copy-grids; else ANALYSIS_SRC symlinked)
            gateways.json          (membrane_embedded only)

Usage:
    python3 scripts/p2_serialize.py [--dry-run] [--system SYSTEM_ID] [--copy-grids]

Options:
    --dry-run       Print coverage counts without writing files.
    --system SID    Process only one system (for testing).
    --copy-grids    Copy pocketgrid.npz files (~7 MB each, ~1.5 GB total) into
                    data/api/v1/systems/ so the output is self-contained.
                    Default: register ANALYSIS_SRC path in the DB only.

Environment:
    ANALYSIS_SRC    Path to read-only analysis directory.
    DATA_ROOT       Project root.
    DATABASE_URL    SQLite connection string (default: sqlite:///db/coupledmd.sqlite).
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

ANALYSIS_SRC = Path(os.environ.get("ANALYSIS_SRC", PROJECT_ROOT.parent / "a"))
DATA_ROOT = Path(os.environ.get("DATA_ROOT", PROJECT_ROOT))
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_ROOT}/db/coupledmd.sqlite")

MASTER_CSV = DATA_ROOT / "data" / "systems_master.csv"
API_OUT = DATA_ROOT / "data" / "api" / "v1"

POCKETS_ATLAS = ANALYSIS_SRC / "paper1_pockets" / "atlas"
GATEWAYS_ATLAS = ANALYSIS_SRC / "paper1_gateways" / "atlas"
POCKETS_DIR = ANALYSIS_SRC / "paper1_pockets"
GATEWAYS_DIR = ANALYSIS_SRC / "paper1_gateways"
SI_DIR = ANALYSIS_SRC / "paper1_si"
STAGE3_DIR = ANALYSIS_SRC / "stage3_atlas" / "per_system_metrics"

SCHEMA_VERSION = "1.0"
GENERATED_AT = datetime.now(timezone.utc).isoformat()

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
    if isinstance(val, float) and (val != val):
        return None
    return val


def clean_nans(obj):
    if isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nans(v) for v in obj]
    if isinstance(obj, float) and obj != obj:
        return None
    return obj


def db_connect() -> sqlite3.Connection | None:
    if not DATABASE_URL.startswith("sqlite:///"):
        return None
    db_path = Path(DATABASE_URL.replace("sqlite:///", ""))
    if not db_path.is_absolute():
        db_path = DATA_ROOT / db_path
    if not db_path.exists():
        return None
    return sqlite3.connect(db_path)


def register_pocket_file(con: sqlite3.Connection, sid: str, file_type: str, path: Path):
    con.execute(
        "INSERT OR REPLACE INTO system_pocket_files "
        "(system_id, file_type, file_path, file_size_bytes) VALUES (?,?,?,?)",
        (sid, file_type, str(path), file_size(path)),
    )


def register_gateway_file(con: sqlite3.Connection, sid: str, file_type: str, path: Path):
    con.execute(
        "INSERT OR REPLACE INTO system_gateway_files "
        "(system_id, file_type, file_path, file_size_bytes) VALUES (?,?,?,?)",
        (sid, file_type, str(path), file_size(path)),
    )


# --------------------------------------------------------------------------- #
# Per-system serialization
# --------------------------------------------------------------------------- #

def serialize_system(sid: str, meta: dict, copy_grids: bool,
                     con: sqlite3.Connection | None) -> dict:
    out_dir = API_OUT / "systems" / sid
    coverage = {
        "system_id": sid,
        "has_pockets": False,
        "has_pockets_gpcrdb": False,
        "has_pocketgrid": False,
        "has_gateways": False,
    }

    # pockets.json
    src = POCKETS_ATLAS / f"{sid}_pockets.json"
    if src.exists():
        data = read_json(src)
        data["_schema_version"] = SCHEMA_VERSION
        dst = out_dir / "pockets.json"
        write_json(dst, data)
        coverage["has_pockets"] = True
        if con:
            register_pocket_file(con, sid, "pockets_json", dst)

    # pockets_gpcrdb.json
    src = POCKETS_ATLAS / f"{sid}_pockets_gpcrdb.json"
    if src.exists():
        data = read_json(src)
        data["_schema_version"] = SCHEMA_VERSION
        dst = out_dir / "pockets_gpcrdb.json"
        write_json(dst, data)
        coverage["has_pockets_gpcrdb"] = True
        if con:
            register_pocket_file(con, sid, "pockets_gpcrdb_json", dst)

    # pocketgrid.npz — copy or register ANALYSIS_SRC path
    src_grid = POCKETS_ATLAS / f"{sid}_pocketgrid.npz"
    if src_grid.exists():
        if copy_grids:
            dst_grid = out_dir / "pocketgrid.npz"
            dst_grid.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_grid, dst_grid)
            grid_path = dst_grid
        else:
            grid_path = src_grid  # register ANALYSIS_SRC path in DB; not copied
        coverage["has_pocketgrid"] = True
        if con:
            register_pocket_file(con, sid, "pocketgrid_npz", grid_path)

    # gateways.json — membrane_embedded only
    if meta.get("trajectory_type") == "membrane_embedded":
        src = GATEWAYS_ATLAS / f"{sid}_gateways.json"
        if src.exists():
            data = read_json(src)
            wrapped = {
                "_schema_version": SCHEMA_VERSION,
                "system_id": sid,
                "records": data,
            }
            dst = out_dir / "gateways.json"
            write_json(dst, wrapped)
            coverage["has_gateways"] = True
            if con:
                register_gateway_file(con, sid, "gateways_json", dst)

    # per-system index.json
    pocketgrid_note = (
        f"systems/{sid}/pocketgrid.npz" if copy_grids and coverage["has_pocketgrid"]
        else (str(POCKETS_ATLAS / f"{sid}_pocketgrid.npz")
              if coverage["has_pocketgrid"] else None)
    )
    index = {
        "_schema_version": SCHEMA_VERSION,
        "_generated_at": GENERATED_AT,
        "system_id": sid,
        "metadata": meta,
        "analysis_files": {
            "pockets": f"systems/{sid}/pockets.json" if coverage["has_pockets"] else None,
            "pockets_gpcrdb": f"systems/{sid}/pockets_gpcrdb.json" if coverage["has_pockets_gpcrdb"] else None,
            "pocketgrid_npz": pocketgrid_note,
            "gateways": f"systems/{sid}/gateways.json" if coverage["has_gateways"] else None,
        },
        "notes": {
            "alpha5_geometry": (
                "No per-system alpha5 geometry files in the analysis layer. "
                "Summary-level alpha5-reorganization correlations are in "
                "consensus/reorg_atlas.json."
            ),
        },
    }
    write_json(out_dir / "index.json", index)

    return coverage


# --------------------------------------------------------------------------- #
# Consensus-level serialization
# --------------------------------------------------------------------------- #

def serialize_consensus() -> dict:
    sizes = {}

    src = POCKETS_DIR / "consensus_druggable.json"
    if src.exists():
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

    src = POCKETS_DIR / "consensus_orthosteric.json"
    if src.exists():
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

    src_csv = GATEWAYS_DIR / "gateway_atlas_summary.csv"
    if src_csv.exists():
        df = pd.read_csv(src_csv)
        out = {
            "_schema_version": SCHEMA_VERSION,
            "_generated_at": GENERATED_AT,
            "_source": "paper1_gateways/gateway_atlas_summary.csv",
            "n_records": len(df),
            "columns": list(df.columns),
            "records": df.where(pd.notna(df), None).to_dict(orient="records"),
        }
        p = API_OUT / "consensus" / "gateways.json"
        write_json(p, out)
        sizes["gateways"] = file_size(p)

    src_nom = POCKETS_DIR / "t6_nomination_table.csv"
    if src_nom.exists():
        df_nom = pd.read_csv(src_nom)
        out = {
            "_schema_version": SCHEMA_VERSION,
            "_generated_at": GENERATED_AT,
            "_source": "paper1_pockets/t6_nomination_table.csv",
            "_caveat": DRUGGABILITY_CAVEATS,
            "n_nominations": len(df_nom),
            "columns": list(df_nom.columns),
            "nominations": df_nom.where(pd.notna(df_nom), None).to_dict(orient="records"),
        }
        src_held = POCKETS_DIR / "t6_heldout_recovery.csv"
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

    src_reorg = POCKETS_DIR / "reorg_table.csv"
    if src_reorg.exists():
        df_reorg = pd.read_csv(src_reorg)

        # Enrich with representative system IDs for each (uniprot, family) pair
        df_master = pd.read_csv(MASTER_CSV)
        # Build index: (uniprot, family) → first system_id by total_sampling_ns desc
        sys_idx = (
            df_master.sort_values("total_sampling_ns", ascending=False)
            .groupby(["receptor_uniprot", "g_protein_family"])["system_id"]
            .first()
            .to_dict()
        )

        comparisons = df_reorg.where(pd.notna(df_reorg), None).to_dict(orient="records")
        for c in comparisons:
            c["sid_A"] = sys_idx.get((c["uniprot"], c["famA"]))
            c["sid_B"] = sys_idx.get((c["uniprot"], c["famB"]))

        out = {
            "_schema_version": SCHEMA_VERSION,
            "_generated_at": GENERATED_AT,
            "_source": "paper1_pockets/reorg_table.csv",
            "n_comparisons": len(comparisons),
            "columns": list(df_reorg.columns) + ["sid_A", "sid_B"],
            "comparisons": comparisons,
        }
        src_signed = POCKETS_DIR / "reorg_pocket_signed.csv"
        if src_signed.exists():
            df_signed = pd.read_csv(src_signed)
            out["pocket_level"] = {
                "_source": "paper1_pockets/reorg_pocket_signed.csv",
                "n_records": len(df_signed),
                "columns": list(df_signed.columns),
                "records": df_signed.where(pd.notna(df_signed), None).to_dict(orient="records"),
            }
        src_a5 = SI_DIR / "t8_alpha5_reorg_correlations.csv"
        if src_a5.exists():
            df_a5 = pd.read_csv(src_a5)
            out["alpha5_reorg_correlations"] = {
                "_source": "paper1_si/t8_alpha5_reorg_correlations.csv",
                "_note": (
                    "Summary-level Spearman correlations between alpha5 engagement "
                    "geometry and gateway/pocket reorganization. No per-system "
                    "alpha5 geometry files exist in the current analysis layer."
                ),
                "n_records": len(df_a5),
                "records": df_a5.where(pd.notna(df_a5), None).to_dict(orient="records"),
            }
        p = API_OUT / "consensus" / "reorg_atlas.json"
        write_json(p, out)
        sizes["reorg_atlas"] = file_size(p)

    return sizes


# --------------------------------------------------------------------------- #
# G-protein interface metrics & coupling geometry
# --------------------------------------------------------------------------- #

def serialize_gprotein_metrics(df: pd.DataFrame, con: sqlite3.Connection | None,
                               dry_run: bool) -> dict:
    """Serialize G-protein coupling geometry, per-system metrics, and barcode reference."""
    sizes = {}
    sids = list(df["system_id"])

    # 1. Coupling geometry table → consensus/coupling_geometry.json
    src_coupling = ANALYSIS_SRC / "paper1_coupling_table.csv"
    if src_coupling.exists():
        df_coup = pd.read_csv(src_coupling)
        out = {
            "_schema_version": SCHEMA_VERSION,
            "_generated_at": GENERATED_AT,
            "_source": "paper1_coupling_table.csv",
            "n_records": len(df_coup),
            "records": df_coup.where(pd.notna(df_coup), None).to_dict(orient="records"),
        }
        p = API_OUT / "consensus" / "coupling_geometry.json"
        write_json(p, out)
        sizes["coupling_geometry"] = file_size(p)

    # 2. Per-system G-protein metrics → systems/{sid}/gprotein_metrics.json
    n_metrics = 0
    if not dry_run:
        for sid in sids:
            src_csv = STAGE3_DIR / f"{sid}.csv"
            if not src_csv.exists():
                continue
            df_sys = pd.read_csv(src_csv)

            position_cols = [
                "cgn_position", "cgn_segment", "flock_class",
                "sim_resid", "sim_resname",
                "rmsf_mean", "rmsf_ci_low", "rmsf_ci_high",
                "contact_persistence_mean", "contact_persistence_ci_low",
                "contact_persistence_ci_high",
                "chi1_entropy_mean", "s2_mean",
            ]

            # Map source column names → target column names
            col_map = {
                "cgn_position": "cgn_position",
                "cgn_segment": "cgn_segment",
                "flock_class": "flock_class",
                "sim_resid": "sim_resid",
                "sim_resname": "sim_resname",
                "rmsf_mean": "rmsf_mean",
                "replica_bootstrap_ci_low_rmsf": "rmsf_ci_low",
                "replica_bootstrap_ci_high_rmsf": "rmsf_ci_high",
                "contact_persistence_mean": "contact_persistence_mean",
                "replica_bootstrap_ci_low_cp": "contact_persistence_ci_low",
                "replica_bootstrap_ci_high_cp": "contact_persistence_ci_high",
                "chi1_entropy": "chi1_entropy_mean",
                "s2_mean": "s2_mean",
            }

            # Select and rename columns
            available_cols = [c for c in col_map if c in df_sys.columns]
            df_sel = df_sys[available_cols].rename(columns=col_map)

            # Build position records, replacing NaN with None
            positions = df_sel.where(pd.notna(df_sel), None).to_dict(orient="records")

            out = {
                "_schema_version": SCHEMA_VERSION,
                "system_id": sid,
                "n_positions": len(positions),
                "positions": positions,
            }
            p = API_OUT / "systems" / sid / "gprotein_metrics.json"
            write_json(p, out)
            n_metrics += 1

    sizes["gprotein_metrics_count"] = n_metrics

    # 3. Gα barcode reference → consensus/gprotein_barcode_reference.json
    src_barcode = ANALYSIS_SRC / "galpha_barcode_reference.csv"
    if src_barcode.exists():
        df_bc = pd.read_csv(src_barcode)
        out = {
            "_schema_version": SCHEMA_VERSION,
            "_generated_at": GENERATED_AT,
            "_source": "galpha_barcode_reference.csv",
            "n_records": len(df_bc),
            "records": df_bc.where(pd.notna(df_bc), None).to_dict(orient="records"),
        }
        p = API_OUT / "consensus" / "gprotein_barcode_reference.json"
        write_json(p, out)
        sizes["gprotein_barcode_reference"] = file_size(p)

    return sizes


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main(args):
    t0 = time.time()

    if not MASTER_CSV.exists():
        sys.exit("ERROR: systems_master.csv not found. Run p0_freeze_cohort.py first.")

    df = pd.read_csv(MASTER_CSV)
    print(f"Loaded {len(df)} systems from {MASTER_CSV}")

    if args.system:
        df = df[df["system_id"] == args.system]
        if df.empty:
            sys.exit(f"ERROR: system_id '{args.system}' not found.")
    sids = list(df["system_id"])

    META_COLS = [
        "system_id", "pdb_id", "receptor_name", "receptor_uniprot", "receptor_gene",
        "g_protein_family", "g_alpha_subtype", "ligand_name", "ligand_chem_id",
        "n_replicas", "length_per_replica_ns", "total_sampling_ns",
        "force_field", "lipid_composition", "has_velocities", "has_forces",
        "trajectory_type", "has_bilayer", "structural_provenance",
        "traj_size_bytes", "topo_size_bytes", "master_schema_version",
    ]
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
        n_pockets = sum(1 for s in sids if (POCKETS_ATLAS / f"{s}_pockets.json").exists())
        n_gpcrdb = sum(1 for s in sids if (POCKETS_ATLAS / f"{s}_pockets_gpcrdb.json").exists())
        n_grids = sum(1 for s in sids if (POCKETS_ATLAS / f"{s}_pocketgrid.npz").exists())
        n_gw = sum(1 for s in sids
                   if (GATEWAYS_ATLAS / f"{s}_gateways.json").exists()
                   and meta_by_sid.get(s, {}).get("trajectory_type") == "membrane_embedded")
        grid_mb = n_grids * 7.3
        print(f"  {len(sids)} systems under data/api/v1/systems/")
        print(f"    pockets.json:          {n_pockets}/{len(sids)}")
        print(f"    pockets_gpcrdb.json:   {n_gpcrdb}/{len(sids)}")
        print(f"    pocketgrid.npz:        {n_grids}/{len(sids)} "
              f"({'copy ~' + str(int(grid_mb)) + ' MB' if args.copy_grids else 'register ANALYSIS_SRC paths'})")
        print(f"    gateways.json:         {n_gw}/{len(sids)}")
        return

    # Open DB connection (None if DB not yet created).
    con = db_connect()
    if con:
        print(f"Database connected: {DATABASE_URL}")
    else:
        print("WARNING: database not found — file registration skipped. Run p1_ingest.py first.")

    # Consensus files
    print("\nSerializing consensus files ...")
    consensus_sizes = serialize_consensus()
    for name, sz in consensus_sizes.items():
        print(f"  consensus/{name}.json  {sz/1024:.1f} KB")

    # G-protein interface metrics & coupling geometry
    print("\nSerializing G-protein interface metrics ...")
    gp_sizes = serialize_gprotein_metrics(df, con, args.dry_run)
    for name, sz in gp_sizes.items():
        if name == "gprotein_metrics_count":
            print(f"  gprotein_metrics: {sz} systems")
        else:
            print(f"  consensus/{name}.json  {sz/1024:.1f} KB")

    # Per-system files
    print(f"\nSerializing {len(sids)} systems "
          f"({'copying pocketgrids' if args.copy_grids else 'registering pocketgrid paths'}) ...")
    coverage_rows = []
    for i, sid in enumerate(sids):
        row = serialize_system(sid, meta_by_sid.get(sid, {}), args.copy_grids, con)
        coverage_rows.append(row)
        if (i + 1) % 50 == 0:
            print(f"  ... {i+1}/{len(sids)}")

    if con:
        con.commit()
        # Report DB row counts
        cur = con.cursor()
        cur.execute("SELECT count(*) FROM system_pocket_files")
        n_pf = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM system_gateway_files")
        n_gf = cur.fetchone()[0]
        con.close()
        print(f"\nDatabase updated: {n_pf} pocket file rows, {n_gf} gateway file rows")

    # Master index
    cov_df = pd.DataFrame(coverage_rows)
    index = {
        "_schema_version": SCHEMA_VERSION,
        "_generated_at": GENERATED_AT,
        "n_systems": len(sids),
        "coverage": {
            "has_pockets": int(cov_df["has_pockets"].sum()),
            "has_pockets_gpcrdb": int(cov_df["has_pockets_gpcrdb"].sum()),
            "has_pocketgrid": int(cov_df["has_pocketgrid"].sum()),
            "has_gateways": int(cov_df["has_gateways"].sum()),
        },
        "systems": [
            {k: v for k, v in r.items()}
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
    import subprocess
    du = subprocess.run(["du", "-sh", str(API_OUT)], capture_output=True, text=True)
    print(f"\n=== P2 SUMMARY ===")
    print(f"  pockets.json:         {cov_df['has_pockets'].sum()}/{len(sids)}")
    print(f"  pockets_gpcrdb.json:  {cov_df['has_pockets_gpcrdb'].sum()}/{len(sids)}")
    print(f"  pocketgrid.npz:       {cov_df['has_pocketgrid'].sum()}/{len(sids)}")
    print(f"  gateways.json:        {cov_df['has_gateways'].sum()}/{len(sids)}")
    print(f"  Total API output:     {du.stdout.split()[0]}")
    print(f"  Done in {elapsed:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--system", metavar="SYSTEM_ID")
    parser.add_argument("--copy-grids", action="store_true",
                        help="Copy pocketgrid.npz files (~1.5 GB total)")
    main(parser.parse_args())
