#!/usr/bin/env python3
"""
Fix PBC wrapping in viz structure.pdb files.

Problem: Many structure.pdb files have protein chains split across periodic
boundary images. NGL cannot render cartoon representations when consecutive
CA atoms are 50-180 Angstroms apart instead of the normal ~3.8A.

Solution: Per-segment iterative PBC unwrapping using chain_roles.json to
identify subunit boundaries, then shifting atom coordinates so each
contiguous polypeptide segment forms a continuous chain.

Key design decisions:
1. Receptor_frag* entries are kept as separate segments (not merged with
   Receptor) because other subunits (G_gamma) may occupy the residue range
   between Receptor and Receptor_frag0.
2. PBC wraps are detected using minimum-image convention. A wrap is confirmed
   if either (a) the corrected distance < 10A, or (b) the minimum-image
   correction identifies at least one box wrap AND reduces the distance by >50%.
   This handles cases where a PBC wrap has a large lateral shift (e.g., 12A
   corrected distance from a 157A raw distance).

Usage:
    python3 scripts/fix_viz_pbc.py [--dry-run] [--system SID] [--force]

Options:
    --dry-run     Detect issues only, do not write files
    --system SID  Fix a single system
    --force       Re-fix systems that were already fixed
"""
import argparse
import json
import math
import os
import shutil
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_ROOT = Path(os.environ.get("DATA_ROOT", PROJECT_ROOT))

VIZ_DIR = DATA_ROOT / "data" / "viz"
CHAIN_ROLES_DIR = SCRIPT_DIR / "audit_output" / "chain_roles"
BACKUP_DIR = SCRIPT_DIR / "audit_output" / "pdb_pbc_backup"

JUMP_THRESHOLD = 10.0  # Angstroms; normal peptide CA-CA is ~3.8A


def get_subunit_segments(system_id):
    """Load chain_roles.json and return subunit segments WITHOUT merging ranges.

    Receptor_frag* segments are kept as separate segments but labeled
    'Receptor' for coloring purposes. Each segment is a contiguous residue
    range that should be unwrapped independently.

    This is critical: merging Receptor (693-758) and Receptor_frag0 (815-1141)
    into a single range (693-1141) would include G_gamma residues (759-814)
    in the Receptor's unwrapping, causing incorrect shifts.

    Returns list of (subunit_name, rmin, rmax) sorted by rmin,
    or empty list if no chain_roles file exists.
    """
    roles_path = CHAIN_ROLES_DIR / f"{system_id}_chain_roles.json"
    if not roles_path.exists():
        return []

    with open(roles_path) as f:
        roles_data = json.load(f)

    segments = []
    for role, info in roles_data.get("roles", {}).items():
        # Map Receptor_frag* to 'Receptor' for coloring, but keep as separate segment
        canonical = "Receptor" if role.startswith("Receptor") else role
        if canonical not in ("G_alpha", "Receptor", "G_beta", "G_gamma"):
            continue
        rng = info.get("resid_range", "")
        if "-" in rng:
            rmin, rmax = int(rng.split("-")[0]), int(rng.split("-")[1])
            segments.append((canonical, rmin, rmax))

    return sorted(segments, key=lambda x: x[1])


def detect_pbc_jumps(pdb_path, subunit_segments):
    """Detect intra-segment CA-CA jumps > JUMP_THRESHOLD in a PDB file.

    Only checks consecutive residue numbers within the same segment.
    Jumps between segments (e.g., Receptor -> G_beta) are expected and ignored.

    Returns list of (subunit_name, res1, res2, distance) for each jump.
    """
    box = None
    chain_cas = {}

    with open(pdb_path) as f:
        for line in f:
            if line.startswith("CRYST1") and box is None:
                a = float(line[6:15])
                b = float(line[15:24])
                c = float(line[24:33])
                box = (a, b, c)
            if line.startswith("ATOM"):
                atom_name = line[12:16].strip()
                if atom_name != "CA":
                    continue
                chain_id = line[21]
                try:
                    resnum = int(line[22:26].strip())
                except ValueError:
                    continue
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                except ValueError:
                    continue
                chain_cas.setdefault(chain_id, []).append((resnum, x, y, z))

    if not box:
        return []

    jumps = []
    for chain_id, cas in chain_cas.items():
        cas.sort(key=lambda r: r[0])
        for subname, rmin, rmax in subunit_segments:
            sub_cas = [(r, x, y, z) for r, x, y, z in cas if rmin <= r <= rmax]
            for i in range(1, len(sub_cas)):
                r1, x1, y1, z1 = sub_cas[i-1]
                r2, x2, y2, z2 = sub_cas[i]
                if r2 == r1 + 1:
                    d = math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
                    if d > JUMP_THRESHOLD:
                        jumps.append((subname, r1, r2, d))

    return jumps


