#!/usr/bin/env python3
"""
Phase B — Assign correct chain roles for all CoupledMD systems (v3).

Strategy:
1. Extract segments from viz PDB using spatial gap detection
2. Assign G_alpha using CGN G.* overlap with combined score (frac * n_residues)
3. Assign G_gamma using SIZE (50-120 aa)
4. Among remaining large segments (280+ aa):
   - Assign Receptor and G_beta using size + GPCRdb overlap
5. Assign stabilizers using sequence matching
6. Remaining → UNRESOLVED
"""
import os, sys, json, csv, time, warnings
from collections import defaultdict
import numpy as np

warnings.filterwarnings("ignore")

VIZ_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz"
CACHE_DIR = "/MDdata/data02/jxhuang/gpcr_g/a/cache"
OUT_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output/chain_roles"
os.makedirs(OUT_DIR, exist_ok=True)

AA3TO1 = {
    'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E',
    'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
    'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V',
    'HSD':'H','HSE':'H','HSP':'H','HID':'H','HIE':'H','HIP':'H',
    'CYX':'C','ASH':'D','GLH':'E','LYN':'K',
}

STABILIZER_SEQUENCES = {
    "scFv16": "EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVSAISGSGGSTYYADSVKGRFTISRDNSKNTLYLQMNSLRAEDTAVYYCAKDRLSITIRPRYYGLDVWGQGTTVTVSS",
    "Nb35": "EVQLVESGGGLVQPGGSLRLSCAASGRTFSSYAMGWFRQAPGKEREFVAAISWNGGSTGYADSVKGRFTISRDNAKNTVYLQMNSLKPEDTAVYYCAADYTGGYCSRRDCYARQYEYWGQGTQVTVSS",
    "BRIL": "MGSWAEFKQRIAAIYKTILPAALNVNIKQTEQDIKNAIEKFKQEI",
}


def seq_identity(seq1, seq2):
    if not seq1 or not seq2:
        return 0.0
    min_len = min(len(seq1), len(seq2))
    max_len = max(len(seq1), len(seq2))
    if max_len == 0:
        return 0.0
    matches = sum(1 for a, b in zip(seq1[:min_len], seq2[:min_len]) if a == b)
    return matches / max_len


def extract_segments(pdb_path):
    import MDAnalysis as mda
    u = mda.Universe(pdb_path)
    ca_data = []
    for res in u.residues:
        ca = res.atoms.select_atoms("name CA")
        if len(ca) == 1:
            aa1 = AA3TO1.get(res.resname, 'X')
            ca_data.append((res.resid, aa1, ca.positions[0].copy()))
    if not ca_data:
        return []
    breaks = []
    for i in range(1, len(ca_data)):
        dist = np.linalg.norm(ca_data[i][2] - ca_data[i-1][2])
        if dist > 10.0:
            breaks.append(i)
    segments = []
    prev = 0
    for b in breaks:
        seg_resids = [ca_data[j][0] for j in range(prev, b)]
        seg_seq = ''.join(ca_data[j][1] for j in range(prev, b))
        segments.append({
            'seg_idx': len(segments),
            'resids': seg_resids,
            'sequence': seg_seq,
            'n_residues': len(seg_resids),
            'resid_min': seg_resids[0] if seg_resids else 0,
            'resid_max': seg_resids[-1] if seg_resids else 0,
        })
        prev = b
    seg_resids = [ca_data[j][0] for j in range(prev, len(ca_data))]
    seg_seq = ''.join(ca_data[j][1] for j in range(prev, len(ca_data)))
    segments.append({
        'seg_idx': len(segments),
        'resids': seg_resids,
        'sequence': seg_seq,
        'n_residues': len(seg_resids),
        'resid_min': seg_resids[0] if seg_resids else 0,
        'resid_max': seg_resids[-1] if seg_resids else 0,
    })
    return segments


