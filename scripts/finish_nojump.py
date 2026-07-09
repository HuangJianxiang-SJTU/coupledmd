#!/usr/bin/env python3
"""Stage-2 for the full-res nojump fix: select protein+ligand from the decimated
nojump trajectory, CA-fit to structure.pdb, fix structure.pdb. nojump already
keeps the chains in one consistent image throughout, so NO per-frame assembly is
applied (per-frame assembly is what caused flicker on these systems).

Usage: python3 scripts/finish_nojump.py SYS TPR NOJUMP_DEC_XTC
"""
import sys, shutil, datetime, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np
import MDAnalysis as mda
from MDAnalysis.analysis import align

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "data" / "viz"
sys.path.insert(0, str(ROOT / "scripts"))
from fix_viz_inplace import fix_structure

sid, tpr, dec = sys.argv[1], sys.argv[2], sys.argv[3]
d = VIZ / sid; pdb = d / "structure.pdb"; traj = d / "traj.xtc"
ref = mda.Universe(str(pdb))
u = mda.Universe(tpr, dec)
pl = u.select_atoms("not resname POPC SOD CLA")
if pl.n_atoms != ref.atoms.n_atoms:
    sys.exit(f"ATOM COUNT MISMATCH {pl.n_atoms} vs {ref.atoms.n_atoms}")

# write protein+lig to a temp xtc (nojump image preserved, no reassembly)
tmp = d / "traj.noj.tmp.xtc"
with mda.Writer(str(tmp), pl.n_atoms) as W:
    for ts in u.trajectory:
        W.write(pl)

# fix structure.pdb against the new traj box (reassembly is a no-op if already whole)
fix_structure(sid, mda.Universe(str(pdb), str(tmp)))

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.move(str(traj), str(traj) + f".broken_pbc_{ts}")
align.AlignTraj(mda.Universe(str(pdb), str(tmp)), mda.Universe(str(pdb)),
                select="name CA", filename=str(traj)).run()
tmp.unlink(missing_ok=True)
print(f"  wrote {traj}")