def is_pbc_wrap(dx, dy, dz, box):
    """Determine if a CA-CA displacement is a PBC wrap.

    Uses minimum-image convention. A wrap is confirmed if:
    (a) The corrected distance < JUMP_THRESHOLD, OR
    (b) The minimum-image correction identifies at least one box wrap (|n|>=1)
        AND reduces the distance by more than 50%.

    Condition (b) handles cases where a PBC wrap has a large lateral shift
    (e.g., 12A corrected distance from a 157A raw distance due to z-wrap
    plus x/y drift).

    Returns (is_wrap, nx, ny, nz) where n* are the box wrap counts.
    """
    raw_d = math.sqrt(dx**2 + dy**2 + dz**2)
    if raw_d < JUMP_THRESHOLD:
        return False, 0, 0, 0

    nx = round(dx / box[0])
    ny = round(dy / box[1])
    nz = round(dz / box[2])

    corrected_d = math.sqrt((dx - nx*box[0])**2 + (dy - ny*box[1])**2 + (dz - nz*box[2])**2)

    # Condition (a): corrected distance is within normal range
    if corrected_d < JUMP_THRESHOLD:
        return True, nx, ny, nz

    # Condition (b): PBC wrap detected AND significant distance reduction
    has_wrap = (nx != 0 or ny != 0 or nz != 0)
    if has_wrap and corrected_d < raw_d * 0.5:
        return True, nx, ny, nz

    return False, nx, ny, nz


