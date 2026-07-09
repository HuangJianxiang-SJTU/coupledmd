#!/usr/bin/env python3
"""Temporally-consistent chain imaging for elongated GPCR-G complexes that diffuse
across the periodic boundary (Gq_8DPF, Gi_8J22, G12_8H8J). Per-frame greedy
assembly is ambiguous for these (~1.3-1.5 box long): round() flips a chain's image
between adjacent frames, producing a chain that jumps a box back and forth. The
fix is nojump-on-chains:

  frame 0  : greedy proximity assembly of the chain-role segments into one image.
  frame i>0: shift each chain by integer box vectors so its centroid is closest to
             its OWN centroid in frame i-1 (temporal continuity — no flipping).

Input is the stage-1 `gmx -pbc whole -skip 4` xtc (molecules already whole). Then
per-frame CA Kabsch fit to structure.pdb. Also fixes structure.pdb (reassembly +
CRYST1 + elements) so the static reference matches.

Usage: python3 scripts/fix_viz_gromacs_nojump.py SYS TPR WHOLE_XTC
"""
import sys, json, shutil, datetime, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np
import MDAnalysis as mda
from MDAnalysis.analysis import align

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "data" / "viz"
ROLES = ROOT / "scripts" / "audit_output" / "chain_roles"
sys.path.insert(0, str(ROOT / "scripts"))
from fix_viz_inplace import assemble as greedy_assemble, fix_structure


def main():
    sid, tpr, whole = sys.argv[1], sys.argv[2], sys.argv[3]
    d = VIZ / sid; pdb = d / "structure.pdb"; traj = d / "traj.xtc"
    ref = mda.Universe(str(pdb))
    u = mda.Universe(tpr, whole)
    protlig = u.select_atoms("not resname POPC SOD CLA")
    if protlig.n_atoms != ref.atoms.n_atoms:
        sys.exit(f"ATOM COUNT MISMATCH {protlig.n_atoms} vs {ref.atoms.n_atoms}")

    # role segments as index arrays INTO protlig
    roles = json.load(open(ROLES / f"{sid}_chain_roles.json"))["roles"]
    pl_resids = protlig.residues.resids
    # map: build per-chain atom-index arrays within protlig by residue range
    segs = []
    # protlig atoms in order; use a structure.pdb-based resid selection on protlig
    rl = mda.Universe(str(pdb))  # has resids 1..N matching viz
    for lbl, info in roles.items():
        r0, r1 = [int(x) for x in info["resid_range"].split("-")]
        idx = rl.select_atoms(f"resid {r0}:{r1}").indices
        if len(idx):
            segs.append(idx)

    tmp = d / "traj.nojump.tmp.xtc"
    prev_cens = None
    with mda.Writer(str(tmp), protlig.n_atoms) as W:
        for ts in u.trajectory:
            box = u.dimensions[:3].copy()
            pos = protlig.positions.copy()
            if prev_cens is None:
                # frame 0: greedy proximity assembly
                seglist = [(i, s) for i, s in enumerate(segs)]
                pos = greedy_assemble(pos, seglist, box)
            else:
                # nojump: each chain to the image nearest its previous centroid
                for s, pc in zip(segs, prev_cens):
                    c = pos[s].mean(0)
                    shift = box * np.round((pc - c) / box)
                    if np.any(np.abs(shift) > 1e-3):
                        pos[s] += shift
            prev_cens = [pos[s].mean(0) for s in segs]
            protlig.positions = pos
            W.write(protlig)

    # fix structure.pdb (reassembly + CRYST1 + elements) before the CA fit
    fix_structure(sid, mda.Universe(str(pdb), str(tmp)))

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.move(str(traj), str(traj) + f".broken_pbc_{ts}")
    align.AlignTraj(mda.Universe(str(pdb), str(tmp)), mda.Universe(str(pdb)),
                    select="name CA", filename=str(traj)).run()
    tmp.unlink(missing_ok=True)
    print(f"DONE {sid}")


if __name__ == "__main__":
    main()
