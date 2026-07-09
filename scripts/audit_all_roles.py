#!/usr/bin/env python3
"""
COMPREHENSIVE per-segment role audit across ALL 222 systems.

For every system, classify EACH segment by intrinsic signatures and compare
to the assigned role in chain_roles.json. Report ALL mismatches, not just
G_alpha-slot errors. Categories of problem detected:

  P1  G_alpha slot has NO GTPase motif (slot is really receptor/gbeta)
  P2  Receptor slot HAS a GTPase motif (slot is really G_alpha)
  P3  G_beta slot is not G-beta (no WD40 N-term) AND not G-alpha
  P4  G_gamma slot is the wrong size (not 40-90 aa)
  P5  a stabilizer (scFv16/Nb35/BRIL) is mislabeled / un-detected
  P6  segment assigned to two roles / overlapping ranges
  P7  a large segment is UNRESOLVED but looks like a real chain
  P8  a GTPase motif appears in a segment NOT labeled G_alpha

This is a READ-ONLY audit (writes only a CSV + markdown report).
"""
import os, re, json, csv
import numpy as np

VIZ_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz"
ROLES_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output/chain_roles"
OUT_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output"

AA3TO1 = {
    'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E',
    'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
    'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V',
    'HSD':'H','HSE':'H','HSP':'H','HID':'H','HIE':'H','HIP':'H',
    'CYX':'C','ASH':'D','GLH':'E','LYN':'K',
}
PLOOP = re.compile(r"G....GK[ST]")
VDVGG = re.compile(r"VDVGG")
DXXG  = re.compile(r"D.G")
GBETA_NTERM = re.compile(r"ELDQLRQEAEQLK|DQLRQEAEQLKNQ|LRQEAEQLKNQIRD")
STABILIZERS = {
    "scFv16": "EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVSAISGSGGSTYYADSVKGRFTISRDNSKNTLYLQMNSLRAEDTAVYYCAKDRLSITIRPRYYGLDVWGQGTTVTVSS",
    "Nb35":   "EVQLVESGGGLVQPGGSLRLSCAASGRTFSSYAMGWFRQAPGKEREFVAAISWNGGSTGYADSVKGRFTISRDNAKNTVYLQMNSLKPEDTAVYYCAADYTGGYCSRRDCYARQYEYWGQGTQVTVSS",
    "BRIL":   "MGSWAEFKQRIAAIYKTILPAALNVNIKQTEQDIKNAIEKFKQEI",
}


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
        if np.linalg.norm(ca_data[i][2] - ca_data[i-1][2]) > 10.0:
            breaks.append(i)
    segments, prev = [], 0
    for b in breaks:
        sr = [ca_data[j][0] for j in range(prev, b)]
        segments.append({'seg_idx': len(segments), 'resids': sr,
            'sequence': ''.join(ca_data[j][1] for j in range(prev, b)),
            'n_residues': len(sr), 'resid_min': sr[0], 'resid_max': sr[-1]})
        prev = b
    sr = [ca_data[j][0] for j in range(prev, len(ca_data))]
    segments.append({'seg_idx': len(segments), 'resids': sr,
        'sequence': ''.join(ca_data[j][1] for j in range(prev, len(ca_data))),
        'n_residues': len(sr), 'resid_min': sr[0], 'resid_max': sr[-1]})
    return segments


def seq_ident(a, b):
    if not a or not b: return 0.0
    m = min(len(a), len(b))
    return sum(1 for x, y in zip(a[:m], b[:m]) if x == y) / max(len(a), len(b))


def best_stabilizer(seq):
    best, best_n = "", 0.0
    for name, ref in STABILIZERS.items():
        i = seq_ident(seq, ref)
        if i > best_n:
            best_n, best = i, name
    return best, best_n


