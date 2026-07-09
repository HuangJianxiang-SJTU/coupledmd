#!/usr/bin/env python3
"""
Fix G_alpha / Receptor (and related) chain-role misassignments.

WHY THIS EXISTS
---------------
b_assign_roles.py trusts the upstream CGN mapping (a/cache/<sid>/cgn_mapping.csv)
to decide which spatial segment is G_alpha.  For ~24 systems that CGN mapping is
itself swapped -- it maps G-alpha CGN numbering onto residues that are physically
the RECEPTOR.  b_assign_roles.py then faithfully labels the receptor "G_alpha"
and the real G-alpha "Receptor", which is exactly the "purple GPCR / gray Galpha"
shown on the web.

This script RE-DERIVES every role from INTRINSIC sequence signatures that do not
depend on the (possibly-wrong) CGN mapping, then rewrites chain_roles.json for the
affected systems.  Because it re-derives all four roles (not a blind pairwise
swap) it also handles 3-way rotations like Gi_7VIF (Gbeta<->Galpha<->Receptor).

DISCRIMINATORS (sequence-intrinsic, CGN-independent)
----------------------------------------------------
  G_alpha  : the GTPase Ras-like domain.  ALWAYS carries the Walker-A P-loop
             GxxxxGK[ST] and/or the Switch-II motif VDVGG.  Unique signal.
  G_beta   : WD40 7-bladed propeller, ~335-345 aa, conserved N-terminus
             'ELDQLRQEAEQLK...'.  No GTPase motif.
  Receptor : 7-TM GPCR, no GTPase motif, no G-beta N-terminus.
  G_gamma  : smallest segment (~50-75 aa).

USAGE
-----
  python3 scripts/fix_chain_swaps.py            # all 24 flagged systems
  python3 scripts/fix_chain_swaps.py G12_7SF7   # one system (debug)
  python3 scripts/fix_chain_swaps.py --dry-run  # show diffs, write nothing

It ALWAYS backs up the original JSON to *.bak, writes a human-readable
CHAIN_SWAP_FIX_LOG.md, and never touches non-flagged systems.
"""
import os, sys, re, json, shutil
from collections import OrderedDict
import numpy as np

VIZ_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz"
ROLES_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output/chain_roles"
OUT_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output"

# 24 systems flagged by audit_chain_swap.py (G_alpha slot lacks GTPase motif).
SWAP_SYSTEMS = [
    "G12_7SF7", "G12_7SF8", "Gi_7T96", "Gi_7VH0", "Gi_7VIF", "Gi_7VKT",
    "Gi_7XXI", "Gi_8DZQ", "Gi_8HK2", "Gi_8HK5", "Gi_8IC0", "Gi_8J21",
    "Gi_8J22", "Gi_8XIP", "Gi_8XIQ", "Gi_9IIX", "Gq_7F6G", "Gq_7W3Z",
    "Gq_7Y26", "Gq_8J9N", "Gq_8JBG", "Gs_7T9N", "Gs_8KGK", "Gs_8KH5",
]

AA3TO1 = {
    'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C', 'GLN': 'Q',
    'GLU': 'E', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K',
    'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S', 'THR': 'T', 'TRP': 'W',
    'TYR': 'Y', 'VAL': 'V', 'HSD': 'H', 'HSE': 'H', 'HSP': 'H', 'HID': 'H',
    'HIE': 'H', 'HIP': 'H', 'CYX': 'C', 'ASH': 'D', 'GLH': 'E', 'LYN': 'K',
}

# G-alpha GTPase motifs (Ras-like domain).  Present in ALL G-alpha families.
PLOOP = re.compile(r"G....GK[ST]")     # Walker-A P-loop  GxxxxGKS/T
VDVGG = re.compile(r"VDVGG")           # Switch-II  VDVGG
# G-beta conserved N-terminal signature (human GNB1/2/3/4/5 all share it).
GBETA_NTERM = re.compile(r"ELDQLRQEAEQLK|DQLRQEAEQLKNQ|LRQEAEQLKNQIRD")


def extract_segments(pdb_path):
    """Spatial segmentation by CA-CA gap > 10 A (identical to b_assign_roles.py)."""
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


def has_gtpase(seq):
    return bool(PLOOP.search(seq) or VDVGG.search(seq))


def has_gbeta_sig(seq):
    return bool(GBETA_NTERM.search(seq))