def fix_pdb(pdb_path, subunit_segments, box):
    """Apply per-segment PBC unwrapping to a structure.pdb file.

    For each segment, iteratively unwraps CA positions so consecutive
    CA-CA distances are minimized (minimum-image convention), then
    applies the same coordinate shifts to all atoms in that residue.

    Returns (n_shifted_atoms, n_jumps_fixed) or raises on error.
    """
    # Read all ATOM lines grouped by chain
    chain_atoms = {}  # chain -> [(resnum, line), ...]
    header_lines = []

    with open(pdb_path) as f:
        for line in f:
            if line.startswith("CRYST1"):
                header_lines.append(line)
            elif line.startswith("ATOM"):
                chain_id = line[21]
                try:
                    resnum = int(line[22:26].strip())
                except ValueError:
                    continue
                chain_atoms.setdefault(chain_id, []).append((resnum, line))
            elif line.startswith("MODEL") or line.startswith("ENDMDL") or line.startswith("TER") or line.startswith("END"):
                pass  # skip; we'll regenerate structure
            elif not line.startswith("HETATM"):
                header_lines.append(line)

    n_shifted = 0
    n_jumps_fixed = 0

    for chain_id in chain_atoms:
        atoms = chain_atoms[chain_id]
        atoms.sort(key=lambda a: a[0])

        # Extract CA positions for shift computation
        ca_pos = {}
        for resnum, line in atoms:
            atom_name = line[12:16].strip()
            if atom_name == "CA":
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    ca_pos[resnum] = (x, y, z)
                except ValueError:
                    pass

        # Compute per-segment PBC shifts using iterative CA unwrapping
        residue_shifts = {}  # resnum -> (sx, sy, sz)

        for subname, rmin, rmax in subunit_segments:
            sub_cas = [(r, ca_pos[r]) for r in sorted(ca_pos.keys()) if rmin <= r <= rmax]
            if not sub_cas:
                continue

            current_shift = [0.0, 0.0, 0.0]
            prev_ca = None  # unwrapped position of previous CA

            for resnum, (x, y, z) in sub_cas:
                if prev_ca is not None:
                    # Vector from prev unwrapped CA to this CA (with current shift)
                    dx = (x + current_shift[0]) - prev_ca[0]
                    dy = (y + current_shift[1]) - prev_ca[1]
                    dz = (z + current_shift[2]) - prev_ca[2]

                    # Check if this is a PBC wrap
                    is_wrap, nx, ny, nz = is_pbc_wrap(dx, dy, dz, box)

                    if is_wrap:
                        new_shift = [current_shift[0] - nx * box[0],
                                     current_shift[1] - ny * box[1],
                                     current_shift[2] - nz * box[2]]
                        current_shift = new_shift
                        if nx != 0 or ny != 0 or nz != 0:
                            n_jumps_fixed += 1
                    # If not a PBC wrap, keep current_shift unchanged.
                    # This handles structural breaks (missing loops, chain swaps)
                    # where residues are genuinely far apart.

                unwrapped = (x + current_shift[0], y + current_shift[1], z + current_shift[2])
                prev_ca = unwrapped
                residue_shifts[resnum] = tuple(current_shift)

        # Apply shifts to all atoms in this chain
        new_atoms = []
        for resnum, line in atoms:
            shift = residue_shifts.get(resnum, (0.0, 0.0, 0.0))
            if shift == (0.0, 0.0, 0.0):
                new_atoms.append((resnum, line))
            else:
                try:
                    x = float(line[30:38]) + shift[0]
                    y = float(line[38:46]) + shift[1]
                    z = float(line[46:54]) + shift[2]
                    new_line = line[:30] + f"{x:8.3f}{y:8.3f}{z:8.3f}" + line[54:]
                    new_atoms.append((resnum, new_line))
                    n_shifted += 1
                except ValueError:
                    new_atoms.append((resnum, line))

        chain_atoms[chain_id] = new_atoms

    # Write the fixed PDB
    with open(pdb_path, 'w') as f:
        for line in header_lines:
            f.write(line)
        for chain_id in sorted(chain_atoms.keys()):
            for resnum, line in chain_atoms[chain_id]:
                f.write(line)
            f.write("TER\n")
        f.write("END\n")

    return n_shifted, n_jumps_fixed


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Detect issues only, do not write files")
    parser.add_argument("--system", metavar="SID",
                        help="Fix a single system")
    parser.add_argument("--force", action="store_true",
                        help="Re-fix systems that were already fixed")
    args = parser.parse_args()

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Collect systems to process
    if args.system:
        systems = [args.system]
    else:
        systems = sorted(d.name for d in VIZ_DIR.iterdir()
                        if d.is_dir() and (d / "structure.pdb").exists())

    print(f"PBC fix for viz structure.pdb files")
    print(f"Systems to check: {len(systems)}")
    print(f"Dry run: {args.dry_run}")
    print()

    t0 = time.time()
    needs_fix = 0
    fixed = 0
    already_ok = 0
    errors = 0
    structural = 0

    for i, sid in enumerate(systems):
        pdb_path = VIZ_DIR / sid / "structure.pdb"
        if not pdb_path.exists():
            continue

        # Get subunit segments
        segments = get_subunit_segments(sid)
        if not segments:
            # No chain_roles -- skip
            continue

        # Detect PBC jumps
        jumps = detect_pbc_jumps(pdb_path, segments)

        if not jumps:
            already_ok += 1
            continue

        needs_fix += 1

        if args.dry_run:
            print(f"  [{i+1}/{len(systems)}] {sid}: {len(jumps)} PBC jump(s) -- ", end="")
            print(", ".join(f"{s} res {r1}->{r2} ({d:.0f}A)" for s, r1, r2, d in jumps))
            continue

        # Check if already fixed (backup exists and no --force)
        backup_path = BACKUP_DIR / f"{sid}_structure.pdb.bak"
        if backup_path.exists() and not args.force:
            # Already fixed previously
            continue

        # Back up original
        if not backup_path.exists():
            shutil.copy2(pdb_path, backup_path)

        # Read box dimensions from backup (original file)
        box = None
        with open(backup_path) as f:
            for line in f:
                if line.startswith("CRYST1"):
                    a = float(line[6:15])
                    b = float(line[15:24])
                    c = float(line[24:33])
                    box = (a, b, c)
                    break

        if not box:
            print(f"  [{i+1}/{len(systems)}] {sid}: ERROR - no CRYST1 record")
            errors += 1
            continue

        # Apply fix
        try:
            n_shifted, n_jumps = fix_pdb(pdb_path, segments, box)
        except Exception as e:
            print(f"  [{i+1}/{len(systems)}] {sid}: ERROR - {e}")
            errors += 1
            # Restore backup
            if backup_path.exists():
                shutil.copy2(backup_path, pdb_path)
            continue

        # Verify fix
        post_jumps = detect_pbc_jumps(pdb_path, segments)

        if post_jumps:
            # Classify remaining jumps
            pbc_remaining = 0
            struct_remaining = 0
            for s, r1, r2, d in post_jumps:
                # Re-read positions to classify
                chain_cas = {}
                with open(pdb_path) as f:
                    for line in f:
                        if line.startswith("ATOM"):
                            atom_name = line[12:16].strip()
                            if atom_name != "CA":
                                continue
                            chain_id = line[21]
                            try:
                                resnum = int(line[22:26].strip())
                                x = float(line[30:38])
                                y = float(line[38:46])
                                z = float(line[46:54])
                                chain_cas.setdefault(chain_id, []).append((resnum, x, y, z))
                            except ValueError:
                                continue
                
                for chain_id, cas in chain_cas.items():
                    for r, x, y, z in cas:
                        if r == r1:
                            pos1 = (x, y, z)
                        if r == r2:
                            pos2 = (x, y, z)
                
                dx = pos2[0] - pos1[0]
                dy = pos2[1] - pos1[1]
                dz = pos2[2] - pos1[2]
                is_wrap, _, _, _ = is_pbc_wrap(dx, dy, dz, box)
                if is_wrap:
                    pbc_remaining += 1
                else:
                    struct_remaining += 1
            
            if pbc_remaining == 0 and struct_remaining > 0:
                # All remaining jumps are structural (not PBC) - consider this fixed
                structural += 1
                print(f"  [{i+1}/{len(systems)}] {sid}: FIXED (PBC) - {len(jumps)} PBC jump(s) resolved, "
                      f"{struct_remaining} structural break(s) remain ({n_shifted} atoms shifted, {n_jumps} wraps corrected)")
            else:
                print(f"  [{i+1}/{len(systems)}] {sid}: PARTIALLY FIXED - {len(jumps)} -> {len(post_jumps)} jumps remaining "
                      f"({n_shifted} atoms shifted, {n_jumps} wraps corrected)")
                for s, r1, r2, d in post_jumps:
                    print(f"    Still broken: {s} res {r1}->{r2} ({d:.1f}A)")
        else:
            fixed += 1
            print(f"  [{i+1}/{len(systems)}] {sid}: FIXED - {len(jumps)} jump(s) resolved ({n_shifted} atoms shifted, {n_jumps} wraps corrected)")

    elapsed = time.time() - t0

    print()
    print("=" * 60)
    print(f"PBC Fix Summary")
    print(f"  Total systems checked: {len(systems)}")
    print(f"  Already OK: {already_ok}")
    print(f"  Need fix: {needs_fix}")
    print(f"  Fully fixed: {fixed}")
    print(f"  PBC fixed (structural breaks remain): {structural}")
    print(f"  Errors: {errors}")
    if args.dry_run:
        print(f"  (dry run - no files written)")
    print(f"  Elapsed: {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
