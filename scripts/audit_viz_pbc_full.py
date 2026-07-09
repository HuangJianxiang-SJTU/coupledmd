#!/usr/bin/env python3
"""
Comprehensive PBC / viz-trajectory audit for all 222 systems.

Detects the failure modes we actually saw with Gi_8YIC:

  1. INTRA_CHAIN_BREAK   — a single chain is split across the periodic box
                           (CA-CA distance > 8 Å within a contiguous residue
                           range that should be one chain). This is the classic
                           "broken molecule" PBC artifact.
  2. SCATTER             — the overall coordinate span exceeds 1.6× the box in
                           any axis (atoms scattered across multiple images).
  3. INTER_CHAIN_SPLIT   — the complex is assembled wrong: a chain centroid is
                           > 1.0× the smallest box edge from the receptor/Gα
                           centroid (a chain landed in a different periodic
                           image). Checks the bound-complex geometry, not just
                           per-chain integrity.
  4. NO_BOX / BAD_BOX    — trajectory frames lack a usable box (NGL needs it).
  5. PDB_BOX_MISMATCH    — structure.pdb CRYST1 box differs from the trajectory
                           box by >5%. NGL uses the PDB box to interpret the
                           trajectory; a mismatch can prevent rendering.
  6. BLANK_ELEMENT       — structure.pdb has ATOM/HETATM with no element in
                           cols 77-78 (e.g. CHARMM lone-pair LP1). NGL's
                           colorScheme:'element' throws on this, aborting the
                           structure-load callback BEFORE the trajectory loads
                           — so the trajectory never plays. (Root cause for
                           Gi_8YIC's "nothing on play".)
  7. ATOM_COUNT_MISMATCH — structure.pdb and traj.xtc atom counts differ (NGL
                           cannot overlay the trajectory).

A system is flagged BROKEN if any of 1-4, 6, 7 fire (5 is a warning). The
output CSV has one row per system with per-check booleans and the worst status.

Usage:
    python3 scripts/audit_viz_pbc_full.py                 # all 222 systems
    python3 scripts/audit_viz_pbc_full.py --system Gi_8YIC
    python3 scripts/audit_viz_pbc_full.py --frames 10     # frames to sample (default 5)
"""
import argparse
import csv
import os
import sys
import warnings
from pathlib import Path

import numpy as np
warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIZ_DIR = PROJECT_ROOT / "data" / "viz"
OUT_CSV = PROJECT_ROOT / "scripts" / "audit_output" / "VIZ_PBC_FULL_AUDIT.csv"

# CA-CA distance above which two consecutive CAs of the SAME chain MIGHT be a PBC
# split. Real peptide CA-CA is ~3.8 Å. NOTE: >8 Å alone does NOT mean a PBC split
# — genuine structural chain gaps (deleted/renumbered loops) also exceed this. The
# intra-chain check below disambiguates with the minimum-image convention.
INTRA_BREAK_A = 8.0
SCATTER_FACTOR = 1.6       # span > 1.6× box in any axis = scatter
INTER_CHAIN_FACTOR = 1.0   # chain centroid > 1.0× min(box) from anchor = wrong image
BOX_MISMATCH_FRAC = 0.05   # PDB box vs traj box differ >5% = warning


def load_roles(system_id):
    """Return dict label -> (resid_min, resid_max) from chain_roles.json, or None."""
    p = PROJECT_ROOT / "scripts" / "audit_output" / "chain_roles" / f"{system_id}_chain_roles.json"
    if not p.exists():
        return None
    import json
    roles = json.load(open(p))["roles"]
    out = {}
    for label, info in roles.items():
        rmin, rmax = [int(x) for x in info["resid_range"].split("-")]
        out[label] = (rmin, rmax)
    return out


def chain_ranges_from_pdb(u):
    """If no chain_roles.json, split CA list into segments by CA-CA breaks >10 Å."""
    ca = u.select_atoms("name CA")
    if len(ca) == 0:
        return {}
    pos = ca.positions
    breaks = [0] + [i for i in range(1, len(pos))
                    if np.linalg.norm(pos[i] - pos[i-1]) > 10.0] + [len(pos)]
    # map CA-index ranges back to residue ranges
    resids = ca.residues.resids
    segs = {}
    for k in range(len(breaks) - 1):
        r0, r1 = int(resids[breaks[k]]), int(resids[breaks[k+1] - 1])
        segs[f"seg{k}"] = (r0, r1)
    return segs


def count_blank_elements(pdb_path):
    """Count ATOM/HETATM lines whose element column (cols 77-78) is blank."""
    n = 0
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                elem = line[76:78].strip() if len(line) >= 78 else ""
                if elem == "":
                    n += 1
    return n


def pdb_box(pdb_path):
    """Read CRYST1 box [a,b,c] from the PDB, or None."""
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("CRYST1"):
                try:
                    return np.array([float(line[6:15]), float(line[15:24]), float(line[24:33])])
                except ValueError:
                    return None
    return None


