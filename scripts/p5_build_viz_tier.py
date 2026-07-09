#!/usr/bin/env python3
"""
P5: Build the visualization tier — decimated XTC + reference PDB per system.

Source: /MDdata/data04/gpcr_g_database (pre-extracted, protein-only)
  Each system has: protein.pdb + traj1.nc / traj2.nc / traj3.nc

For each system:
  1. Locate its directory in the extracted database (a/ or b/ subtree)
  2. Load protein.pdb as topology + traj1.nc as trajectory (replica 1)
  3. Write structure.pdb (first frame) and decimated traj.xtc (~200 frames)
  4. Register files in system_viz_files table

Output:
  data/viz/{system_id}/
      structure.pdb      protein reference (first frame of rep1)
      traj.xtc           decimated trajectory (~200 frames)

Usage:
    python3 scripts/p5_build_viz_tier.py [--n N] [--system SID] [--dry-run] [--force]

Options:
    --n N         Process only the first N systems
    --system SID  Process a single system
    --dry-run     Print plan without writing files
    --force       Overwrite existing viz files (default: skip already done)

Environment:
    DATA_ROOT, DATABASE_URL
    EXTRACTED_DB   path to pre-extracted database (default: /MDdata/data04/gpcr_g_database)
"""

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_ROOT = Path(os.environ.get("DATA_ROOT", PROJECT_ROOT))
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_ROOT}/db/coupledmd.sqlite")
EXTRACTED_DB = Path(os.environ.get("EXTRACTED_DB", "/MDdata/data04/gpcr_g_database"))
VIZ_OUT = DATA_ROOT / "data" / "viz"
MASTER_CSV = DATA_ROOT / "data" / "systems_master.csv"

# Match GPCRmd standard: 2500 frames for 500 ns (200 ps/frame interval)
# Source trajs have 10000 frames (50 ps/frame) → stride 4 → 2500 frames
TARGET_FRAMES = 2500

# Subdirectory candidates per G-protein family (searched in order)
FAM_DIRS = {
    "G12-13": ["a/a_g12", "b/b2_g12"],
    "Gi":     ["a/a_gi",  "b/b1_gi", "b/b2_gi"],
    "Gq":     ["a/a_gq",  "b/b1_gq", "b/b2_gq"],
    "Gs":     ["a/a_gs",  "b/b1_gs", "b/b2_gs"],
}


def find_system_dir(pdb_id: str, family: str) -> Path | None:
    for sub in FAM_DIRS.get(family, []):
        p = EXTRACTED_DB / sub / pdb_id
        if p.is_dir() and (p / "protein.pdb").exists():
            return p
        # Edge case: files sit directly in the family dir (empty pdb subdir)
        parent = EXTRACTED_DB / sub
        if p.is_dir() and not (p / "protein.pdb").exists():
            if (parent / "protein.pdb").exists():
                return parent
    return None


def db_connect() -> sqlite3.Connection | None:
    if not DATABASE_URL.startswith("sqlite:///"):
        return None
    db_path = Path(DATABASE_URL.replace("sqlite:///", ""))
    if not db_path.is_absolute():
        db_path = DATA_ROOT / db_path
    if not db_path.exists():
        return None
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def ensure_viz_table(con: sqlite3.Connection):
    con.execute("""
        CREATE TABLE IF NOT EXISTS system_viz_files (
            system_id       TEXT NOT NULL REFERENCES systems(system_id),
            file_type       TEXT NOT NULL,   -- structure_pdb | traj_xtc
            file_path       TEXT NOT NULL,
            file_size_bytes INTEGER,
            n_frames        INTEGER,
            n_atoms         INTEGER,
            PRIMARY KEY (system_id, file_type)
        )
    """)
    con.commit()