def process_system(system_id):
    pdb_path = os.path.join(VIZ_DIR, system_id, "structure.pdb")
    if not os.path.exists(pdb_path):
        return None, "No PDB"
    
    try:
        segments = extract_segments(pdb_path)
    except Exception as e:
        return None, f"PDB error: {e}"
    
    if not segments:
        return None, "No segments"
    
    # Get CGN G.* resids (ONLY G.* segments, not H.*)
    cgn_path = os.path.join(CACHE_DIR, system_id, "cgn_mapping.csv")
    ga_resids_cgn = set()
    if os.path.exists(cgn_path):
        with open(cgn_path) as f:
            for row in csv.DictReader(f):
                if row["cgn_segment"].startswith("G."):
                    ga_resids_cgn.add(int(row["sim_resid"]))
    
    # ── ASSIGN ROLES ──
    role_map = {}  # seg_idx → role
    
    # Step 1: Assign G_alpha using combined score (overlap_frac * n_residues)
    best_ga_score = 0
    best_ga_seg = None
    for seg in segments:
        resids = set(seg['resids'])
        n = seg['n_residues']
        if ga_resids_cgn and n > 0:
            ga_overlap = len(resids & ga_resids_cgn)
            ga_frac = ga_overlap / n
            score = ga_frac * n
            if score > best_ga_score:
                best_ga_score = score
                best_ga_seg = seg
    
    if best_ga_seg and best_ga_score > 50:  # minimum score threshold
        role_map[best_ga_seg['seg_idx']] = "G_alpha"
    elif segments:
        # Fallback: largest segment is G_alpha
        seg = max(segments, key=lambda s: s['n_residues'])
        role_map[seg['seg_idx']] = "G_alpha"
    
    # Step 2: Assign G_gamma using SIZE (50-120 aa, smallest segment)
    unassigned = [seg for seg in segments if seg['seg_idx'] not in role_map]
    small_segs = [seg for seg in unassigned if 30 <= seg['n_residues'] <= 120]
    if small_segs:
        seg = min(small_segs, key=lambda s: s['n_residues'])
        role_map[seg['seg_idx']] = "G_gamma"
    
    # Step 3: Among remaining large segments, assign Receptor and G_beta
    unassigned = [seg for seg in segments if seg['seg_idx'] not in role_map]
    large_segs = [seg for seg in unassigned if seg['n_residues'] >= 150]
    
    if len(large_segs) == 1:
        # Only one large segment left
        # If G_beta is already assigned, this is Receptor; vice versa
        if "G_beta" not in role_map.values():
            role_map[large_segs[0]['seg_idx']] = "G_beta"
        else:
            role_map[large_segs[0]['seg_idx']] = "Receptor"
    elif len(large_segs) >= 2:
        # Two or more large segments: assign Receptor and G_beta
        # Key insight: the segment immediately after G_alpha is Receptor
        # The segment after G_gamma is G_beta
        ga_seg_idx = None
        for seg_idx, role in role_map.items():
            if role == "G_alpha":
                ga_seg_idx = seg_idx
                break
        
        # Sort large_segs by position (resid_min)
        large_segs.sort(key=lambda s: s['resid_min'])
        
        if ga_seg_idx is not None:
            # Find the G_alpha segment
            ga_seg = next(seg for seg in segments if seg['seg_idx'] == ga_seg_idx)
            # The large segment with resid_min closest to (ga_seg.resid_max + 1) is Receptor
            best_rec = None
            best_dist = float('inf')
            for seg in large_segs:
                dist = abs(seg['resid_min'] - (ga_seg['resid_max'] + 1))
                if dist < best_dist:
                    best_dist = dist
                    best_rec = seg
            
            if best_rec:
                role_map[best_rec['seg_idx']] = "Receptor"
                # The other large segment(s): the one farthest from G_alpha is G_beta
                remaining = [seg for seg in large_segs if seg['seg_idx'] != best_rec['seg_idx']]
                if remaining:
                    # The largest remaining is G_beta
                    seg = max(remaining, key=lambda s: s['n_residues'])
                    role_map[seg['seg_idx']] = "G_beta"
                    # Any extra large segments are UNRESOLVED
                    for seg2 in remaining:
                        if seg2['seg_idx'] != seg['seg_idx']:
                            role_map[seg2['seg_idx']] = f"UNRESOLVED_seg{seg2['seg_idx']}"
        else:
            # Fallback: first large segment is Receptor, second is G_beta
            role_map[large_segs[0]['seg_idx']] = "Receptor"
            if len(large_segs) > 1:
                role_map[large_segs[1]['seg_idx']] = "G_beta"
            for seg in large_segs[2:]:
                role_map[seg['seg_idx']] = f"UNRESOLVED_seg{seg['seg_idx']}"
    
    # Step 4: Assign remaining segments
    unassigned = [seg for seg in segments if seg['seg_idx'] not in role_map]
    
    for seg in unassigned:
        n = seg['n_residues']
        seq = seg['sequence']
        assigned = False
        
        # Check stabilizers
        for stab_name, stab_seq in STABILIZER_SEQUENCES.items():
            ident = seq_identity(seq, stab_seq)
            if ident > 0.5:
                role_map[seg['seg_idx']] = f"stabilizer_{stab_name}"
                assigned = True
                break
        
        if not assigned:
            if n < 30:
                role_map[seg['seg_idx']] = "peptide_ligand"
            else:
                role_map[seg['seg_idx']] = f"UNRESOLVED_seg{seg['seg_idx']}"

    # Step 5: Recover fragmented Receptor
    # If no Receptor was assigned, UNRESOLVED segments 30–200 aa are likely
    # receptor loop/domain fragments (split by loop gaps or N/C truncations).
    # Larger UNRESOLVED (>200 aa) are left as-is — likely unmatched nanobodies.
    if "Receptor" not in role_map.values():
        unresolved_segs = sorted(
            [seg for seg in segments
             if role_map.get(seg['seg_idx'], '').startswith('UNRESOLVED')
             and 30 <= seg['n_residues'] <= 200],
            key=lambda s: s['n_residues'], reverse=True
        )
        # Label the largest as primary Receptor, rest as Receptor_fragment
        for idx_in_list, seg in enumerate(unresolved_segs):
            if idx_in_list == 0:
                role_map[seg['seg_idx']] = "Receptor"
            else:
                role_map[seg['seg_idx']] = f"Receptor_frag{idx_in_list}"

    # Build output
    result = {
        "system_id": system_id,
        "n_segments": len(segments),
        "roles": {},
    }
    
    for seg in segments:
        role = role_map.get(seg['seg_idx'], f"UNASSIGNED_seg{seg['seg_idx']}")
        result["roles"][role] = {
            "resid_range": f"{seg['resid_min']}-{seg['resid_max']}",
            "n_residues": seg['n_residues'],
        }
    
    # Write chain_roles.json
    out_path = os.path.join(OUT_DIR, f"{system_id}_chain_roles.json")
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result, None


