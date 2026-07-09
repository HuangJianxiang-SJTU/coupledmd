#!/usr/bin/env python3
"""
Run the full viz PBC fix pipeline for one system end-to-end.

Pipeline (see docs/VIZ_PBC_FIX.md + memory viz-pbc-fix-method):
  1. locate protein-only source (find_protein_source)
  2. verify atom count + name order match the viz PDB (abort if not)
  3. build fake TPR (separate-molecule per chain)
  4. make-ndx (alpha5 = last 21 resids of G_alpha)
  5. src-to-xtc (full-res protein-only from pre-extracted db)
  6. gmx -pbc cluster
  7. assemble-multipass (anchor on G_alpha, min-image, Kabsch alpha5, decimate)
  8. fix-structure (reimage PDB chains, CRYST1, elements)
  9. update-db
 10. verify (audit + frame0 RMSD)

Backups: structure.pdb.pre_pbc_fix, traj.xtc -> traj.xtc.broken_pbc_<ts> + traj_orig.xtc.

Usage:
    python3 scripts/fix_one_system.py <system_id> [--keep-tmp]
    python3 scripts/fix_one_system.py Gs_8XVI
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIZ = PROJECT_ROOT / "data" / "viz"
GMXLIB = PROJECT_ROOT / "scripts" / "audit_output" / "gmx_top"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from find_protein_source import find_source  # noqa: E402


def run(cmd, **kw):
    print(f"  $ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    env = dict(os.environ)
    env["GMXLIB"] = str(GMXLIB)
    r = subprocess.run(cmd, shell=isinstance(cmd, str), env=env,
                       capture_output=True, text=True, **kw)
    if r.returncode != 0:
        # print last stderr for diagnosis
        print(r.stderr[-2000:] if r.stderr else "(no stderr)")
        raise RuntimeError(f"command failed (exit {r.returncode}): {cmd}")
    return r


def verify_atom_order(viz_pdb, src_pdb, src_nc):
    import warnings; warnings.filterwarnings("ignore")
    import MDAnalysis as mda
    uv = mda.Universe(str(viz_pdb))
    us = mda.Universe(str(src_pdb), str(src_nc))
    if uv.atoms.n_atoms != us.atoms.n_atoms:
        return False, f"atom count mismatch pdb={uv.atoms.n_atoms} src={us.atoms.n_atoms}"
    if not (uv.atoms.names == us.atoms.names).all():
        return False, "atom name order mismatch"
    return True, f"atoms={uv.atoms.n_atoms} frames={len(us.trajectory)}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("system_id")
    ap.add_argument("--keep-tmp", action="store_true")
    ap.add_argument("--tmp-dir", help="default /tmp/<sys>_pbcfix")
    args = ap.parse_args()

    sid = args.system_id
    sysdir = VIZ / sid
    pdb = sysdir / "structure.pdb"
    traj = sysdir / "traj.xtc"
    roles = PROJECT_ROOT / "scripts" / "audit_output" / "chain_roles" / f"{sid}_chain_roles.json"
    tmp = Path(args.tmp_dir) if args.tmp_dir else Path(f"/tmp/{sid}_pbcfix")
    if not pdb.exists() or not traj.exists():
        sys.exit(f"ERROR: {pdb} or {traj} missing")
    if not roles.exists():
        sys.exit(f"ERROR: {roles} missing")
    tmp.mkdir(parents=True, exist_ok=True)

    print(f"\n=== FIX {sid} ===")
    # 1. locate source
    src_pdb, src_nc = find_source(sid)
    if not src_pdb:
        sys.exit(f"ERROR: no protein-only source found for {sid}")
    print(f"  source: {src_pdb}\n          {src_nc}")

    # 2. verify atom order
    ok, msg = verify_atom_order(pdb, src_pdb, src_nc)
    print(f"  atom-order verify: {msg}")
    if not ok:
        sys.exit(f"ERROR: {msg} — refusing to fix (silent-corruption risk)")

    # backups
    ts = time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(traj, str(traj) + f".broken_pbc_{ts}")
    if not (sysdir / "traj_orig.xtc").exists():
        shutil.copy2(traj, sysdir / "traj_orig.xtc")

    FIX = ["python3", str(PROJECT_ROOT / "scripts" / "fix_viz_pbc_pdb.py")]
    # 3. fake TPR
    print("  [3/10] build fake TPR")
    run(FIX + ["build-fake-tpr", "--pdb", str(pdb), "--roles", str(roles), "--outdir", str(tmp)])
    run(["gmx", "grompp", "-f", str(tmp / "fake.mdp"), "-c", str(tmp / "fake.gro"),
         "-p", str(tmp / "fake.top"), "-o", str(tmp / "fake.tpr"), "-maxwarn", "5"])

    # 4. ndx
    print("  [4/10] make-ndx")
    run(FIX + ["make-ndx", "--pdb", str(pdb), "--roles", str(roles), "--out", str(tmp / f"{sid}.ndx")])

    # 5. src-to-xtc (use SOURCE protein.pdb as topology so atom order matches)
    print("  [5/10] src-to-xtc (full-res)")
    run(FIX + ["src-to-xtc", "--pdb", src_pdb, "--src", src_nc, "--out", str(tmp / f"{sid}_fullres.xtc")])

    # 6. cluster
    print("  [6/10] gmx -pbc cluster")
    cluster_cmd = ("printf '1\\n1\\n' | gmx trjconv -s " + str(tmp / "fake.tpr")
                   + " -f " + str(tmp / f"{sid}_fullres.xtc")
                   + " -n " + str(tmp / f"{sid}.ndx") + " -o " + str(tmp / f"{sid}_cluster.xtc")
                   + " -pbc cluster")
    run(cluster_cmd)

    # 7. assemble-multipass -> live traj
    print("  [7/10] assemble-multipass")
    run(FIX + ["assemble-multipass", "--pdb", str(pdb), "--cluster", str(tmp / f"{sid}_cluster.xtc"),
               "--roles", str(roles), "--ndx", str(tmp / f"{sid}.ndx"),
               "--out", str(traj), "--stride", "4"])

    # 8. fix-structure
    print("  [8/10] fix-structure")
    run(FIX + ["fix-structure", "--pdb", str(pdb), "--xtc", str(traj), "--roles", str(roles)])

    # 9. update-db
    print("  [9/10] update-db")
    run(FIX + ["update-db", "--system", sid])

    # 10. verify
    print("  [10/10] verify (audit + frame0 RMSD)")
    r = run(["python3", str(PROJECT_ROOT / "scripts" / "audit_viz_pbc_full.py"),
             "--system", sid, "--frames", "10"])
    # the audit prints the per-system status line
    for line in (r.stdout or "").splitlines():
        if sid in line:
            print("  " + line.strip())

    # frame0 RMSD
    import warnings; warnings.filterwarnings("ignore")
    import numpy as np, MDAnalysis as mda
    u = mda.Universe(str(pdb), str(traj)); up = mda.Universe(str(pdb)); u.trajectory[0]
    rmsd = np.sqrt(((u.atoms.positions - up.atoms.positions) ** 2).sum(1).mean())
    print(f"  frame0 RMSD vs pdb: {rmsd:.3f} Å   (target ~0.0; WARN residual acceptable)")

    if not args.keep_tmp:
        shutil.rmtree(tmp, ignore_errors=True)
        # clean stray gmx files in viz dir
        for stray in ["mdout.mdp", "index.ndx", "processed.gro"]:
            f = sysdir / stray
            if f.exists():
                f.unlink()
    print(f"=== DONE {sid} ===\n")


if __name__ == "__main__":
    main()