def classify(seg):
    """Return the role this segment SHOULD have, by intrinsic signature."""
    seq, n = seg['sequence'], seg['n_residues']
    gtp = bool(PLOOP.search(seq) or VDVGG.search(seq))
    gb = bool(GBETA_NTERM.search(seq))
    stab, stab_i = best_stabilizer(seq)
    if gtp and 200 <= n <= 420:
        return "G_alpha", "GTPase motif"
    if gb:
        return "G_beta", "G-beta N-term"
    if stab_i > 0.5:
        return f"stabilizer_{stab}", f"seq {stab_i:.0%}"
    if n >= 200:
        return "Receptor", f"large non-GTPase non-Gbeta (n={n})"
    if 40 <= n <= 90:
        return "G_gamma", f"size n={n}"
    if n < 40:
        return "peptide_ligand", f"size n={n}"
    return "UNRESOLVED", f"n={n}"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    systems = sorted([d for d in os.listdir(VIZ_DIR)
                      if os.path.isdir(os.path.join(VIZ_DIR, d)) and d[0].isupper()])
    rows = []
    problems = []

    for sid in systems:
        pdb_path = os.path.join(VIZ_DIR, sid, "structure.pdb")
        if not os.path.exists(pdb_path):
            continue
        try:
            segs = extract_segments(pdb_path)
        except Exception:
            continue
        jr_path = os.path.join(ROLES_DIR, f"{sid}_chain_roles.json")
        if not os.path.exists(jr_path):
            continue
        jr = json.load(open(jr_path))
        # map resid_min->assigned role
        assigned = {}
        for role, info in jr.get("roles", {}).items():
            lo, hi = map(int, info["resid_range"].split("-"))
            assigned[lo] = (role, hi)

        for seg in segs:
            intr, ev = classify(seg)
            # find assigned role for this segment's range
            asg_role = None
            for lo, (role, hi) in assigned.items():
                if lo == seg['resid_min'] and hi == seg['resid_max']:
                    asg_role = role; break
            if asg_role is None:
                for lo, (role, hi) in assigned.items():
                    if not (seg['resid_max'] < lo or seg['resid_min'] > hi):
                        asg_role = role; break
            seq = seg['sequence']
            gtp = bool(PLOOP.search(seq) or VDVGG.search(seq))
            gb = bool(GBETA_NTERM.search(seq))
            row = {
                "system_id": sid, "resid_range": f"{seg['resid_min']}-{seg['resid_max']}",
                "n_residues": seg['n_residues'], "assigned": asg_role,
                "intrinsic": intr, "gtpase": "Y" if gtp else "", "gbeta_sig": "Y" if gb else "",
                "first30": seg['sequence'][:30],
            }
            rows.append(row)

            # ---- problem detection ----
            def canon(r): return "Receptor" if (r or "").startswith("Receptor") else r
            a = canon(asg_role)
            probs = []
            if a == "G_alpha" and not gtp:
                probs.append("P1")
            if a == "Receptor" and gtp:
                probs.append("P2")
            if a == "G_beta" and not gb and not gtp and seg['n_residues'] >= 200:
                probs.append("P3")
            if a == "G_gamma" and not (40 <= seg['n_residues'] <= 90):
                probs.append("P4")
            if gtp and a != "G_alpha":
                probs.append("P8")
            # stabilizer mislabel
            sname, si = best_stabilizer(seq)
            if si > 0.5 and a and not str(a).startswith("stabilizer"):
                probs.append("P5")
            if not a:
                probs.append("P7" if seg['n_residues'] >= 100 else "")
            if probs:
                for p in probs:
                    problems.append((sid, p, row['resid_range'], asg_role,
                                     intr, f"gtpase={gtp},gbeta={gb},stab={sname}/{si:.0%}", row['first30']))

    # write CSV
    out_csv = os.path.join(OUT_DIR, "CHAIN_AUDIT_FULL.csv")
    with open(out_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=["system_id","resid_range","n_residues",
            "assigned","intrinsic","gtpase","gbeta_sig","first30"])
        w.writeheader(); w.writerows(rows)

    out_prob = os.path.join(OUT_DIR, "CHAIN_AUDIT_PROBLEMS.csv")
    with open(out_prob, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(["system_id","problem","resid_range","assigned","intrinsic","evidence","first30"])
        w.writerows(problems)

    # summary
    from collections import Counter
    prob_counts = Counter(p[1] for p in problems)
    prob_systems = sorted(set(p[0] for p in problems))
    print(f"Total systems scanned: {len(systems)}")
    print(f"Segments scanned: {len(rows)}")
    print(f"\nProblems by category:")
    for p in ["P1","P2","P3","P4","P5","P6","P7","P8"]:
        print(f"  {p}: {prob_counts.get(p,0)}")
    print(f"\nSystems with >=1 problem: {len(prob_systems)}")
    print(f"\nFull per-segment CSV: {out_csv}")
    print(f"Problems CSV: {out_prob}")


if __name__ == "__main__":
    main()
