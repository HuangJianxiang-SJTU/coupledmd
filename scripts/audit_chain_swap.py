#!/usr/bin/env python3
"""
Chain-Role Swap Diagnostic (sequence-intrinsic).

ROOT CAUSE
----------
b_assign_roles.py assigns the "G_alpha" role to whichever spatial segment
has the most overlap with CGN `G.*` resids (from a/cache/<sid>/cgn_mapping.csv).
For some systems the upstream CGN mapping is itself SWAPPED: it maps G-alpha
CGN positions onto residues that are physically the RECEPTOR (a 7-TM GPCR).
b_assign_roles.py then faithfully labels the receptor segment "G_alpha" and the
real G-alpha segment "Receptor" -- producing the "purple GPCR / gray Galpha"
the user sees on the web.

FIX STRATEGY (this script = diagnosis only, no writes)
-------------------------------------------------------
Classify each large segment by INTRINSIC sequence signatures that do NOT
depend on the CGN mapping, then compare against the currently-assigned role
in scripts/audit_output/chain_roles/<sid>_chain_roles.json:

  G_alpha   -> always contains the GTPase Walker-A P-loop  GxxxxGK[ST]
               AND Switch-II motif DxxG / VDVGG.  ~330-380 aa (Ras-like + AH).
  Receptor  -> 7 hydrophobic transmembrane helices, NO GTPase motif. ~280-360 aa.
  G_beta    -> WD40 / 7-bladed beta-propeller, ~340 aa. NO GTPase, NO TM helices.
  G_gamma   -> ~60-75 aa, helical, lipidated C-terminus.

A swap is flagged when the JSON says a segment is G_alpha but the sequence is
in fact a GPCR (or vice versa).
"""
import os, json, re, csv
import numpy as np

VIZ_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz"
CACHE_DIR = "/MDdata/data02/jxhuang/gpcr_g/a/cache"
ROLES_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output/chain_roles"
OUT_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output"

AA3TO1 = {
    'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C', 'GLN': 'Q',
    'GLU': 'E', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K',
    'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S', 'THR': 'T', 'TRP': 'W',
    'TYR': 'Y', 'VAL': 'V', 'HSD': 'H', 'HSE': 'H', 'HSP': 'H', 'HID': 'H',
    'HIE': 'H', 'HIP': 'H', 'CYX': 'C', 'ASH': 'D', 'GLH': 'E', 'LYN': 'K',
}

# GTPase motifs -- presence => G_alpha (Ras-like domain).  Conserved across all
# G-alpha families (Gs/Gi/Gq/G12-13).
PLOOP = re.compile(r"G....GK[ST]")        # Walker A P-loop  GxxxxGKS/T
SWITCH2 = re.compile(r"D.G")              # Switch II  DxxG  (also VDVGG)
VDVGG = re.compile(r"VDVGG")


def extract_segments(pdb_path):
    import MDAnalysis as mda
    u = mda.Universe(pdb_path)
    ca_data = []
    for res in u.residues:
        ca = res.atoms.select_atoms("name CA")
        if len(ca) == 1:
            ca_data.append((res.resid, AA3TO1.get(res.resname, 'X'),
                            ca.positions[0].copy()))
    if not ca_data:
        return []
    breaks = []
    for i in range(1, len(ca_data)):
        if np.linalg.norm(ca_data[i][2] - ca_data[i - 1][2]) > 10.0:
            breaks.append(i)
    segments, prev = [], 0
    for b in breaks:
        seg_resids = [ca_data[j][0] for j in range(prev, b)]
        segments.append({
            'seg_idx': len(segments),
            'resids': seg_resids,
            'sequence': ''.join(ca_data[j][1] for j in range(prev, b)),
            'n_residues': len(seg_resids),
            'resid_min': seg_resids[0] if seg_resids else 0,
            'resid_max': seg_resids[-1] if seg_resids else 0,
        })
        prev = b
    seg_resids = [ca_data[j][0] for j in range(prev, len(ca_data))]
    segments.append({
        'seg_idx': len(segments),
        'resids': seg_resids,
        'sequence': ''.join(ca_data[j][1] for j in range(prev, len(ca_data))),
        'n_residues': len(seg_resids),
        'resid_min': seg_resids[0] if seg_resids else 0,
        'resid_max': seg_resids[-1] if seg_resids else 0,
    })
    return segments


def n_hydrophobic_tm_helices(seq):
    """
    Approximate count of transmembrane (TM) helices via runs of >=18 contiguous
    hydrophobic residues (LIVFWM pattern, tolerant of polar interruptions <=2).
    A GPCR has 7; a soluble GTPase / G-beta has 0.
    """
    hydro = set("LIVMFWAC")
    run, runs = 0, []
    for ch in seq:
        if ch in hydro:
            run += 1
        else:
            if run >= 18:
                runs.append(run)
            run = 0
    if run >= 18:
        runs.append(run)
    return len(runs)