def main():
    t0 = time.time()
    print("=" * 70)
    print("PHASE B — CHAIN ROLE ASSIGNMENT (v3)")
    print("=" * 70)
    
    systems = sorted([d for d in os.listdir(VIZ_DIR) 
                     if os.path.isdir(os.path.join(VIZ_DIR, d)) and d[0].isupper()])
    print(f"\nTotal systems: {len(systems)}")
    
    results = []
    errors = []
    n_ok = 0
    role_counts = defaultdict(int)
    
    for i, sid in enumerate(systems):
        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(systems)}...")
        
        result, error = process_system(sid)
        if error:
            errors.append((sid, error))
            continue
        
        results.append(result)
        roles = result.get("roles", {})
        
        for role in roles:
            role_counts[role.split("_seg")[0].split("_seg")[0]] += 1
        
        core_roles = {"G_alpha", "Receptor", "G_beta", "G_gamma"}
        if core_roles.issubset(roles.keys()):
            n_ok += 1
    
    print(f"\n=== ASSIGNMENT SUMMARY ===")
    print(f"  Total systems processed: {len(results)}")
    print(f"  Systems with all 4 core roles: {n_ok}")
    print(f"\n  Role counts:")
    for role in ["G_alpha", "Receptor", "G_beta", "G_gamma", "stabilizer_scFv16", "stabilizer_Nb35", "stabilizer_BRIL", "peptide_ligand", "UNRESOLVED"]:
        print(f"    {role}: {role_counts.get(role, 0)}")
    
    if errors:
        print(f"\n  Errors: {len(errors)}")
    
    elapsed = time.time() - t0
    print(f"\n  Elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
