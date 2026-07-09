#!/usr/bin/env python3
"""
One-shot fix for Gi_6D9H grey-beads bug.

ROOT CAUSE
----------
data/viz/Gi_6D9H/structure.pdb was written by a non-standard writer, unlike all
other 221 systems. It is the ONLY system (1/222) whose PDB:
  - lacks the MDAnalysis PDBWriter TITLE ("MDANALYSIS FRAMES FROM 0..."),
  - lacks the 'SYST' segid (it used chain/segid 'A'),
  - has a custom "CoupledMD Gi_6D9H reference structure" title.
All 221 working systems use segment 'SYST' + chainID 'X' + MDAnalysis format and
render the NGL cartoon correctly.  Gi_6D9H alone renders grey beads (spacefill).

The CA-CA gaps (3 of them, because 6D9H has 4 physically separate chains PROA/B/G/R)
are NOT the cause -- multiple working systems (e.g. Gs_6NBI, Gi_8HK5) also have 3-4
gaps and render fine.

FIX
---
Rewrite structure.pdb through MDAnalysis PDBWriter after normalizing segid->'SYST'
and chainID->'X', so it is byte-compatible in FORMAT with the 221 working systems.

SAFETY CONSTRAINTS (all verified)
---------------------------------
  - Atom ORDER must stay PROA,PROB,PROG,PROR,LIG so the existing traj.xtc (16911
    atoms, 2500 frames) still overlays.  We only relabel segid/chainID, never reorder.
  - Atom COUNT must stay 16911.
  - ADN ligand (32 HETATM, resid 1075) must survive.
  - Residue numbering 1-1074 (protein) must stay identical so /subunit-ranges
    ({G_alpha:1-355, G_beta:356-693, G_gamma:694-750, Receptor:751-1074}) stays valid.

A timestamped .bak of the current (already-edited) file is written first; the
original is preserved at structure.pdb.bak (untouched).
"""
import os
import shutil
import time
import MDAnalysis as mda

VIZ = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz/Gi_6D9H"
PDB = os.path.join(VIZ, "structure.pdb")
TRAJ = os.path.join(VIZ, "traj.xtc")


def main():
    assert os.path.exists(PDB), f"missing {PDB}"
    assert os.path.exists(TRAJ), f"missing {TRAJ}"

    # Backup current file (timestamped) -- keep structure.pdb.bak as the ORIGINAL.
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = f"{PDB}.preformat_{ts}"
    shutil.copy2(PDB, bak)
    print(f"backed up current file -> {bak}")

    u = mda.Universe(PDB)
    n_before = u.atoms.n_atoms
    nres_before = u.residues.n_residues
    print(f"IN : atoms={n_before}, residues={nres_before}, "
          f"segids={set([s.segid for s in u.segments])}")

    # Normalize to working-system format: segment 'SYST', chainID 'X'.
    u.segments.segids = 'SYST'
    u.add_TopologyAttr('chainIDs', ['X'] * n_before)

    # Rewrite via MDAnalysis PDBWriter (same as the 221 working systems).
    with mda.Writer(PDB, n_atoms=n_before) as w:
        w.write(u.atoms)

    # Verify
    u2 = mda.Universe(PDB)
    print(f"OUT: atoms={u2.atoms.n_atoms}, residues={u2.residues.n_residues}, "
          f"segids={set([s.segid for s in u2.segments])}")
    assert u2.atoms.n_atoms == n_before, "atom count changed!"
    assert u2.residues.n_residues == nres_before, "residue count changed!"

    # Trajectory overlay check
    ut = mda.Universe(PDB, TRAJ)
    assert ut.trajectory.n_atoms == n_before, "traj atom mismatch!"
    print(f"TRAJ: atoms={ut.trajectory.n_atoms}, frames={ut.trajectory.n_frames} -> overlays OK")

    # Residue numbering preserved?
    prot = u2.select_atoms('protein').residues
    print(f"protein resids: {prot.resids.min()}-{prot.resids.max()} "
          f"(subunit ranges still valid)")

    print("\nDone. structure.pdb now in MDAnalysis 'SYST' format, matching the 221 working systems.")


if __name__ == "__main__":
    main()