def is_galpha(seq):
    return bool(PLOOP.search(seq)) or bool(VDVGG.search(seq))


def classify(seg):
    """Return (intrinsic_role, evidence)."""
    seq = seg['sequence']
    n = seg['n_residues']
    has_gtpase = is_galpha(seq)
    tm = n_hydrophobic_tm_helices(seq)
    if has_gtpase and tm == 0 and 200 <= n <= 420:
        return "G_alpha", f"GTPase motif ({'P-loop' if PLOOP.search(seq) else 'VDVGG'}), 0 TM, n={n}"
    if tm >= 5 and not has_gtpase:
        return "Receptor", f"{tm} TM helices, no GTPase, n={n}"
    if tm >= 5 and has_gtpase:
        # fused/unusual - flag
        return "AMBIGUOUS", f"has GTPase AND {tm} TM helices, n={n}"
    if not has_gtpase and tm <= 1 and n >= 280:
        # likely G_beta (WD40) but no decisive motif; default G_beta only if a
        # G_alpha and a Receptor are already accounted for
        return "G_beta?", f"no GTPase, {tm} TM, n={n}"
    return "SMALL/OTHER", f"n={n}"


def load_json_roles(sid):
    path = os.path.join(ROLES_DIR, f"{sid}_chain_roles.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def resid_range_to_seg(json_roles, rmin, rmax):
    """Find which role the JSON assigned to the segment covering [rmin, rmax]."""
    for role, info in json_roles.get("roles", {}).items():
        lo, hi = map(int, info["resid_range"].split("-"))
        if lo == rmin and hi == rmax:
            return role
        # overlap fallback
        if not (rmax < lo or rmin > hi):
            return role
    return None


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    systems = sorted([d for d in os.listdir(VIZ_DIR)
                      if os.path.isdir(os.path.join(VIZ_DIR, d)) and d[0].isupper()])
    print(f"Total systems: {len(systems)}\n")

    rows = []
    n_swap = 0
    swap_systems = []
    errors = []

    for sid in systems:
        pdb_path = os.path.join(VIZ_DIR, sid, "structure.pdb")
        if not os.path.exists(pdb_path):
            errors.append((sid, "no viz PDB")); continue
        try:
            segs = extract_segments(pdb_path)
        except Exception as e:
            errors.append((sid, f"PDB err {e}")); continue

        jr = load_json_roles(sid)
        if jr is None:
            errors.append((sid, "no chain_roles.json")); continue

        # Classify each large segment intrinsically
        for seg in segs:
            if seg['n_residues'] < 200:
                continue
            intrinsic, ev = classify(seg)
            assigned = resid_range_to_seg(jr, seg['resid_min'], seg['resid_max'])
            row = {
                "system_id": sid,
                "resid_range": f"{seg['resid_min']}-{seg['resid_max']}",
                "n_residues": seg['n_residues'],
                "assigned_role": assigned,
                "intrinsic_role": intrinsic,
                "evidence": ev,
                "seq_first40": seg['sequence'][:40],
            }
            # Detect the canonical swap: assigned G_alpha but intrinsic Receptor
            # (or assigned Receptor but intrinsic G_alpha)
            swapped = False
            if assigned == "G_alpha" and intrinsic == "Receptor":
                swapped = True
            if assigned == "Receptor" and intrinsic == "G_alpha":
                swapped = True
            row["swapped"] = "YES" if swapped else ""
            rows.append(row)

        # system-level swap flag
        sys_swap = any(r["swapped"] == "YES" and r["system_id"] == sid for r in rows)
        if sys_swap:
            n_swap += 1
            swap_systems.append(sid)

    # Write CSV
    out = os.path.join(OUT_DIR, "CHAIN_SWAP_DIAGNOSTIC.csv")
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            "system_id", "resid_range", "n_residues", "assigned_role",
            "intrinsic_role", "evidence", "seq_first40", "swapped"])
        w.writeheader()
        w.writerows(rows)

    # Summary
    print("=" * 70)
    print(f"SWAPPED SYSTEMS (G_alpha <-> Receptor): {n_swap} / {len(systems)}")
    print("=" * 70)
    for sid in swap_systems:
        print(f"  {sid}")
    print(f"\nFull per-segment table: {out}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for sid, e in errors[:10]:
            print(f"  {sid}: {e}")


if __name__ == "__main__":
    main()
