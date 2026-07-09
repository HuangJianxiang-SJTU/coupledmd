#!/usr/bin/env python3
"""Per-frame CONTACT-based assembly for the hard NPT GROMACS complexes
(Gq_8DPF, Gi_8J22, G12_8H8J). Centroid/integer-box reassembly fails (complex >
box, NPT box fluctuates); the robust unit is contact (min atom-atom distance):
each chain is placed in the integer-box image (search +-2) that minimizes its
min CA-CA distance to the already-placed chains, best-first. This handles the
per-frame-varying shift that makes these complexes flicker. Then per-frame CA
Kabsch fit to structure.pdb removes the residual image flicker for the (majority)
compact frames.

Input: stage-1 `gmx -pbc whole -skip 4` xtc (molecules whole). Reports the
fraction of frames left non-compact (real G-protein excursions integer shifts
can't compact -- rendered honestly, not forced).

Usage: python3 scripts/fix_viz_contact.py SYS TPR WHOLE_XTC
"""
import sys, json, shutil, datetime, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np
import MDAnalysis as mda
from MDAnalysis.analysis import align
from scipy.spatial.distance import cdist

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "data" / "viz"
ROLES = ROOT / "scripts" / "audit_output" / "chain_roles"
sys.path.insert(0, str(ROOT / "scripts"))
from fix_viz_inplace import fix_structure
SH = np.array([[i, j, k] for i in range(-2, 3) for j in range(-2, 3) for k in range(-2, 3)])


def main():
    sid, tpr, whole = sys.argv[1], sys.argv[2], sys.argv[3]
    d = VIZ / sid; pdb = d / "structure.pdb"; traj = d / "traj.xtc"
    ref = mda.Universe(str(pdb))
    u = mda.Universe(tpr, whole)
    pl = u.select_atoms("not resname POPC SOD CLA")
    if pl.n_atoms != ref.atoms.n_atoms:
        sys.exit(f"ATOM COUNT MISMATCH {pl.n_atoms} vs {ref.atoms.n_atoms}")
    roles = json.load(open(ROLES / f"{sid}_chain_roles.json"))["roles"]
    segs = []
    for v in roles.values():
        a, b = [int(x) for x in v["resid_range"].split("-")]
        idx = ref.select_atoms(f"resid {a}:{b}").indices
        if not len(idx):
            continue
        ca = ref.select_atoms(f"name CA and resid {a}:{b}").indices
        segs.append((idx, ca if len(ca) >= 2 else idx[::max(1, len(idx) // 150)]))

    def assemble(pos, box):
        order = sorted(range(len(segs)), key=lambda i: -len(segs[i][0]))
        placed = pos[segs[order[0]][1]].copy(); done = {order[0]}
        while len(done) < len(segs):
            bs = bsh = None; bd = np.inf
            for oi in order:
                if oi in done:
                    continue
                r = pos[segs[oi][1]]
                for sh in SH * box:
                    dd = cdist(r + sh, placed).min()
                    if dd < bd:
                        bd, bsh, bs = dd, sh, oi
            if np.any(np.abs(bsh) > 1e-3):
                pos[segs[bs][0]] += bsh
            placed = np.vstack([placed, pos[segs[bs][1]]]); done.add(bs)
        return pos

    tmp = d / "traj.contact.tmp.xtc"
    noncompact = 0; nfr = len(u.trajectory)
    with mda.Writer(str(tmp), pl.n_atoms) as W:
        for ts in u.trajectory:
            box = u.dimensions[:3].copy()
            pos = assemble(pl.positions.copy(), box)
            if (pos.ptp(0) / box > 1.15).any():
                noncompact += 1
            pl.positions = pos
            W.write(pl)
    print(f"{sid}: {noncompact}/{nfr} frames non-compact (>1.15 box) after assembly")

    fix_structure(sid, mda.Universe(str(pdb), str(tmp)))
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.move(str(traj), str(traj) + f".broken_pbc_{ts}")
    align.AlignTraj(mda.Universe(str(pdb), str(tmp)), mda.Universe(str(pdb)),
                    select="name CA", filename=str(traj)).run()
    tmp.unlink(missing_ok=True)
    print(f"DONE {sid}")


if __name__ == "__main__":
    main()
