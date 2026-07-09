#!/usr/bin/env python3
"""
Fix PBC artifacts in a viz trajectory using a PDB-only fake-TPR approach.

Generalizable across GROMACS and AMBER systems: needs only the protein+ligand
PDB and the full-resolution source trajectory. See docs/VIZ_PBC_FIX.md for the
full rationale and worked example.

Subcommands (run in order):
  build-fake-tpr  : guess bonds in PDB (drop >2.5 Å PBC artifacts), gmx grompp
                    → fake TPR carrying molecule/bond connectivity.
  make-ndx        : write alpha5_CA + System index from the PDB.
  src-to-xtc      : MDAnalysis reads any source traj (.nc/.trr/.xtc/...) and
                    writes a full-resolution .xtc (gmx can't read AMBER .nc).
  assemble        : per-chain nearest-image reimage + alpha5 Kabsch fit to
                    structure.pdb + decimate. Run AFTER `gmx trjconv -pbc
                    cluster` on the full-res xtc.
  update-db       : refresh system_viz_files row (file_size_bytes/n_frames).

Typical pipeline for one system:
  python3 scripts/fix_viz_pbc_pdb.py build-fake-tpr --pdb ... --roles ... --outdir /tmp/<sys>_fake
  gmx grompp -f /tmp/<sys>_fake/fake.mdp -c /tmp/<sys>_fake/fake.gro -p /tmp/<sys>_fake/fake.top -o /tmp/<sys>_fake/fake.tpr -maxwarn 5
  python3 scripts/fix_viz_pbc_pdb.py make-ndx --pdb ... --out /tmp/<sys>.ndx
  python3 scripts/fix_viz_pbc_pdb.py src-to-xtc --pdb ... --src <nc/trr/xtc> --out /tmp/<sys>_fullres.xtc
  printf '1\\n1\\n' | gmx trjconv -s /tmp/<sys>_fake/fake.tpr -f /tmp/<sys>_fullres.xtc -n /tmp/<sys>.ndx -o /tmp/<sys>_cluster.xtc -pbc cluster
  python3 scripts/fix_viz_pbc_pdb.py assemble --pdb ... --cluster /tmp/<sys>_cluster.xtc --roles ... --ndx /tmp/<sys>.ndx --out data/viz/<sys>/traj.xtc --stride 4
  python3 scripts/fix_viz_pbc_pdb.py update-db --system <sys>
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

MAX_BOND_A = 2.5  # real covalent bonds are <2.5 Å; longer = PBC artifact in PDB
VDW = {'H': 1.1, 'C': 1.7, 'N': 1.55, 'O': 1.52, 'S': 1.8, 'P': 1.8}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIZ_DIR = PROJECT_ROOT / "data" / "viz"
ROLES_DIR = PROJECT_ROOT / "scripts" / "audit_output" / "chain_roles"
DB_PATH = PROJECT_ROOT / "db" / "coupledmd.sqlite"


def _load_segments(u, roles_path):
    """List of (label, AtomGroup). Split by PDB segid, else by chain_roles.json."""
    segids = list(dict.fromkeys(u.residues.segids.astype(str)))
    if len(segids) > 1:
        return [(s, u.select_atoms(f"segid {s}")) for s in segids]
    if roles_path and Path(roles_path).exists():
        roles = json.load(open(roles_path))["roles"]
        segs = []
        for label, info in roles.items():
            rmin, rmax = [int(x) for x in info["resid_range"].split("-")]
            ag = u.select_atoms(f"resid {rmin}:{rmax}")
            if ag.n_atoms:
                segs.append((label, ag))
        if segs:
            return segs
    return [("MOL", u.atoms)]


def _read_alpha5_ndx(ndx_path):
    a5 = []
    with open(ndx_path) as f:
        ina = False
        for line in f:
            if '[ alpha5_CA ]' in line:
                ina = True; continue
            if line.startswith('['):
                ina = False; continue
            if ina:
                a5.extend(int(x) - 1 for x in line.split())
    return np.array(a5)


def cmd_build_fake_tpr(args):
    """Subcommand: build fake topology + gro + mdp from PDB."""
    import warnings; warnings.filterwarnings("ignore")
    import MDAnalysis as mda
    u = mda.Universe(args.pdb)
    u.guess_TopologyAttrs(context='default', to_guess=['elements', 'types'])
    u.atoms[u.atoms.elements == ''].elements = 'C'
    u.atoms[u.atoms.types == ''].types = 'C'
    u.atoms.guess_bonds(vdwradii=VDW)

    pos = u.atoms.positions
    all_bonds = u.bonds.to_indices()
    blens = np.linalg.norm(pos[all_bonds[:, 0]] - pos[all_bonds[:, 1]], axis=1)
    keep = blens <= MAX_BOND_A
    n_drop = int((~keep).sum())
    if n_drop:
        print(f"Dropping {n_drop} spurious bonds (>{MAX_BOND_A} Å, PBC artifacts in PDB)")
    good = all_bonds[keep]
    print(f"PDB: {u.atoms.n_atoms} atoms, {u.residues.n_residues} residues, "
          f"{len(good)} real bonds kept")

    segs = _load_segments(u, args.roles)
    # catch-all for atoms not covered by any role (unassigned ligands/ions) —
    # they must be in the topology or grompp aborts on a coord/topology count
    # mismatch. Each becomes its own single-atom moleculetype (no guessed bonds
    # to roles' atoms) so cluster treats it as a movable unit.
    covered = set()
    for _lbl, ag in segs:
        covered.update(ag.indices.tolist())
    uncovered_idx = [i for i in u.atoms.indices if i not in covered]
    if uncovered_idx:
        unc_ag = u.atoms[uncovered_idx]
        # group uncovered atoms by residue so each residue is one molecule
        for res in unc_ag.residues:
            segs.append((f"UNC_{res.resname[:4]}", res.atoms))
        print(f"  + {len(uncovered_idx)} uncovered atoms ({len(unc_ag.residues)} residues) "
              f"added as catch-all moleculetypes")
    print(f"Molecules: {len(segs)}")

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    top = outdir / "fake.top"; gro = outdir / "fake.gro"; mdp = outdir / "fake.mdp"

    def sane(s):
        return "".join(c if c.isalnum() else "_" for c in str(s))[:8] or "MOL"

    mol_names = []
    with open(top, "w") as f:
        f.write("; Fake topology for PBC post-processing\n")
        f.write("[ defaults ]\n1 2 no 1.0 1.0\n\n")
        f.write("[ atomtypes ]\n; name bond_type atomic_number mass charge ptype sigma epsilon\n")
        f.write("X X 6 12.000 0.000 A 0.340 0.276\n\n")
        f.write("[ bondtypes ]\n; i j func b0 kb\nX X 1 0.15 250000\n\n")
        for label, ag in segs:
            name = sane(label); base, k = name, 1
            while name in mol_names:
                k += 1; name = f"{base[:6]}{k}"
            mol_names.append(name)
            local_idx = {g: i + 1 for i, g in enumerate(ag.indices)}
            seg_set = set(ag.indices.tolist())
            seg_bonds = set((local_idx[i], local_idx[j]) for i, j in good
                            if i in seg_set and j in seg_set)
            # CRITICAL: also add a sequential backbone bond between consecutive
            # residues (first-atom of residue k -> first-atom of residue k+1).
            # The geometry-guessed bonds above are severed when the reference PDB
            # itself has PBC breaks (a chain fragments into N connected components),
            # which makes `gmx -pbc cluster` treat each fragment as a separate
            # cluster and leaves the chain broken. The sequential bond guarantees a
            # single connected molecule per chain regardless of PBC geometry, so
            # cluster can reimage the whole chain into one image.
            res_iter = list(ag.residues)
            for k in range(len(res_iter) - 1):
                a0 = res_iter[k].atoms[0]
                a1 = res_iter[k + 1].atoms[0]
                if a0.index != a1.index:
                    seg_bonds.add((local_idx[a0.index], local_idx[a1.index]))
            seg_bonds = sorted(seg_bonds)
            print(f"  {label}: {ag.n_atoms} atoms, {len(seg_bonds)} bonds")
            f.write(f"[ moleculetype ]\n; name nrexcl\n{name} 3\n\n[ atoms ]\n")
            f.write("; nr type resnr residue atom cgnr mass\n")
            for i, a in enumerate(ag, start=1):
                f.write(f"{i:6d} X {a.resindex+1:5d} {a.resname[:5]:<5s} {a.name[:5]:<5s} {i:5d} 12.000\n")
            f.write("\n[ bonds ]\n; ai aj funct\n")
            for i, j in seg_bonds:
                f.write(f"{i:6d} {j:6d} 1\n")
            f.write("\n")
        f.write("[ system ]\nFake PBC system\n\n[ molecules ]\n; Compound #mols\n")
        for name in mol_names:
            f.write(f"{name} 1\n")

    with mda.Writer(str(gro), n_atoms=u.atoms.n_atoms):
        u.atoms.write(str(gro))
    with open(mdp, "w") as f:
        f.write("integrator = md\nnsteps = 0\ndt = 0\ncutoff-scheme = Verlet\n")
    print(f"\nWrote: {top}, {gro}, {mdp}")
    print(f"Run: gmx grompp -f {mdp} -c {gro} -p {top} -o {outdir/'fake.tpr'} -maxwarn 5")


def cmd_make_ndx(args):
    """Subcommand: write alpha5_CA + System index from PDB.

    alpha5 = the C-terminal ~21 residues of G_alpha (the helix that inserts
    into the receptor), derived from --roles when available. Falls back to the
    hardcoded resid 330:350 only if no roles file is given (the Gi_8YIC case).
    """
    import warnings; warnings.filterwarnings("ignore")
    import MDAnalysis as mda
    u = mda.Universe(args.pdb)
    sel = "name CA and resid 330:350"
    if args.roles and Path(args.roles).exists():
        roles = json.load(open(args.roles))["roles"]
        if "G_alpha" in roles:
            r0, r1 = [int(x) for x in roles["G_alpha"]["resid_range"].split("-")]
            # last 21 residues of G_alpha = the alpha5 helix
            a5_lo, a5_hi = max(r0, r1 - 20), r1
            sel = f"name CA and resid {a5_lo}:{a5_hi}"
            print(f"alpha5 from roles: G_alpha {r0}-{r1} -> {a5_lo}:{a5_hi}")
    a5 = u.select_atoms(sel)
    if a5.n_atoms == 0:
        sys.exit(f"ERROR: no CA atoms at selection '{sel}' — check roles/G_alpha range")
    print(f"alpha5_CA: {a5.n_atoms} atoms")
    with open(args.out, "w") as f:
        f.write("[ alpha5_CA ]\n")
        idx = (a5.atoms.indices + 1).tolist()
        for i in range(0, len(idx), 15):
            f.write(" ".join(map(str, idx[i:i+15])) + "\n")
        f.write("[ System ]\n")
        idx = (u.atoms.indices + 1).tolist()
        for i in range(0, len(idx), 15):
            f.write(" ".join(map(str, idx[i:i+15])) + "\n")
    print(f"Wrote: {args.out}")


def cmd_src_to_xtc(args):
    """Subcommand: read any source trajectory via MDAnalysis, write full-res XTC."""
    import warnings; warnings.filterwarnings("ignore")
    import MDAnalysis as mda
    from MDAnalysis.coordinates.XTC import XTCWriter
    u = mda.Universe(args.pdb, args.src)
    print(f"source: {u.atoms.n_atoms} atoms, {len(u.trajectory)} frames")
    n = 0
    with XTCWriter(args.out, n_atoms=u.atoms.n_atoms) as w:
        for ts in u.trajectory:
            w.write(u.atoms); n += 1
            if n % 2000 == 0:
                print(f"  {n}/{len(u.trajectory)} frames...")
    print(f"Wrote {n} frames -> {args.out} ({os.path.getsize(args.out)/1e6:.1f} MB)")


def cmd_assemble(args):
    """Subcommand: per-chain reimage + alpha5 Kabsch fit + decimate."""
    import warnings; warnings.filterwarnings("ignore")
    import MDAnalysis as mda
    from MDAnalysis.coordinates.XTC import XTCWriter
    u = mda.Universe(args.pdb, args.cluster)
    u_ref = mda.Universe(args.pdb)
    chains = {}
    for name, (r0, r1) in _chain_ranges_from_roles(args.roles, u):
        chains[name] = u.select_atoms(f"resid {r0}:{r1}").indices
    ref_centroids = {n: u_ref.atoms.positions[idx].mean(0) for n, idx in chains.items()}
    a5 = _read_alpha5_ndx(args.ndx)
    ref_a5 = u_ref.atoms.positions[a5]

    def rot_to(P, Q):
        Pc = P - P.mean(0); Qc = Q - Q.mean(0)
        C = Pc.T @ Qc; V, S, Wt = np.linalg.svd(C)
        d = np.sign(np.linalg.det(V @ Wt)); D = np.diag([1, 1, d]); U = V @ D @ Wt
        return U, P.mean(0), Q.mean(0)

    n_out = 0
    with XTCWriter(args.out, n_atoms=u.atoms.n_atoms) as w:
        for i, ts in enumerate(u.trajectory):
            if args.stride and i % args.stride != 0:
                continue
            box = ts.dimensions[:3]
            pos = u.atoms.positions.copy()
            for name, idx in chains.items():
                cc = pos[idx].mean(0)
                pos[idx] += np.round((ref_centroids[name] - cc) / box) * box
            U, cmob, cref = rot_to(pos[a5], ref_a5)
            u.atoms.positions = (pos - cmob) @ U + cref
            w.write(u.atoms); n_out += 1
    print(f"Wrote {n_out} frames -> {args.out} ({os.path.getsize(args.out)/1e6:.1f} MB)")


def cmd_assemble_multipass(args):
    """Subcommand: anchor-based complex imaging + alpha5 Kabsch fit + decimate.

    The stable assembly method for multi-chain complexes. `gmx -pbc cluster`
    keeps each chain internally whole but leaves separate chains in different
    periodic images. Per frame: anchor on G_alpha (kept fixed within the frame)
    and shift every other chain by integer box vectors so its centroid is in the
    nearest image to the anchor centroid (``round((anchor_c - chain_c)/box)*box``).
    This is iterated a few passes (the anchor is recomputed each pass from the
    already-assembled chains) so a chain that was the anchor's neighbour can in
    turn pull a farther chain. Then Kabsch-fit alpha5 to structure.pdb.

    NOTE: anchoring on the moving *complex* centroid (an earlier version) is
    WRONG — a single mis-imaged chain (e.g. a peptide ligand straddling a box
    edge) corrupts the centroid and every chain reads as within-half-box of it,
    so nothing moves. Anchoring on G_alpha (the central, largest chain) avoids
    this. Reimagining to the *reference PDB* centroids (as `assemble` does)
    drifts/flips between frames — do not use that for multi-chain.
    """
    import warnings; warnings.filterwarnings("ignore")
    import MDAnalysis as mda
    from MDAnalysis.coordinates.XTC import XTCWriter
    u = mda.Universe(args.pdb, args.cluster)
    u_ref = mda.Universe(args.pdb)
    chains = {}
    for name, (r0, r1) in _chain_ranges_from_roles(args.roles, u):
        chains[name] = u.select_atoms(f"resid {r0}:{r1}").indices
    anchor = "G_alpha" if "G_alpha" in chains else ("Receptor" if "Receptor" in chains else list(chains)[0])
    a5 = _read_alpha5_ndx(args.ndx)
    ref_a5 = u_ref.atoms.positions[a5]

    def rot_to(P, Q):
        Pc = P - P.mean(0); Qc = Q - Q.mean(0)
        C = Pc.T @ Qc; V, S, Wt = np.linalg.svd(C)
        d = np.sign(np.linalg.det(V @ Wt)); D = np.diag([1, 1, d]); U = V @ D @ Wt
        return U, P.mean(0), Q.mean(0)

    n_out = 0; n_passes = 0
    with XTCWriter(args.out, n_atoms=u.atoms.n_atoms) as w:
        for i, ts in enumerate(u.trajectory):
            if args.stride and i % args.stride != 0:
                continue
            box = ts.dimensions[:3]
            pos = u.atoms.positions.copy()
            # iterate: anchor on G_alpha, pull every other chain to its nearest
            # image; recompute the anchor from the assembled complex each pass so
            # a chain imaged in pass 1 can help image a farther one in pass 2.
            for _ in range(args.max_passes):
                moved = False
                ac = pos[chains[anchor]].mean(0)
                for name, idx in chains.items():
                    if name == anchor:
                        continue
                    cc = pos[idx].mean(0)
                    shift = np.round((ac - cc) / box) * box
                    if np.any(shift != 0):
                        pos[idx] += shift
                        moved = True
                if not moved:
                    break
                n_passes += 1
            U, cmob, cref = rot_to(pos[a5], ref_a5)
            u.atoms.positions = (pos - cmob) @ U + cref
            w.write(u.atoms); n_out += 1
    print(f"Wrote {n_out} frames -> {args.out} ({os.path.getsize(args.out)/1e6:.1f} MB); "
          f"imaging passes used (cumulative): {n_passes}; anchor: {anchor}")


def cmd_fix_structure(args):
    """Subcommand: fix structure.pdb in place (the §6 fix).

    1. Reimage each chain to the G_alpha (or Receptor) centroid using the TRUE
       trajectory box (frame 0), not the PDB's own (possibly stale) box.
    2. Rewrite the CRYST1 record to the true trajectory box.
    3. Assign elements to blank atoms (LP/LPH -> H, else guess from atom name).
    4. Preserve clean PDB formatting: surgical coordinate-column (31-54)
       replacement on a clean template; MDAnalysis's PDB writer is NOT used
       (it corrupts the element column and adds HEADER).
    Backs up to structure.pdb.pre_chain_fix.
    """
    import warnings; warnings.filterwarnings("ignore")
    import MDAnalysis as mda
    pdb_path = Path(args.pdb)
    xtc_path = Path(args.xtc) if args.xtc else (pdb_path.parent / "traj.xtc")

    # true box from trajectory frame 0
    u = mda.Universe(str(pdb_path), str(xtc_path))
    u.trajectory[0]
    true_box = np.array(u.dimensions[:3], dtype=float)
    # chain index groups + anchor
    chains = {}
    for name, (r0, r1) in _chain_ranges_from_roles(args.roles, u):
        chains[name] = u.select_atoms(f"resid {r0}:{r1}").indices
    anchor = "G_alpha" if "G_alpha" in chains else ("Receptor" if "Receptor" in chains else list(chains)[0])
    all_idx = np.concatenate(list(chains.values()))

    # reimage chain centroids to the anchor centroid using the true box
    pos = u.atoms.positions.copy()
    # converge multi-pass to the anchor (anchor stays put)
    anchor_c = pos[chains[anchor]].mean(0)
    for _ in range(args.max_passes):
        moved = False
        for name, idx in chains.items():
            if name == anchor:
                continue
            cc = pos[idx].mean(0)
            shift = np.round((anchor_c - cc) / true_box) * true_box
            if np.any(shift != 0):
                pos[idx] += shift
                moved = True
        if not moved:
            break
    # now pos holds the reimaged frame-0 coordinates

    # read the existing PDB as the clean template (byte-identical except coords/CRYST1/elements)
    with open(pdb_path) as f:
        lines = f.readlines()
    # map atom order in template -> row index in `pos`. MDAnalysis loads atoms in
    # file order, so atom i (0-based) corresponds to the i-th ATOM/HETATM line.
    atom_i = 0
    out = []
    cryst_written = False
    cryst_line = (f"CRYST1{true_box[0]:9.3f}{true_box[1]:9.3f}{true_box[2]:9.3f}"
                  f"  90.00  90.00  90.00 P 1           1\n")
    for line in lines:
        if line.startswith("CRYST1"):
            if not cryst_written:
                out.append(cryst_line); cryst_written = True
            continue
        if line.startswith(("ATOM", "HETATM")):
            x, y, z = pos[atom_i]
            atom_i += 1
            l = line.rstrip("\n")
            # cols 31-54 (0-indexed 30:54): x y z, each %8.3f
            l = l[:30] + f"{x:8.3f}{y:8.3f}{z:8.3f}" + l[54:]
            # element column 77-78 (0-indexed 76:78)
            if len(l) >= 78:
                elem = l[76:78].strip()
            else:
                elem = ""
            if elem == "":
                name = l[12:16].strip().lstrip("0123456789")
                elem = "H" if name.startswith("LP") else (name[0].upper() if name else "C")
                if len(l) < 78:
                    l = l.ljust(78)
                l = l[:76] + f"{elem:>2s}" + l[78:]
            out.append(l + "\n")
        else:
            out.append(line)
    if not cryst_written:
        out.insert(0, cryst_line)
    if atom_i != u.atoms.n_atoms:
        sys.exit(f"ERROR: template had {atom_i} ATOM/HETATM lines but trajectory has "
                 f"{u.atoms.n_atoms} atoms — atom-order mismatch, refusing to write")
    backup = str(pdb_path) + ".pre_chain_fix"
    import shutil
    shutil.copy2(pdb_path, backup)
    with open(pdb_path, "w") as f:
        f.writelines(out)
    print(f"Fixed {pdb_path}: reimaged {len(chains)} chains to {anchor} centroid, "
          f"CRYST1 -> {true_box[0]:.1f}/{true_box[1]:.1f}/{true_box[2]:.1f}, "
          f"elements assigned. Backup: {backup}")


def _chain_ranges_from_roles(roles_path, u):
    if roles_path and Path(roles_path).exists():
        roles = json.load(open(roles_path))["roles"]
        return [(lbl, [int(x) for x in info["resid_range"].split("-")])
                for lbl, info in roles.items()]
    # fallback: one segment = whole system
    return [("MOL", (int(u.residues.resids[0]), int(u.residues.resids[-1])))]


def cmd_update_db(args):
    """Subcommand: refresh system_viz_files row from disk."""
    import sqlite3
    import warnings; warnings.filterwarnings("ignore")
    import MDAnalysis as mda
    sid = args.system
    sysdir = VIZ_DIR / sid
    pdb = sysdir / "structure.pdb"; traj = sysdir / "traj.xtc"
    if not traj.exists():
        sys.exit(f"ERROR: {traj} not found")
    u = mda.Universe(str(pdb), str(traj))
    n_frames = len(u.trajectory); n_atoms = u.atoms.n_atoms
    traj_size = os.path.getsize(traj); pdb_size = os.path.getsize(pdb)
    con = sqlite3.connect(str(DB_PATH))
    con.execute("UPDATE system_viz_files SET file_size_bytes=?, n_frames=?, n_atoms=? "
                "WHERE system_id=? AND file_type='traj_xtc'",
                (traj_size, n_frames, n_atoms, sid))
    con.execute("UPDATE system_viz_files SET file_size_bytes=?, n_atoms=? "
                "WHERE system_id=? AND file_type='structure_pdb'",
                (pdb_size, n_atoms, sid))
    con.commit(); con.close()
    print(f"Updated DB for {sid}: traj {traj_size} B / {n_frames} frames; pdb {pdb_size} B")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build-fake-tpr")
    p.add_argument("--pdb", required=True)
    p.add_argument("--roles")
    p.add_argument("--outdir", required=True)
    p.set_defaults(func=cmd_build_fake_tpr)

    p = sub.add_parser("make-ndx")
    p.add_argument("--pdb", required=True)
    p.add_argument("--roles", help="chain_roles.json (derive alpha5 from G_alpha range)")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_make_ndx)

    p = sub.add_parser("src-to-xtc")
    p.add_argument("--pdb", required=True)
    p.add_argument("--src", required=True, help="source trajectory (.nc/.trr/.xtc/...)")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_src_to_xtc)

    p = sub.add_parser("assemble")
    p.add_argument("--pdb", required=True)
    p.add_argument("--cluster", required=True, help="gmx -pbc cluster output xtc")
    p.add_argument("--roles")
    p.add_argument("--ndx", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--stride", type=int, default=4)
    p.set_defaults(func=cmd_assemble)

    p = sub.add_parser("assemble-multipass",
                       help="multi-pass complex-centroid imaging (stable for multi-chain)")
    p.add_argument("--pdb", required=True)
    p.add_argument("--cluster", required=True, help="gmx -pbc cluster output xtc")
    p.add_argument("--roles")
    p.add_argument("--ndx", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--stride", type=int, default=4)
    p.add_argument("--max-passes", type=int, default=10)
    p.set_defaults(func=cmd_assemble_multipass)

    p = sub.add_parser("fix-structure",
                       help="fix structure.pdb in place: reimage chains, CRYST1, elements")
    p.add_argument("--pdb", required=True)
    p.add_argument("--xtc", help="trajectory to read the true box from (default: sibling traj.xtc)")
    p.add_argument("--roles")
    p.add_argument("--max-passes", type=int, default=10)
    p.set_defaults(func=cmd_fix_structure)

    p = sub.add_parser("update-db")
    p.add_argument("--system", required=True)
    p.set_defaults(func=cmd_update_db)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
