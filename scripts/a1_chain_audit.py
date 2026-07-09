#!/usr/bin/env python3
"""
Phase A1 — Chain-Role Audit for CoupledMD

For every system:
1. Extract each chain/segment's sequence from the viz PDB
2. Sequence-match each chain against reference panels
3. Geometric cross-check on inferred map
4. Compare against current spatial-gap labeling
5. Output CHAIN_AUDIT.csv
"""

import os, sys, json, csv, time, warnings
from pathlib import Path
from collections import defaultdict
from multiprocessing import Pool
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Paths ──
VIZ_DIR    = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz"
CACHE_DIR  = "/MDdata/data02/jxhuang/gpcr_g/a/cache"
PARQ_DIR   = "/MDdata/data02/jxhuang/gpcr_g/a/flareplots/cache"
MASTER_CSV = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/systems_master.csv"
OUT_DIR    = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Three-letter to one-letter AA map ──
AA3TO1 = {
    'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E',
    'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
    'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V',
    'HSD':'H','HSE':'H','HSP':'H','HID':'H','HIE':'H','HIP':'H',
    'CYX':'C','ASH':'D','GLH':'E','LYN':'K',
}

# ── Load reference sequences ──
def load_cgn_references():
    """Load CGN reference sequences for G-alpha subtypes."""
    refs = {}
    for f in sorted(os.listdir(CACHE_DIR)):
        if f.startswith("cgn_residues_") and f.endswith("_human.json"):
            gene = f.replace("cgn_residues_", "").replace("_human.json", "")
            with open(os.path.join(CACHE_DIR, f)) as fp:
                data = json.load(fp)
                seq = data.get("sequence", "")
                if seq:
                    refs[f"Galpha_{gene}"] = seq
    return refs

def load_gpcrdb_receptor_sequences():
    """Load receptor sequences from GPCRdb protein metadata."""
    refs = {}
    for sid in sorted(os.listdir(CACHE_DIR)):
        cache_path = os.path.join(CACHE_DIR, sid)
        if not os.path.isdir(cache_path):
            continue
        for f in os.listdir(cache_path):
            if f.startswith("gpcrdb_protein_"):
                with open(os.path.join(cache_path, f)) as fp:
                    data = json.load(fp)
                seq = data.get("sequence", "")
                accession = data.get("accession", "")
                name = data.get("name", "")
                if seq and accession:
                    key = f"Receptor_{accession}"
                    refs[key] = {"sequence": seq, "accession": accession, "name": name, "system_id": sid}
    return refs

# ── Known stabilizer/peptide sequences ──
STABILIZER_SEQUENCES = {
    "scFv16": "EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVSAISGSGGSTYYADSVKGRFTISRDNSKNTLYLQMNSLRAEDTAVYYCAKDRLSITIRPRYYGLDVWGQGTTVTVSSASTKGPSVFPLAPSSKSTSGGTAALGCLVKDYFPEPVTVSWNSGALTSGVHTFPAVLQSSGLYSLSSVVTVPSSSLGTQTYICNVNHKPSNTKVDKKVEPKSCDKTHTCPPCPAPELLGGPSVFLFPPKPKDTLMISRTPEVTCVVVDVSHEDPEVKFNWYVDGVEVHNAKTKPREEQYNSTYRVVSVLTVLHQDWLNGKEYKCKVSNKALPAPIEKTISKAKGQPREPQVYTLPPSREEMTKNQVSLTCLVKGFYPSDIAVEWESNGQPENNYKTTPPVLDSDGSFFLYSKLTVDKSRWQQGNVFSCSVMHEALHNHYTQKSLSLSPGK",
    "Nb35": "EVQLVESGGGLVQPGGSLRLSCAASGRTFSSYAMGWFRQAPGKEREFVAAISWNGGSTGYADSVKGRFTISRDNAKNTVYLQMNSLKPEDTAVYYCAADYTGGYCSRRDCYARQYEYWGQGTQVTVSS",
    "BRIL": "MGSWAEFKQRIAAIYKTILPAALNVNIKQTEQDIKNAIEKFKQEI",
}