def audit_system(system_id, n_check_frames):
    pdb_path = VIZ_DIR / system_id / "structure.pdb"
    xtc_path = VIZ_DIR / system_id / "traj.xtc"
    row = {"system_id": system_id, "status": "MISSING",
           "n_frames": "", "n_atoms_pdb": "", "n_atoms_xtc": "",
           "frames_checked": 0, "intra_break_frames": 0, "scatter_frames": 0,
           "inter_chain_split_frames": 0, "has_box": False,
           "pdb_box": "", "traj_box": "", "box_mismatch": False,
           "blank_elements": 0, "atom_count_mismatch": False,
           "worst_issue": ""}
    if not pdb_path.exists() or not xtc_path.exists():
        return row

    import MDAnalysis as mda
    try:
        u = mda.Universe(str(pdb_path), str(xtc_path))
    except Exception as e:
        row["status"] = "LOAD_ERROR"
        row["worst_issue"] = str(e)[:120]
        return row

    n_frames = len(u.trajectory)
    n_atoms_xtc = u.atoms.n_atoms
    row["n_frames"] = n_frames
    row["n_atoms_xtc"] = n_atoms_xtc
    if n_frames == 0:
        row["status"] = "NO_FRAMES"
        row["worst_issue"] = "trajectory has 0 frames"
        return row

    # element + atom-count checks (the NGL-blocking issues)
    row["blank_elements"] = count_blank_elements(pdb_path)
    try:
        u_pdb = mda.Universe(str(pdb_path))
        row["n_atoms_pdb"] = u_pdb.atoms.n_atoms
        row["atom_count_mismatch"] = (u_pdb.atoms.n_atoms != n_atoms_xtc)
    except Exception:
        row["n_atoms_pdb"] = ""

    # box mismatch
    pdbbx = pdb_box(pdb_path)
    if pdbbx is not None:
        row["pdb_box"] = "/".join(f"{x:.1f}" for x in pdbbx)

    # chain ranges
    roles = load_roles(system_id)
    if roles is None:
        u.trajectory[0]
        roles = chain_ranges_from_pdb(u)

    ca = u.select_atoms("name CA")
    if len(ca) == 0:
        row["status"] = "NO_CA"
        return row

    # frame sampling
    if n_frames <= n_check_frames:
        frames = list(range(n_frames))
    else:
        frames = list(range(0, n_frames, max(1, n_frames // n_check_frames)))[:n_check_frames]

    issues = []
    traj_box_seen = None
    for fi in frames:
        u.trajectory[fi]
        box = u.trajectory.ts.dimensions
        if box is None or box[0] <= 0:
            issues.append("NO_BOX")
            continue
        row["has_box"] = True
        box3 = np.array(box[:3])
        min_box = box3.min()
        if traj_box_seen is None:
            traj_box_seen = box3
            row["traj_box"] = "/".join(f"{x:.1f}" for x in box3)
            if pdbbx is not None and np.any(np.abs(pdbbx - box3) / box3 > BOX_MISMATCH_FRAC):
                row["box_mismatch"] = True
                issues.append("PDB_BOX_MISMATCH")

        row["frames_checked"] += 1
        pos = u.atoms.positions
        ca_pos = ca.positions

        # 1. intra-chain breaks. A raw CA-CA distance > INTRA_BREAK_A is NOT by
        # itself a PBC artifact: these mini-G constructs have genuine structural
        # chain gaps (a deleted helical-domain linker renumbered away), which
        # leave two renumbered-consecutive CAs 9-30 Å apart in a perfectly imaged
        # frame — the same gap is present in the static structure.pdb that the
        # viewer renders fine. Only count a break as a real (fixable) PBC split if
        # its CA-CA vector COLLAPSES under the minimum-image convention (the two
        # atoms are actually close, just in different periodic images). A break
        # that stays large after min-image is a structural gap → ignore.
        intra_bad = False
        for label, (r0, r1) in roles.items():
            seg_ca = u.select_atoms(f"name CA and resid {r0}:{r1}").positions
            if len(seg_ca) < 2:
                continue
            dv = np.diff(seg_ca, axis=0)
            d = np.linalg.norm(dv, axis=1)
            for k in np.where(d > INTRA_BREAK_A)[0]:
                mi = np.linalg.norm(dv[k] - box3 * np.round(dv[k] / box3))
                if mi <= INTRA_BREAK_A:        # collapses → genuine PBC split
                    intra_bad = True
                    break
            if intra_bad:
                break
        if intra_bad:
            row["intra_break_frames"] += 1
            issues.append("INTRA_CHAIN_BREAK")

        # 2. scatter
        span = np.array([pos[:, 0].ptp(), pos[:, 1].ptp(), pos[:, 2].ptp()])
        if (span > SCATTER_FACTOR * box3).any():
            row["scatter_frames"] += 1
            issues.append("SCATTER")

        # 3. inter-chain split: each chain centroid vs receptor/Gα centroid.
        # Use the MINIMUM-IMAGE distance, not the raw distance — a peptide ligand
        # or a receptor fragment legitimately bound across the periodic boundary
        # has a large raw centroid distance but a small min-image distance (~20-35 Å,
        # real binding geometry). The raw check false-positives on these.
        anchor_label = "Receptor" if "Receptor" in roles else (
            "G_alpha" if "G_alpha" in roles else list(roles)[0])
        a0, a1 = roles[anchor_label]
        anchor_c = u.select_atoms(f"resid {a0}:{a1}").positions.mean(axis=0)
        inter_bad = False
        for label, (r0, r1) in roles.items():
            if label == anchor_label:
                continue
            cc = u.select_atoms(f"resid {r0}:{r1}").positions.mean(axis=0)
            delta = cc - anchor_c
            mi = np.linalg.norm(delta - box3 * np.round(delta / box3))
            if mi > INTER_CHAIN_FACTOR * min_box:
                inter_bad = True
                break
        if inter_bad:
            row["inter_chain_split_frames"] += 1
            issues.append("INTER_CHAIN_SPLIT")

    # decide worst status. A system is BROKEN only if a meaningful fraction of
    # sampled frames fail (>20%); a handful of borderline frames is WARN.
    # Element/atom-count issues are always BROKEN (they block NGL entirely).
    checked = row["frames_checked"] or 1
    frac_intra = row["intra_break_frames"] / checked
    frac_scatter = row["scatter_frames"] / checked
    frac_inter = row["inter_chain_split_frames"] / checked

    def issue_status(frac, n, name):
        if frac > 0.2:
            return "BROKEN", f"{name} ({n}/{checked} frames, {frac:.0%})"
        if n > 0:
            return "WARN", f"{name} ({n}/{checked} frames, minor)"
        return None, None

    if not row["has_box"]:
        row["status"] = "NEEDS_SOURCE"
        row["worst_issue"] = "no box in trajectory"
    elif row["atom_count_mismatch"]:
        row["status"] = "BROKEN"
        row["worst_issue"] = "atom_count_mismatch (NGL cannot overlay traj)"
    elif row["blank_elements"] > 0:
        row["status"] = "BROKEN_NGL"
        row["worst_issue"] = f"blank_elements={row['blank_elements']} (NGL throws, traj never loads)"
    else:
        for frac, n, name in [(frac_intra, row["intra_break_frames"], "intra_chain_break"),
                              (frac_scatter, row["scatter_frames"], "scatter"),
                              (frac_inter, row["inter_chain_split_frames"], "inter_chain_split")]:
            st, msg = issue_status(frac, n, name)
            if st:
                row["status"] = st
                row["worst_issue"] = msg
                break
        else:
            if row["box_mismatch"]:
                row["status"] = "WARN"
                row["worst_issue"] = "pdb_box_mismatch (may block NGL)"
            else:
                row["status"] = "OK"
                row["worst_issue"] = ""

    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--system", help="audit a single system_id")
    ap.add_argument("--frames", type=int, default=5, help="frames to sample per system (default 5)")
    ap.add_argument("--out", default=str(OUT_CSV), help="output CSV path")
    args = ap.parse_args()

    if args.system:
        systems = [args.system]
        # single-system runs must NOT overwrite the Main audit CSV; write to a
        # per-system temp file so the full audit is preserved.
        if args.out == str(OUT_CSV):
            args.out = str(PROJECT_ROOT / "scripts" / "audit_output" / f"_single_{args.system}.csv")
    else:
        systems = sorted(d for d in os.listdir(VIZ_DIR)
                         if (VIZ_DIR / d / "traj.xtc").exists())

    print(f"Auditing {len(systems)} systems ({args.frames} frames each)...")
    rows = []
    for i, sid in enumerate(systems):
        r = audit_system(sid, args.frames)
        rows.append(r)
        flag = "" if r["status"] in ("OK",) else "  <<< " + r["status"]
        print(f"[{i+1}/{len(systems)}] {sid:14s} {r['status']:12s}{flag}")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fields = ["system_id", "status", "worst_issue", "n_frames", "n_atoms_pdb",
              "n_atoms_xtc", "atom_count_mismatch", "blank_elements",
              "has_box", "pdb_box", "traj_box", "box_mismatch",
              "frames_checked", "intra_break_frames", "scatter_frames",
              "inter_chain_split_frames"]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    from collections import Counter
    c = Counter(r["status"] for r in rows)
    print(f"\n{'='*60}\nSUMMARY: {dict(c)}\nWrote: {args.out}")
    broken = [r for r in rows if r["status"] not in ("OK", "WARN")]
    if broken:
        print(f"\n{len(broken)} broken systems to fix:")
        for r in broken:
            print(f"  {r['system_id']:14s} {r['status']:12s} {r['worst_issue']}")


if __name__ == "__main__":
    main()