def reassign_roles(segments):
    """
    Re-derive all four roles from intrinsic sequence signatures.
    Returns dict: role -> (seg, evidence).
    """
    assigned = OrderedDict()   # role -> seg dict
    evidence = {}
    used = set()               # seg_idx of assigned segments

    def free(lst=None):
        src = lst if lst is not None else segments
        return [s for s in src if s['seg_idx'] not in used]

    # 1) G_gamma: smallest segment in the typical G-gamma size window.
    #    Use 40-90 aa to exclude peptide ligands (<~36 aa, e.g. chemokine
    #    peptides) while still catching slightly long G-gamma variants.
    ggamma_candidates = [s for s in free() if 40 <= s['n_residues'] <= 90]
    if ggamma_candidates:
        seg = min(ggamma_candidates, key=lambda s: s['n_residues'])
        assigned["G_gamma"] = seg; used.add(seg['seg_idx'])
        evidence["G_gamma"] = f"smallest 40-90aa segment n={seg['n_residues']}"

    # 2) G_alpha: the UNIQUE segment carrying the GTPase motif
    ga = [s for s in free() if has_gtpase(s['sequence'])]
    if len(ga) == 1:
        seg = ga[0]
        m = PLOOP.search(seg['sequence']) or VDVGG.search(seg['sequence'])
        evidence["G_alpha"] = f"GTPase motif {m.group(0)} at ~pos {m.start()}, n={seg['n_residues']}"
    elif len(ga) > 1:
        # two GTPase hits: pick the one in the canonical G-alpha size range
        ga_sized = [s for s in ga if 280 <= s['n_residues'] <= 420]
        seg = ga_sized[0] if ga_sized else max(ga, key=lambda s: s['n_residues'])
        evidence["G_alpha"] = f"GTPase motif (multiple hits; chose n={seg['n_residues']})"
    else:
        raise RuntimeError("no segment with GTPase motif -- cannot find G_alpha")
    assigned["G_alpha"] = seg; used.add(seg['seg_idx'])

    # 3) G_beta: the segment with the conserved G-beta N-terminus
    gb = [s for s in free() if has_gbeta_sig(s['sequence'])]
    if gb:
        seg = max(gb, key=lambda s: s['n_residues'])
        evidence["G_beta"] = f"G-beta N-term signature, n={seg['n_residues']}"
    else:
        # fallback: largest remaining segment that is NOT the receptor candidate
        remaining2 = [s for s in free() if s['n_residues'] >= 200]
        if remaining2:
            seg = max(remaining2, key=lambda s: s['n_residues'])
            evidence["G_beta"] = f"fallback: largest remaining n={seg['n_residues']}"
        else:
            seg = None
    if seg is not None:
        assigned["G_beta"] = seg; used.add(seg['seg_idx'])

    # 4) Receptor: the remaining large segment
    big = [s for s in free() if s['n_residues'] >= 200]
    if big:
        seg = max(big, key=lambda s: s['n_residues'])
        assigned["Receptor"] = seg; used.add(seg['seg_idx'])
        evidence["Receptor"] = f"remaining large segment, n={seg['n_residues']}"

    # 5) any leftover segments -> note them (stabilizers / peptide ligands)
    for s in free():
        assigned[f"UNRESOLVED_seg{s['seg_idx']}"] = s; used.add(s['seg_idx'])
        evidence[f"UNRESOLVED_seg{s['seg_idx']}"] = f"leftover n={s['n_residues']}"

    return assigned, evidence


def role_for_resid_range(jr, rmin, rmax):
    for role, info in jr.get("roles", {}).items():
        lo, hi = map(int, info["resid_range"].split("-"))
        if lo == rmin and hi == rmax:
            return role
    return None


def fix_system(sid, dry_run):
    pdb_path = os.path.join(VIZ_DIR, sid, "structure.pdb")
    if not os.path.exists(pdb_path):
        return None, "no viz PDB"
    segs = extract_segments(pdb_path)
    if not segs:
        return None, "no segments"

    new_assigned, evidence = reassign_roles(segs)

    jr_path = os.path.join(ROLES_DIR, f"{sid}_chain_roles.json")
    if not os.path.exists(jr_path):
        return None, "no chain_roles.json"
    with open(jr_path) as f:
        old = json.load(f, object_pairs_hook=OrderedDict)

    # Build new roles dict keyed by role -> {resid_range, n_residues}
    new_roles = OrderedDict()
    for role, seg in new_assigned.items():
        if role.startswith("UNRESOLVED"):
            new_roles[role] = OrderedDict([
                ("resid_range", f"{seg['resid_min']}-{seg['resid_max']}"),
                ("n_residues", seg['n_residues']),
            ])
        else:
            new_roles[role] = OrderedDict([
                ("resid_range", f"{seg['resid_min']}-{seg['resid_max']}"),
                ("n_residues", seg['n_residues']),
            ])

    # Diff old vs new (by resid range, which is the physical identity)
    changes = []
    for role, info in new_roles.items():
        if role.startswith("UNRESOLVED"):
            continue
        old_role = role_for_resid_range(old, *map(int, info["resid_range"].split("-")))
        if old_role != role:
            changes.append((info["resid_range"], old_role, role, evidence.get(role, "")))

    if not changes:
        return {"system_id": sid, "changes": [], "unchanged": True}, None

    if not dry_run:
        shutil.copy2(jr_path, jr_path + ".bak")
        out = OrderedDict([
            ("system_id", sid),
            ("n_segments", len(segs)),
            ("roles", new_roles),
        ])
        with open(jr_path, 'w') as f:
            json.dump(out, f, indent=2)

    return {"system_id": sid, "changes": changes, "unchanged": False,
            "new_roles": new_roles}, None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    systems = args if args else SWAP_SYSTEMS

    os.makedirs(OUT_DIR, exist_ok=True)
    log_lines = []
    log_lines.append("# Chain-Role Swap Fix Log\n")
    log_lines.append(f"Mode: {'DRY-RUN (no files written)' if dry_run else 'APPLY'}\n")
    log_lines.append(f"Systems: {len(systems)}\n\n")

    n_fixed = 0
    for sid in systems:
        res, err = fix_system(sid, dry_run)
        if err:
            log_lines.append(f"## {sid}\nERROR: {err}\n\n")
            continue
        if res["unchanged"]:
            log_lines.append(f"## {sid}\nNo change needed.\n\n")
            continue
        n_fixed += 1
        log_lines.append(f"## {sid}\n")
        log_lines.append("| resid_range | old role | new role | evidence |\n")
        log_lines.append("|---|---|---|---|\n")
        for rng, oldr, newr, ev in res["changes"]:
            log_lines.append(f"| {rng} | {oldr} | **{newr}** | {ev} |\n")
        log_lines.append("\n")

    log_path = os.path.join(OUT_DIR, "CHAIN_SWAP_FIX_LOG.md")
    with open(log_path, 'w') as f:
        f.write(''.join(log_lines))

    print(f"{'Would fix' if dry_run else 'Fixed'} {n_fixed}/{len(systems)} systems.")
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