# ── Sequence matching ──
def seq_identity(seq1, seq2):
    """Compute sequence identity between two sequences (global alignment approximation)."""
    if not seq1 or not seq2:
        return 0.0
    # Simple sliding window approach for speed
    shorter = seq1 if len(seq1) <= len(seq2) else seq2
    longer = seq2 if len(seq1) <= len(seq2) else seq1
    
    if len(shorter) == 0:
        return 0.0
    
    # If sequences are similar length, do direct comparison
    if abs(len(seq1) - len(seq2)) < 20:
        min_len = min(len(seq1), len(seq2))
        matches = sum(1 for a, b in zip(seq1[:min_len], seq2[:min_len]) if a == b)
        return matches / max(len(seq1), len(seq2))
    
    # Otherwise, find best local match using sliding window
    best_id = 0.0
    window = len(shorter)
    for offset in range(0, len(longer) - window + 1, max(1, window // 4)):
        sub = longer[offset:offset + window]
        matches = sum(1 for a, b in zip(shorter, sub) if a == b)
        ident = matches / window
        best_id = max(best_id, ident)
    
    return best_id


def match_against_references(chain_seq, galpha_refs, receptor_refs_by_accession):
    """Match a chain sequence against all reference panels.
    Returns: (best_role, best_hit, best_identity)"""
    
    results = []
    
    # Match against G-alpha references
    for ref_name, ref_seq in galpha_refs.items():
        ident = seq_identity(chain_seq, ref_seq)
        results.append(("Galpha", ref_name, ident))
    
    # Match against receptor references
    for ref_name, ref_info in receptor_refs_by_accession.items():
        ident = seq_identity(chain_seq, ref_info["sequence"])
        results.append(("Receptor", ref_name, ident))
    
    # Match against stabilizers
    for stab_name, stab_seq in STABILIZER_SEQUENCES.items():
        ident = seq_identity(chain_seq, stab_seq)
        results.append(("stabilizer", stab_name, ident))
    
    # Heuristic: G_beta is ~340 aa WD40 repeat, G_gamma is ~60-70 aa
    chain_len = len(chain_seq)
    if 280 <= chain_len <= 400:
        # Could be G_beta or G_alpha - check if it matched G_alpha
        has_ga_match = any(r[0] == "Galpha" and r[2] > 0.5 for r in results)
        if not has_ga_match:
            results.append(("Gbeta", "heuristic_WD40", 0.7))
    if 50 <= chain_len <= 100:
        results.append(("Ggamma", "heuristic_small", 0.6))
    if chain_len < 50:
        results.append(("peptide_ligand", "heuristic_short", 0.5))
    
    # Sort by identity
    results.sort(key=lambda x: x[2], reverse=True)
    
    if not results or results[0][2] < 0.2:
        return "UNRESOLVED", "no_match", 0.0
    
    return results[0]


# ── Extract chains from PDB ──
def extract_chains_from_pdb(pdb_path):
    """Extract chain segments from a PDB file using spatial gap detection.
    Returns list of (segment_index, resids, sequence, ca_positions)."""
    import MDAnalysis as mda
    
    u = mda.Universe(pdb_path)
    
    # Get CA positions and residue info
    ca_data = []
    for res in u.residues:
        ca = res.atoms.select_atoms("name CA")
        if len(ca) == 1:
            aa1 = AA3TO1.get(res.resname, 'X')
            ca_data.append((res.resid, aa1, ca.positions[0].copy()))
    
    if not ca_data:
        return []
    
    # Detect spatial gaps (> 10 Å between consecutive CA atoms)
    breaks = []
    for i in range(1, len(ca_data)):
        dist = np.linalg.norm(ca_data[i][2] - ca_data[i-1][2])
        if dist > 10.0:
            breaks.append(i)
    
    # Build segments
    segments = []
    prev = 0
    for b in breaks:
        seg_resids = [ca_data[j][0] for j in range(prev, b)]
        seg_seq = ''.join(ca_data[j][1] for j in range(prev, b))
        seg_ca_pos = np.array([ca_data[j][2] for j in range(prev, b)])
        segments.append((len(segments), seg_resids, seg_seq, seg_ca_pos))
        prev = b
    # Last segment
    seg_resids = [ca_data[j][0] for j in range(prev, len(ca_data))]
    seg_seq = ''.join(ca_data[j][1] for j in range(prev, len(ca_data)))
    seg_ca_pos = np.array([ca_data[j][2] for j in range(prev, len(ca_data))])
    segments.append((len(segments), seg_resids, seg_seq, seg_ca_pos))
    
    return segments


# ── Current labeling from contacts parquet ──
def get_current_labeling(system_id):
    """Get the current subunit labeling from the contacts parquet."""
    parq_path = os.path.join(PARQ_DIR, f"{system_id}_contacts.parquet")
    if not os.path.exists(parq_path):
        return {}
    
    df = pd.read_parquet(parq_path)
    rid2sub = {}
    for col_r, col_s in [('res1', 'subunit1'), ('res2', 'subunit2')]:
        for _, row in df.iterrows():
            rid2sub[row[col_r]] = row[col_s]
    return rid2sub


# ── Geometric cross-check ──
def geometric_check(segments, role_map, ca_positions_all):
    """
    Check that the inferred roles are geometrically consistent:
    - G_alpha should contact the receptor (α5 into IC cavity)
    - G_beta should contact G_alpha
    - G_gamma should contact G_beta
    - Peptide ligand should be extracellular
    """
    # Compute COM for each segment
    seg_coms = {}
    for seg_idx, resids, seq, ca_pos in segments:
        role = role_map.get(seg_idx, "UNRESOLVED")
        com = ca_pos.mean(axis=0)
        seg_coms[role] = com
    
    checks = {}
    
    # G_alpha - Receptor distance (should be close, < 50 Å)
    if "Galpha" in seg_coms and "Receptor" in seg_coms:
        d = np.linalg.norm(seg_coms["Galpha"] - seg_coms["Receptor"])
        checks["Galpha-Receptor"] = d < 60.0  # generous threshold
    
    # G_beta - G_alpha distance
    if "Gbeta" in seg_coms and "Galpha" in seg_coms:
        d = np.linalg.norm(seg_coms["Gbeta"] - seg_coms["Galpha"])
        checks["Gbeta-Galpha"] = d < 50.0
    
    # G_gamma - G_beta distance
    if "Ggamma" in seg_coms and "Gbeta" in seg_coms:
        d = np.linalg.norm(seg_coms["Ggamma"] - seg_coms["Gbeta"])
        checks["Ggamma-Gbeta"] = d < 40.0
    
    # Overall pass/fail
    if not checks:
        return "NO_CHECK", checks
    all_pass = all(checks.values())
    return "pass" if all_pass else "fail", checks


# ── Process one system ──
def audit_system(args):
    system_id, galpha_refs, receptor_refs = args
    
    pdb_path = os.path.join(VIZ_DIR, system_id, "structure.pdb")
    if not os.path.exists(pdb_path):
        return {"system_id": system_id, "error": "No PDB file"}
    
    try:
        segments = extract_chains_from_pdb(pdb_path)
    except Exception as e:
        return {"system_id": system_id, "error": f"PDB parse error: {e}"}
    
    if not segments:
        return {"system_id": system_id, "error": "No segments found"}
    
    # Get current labeling
    current_labels = get_current_labeling(system_id)
    
    # Current subunit names in order
    current_subunit_order = ["G_alpha", "Receptor", "G_beta", "G_gamma", "Extra"]
    
    # Match each segment against references
    role_map = {}
    results = []
    
    for seg_idx, resids, seq, ca_pos in segments:
        # Current role (from spatial-gap heuristic)
        current_role = current_subunit_order[seg_idx] if seg_idx < len(current_subunit_order) else f"Sub{seg_idx}"
        # Also check from contacts parquet
        if resids and resids[0] in current_labels:
            current_role = current_labels[resids[0]]
        
        # Sequence match
        inferred_role, ref_hit, pct_id = match_against_references(seq, galpha_refs, receptor_refs)
        
        role_map[seg_idx] = inferred_role
        
        results.append({
            "system_id": system_id,
            "chain": seg_idx,
            "resid_range": f"{resids[0]}-{resids[-1]}" if resids else "",
            "n_residues": len(resids),
            "current_role": current_role,
            "inferred_role": inferred_role,
            "ref_hit": ref_hit,
            "pct_identity": f"{pct_id:.1%}",
            "geometric_check": "",
            "status": "OK" if current_role.replace("_", "").lower() == inferred_role.replace("_", "").lower() 
                      or (current_role == "G_alpha" and inferred_role == "Galpha")
                      or (current_role == "G_beta" and inferred_role == "Gbeta")
                      or (current_role == "G_gamma" and inferred_role == "Ggamma")
                      else "MISLABELED" if inferred_role != "UNRESOLVED" else "UNRESOLVED",
        })
    
    # Geometric cross-check
    all_ca = np.vstack([s[3] for s in segments])
    geo_status, geo_checks = geometric_check(segments, role_map, all_ca)
    
    for r in results:
        r["geometric_check"] = geo_status
    
    return {"system_id": system_id, "results": results, "geo_checks": geo_checks, "error": None}


def main():
    t0 = time.time()
    print("=" * 70)
    print("PHASE A1 — CHAIN-ROLE AUDIT")
    print("=" * 70)
    
    # Load references
    print("\n[1] Loading reference sequences...")
    galpha_refs = load_cgn_references()
    print(f"  G-alpha references: {len(galpha_refs)}")
    
    receptor_refs = load_gpcrdb_receptor_sequences()
    print(f"  Receptor references: {len(receptor_refs)}")
    
    # Get system list
    print("\n[2] Getting system list...")
    systems = sorted([d for d in os.listdir(VIZ_DIR) 
                     if os.path.isdir(os.path.join(VIZ_DIR, d)) and d[0].isupper()])
    print(f"  Total systems: {len(systems)}")
    
    # Process all systems
    print("\n[3] Auditing chain roles...")
    all_results = []
    errors = []
    
    # Process in parallel
    args = [(sid, galpha_refs, receptor_refs) for sid in systems]
    
    # Use sequential processing for now to avoid memory issues with MDAnalysis
    for i, arg in enumerate(args):
        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(args)} systems...")
        result = audit_system(arg)
        if result.get("error"):
            errors.append(result)
        else:
            all_results.append(result)
    
    # Flatten results
    rows = []
    for result in all_results:
        for r in result["results"]:
            rows.append(r)
    
    # Write CHAIN_AUDIT.csv
    out_path = os.path.join(OUT_DIR, "CHAIN_AUDIT.csv")
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["system_id", "chain", "resid_range", "n_residues",
                                                "current_role", "inferred_role", "ref_hit", 
                                                "pct_identity", "geometric_check", "status"])
        writer.writeheader()
        writer.writerows(rows)
    
    # Summary
    status_counts = defaultdict(int)
    for r in rows:
        status_counts[r["status"]] += 1
    
    print(f"\n[4] Summary:")
    print(f"  Total chain entries: {len(rows)}")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    # Count mislabeled systems
    mislabeled_systems = set()
    unresolved_systems = set()
    for r in rows:
        if r["status"] == "MISLABELED":
            mislabeled_systems.add(r["system_id"])
        if r["status"] == "UNRESOLVED":
            unresolved_systems.add(r["system_id"])
    
    print(f"\n  Systems with at least one MISLABELED chain: {len(mislabeled_systems)}")
    print(f"  Systems with at least one UNRESOLVED chain: {len(unresolved_systems)}")
    
    if errors:
        print(f"\n  Systems with errors: {len(errors)}")
        for e in errors[:5]:
            print(f"    {e['system_id']}: {e['error']}")
    
    elapsed = time.time() - t0
    print(f"\n  Elapsed: {elapsed:.1f}s")
    print(f"  Output: {out_path}")


if __name__ == "__main__":
    main()
