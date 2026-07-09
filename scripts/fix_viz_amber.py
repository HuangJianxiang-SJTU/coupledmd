#!/usr/bin/env python3
"""Rebuild a PBC-broken AMBER viz trajectory from the full-solvated source via
cpptraj `autoimage` (uses real prmtop molecule definitions + the membrane as a
stable anchor — succeeds where chain-level reassembly of the protein-only viz
trajectory fails, e.g. intra-molecule wraps).

Pipeline:
  1. cpptraj: parm prmtop; trajin nc 1 last <stride>; autoimage; strip <solvent>;
     trajout tmp.xtc  -> full protein+ligand, reassembled, decimated to ~2500 fr.
  2. MDAnalysis: load structure.pdb + tmp.xtc, assert atom count + names match.
  3. Per-frame greedy proximity assembly over chain-role segments (belt-and-
     suspenders for any chain autoimage still left a box away).
  4. Per-frame CA Kabsch fit to the (reassembled) structure.pdb -> traj.xtc.
  5. fix_structure: reassemble structure.pdb, rewrite CRYST1, assign elements.

Backups: traj.xtc.broken_pbc_<ts>, structure.pdb.pre_reassembly.

Usage: python3 scripts/fix_viz_amber.py SYSTEM_ID PRMTOP NC [--target 2500] [--strip MASK]
"""
import sys, argparse, subprocess, warnings, datetime, shutil
warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np
import MDAnalysis as mda
from MDAnalysis.analysis import align

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "data" / "viz"
sys.path.insert(0, str(ROOT / "scripts"))
from fix_viz_inplace import assemble, load_segments, fix_structure, verify

CPPTRAJ = "/opt/softwares/amber24/bin/cpptraj"
AMBERHOME = "/opt/softwares/amber24"
DEFAULT_STRIP = ":WAT,POPC,SOD,CLA,CHL1,POPE,POPS,POT,TIP3,CHOL,K+,Na+,Cl-"
SCRATCH = Path("/tmp/claude-1001/-MDdata-data02-jxhuang-gpcr-g-gpcr-g-server/"
               "2b04bb95-6e84-4bf5-9eff-30987eb656e6/scratchpad")


def nframes(prmtop, nc):
    out = subprocess.run([CPPTRAJ, "-p", prmtop, "-y", nc, "-tl"],
                         capture_output=True, text=True,
                         env={"AMBERHOME": AMBERHOME, "PATH": "/usr/bin:/bin"})
    for line in (out.stdout + out.stderr).splitlines():
        if line.strip().startswith("Frames:"):
            return int(line.split(":")[1].split()[0])
    raise RuntimeError("could not read frame count:\n" + out.stdout + out.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("system"); ap.add_argument("prmtop"); ap.add_argument("nc")
    ap.add_argument("--target", type=int, default=2500)
    ap.add_argument("--strip", default=DEFAULT_STRIP)
    args = ap.parse_args()
    sid = args.system
    d = VIZ / sid; pdb = d / "structure.pdb"; traj = d / "traj.xtc"

    nf = nframes(args.prmtop, args.nc)
    stride = max(1, nf // args.target)
    tmp = SCRATCH / f"{sid}_autoimage.xtc"
    print(f"=== {sid} === source {nf} frames, stride {stride} -> ~{nf//stride}")

    cin = SCRATCH / f"{sid}_autoimage.in"
    cin.write_text(f"parm {args.prmtop}\ntrajin {args.nc} 1 {nf} {stride}\n"
                   f"autoimage\nstrip {args.strip}\ntrajout {tmp} xtc\ngo\n")
    r = subprocess.run([CPPTRAJ, "-i", str(cin)], capture_output=True, text=True,
                       env={"AMBERHOME": AMBERHOME, "PATH": "/usr/bin:/bin"})
    if not tmp.exists():
        sys.exit(f"cpptraj failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")

    ref = mda.Universe(str(pdb))
    u = mda.Universe(str(pdb), str(tmp))           # structure.pdb topology + autoimaged xtc
    if u.atoms.n_atoms != ref.atoms.n_atoms:
        sys.exit(f"ATOM COUNT MISMATCH: autoimage {u.atoms.n_atoms} vs viz {ref.atoms.n_atoms}")
    if not (u.atoms.names == ref.atoms.names).all():
        sys.exit("ATOM ORDER MISMATCH between stripped source and structure.pdb")
    segs = load_segments(sid, u)

    tmp2 = SCRATCH / f"{sid}_assembled.xtc"
    with mda.Writer(str(tmp2), u.atoms.n_atoms) as W:
        for ts in u.trajectory:
            box = u.dimensions[:3].copy()
            u.atoms.positions = assemble(u.atoms.positions, segs, box)
            W.write(u.atoms)

    # fix structure.pdb first (so the CA fit targets the reassembled reference)
    u_box = mda.Universe(str(pdb), str(tmp2))
    fix_structure(sid, u_box)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.move(str(traj), str(traj) + f".broken_pbc_{ts}")
    align.AlignTraj(mda.Universe(str(pdb), str(tmp2)), mda.Universe(str(pdb)),
                    select="name CA", filename=str(traj)).run()
    verify(sid)


if __name__ == "__main__":
    main()
