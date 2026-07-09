#!/usr/bin/env python3
"""Reassemble a PBC-scattered GROMACS viz trajectory from the full-solvated
source (now.tpr + prod1_now.trr).

Two stages — gmx does the molecule-making (fast, sequential read of the big trr),
this script does the cheap chain assembly + fit:

  STAGE 1 (run separately, in the source dir):
      printf 'System\n' | gmx trjconv -s now.tpr -f prod1_now.trr \
          -pbc whole -skip 4 -o whole.xtc
    `-pbc whole` with the REAL tpr makes every molecule whole via its true bond
    list — it does NOT abort with "inconsistent shifts" the way the fake-TPR /
    protein-only attempts did, and reading sequentially is far faster than the
    random-access MDAnalysis seeks the trr would need. (Do NOT use MDAnalysis
    `unwrap()` here — it runs at ~1 s/frame, hours for 2500 frames.)

  STAGE 2 (this script, given the small whole.xtc):
      1. Load now.tpr (for atom selection + fragments) + whole.xtc.
      2. Select protein+ligand = everything except POPC/SOD/CLA (matches the viz
         structure.pdb atom order exactly, verified per system).
      3. Per frame: iterative-centroid assembly — shift each (already-whole)
         fragment by integer box vectors toward the running complex centroid
         until converged, so separate chains land in one periodic image.
      4. Per-frame Kabsch fit (CA) to structure.pdb → smooth playback, frame0≈ref.

Usage:
    python3 scripts/fix_viz_gromacs.py SYSTEM_ID TPR WHOLE_XTC [--stride 1]
(WHOLE_XTC is the stage-1 output; use --stride 1 since it is already decimated.)
"""
import argparse, warnings, sys
warnings.filterwarnings('ignore')
import numpy as np
import MDAnalysis as mda
from MDAnalysis.analysis import align
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def assemble(frags, box):
    """Greedy proximity assembly of whole fragments into one periodic image.

    A single global anchor (centroid OR largest chain) FAILS for a GPCR–G
    complex because it is elongated (~1.1 box): chains at opposite ends sit
    ~half a box apart, where round(0.45)=0 / round(0.5) is ambiguous and the
    wrong image is picked. The fix: place the largest chain, then add each
    remaining chain in the image that puts its centroid CLOSEST to an
    already-placed chain. Bound partners are in contact (<half box) in the
    correct image, so each step's round(...) is unambiguous — this walks the
    binding graph (receptor→Gα→Gβ→Gγ, ligand→receptor) without needing to know
    it. Equivalent to `gmx -pbc cluster` / cpptraj `autoimage`."""
    order = sorted(frags, key=lambda f: -f.n_atoms)
    placed = [order[0]]
    placed_cens = [order[0].positions.mean(0)]
    for f in order[1:]:
        c = f.positions.mean(0)
        best_shift, best_d = np.zeros(3), np.inf
        for pc in placed_cens:
            shift = box * np.round((pc - c) / box)
            d = np.linalg.norm((c + shift) - pc)
            if d < best_d:
                best_d, best_shift = d, shift
        if np.any(np.abs(best_shift) > 1e-3):
            f.translate(best_shift)
        placed.append(f)
        placed_cens.append(f.positions.mean(0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('system')
    ap.add_argument('tpr')
    ap.add_argument('trr')
    ap.add_argument('--stride', type=int, default=4)
    ap.add_argument('--maxframes', type=int, default=0, help='for testing: cap frames read')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    viz_pdb = ROOT / 'data' / 'viz' / args.system / 'structure.pdb'
    out = Path(args.out) if args.out else ROOT / 'data' / 'viz' / args.system / 'traj.xtc'
    tmp = out.with_suffix('.assembled.tmp.xtc')

    ref = mda.Universe(str(viz_pdb))
    u = mda.Universe(args.tpr, args.trr)
    protlig = u.select_atoms('not resname POPC SOD CLA')
    if protlig.n_atoms != ref.atoms.n_atoms:
        sys.exit(f'ATOM COUNT MISMATCH: protlig {protlig.n_atoms} vs viz {ref.atoms.n_atoms}')
    if not (protlig.names == ref.atoms.names).all():
        sys.exit('ATOM ORDER MISMATCH between protlig selection and structure.pdb')
    frags = list(protlig.fragments)
    nfr = len(u.trajectory)
    idx = list(range(0, nfr, args.stride))
    if args.maxframes:
        idx = idx[:args.maxframes]
    print(f'{args.system}: {protlig.n_atoms} atoms, {len(frags)} fragments, '
          f'writing {len(idx)} frames (stride {args.stride}) of {nfr}')

    with mda.Writer(str(tmp), protlig.n_atoms) as W:
        for n, i in enumerate(idx):
            u.trajectory[i]
            box = u.dimensions[:3].copy()
            assemble(frags, box)
            W.write(protlig)
            if n % 500 == 0:
                print(f'  frame {n}/{len(idx)}', flush=True)

    # per-frame CA fit to structure.pdb
    align.AlignTraj(mda.Universe(str(viz_pdb), str(tmp)), ref,
                    select='name CA', filename=str(out)).run()
    tmp.unlink(missing_ok=True)

    v = mda.Universe(str(viz_pdb), str(out))
    v.trajectory[0]
    r0 = np.sqrt(((v.atoms.positions - ref.atoms.positions) ** 2).sum(1).mean())
    mx = np.zeros(3)
    for fi in np.linspace(0, len(v.trajectory) - 1, 15).astype(int):
        v.trajectory[fi]
        p = v.atoms.positions
        mx = np.maximum(mx, np.array([p[:, 0].ptp(), p[:, 1].ptp(), p[:, 2].ptp()]) / v.dimensions[:3])
    print(f'DONE {args.system}: frames {len(v.trajectory)}, frame0 RMSD {r0:.2f} A, '
          f'max span/box {mx.round(2)}')


if __name__ == '__main__':
    main()
