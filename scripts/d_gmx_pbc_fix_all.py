#!/usr/bin/env python3
"""
Phase D — Fix PBC for ALL 222 viz trajectories using GROMACS.

Three-step pipeline per system:
  1. gmx editconf  : center structure.pdb in box → processed.gro
  2. gmx trjconv   : -pbc nojump  (remove jumps across periodic boundaries)
  3. gmx trjconv   : -fit rotxy+trans (align all frames to first frame)

Uses a patched atommass.dat (in GMXLIB) to handle non-standard ligand atom names.

Backups: each original traj.xtc is copied to traj.xtc.bak before processing.
"""

import os
import sys
import json
import time
import shutil
import subprocess
import argparse

# ── Paths ──────────────────────────────────────────────────────────────────
VIZ_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz"
GMX_TOP_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output/gmx_top"
LOG_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output"
LOG_FILE = os.path.join(LOG_DIR, "gmx_pbc_fix_log.json")

# GMXLIB environment variable to use patched atommass.dat
GMX_ENV = os.environ.copy()
GMX_ENV["GMXLIB"] = GMX_TOP_DIR


def run_gmx(cmd, input_text, cwd, timeout_s=600):
    """Run a gmx command with stdin input, return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=timeout_s,
        env=GMX_ENV,
    )
    return proc.returncode, proc.stdout, proc.stderr


def fix_one(system_id, dry_run=False):
    """Fix PBC for a single system. Returns status dict."""
    sysdir = os.path.join(VIZ_DIR, system_id)
    pdb_path = os.path.join(sysdir, "structure.pdb")
    xtc_path = os.path.join(sysdir, "traj.xtc")
    bak_path = os.path.join(sysdir, "traj.xtc.bak")

    # Check prerequisites
    if not os.path.exists(pdb_path):
        return {"status": "SKIP", "error": "No structure.pdb"}
    if not os.path.exists(xtc_path):
        return {"status": "SKIP", "error": "No traj.xtc"}

    if dry_run:
        return {"status": "DRY-RUN", "xtc_size_mb": os.path.getsize(xtc_path) / 1e6}

    t0 = time.time()

    # ── Step 0: Backup ──────────────────────────────────────────────────
    if os.path.exists(bak_path):
        # Already backed up — restore from backup so we always process the original
        shutil.copy2(bak_path, xtc_path)
        backup_msg = "restored from backup"
    else:
        shutil.copy2(xtc_path, bak_path)
        backup_msg = "created"
    t_backup = time.time()

    # ── Step 1: gmx editconf — center structure.pdb in box ──────────────
    gro_path = os.path.join(sysdir, "processed.gro")
    rc, stdout, stderr = run_gmx(
        ["gmx", "editconf", "-f", "structure.pdb", "-o", "processed.gro", "-c"],
        "0\n",
        cwd=sysdir,
    )
    if rc != 0:
        # Restore from backup on failure
        shutil.copy2(bak_path, xtc_path)
        return {"status": "ERROR", "step": "editconf", "error": stderr.strip()[-200:]}
    t_editconf = time.time()

    # ── Step 2: gmx trjconv -pbc nojump ─────────────────────────────────
    nojump_path = os.path.join(sysdir, "traj_nojump.xtc")
    rc, stdout, stderr = run_gmx(
        [
            "gmx", "trjconv",
            "-s", "processed.gro",
            "-f", "traj.xtc.bak",
            "-o", "traj_nojump.xtc",
            "-pbc", "nojump",
        ],
        "0\n",
        cwd=sysdir,
        timeout_s=1800,
    )
    if rc != 0:
        shutil.copy2(bak_path, xtc_path)
        _cleanup(sysdir, gro_path, nojump_path)
        return {"status": "ERROR", "step": "nojump", "error": stderr.strip()[-200:]}
    t_nojump = time.time()

    # ── Step 3: gmx trjconv -fit rotxy+trans (align to first frame) ─────
    rc, stdout, stderr = run_gmx(
        [
            "gmx", "trjconv",
            "-s", "processed.gro",
            "-f", "traj_nojump.xtc",
            "-o", "traj.xtc",
            "-fit", "rotxy+trans",
        ],
        "0\n0\n",
        cwd=sysdir,
        timeout_s=1800,
    )
    t_fit = time.time()

    # ── Cleanup temp files ──────────────────────────────────────────────
    _cleanup(sysdir, gro_path, nojump_path)

    if rc != 0:
        shutil.copy2(bak_path, xtc_path)
        return {"status": "ERROR", "step": "fit", "error": stderr.strip()[-200:]}

    elapsed = t_fit - t0
    new_size_mb = os.path.getsize(xtc_path) / 1e6

    return {
        "status": "OK",
        "backup": backup_msg,
        "time_total_s": round(elapsed, 1),
        "time_backup_s": round(t_backup - t0, 1),
        "time_editconf_s": round(t_editconf - t_backup, 1),
        "time_nojump_s": round(t_nojump - t_editconf, 1),
        "time_fit_s": round(t_fit - t_nojump, 1),
        "output_mb": round(new_size_mb, 1),
    }


def _cleanup(sysdir, gro_path, nojump_path):
    """Remove temporary files."""
    for p in [gro_path, nojump_path]:
        if os.path.exists(p):
            os.remove(p)


def build_mass_db():
    """
    Scan all structure.pdb files for atom names, compare against GROMACS
    atommass.dat, and add missing entries (mass=12.0) to a local copy.
    """
    src_mass = "/usr/share/gromacs/top/atommass.dat"
    dest_dir = GMX_TOP_DIR
    os.makedirs(dest_dir, exist_ok=True)
    dest_mass = os.path.join(dest_dir, "atommass.dat")

    # Collect all atom names from all PDB files
    print("Scanning all structure.pdb files for atom names...")
    all_atoms = set()
    for entry in sorted(os.listdir(VIZ_DIR)):
        pdb = os.path.join(VIZ_DIR, entry, "structure.pdb")
        if not os.path.isfile(pdb):
            continue
        with open(pdb) as f:
            for line in f:
                if line.startswith("ATOM"):
                    name = line[12:16].strip().replace("'", "")
                    all_atoms.add(name)

    # Read known atoms from source atommass.dat
    known = set()
    with open(src_mass) as f:
        for line in f:
            parts = line.split()
            if not line.startswith(";") and len(parts) >= 3:
                known.add(parts[1])

    # Find unknown atoms
    unknown = sorted(all_atoms - known)

    if not unknown:
        print(f"  All {len(all_atoms)} atom names found in mass database.")
        shutil.copy2(src_mass, dest_mass)
        return

    print(f"  Total unique atoms: {len(all_atoms)}")
    print(f"  Already known:      {len(known)}")
    print(f"  Adding {len(unknown)} missing entries with mass=12.0")

    # Copy original + append missing
    shutil.copy2(src_mass, dest_mass)
    with open(dest_mass, "a") as f:
        f.write("\n; === Auto-added ligand atoms (default mass 12.0) ===\n")
        for atom in unknown:
            f.write(f"???  {atom:<4s}   12.00000\n")


def main():
    parser = argparse.ArgumentParser(description="Fix PBC for all viz trajectories using GROMACS")
    parser.add_argument("--dry-run", action="store_true", help="List systems without processing")
    parser.add_argument("--rebuild-mass-db", action="store_true", help="Rebuild patched atommass.dat")
    parser.add_argument("--limit", type=int, default=0, help="Process only first N systems (0=all)")
    parser.add_argument("--systems", nargs="+", help="Process only specific system IDs")
    args = parser.parse_args()

    # Build mass database
    if args.rebuild_mass_db or not os.path.exists(os.path.join(GMX_TOP_DIR, "atommass.dat")):
        build_mass_db()

    # Collect systems to process
    if args.systems:
        systems = args.systems
    else:
        systems = sorted(
            d for d in os.listdir(VIZ_DIR)
            if os.path.isdir(os.path.join(VIZ_DIR, d))
            and os.path.exists(os.path.join(VIZ_DIR, d, "traj.xtc"))
        )

    if args.limit > 0:
        systems = systems[: args.limit]

    print(f"{'='*70}")
    print(f"Phase D — GROMACS PBC fix (nojump + rotxy+trans alignment)")
    print(f"Systems to process: {len(systems)}")
    print(f"{'='*70}")

    results = []
    t_start = time.time()

    for i, sid in enumerate(systems):
        tag = f"[{i+1}/{len(systems)}]"
        print(f"\n{tag} {sid} ...", end=" ", flush=True)
        t1 = time.time()

        result = fix_one(sid, dry_run=args.dry_run)
        t2 = time.time()

        result["system_id"] = sid
        result["wall_s"] = round(t2 - t1, 1)

        if result["status"] == "OK":
            print(f"OK ({result['time_total_s']}s, {result['output_mb']} MB)")
        elif result["status"] == "DRY-RUN":
            print(f"DRY-RUN ({result['xtc_size_mb']} MB)")
        elif result["status"] == "SKIP":
            print(f"SKIP — {result['error']}")
        else:
            print(f"ERROR at {result['step']}: {result['error']}")

        results.append(result)

        # Flush log to disk incrementally
        if (i + 1) % 10 == 0 or i == len(systems) - 1:
            os.makedirs(LOG_DIR, exist_ok=True)
            with open(LOG_FILE, "w") as f:
                json.dump(results, f, indent=2)

    elapsed = time.time() - t_start

    # Summary
    n_ok = sum(1 for r in results if r["status"] == "OK")
    n_err = sum(1 for r in results if r["status"] == "ERROR")
    n_skip = sum(1 for r in results if r["status"] == "SKIP")

    print(f"\n{'='*70}")
    print(f"SUMMARY: {n_ok} OK, {n_err} ERROR, {n_skip} SKIP out of {len(systems)}")
    print(f"Total wall time: {elapsed:.1f}s")
    print(f"Log saved to: {LOG_FILE}")
    print(f"Backups at: {VIZ_DIR}/*/traj.xtc.bak")

    if n_err > 0:
        print(f"\nFailed systems:")
        for r in results:
            if r["status"] == "ERROR":
                print(f"  {r['system_id']}: {r['step']} — {r['error']}")


if __name__ == "__main__":
    main()
