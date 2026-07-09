#!/usr/bin/env python3
"""Rename HSD/HSP -> HIS in Gi_6D9H structure.pdb so NGLView cartoon renders continuously."""
import os, shutil, time
import MDAnalysis as mda

VIZ = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz/Gi_6D9H"
PDB = os.path.join(VIZ, "structure.pdb")
TRAJ = os.path.join(VIZ, "traj.xtc")

def main():
    assert os.path.exists(PDB), f"missing {PDB}"

    # Backup
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = f"{PDB}.resname_bak_{ts}"
    shutil.copy2(PDB, bak)
    print(f"backed up -> {bak}")

    u = mda.Universe(PDB)
    n_before = u.atoms.n_atoms
    print(f"IN: atoms={n_before}")

    # Rename HSD -> HIS
    hsd = u.select_atoms("resname HSD")
    n_hsd = hsd.n_atoms
    hsd.residues.resnames = "HIS"
    print(f"renamed HSD ({n_hsd} atoms) -> HIS")

    # Rename HSP -> HIS
    hsp = u.select_atoms("resname HSP")
    n_hsp = hsp.n_atoms
    hsp.residues.resnames = "HIS"
    print(f"renamed HSP ({n_hsp} atoms) -> HIS")

    # Rewrite PDB (same format as the 221 working systems)
    with mda.Writer(PDB, n_atoms=n_before) as w:
        w.write(u.atoms)

    # Verify
    u2 = mda.Universe(PDB)
    assert u2.atoms.n_atoms == n_before, "atom count changed!"
    remaining = u2.select_atoms("resname HSD or resname HSP")
    print(f"OUT: atoms={u2.atoms.n_atoms}, remaining HSD/HSP={remaining.n_atoms}")

    # Trajectory overlay check
    ut = mda.Universe(PDB, TRAJ)
    assert ut.trajectory.n_atoms == n_before, "traj atom mismatch!"
    print(f"TRAJ: atoms={ut.trajectory.n_atoms}, frames={ut.trajectory.n_frames} -> overlays OK")

    print("\nDone. HSD/HSP → HIS. NGLView cartoon should now render continuously.")

if __name__ == "__main__":
    main()
