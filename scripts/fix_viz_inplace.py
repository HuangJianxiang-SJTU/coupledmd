#!/usr/bin/env python3
"""In-place PBC fix for viz systems whose only defect is a WHOLE chain/segment
imaged one box vector away (the "whole-segment wrap" class — reassembly by chain
collapses the all-atom span back below the box). No source trajectory is needed:
the existing data/viz/<sys>/traj.xtc already carries every frame; we just snap each
chain back into one periodic image, then re-fit.

For each frame (and for structure.pdb) we apply GREEDY PROXIMITY assembly over the
chain-role segments: place the largest segment, then translate each remaining
segment by integer box vectors so its centroid is closest to an already-placed
segment. This walks the binding graph (receptor-Galpha-Gbeta-Ggamma, ligand-
receptor) and is stable because bound partners are <half-box apart in the correct
image (single-anchor reimaging strands an end chain of an elongated complex —
see docs/VIZ_PBC_FIX.md). It does NOT touch internal coordinates, only rigid
integer-box translations of whole chains.

Steps:
  1. structure.pdb: reassemble its single frame, rewrite CRYST1 to the trajectory
     box, assign elements to blank atoms, surgical column-preserving write.
     Backup -> structure.pdb.pre_reassembly.
  2. traj.xtc: per-frame reassemble -> temp xtc -> per-frame CA Kabsch fit to the
     fixed structure.pdb -> traj.xtc. Backup -> traj.xtc.broken_pbc_<ts>.

Usage:  python3 scripts/fix_viz_inplace.py SYSTEM_ID [SYSTEM_ID ...]
"""
import sys, json, shutil, warnings, datetime
warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np
import MDAnalysis as mda
from MDAnalysis.analysis import align

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "data" / "viz"
ROLES = ROOT / "scripts" / "audit_output" / "chain_roles"


def load_segments(sid, u):
    """Return list of (label, atom-index array) from chain_roles.json."""
    roles = json.load(open(ROLES / f"{sid}_chain_roles.json"))["roles"]
    segs = []
    for lbl, info in roles.items():
        r0, r1 = [int(x) for x in info["resid_range"].split("-")]
        idx = u.select_atoms(f"resid {r0}:{r1}").indices
        if len(idx):
            segs.append((lbl, idx))
    return segs


def assemble(pos, segs, box):
    """Greedy proximity assembly. Returns a copy of pos with whole segments
    translated by integer box vectors into one periodic image."""
    pos = pos.copy()
    order = sorted(segs, key=lambda s: -len(s[1]))
    placed_cens = [pos[order[0][1]].mean(0)]
    for _, idx in order[1:]:
        c = pos[idx].mean(0)
        best_shift, best_d = np.zeros(3), np.inf
        for pc in placed_cens:
            shift = box * np.round((pc - c) / box)
            d = np.linalg.norm((c + shift) - pc)
            if d < best_d:
                best_d, best_shift = d, shift
        if np.any(np.abs(best_shift) > 1e-3):
            pos[idx] += best_shift
        placed_cens.append(pos[idx].mean(0))
    return pos


def fix_structure(sid, u_traj):
    """Reassemble structure.pdb, rewrite CRYST1 to the traj box, assign elements,
    surgical column-preserving write. Returns nothing; writes in place."""
    pdb = VIZ / sid / "structure.pdb"
    u = mda.Universe(str(pdb))
    u_traj.trajectory[0]
    box = np.array(u_traj.dimensions[:3], dtype=float)   # true trajectory box
    segs = load_segments(sid, u)
    pos = assemble(u.atoms.positions, segs, box)

    lines = open(pdb).readlines()
    cryst = (f"CRYST1{box[0]:9.3f}{box[1]:9.3f}{box[2]:9.3f}"
             f"  90.00  90.00  90.00 P 1           1\n")
    out, ai, cryst_done = [], 0, False
    for line in lines:
        if line.startswith("CRYST1"):
            if not cryst_done:
                out.append(cryst); cryst_done = True
            continue
        if line.startswith(("ATOM", "HETATM")):
            x, y, z = pos[ai]; ai += 1
            l = line.rstrip("\n")
            l = l[:30] + f"{x:8.3f}{y:8.3f}{z:8.3f}" + l[54:]
            elem = l[76:78].strip() if len(l) >= 78 else ""
            if elem == "":
                nm = l[12:16].strip().lstrip("0123456789")
                elem = "H" if nm.startswith("LP") else (nm[0].upper() if nm else "C")
                if len(l) < 78:
                    l = l.ljust(78)
                l = l[:76] + f"{elem:>2s}" + l[78:]
            out.append(l + "\n")
        else:
            out.append(line)
    if not cryst_done:
        out.insert(0, cryst)
    if ai != u.atoms.n_atoms:
        sys.exit(f"{sid}: PDB atom-order mismatch ({ai} vs {u.atoms.n_atoms})")
    shutil.copy2(pdb, str(pdb) + ".pre_reassembly")
    open(pdb, "w").writelines(out)
    return box


def fix_traj(sid, segs):
    """Per-frame reassemble -> CA fit to fixed structure.pdb -> traj.xtc."""
    d = VIZ / sid
    pdb, traj = d / "structure.pdb", d / "traj.xtc"
    ref = mda.Universe(str(pdb))
    u = mda.Universe(str(pdb), str(traj))
    n = u.atoms.n_atoms
    tmp = d / "traj.reassembled.tmp.xtc"
    with mda.Writer(str(tmp), n) as W:
        for ts in u.trajectory:
            box = u.dimensions[:3].copy()
            u.atoms.positions = assemble(u.atoms.positions, segs, box)
            W.write(u.atoms)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.move(str(traj), str(traj) + f".broken_pbc_{ts}")
    align.AlignTraj(mda.Universe(str(pdb), str(tmp)), ref,
                    select="name CA", filename=str(traj)).run()
    tmp.unlink(missing_ok=True)


def verify(sid):
    u = mda.Universe(str(VIZ / sid / "structure.pdb"), str(VIZ / sid / "traj.xtc"))
    ref = mda.Universe(str(VIZ / sid / "structure.pdb"))
    u.trajectory[0]
    r0 = np.sqrt(((u.atoms.positions - ref.atoms.positions) ** 2).sum(1).mean())
    mx = np.zeros(3)
    for fi in np.linspace(0, len(u.trajectory) - 1, 20).astype(int):
        u.trajectory[fi]
        p = u.atoms.positions
        mx = np.maximum(mx, p.ptp(0) / u.dimensions[:3])
    blank = int((ref.atoms.elements == "").sum()) if hasattr(ref.atoms, "elements") else -1
    print(f"  VERIFY {sid}: frame0_RMSD={r0:.2f}A  max_span/box={mx.round(2)}  blank_elem={blank}")
    return mx.max()


def main():
    for sid in sys.argv[1:]:
        print(f"=== {sid} ===")
        u_traj = mda.Universe(str(VIZ / sid / "structure.pdb"), str(VIZ / sid / "traj.xtc"))
        segs = load_segments(sid, u_traj)
        fix_structure(sid, u_traj)
        fix_traj(sid, segs)
        verify(sid)


if __name__ == "__main__":
    main()
