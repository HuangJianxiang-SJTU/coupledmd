#!/usr/bin/env python3
"""
P1: Define the metadata schema and ingest systems_master into SQLite.

Idempotent: safe to re-run; will replace rows for existing system_ids.
Designed so swapping to Postgres requires only a DATABASE_URL change.

Usage:
    python3 scripts/p1_ingest.py [--dry-run]

Options:
    --dry-run   Print row counts and schema without touching the database.

Environment:
    DATABASE_URL   SQLite or Postgres connection string (default: sqlite:///db/coupledmd.sqlite)
    DATA_ROOT      Project root (default: parent of this script's directory)
"""

import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DATA_ROOT = Path(os.environ.get("DATA_ROOT", PROJECT_ROOT))
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_ROOT}/db/coupledmd.sqlite")
MASTER_CSV = DATA_ROOT / "data" / "systems_master.csv"


# --------------------------------------------------------------------------- #
# Schema DDL
# --------------------------------------------------------------------------- #

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version     TEXT    NOT NULL,
    applied_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS systems (
    -- identity
    system_id               TEXT    PRIMARY KEY,
    pdb_id                  TEXT    NOT NULL,
    source_pdb              TEXT,

    -- receptor
    receptor_name           TEXT,
    receptor_uniprot        TEXT,
    receptor_gene           TEXT,

    -- G protein
    g_protein_family        TEXT    NOT NULL,   -- Gi, Gs, Gq, G12-13
    g_alpha_subtype         TEXT,

    -- ligand
    ligand_name             TEXT,
    ligand_chem_id          TEXT,
    ligand_class            TEXT,
    peptide_ligand_chain    TEXT,
    peptide_ligand_sequence TEXT,
    peptide_ligand_length   INTEGER,

    -- simulation
    n_replicas              INTEGER NOT NULL,
    length_per_replica_ns   REAL    NOT NULL,
    total_sampling_ns       REAL    NOT NULL,
    force_field             TEXT    NOT NULL,
    force_field_orig        TEXT,
    lipid_composition       TEXT,
    n_protein_residues      INTEGER,
    has_velocities          INTEGER,            -- boolean as 0/1
    has_forces              INTEGER,

    -- classification (derived at P0)
    trajectory_type         TEXT    NOT NULL,   -- membrane_embedded | protein_only
    has_bilayer             INTEGER NOT NULL,
    structural_provenance   TEXT    NOT NULL,   -- experimental | engineered_uncertain

    -- file paths (raw source; served tiers are in separate table)
    trajectory_path         TEXT,
    topology_path           TEXT,
    source_directory        TEXT,
    full_system_trajectory_path  TEXT,
    protein_only_trajectory_path TEXT,

    -- file metadata
    traj_size_bytes         INTEGER,
    topo_size_bytes         INTEGER,
    traj_sha256             TEXT,
    topo_sha256             TEXT,
    traj_exists             INTEGER,
    topo_exists             INTEGER,

    -- audit
    notes                   TEXT,
    cleanup_notes           TEXT,
    master_schema_version   TEXT,
    ingested_at             TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Index for common filter patterns
CREATE INDEX IF NOT EXISTS idx_systems_family   ON systems (g_protein_family);
CREATE INDEX IF NOT EXISTS idx_systems_uniprot  ON systems (receptor_uniprot);
CREATE INDEX IF NOT EXISTS idx_systems_gene     ON systems (receptor_gene);
CREATE INDEX IF NOT EXISTS idx_systems_pdb      ON systems (pdb_id);
CREATE INDEX IF NOT EXISTS idx_systems_traj_type ON systems (trajectory_type);
CREATE INDEX IF NOT EXISTS idx_systems_provenance ON systems (structural_provenance);

-- Placeholder tables for P2 analysis-layer links.
-- Populated by p2_serialize.py.
CREATE TABLE IF NOT EXISTS system_pocket_files (
    system_id   TEXT    NOT NULL REFERENCES systems(system_id),
    file_type   TEXT    NOT NULL,   -- pockets_json | pockets_gpcrdb_json | pocketgrid_npz
    file_path   TEXT    NOT NULL,
    file_size_bytes INTEGER,
    PRIMARY KEY (system_id, file_type)
);

CREATE TABLE IF NOT EXISTS system_gateway_files (
    system_id   TEXT    NOT NULL REFERENCES systems(system_id),
    file_type   TEXT    NOT NULL,   -- gateways_json
    file_path   TEXT    NOT NULL,
    file_size_bytes INTEGER,
    PRIMARY KEY (system_id, file_type)
);
"""


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def _bool_to_int(val) -> int | None:
    if pd.isna(val):
        return None
    return int(bool(val))


def main(args):
    if not MASTER_CSV.exists():
        sys.exit(f"ERROR: systems_master.csv not found at {MASTER_CSV}\n"
                 "Run scripts/p0_freeze_cohort.py first.")

    df = pd.read_csv(MASTER_CSV)
    print(f"Read {len(df)} systems from {MASTER_CSV}")

    if args.dry_run:
        print("\n[DRY RUN] Would create/update database at:")
        print(f"  {DATABASE_URL}")
        print(f"\nSchema tables: systems, system_pocket_files, system_gateway_files, schema_version")
        print(f"Would ingest {len(df)} rows into 'systems'.")
        print("\nSample row (system_id, family, force_field, trajectory_type):")
        print(df[["system_id", "g_protein_family", "force_field",
                   "trajectory_type", "structural_provenance"]].head(3).to_string())
        return

    # Lazy SQLite import — same interface works with sqlalchemy for Postgres swap.
    import sqlite3

    if not DATABASE_URL.startswith("sqlite:///"):
        sys.exit("ERROR: Only SQLite is supported in P1. "
                 "Set DATABASE_URL=sqlite:///path/to/db.sqlite")

    db_path = Path(DATABASE_URL.replace("sqlite:///", ""))
    if not db_path.is_absolute():
        db_path = DATA_ROOT / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Apply schema (idempotent via CREATE IF NOT EXISTS).
    cur.executescript(SCHEMA_SQL)

    # Record schema version if not already there.
    cur.execute("SELECT count(*) FROM schema_version WHERE version='1.0'")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO schema_version (version) VALUES ('1.0')")

    # Upsert: INSERT OR REPLACE handles re-runs.
    upsert_sql = """
        INSERT OR REPLACE INTO systems (
            system_id, pdb_id, source_pdb,
            receptor_name, receptor_uniprot, receptor_gene,
            g_protein_family, g_alpha_subtype,
            ligand_name, ligand_chem_id, ligand_class,
            peptide_ligand_chain, peptide_ligand_sequence, peptide_ligand_length,
            n_replicas, length_per_replica_ns, total_sampling_ns,
            force_field, force_field_orig, lipid_composition, n_protein_residues,
            has_velocities, has_forces,
            trajectory_type, has_bilayer, structural_provenance,
            trajectory_path, topology_path, source_directory,
            full_system_trajectory_path, protein_only_trajectory_path,
            traj_size_bytes, topo_size_bytes, traj_sha256, topo_sha256,
            traj_exists, topo_exists,
            notes, cleanup_notes, master_schema_version
        ) VALUES (
            :system_id, :pdb_id, :source_pdb,
            :receptor_name, :receptor_uniprot, :receptor_gene,
            :g_protein_family, :g_alpha_subtype,
            :ligand_name, :ligand_chem_id, :ligand_class,
            :peptide_ligand_chain, :peptide_ligand_sequence, :peptide_ligand_length,
            :n_replicas, :length_per_replica_ns, :total_sampling_ns,
            :force_field, :force_field_orig, :lipid_composition, :n_protein_residues,
            :has_velocities, :has_forces,
            :trajectory_type, :has_bilayer, :structural_provenance,
            :trajectory_path, :topology_path, :source_directory,
            :full_system_trajectory_path, :protein_only_trajectory_path,
            :traj_size_bytes, :topo_size_bytes, :traj_sha256, :topo_sha256,
            :traj_exists, :topo_exists,
            :notes, :cleanup_notes, :master_schema_version
        )
    """

    rows_inserted = 0
    for _, row in df.iterrows():
        record = {
            "system_id": row["system_id"],
            "pdb_id": row["pdb_id"],
            "source_pdb": row.get("source_pdb") if not pd.isna(row.get("source_pdb", float("nan"))) else None,
            "receptor_name": row["receptor_name"] if not pd.isna(row.get("receptor_name", float("nan"))) else None,
            "receptor_uniprot": row["receptor_uniprot"] if not pd.isna(row.get("receptor_uniprot", float("nan"))) else None,
            "receptor_gene": row["receptor_gene"] if not pd.isna(row.get("receptor_gene", float("nan"))) else None,
            "g_protein_family": row["g_protein_family"],
            "g_alpha_subtype": row["g_alpha_subtype"] if not pd.isna(row.get("g_alpha_subtype", float("nan"))) else None,
            "ligand_name": row["ligand_name"] if not pd.isna(row.get("ligand_name", float("nan"))) else None,
            "ligand_chem_id": row["ligand_chem_id"] if not pd.isna(row.get("ligand_chem_id", float("nan"))) else None,
            "ligand_class": str(row["ligand_class"]) if not pd.isna(row.get("ligand_class", float("nan"))) else None,
            "peptide_ligand_chain": row["peptide_ligand_chain"] if not pd.isna(row.get("peptide_ligand_chain", float("nan"))) else None,
            "peptide_ligand_sequence": row["peptide_ligand_sequence"] if not pd.isna(row.get("peptide_ligand_sequence", float("nan"))) else None,
            "peptide_ligand_length": int(row["peptide_ligand_length"]) if not pd.isna(row.get("peptide_ligand_length", float("nan"))) else None,
            "n_replicas": int(row["n_replicas"]),
            "length_per_replica_ns": float(row["length_per_replica_ns"]),
            "total_sampling_ns": float(row["total_sampling_ns"]),
            "force_field": row["force_field"],
            "force_field_orig": row["force_field_orig"],
            "lipid_composition": row["lipid_composition"] if not pd.isna(row.get("lipid_composition", float("nan"))) else None,
            "n_protein_residues": int(row["n_protein_residues"]) if not pd.isna(row.get("n_protein_residues", float("nan"))) else None,
            "has_velocities": _bool_to_int(row["has_velocities"]),
            "has_forces": _bool_to_int(row["has_forces"]),
            "trajectory_type": row["trajectory_type"],
            "has_bilayer": _bool_to_int(row["has_bilayer"]),
            "structural_provenance": row["structural_provenance"],
            "trajectory_path": row["trajectory_path"] if not pd.isna(row.get("trajectory_path", float("nan"))) else None,
            "topology_path": row["topology_path"] if not pd.isna(row.get("topology_path", float("nan"))) else None,
            "source_directory": row["source_directory"] if not pd.isna(row.get("source_directory", float("nan"))) else None,
            "full_system_trajectory_path": row["full_system_trajectory_path"] if not pd.isna(row.get("full_system_trajectory_path", float("nan"))) else None,
            "protein_only_trajectory_path": row["protein_only_trajectory_path"] if not pd.isna(row.get("protein_only_trajectory_path", float("nan"))) else None,
            "traj_size_bytes": int(row["traj_size_bytes"]) if not pd.isna(row.get("traj_size_bytes", float("nan"))) else None,
            "topo_size_bytes": int(row["topo_size_bytes"]) if not pd.isna(row.get("topo_size_bytes", float("nan"))) else None,
            "traj_sha256": row["traj_sha256"] if not pd.isna(row.get("traj_sha256", float("nan"))) else None,
            "topo_sha256": row["topo_sha256"] if not pd.isna(row.get("topo_sha256", float("nan"))) else None,
            "traj_exists": _bool_to_int(row["traj_exists"]),
            "topo_exists": _bool_to_int(row["topo_exists"]),
            "notes": row["notes"] if not pd.isna(row.get("notes", float("nan"))) else None,
            "cleanup_notes": row["cleanup_notes"] if not pd.isna(row.get("cleanup_notes", float("nan"))) else None,
            "master_schema_version": str(row["master_schema_version"]) if not pd.isna(row.get("master_schema_version", float("nan"))) else "1.0",
        }
        cur.execute(upsert_sql, record)
        rows_inserted += 1

    con.commit()

    # Row count report.
    cur.execute("SELECT count(*) FROM systems")
    n_systems = cur.fetchone()[0]
    cur.execute("SELECT g_protein_family, count(*) FROM systems GROUP BY g_protein_family ORDER BY count(*) DESC")
    family_counts = cur.fetchall()
    cur.execute("SELECT force_field, count(*) FROM systems GROUP BY force_field")
    ff_counts = cur.fetchall()
    cur.execute("SELECT trajectory_type, count(*) FROM systems GROUP BY trajectory_type")
    tt_counts = cur.fetchall()
    cur.execute("SELECT structural_provenance, count(*) FROM systems GROUP BY structural_provenance")
    prov_counts = cur.fetchall()

    con.close()
    elapsed = time.time() - t0

    print(f"\nDatabase: {db_path}")
    print(f"Schema version: 1.0")
    print(f"Rows inserted/replaced: {rows_inserted}")
    print(f"\n=== ROW COUNT REPORT ===")
    print(f"systems table: {n_systems} rows")
    print("\nBy G-protein family:")
    for fam, n in family_counts:
        print(f"  {n:3d}  {fam}")
    print("\nBy force field:")
    for ff, n in ff_counts:
        print(f"  {n:3d}  {ff}")
    print("\nBy trajectory type:")
    for tt, n in tt_counts:
        print(f"  {n:3d}  {tt}")
    print("\nBy structural provenance:")
    for prov, n in prov_counts:
        print(f"  {n:3d}  {prov}")
    print(f"\nDone in {elapsed:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without touching the database")
    main(parser.parse_args())