def process_system(sid: str, src_dir: Path, stride: int,
                   out_dir: Path, dry_run: bool) -> dict | None:
    """Load protein.pdb + traj1.nc from extracted DB → structure.pdb + traj.xtc."""
    pdb_path = src_dir / "protein.pdb"
    traj_path = src_dir / "traj1.nc"

    if not pdb_path.exists():
        print(f"  SKIP {sid}: protein.pdb not found in {src_dir}")
        return None
    if not traj_path.exists():
        print(f"  SKIP {sid}: traj1.nc not found in {src_dir}")
        return None

    if dry_run:
        return {"sid": sid, "src": str(src_dir), "stride": stride}

    try:
        import MDAnalysis as mda
        from MDAnalysis.coordinates.XTC import XTCWriter
    except ImportError as e:
        print(f"  ERROR: missing dependency: {e}")
        return None

    try:
        u = mda.Universe(str(pdb_path), str(traj_path))
    except Exception as e:
        if "n_atoms" in str(e):
            # protein.pdb is full solvated system; load traj topology-free
            u = mda.Universe(str(traj_path), topology_format='NCDF')
            pdb_path = None  # will write PDB from first frame
        else:
            print(f"  SKIP {sid}: MDAnalysis failed: {e}")
            return None

    n_frames_total = len(u.trajectory)
    n_atoms = u.atoms.n_atoms

    out_dir.mkdir(parents=True, exist_ok=True)

    # Write reference PDB (first frame)
    struct_path = out_dir / "structure.pdb"
    u.trajectory[0]
    with mda.Writer(str(struct_path), n_atoms) as w:
        w.write(u.atoms)

    # Write decimated XTC
    # Some NC frames have ts.dimensions=None; MDAnalysis raises TypeError when reading
    # such frames via indexed access. Wrap the seek + write together.
    traj_out = out_dir / "traj.xtc"
    frame_indices = range(0, n_frames_total, stride)
    n_out = 0
    n_skipped = 0
    with XTCWriter(str(traj_out), n_atoms=n_atoms) as w:
        for i in frame_indices:
            try:
                u.trajectory[i]
                w.write(u.atoms)
                n_out += 1
            except TypeError:
                n_skipped += 1
    if n_skipped:
        print(f" ({n_skipped} frames skipped — no box info)", end="")

    return {
        "struct_path": struct_path,
        "traj_path": traj_out,
        "n_frames_in": n_frames_total,
        "n_frames_out": n_out,
        "n_atoms": n_atoms,
    }


def main(args):
    df = pd.read_csv(MASTER_CSV)

    if args.system:
        df = df[df["system_id"] == args.system]
        if df.empty:
            sys.exit(f"ERROR: system_id '{args.system}' not found")
    if args.n:
        df = df.head(args.n)

    print(f"Building viz tier for {len(df)} systems "
          f"({'DRY RUN' if args.dry_run else 'WRITING'})")
    print(f"Source: {EXTRACTED_DB}")

    con = db_connect()
    if con and not args.dry_run:
        ensure_viz_table(con)

    results, skipped = [], []
    t0 = time.time()

    for idx, (_, row) in enumerate(df.iterrows()):
        sid = row["system_id"]
        pdb_id = row["pdb_id"]
        family = row["g_protein_family"]
        out_dir = VIZ_OUT / sid

        # Skip if already done (unless --force)
        if not args.force and not args.dry_run:
            if (out_dir / "structure.pdb").exists() and (out_dir / "traj.xtc").exists():
                print(f"  [{idx+1}/{len(df)}] {sid}  SKIP (already done)")
                skipped.append(sid)
                continue

        src_dir = find_system_dir(pdb_id, family)
        if src_dir is None:
            print(f"  [{idx+1}/{len(df)}] {sid}  SKIP (not found in extracted DB)")
            skipped.append(sid)
            continue

        # stride=4: 10000 frames ÷ 4 = 2500 frames (matches GPCRmd 200 ps/frame standard)
        stride = args.stride or max(1, 10000 // TARGET_FRAMES)

        print(f"  [{idx+1}/{len(df)}] {sid}  stride={stride}", end="", flush=True)

        result = process_system(sid, src_dir, stride, out_dir, args.dry_run)

        if result is None:
            skipped.append(sid)
            continue

        if not args.dry_run:
            sp = result["struct_path"]
            tp = result["traj_path"]
            print(f"  → {result['n_frames_out']} frames, {result['n_atoms']} atoms, "
                  f"XTC {tp.stat().st_size/1e6:.1f} MB")
            if con:
                con.execute(
                    "INSERT OR REPLACE INTO system_viz_files "
                    "(system_id, file_type, file_path, file_size_bytes, n_frames, n_atoms) "
                    "VALUES (?,?,?,?,?,?)",
                    (sid, "structure_pdb", str(sp), sp.stat().st_size, 1, result["n_atoms"]),
                )
                con.execute(
                    "INSERT OR REPLACE INTO system_viz_files "
                    "(system_id, file_type, file_path, file_size_bytes, n_frames, n_atoms) "
                    "VALUES (?,?,?,?,?,?)",
                    (sid, "traj_xtc", str(tp), tp.stat().st_size,
                     result["n_frames_out"], result["n_atoms"]),
                )
                con.commit()
        else:
            print(f"  [DRY] stride={stride} src={src_dir.name}")

        results.append(result)

    if con:
        con.close()

    elapsed = time.time() - t0
    print(f"\nDone: {len(results)} built, {len(skipped)} skipped, in {elapsed:.0f}s")
    if not args.dry_run and results:
        import subprocess
        du = subprocess.run(["du", "-sh", str(VIZ_OUT)], capture_output=True, text=True)
        print(f"Viz tier disk: {du.stdout.strip()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, metavar="N", help="Process only first N systems")
    parser.add_argument("--stride", type=int, metavar="S",
                        help="Frame stride (default: 50 → ~200 frames from 10000)")
    parser.add_argument("--system", metavar="SYSTEM_ID")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite existing viz files")
    main(parser.parse_args())
