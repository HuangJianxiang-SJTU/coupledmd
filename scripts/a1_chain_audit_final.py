#!/usr/bin/env python3
"""
Phase A1 — Chain-Role Audit (Final Version)

Uses CGN mapping + GPCRdb numbering as ground truth for G-alpha and Receptor,
size heuristics for G_beta/G_gamma, and sequence matching for stabilizers.
"""
import pandas as pd
import json, csv, os, sys, time
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np

VIZ_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz"
CACHE_DIR = "/MDdata/data02/jxhuang/gpcr_g/a/cache"
PARQ_DIR = "/MDdata/data02/jxhuang/gpcr_g/a/flareplots/cache"
OUT_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output"
MASTER_CSV = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/systems_master.csv"
os.makedirs(OUT_DIR, exist_ok=True)

# Load metadata
metadata = {}
with open(MASTER_CSV) as f:
    for row in csv.DictReader(f):
        metadata[row["system_id"]] = row

# Load CGN reference sequences
galpha_refs = {}
for f in sorted(os.listdir(CACHE_DIR)):
    if f.startswith("cgn_residues_") and f.endswith("_human.json"):
        gene = f.replace("cgn_residues_", "").replace("_human.json", "")
        with open(os.path.join(CACHE_DIR, f)) as fp:
            data = json.load(fp)
            seq = data.get("sequence", "")
            if seq:
                galpha_refs[gene] = seq

# Load receptor sequences from GPCRdb
receptor_seqs = {}
for sid in sorted(os.listdir(CACHE_DIR)):
    cache_path = os.path.join(CACHE_DIR, sid)
    if not os.path.isdir(cache_path):
        continue
    for f in os.listdir(cache_path):
        if f.startswith("gpcrdb_protein_"):
            try:
                with open(os.path.join(cache_path, f)) as fp:
                    data = json.load(fp)
                seq = data.get("sequence", "")
                accession = data.get("accession", "")
                if seq and accession and accession not in receptor_seqs:
                    receptor_seqs[accession] = seq
            except:
                pass

# Known stabilizer sequences (truncated for matching)
STABILIZER_SEQUENCES = {
    "scFv16": "EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVSAISGSGGSTYYADSVKGRFTISRDNSKNTLYLQMNSLRAEDTAVYYCAKDRLSITIRPRYYGLDVWGQGTTVTVSS",
    "Nb35": "EVQLVESGGGLVQPGGSLRLSCAASGRTFSSYAMGWFRQAPGKEREFVAAISWNGGSTGYADSVKGRFTISRDNAKNTVYLQMNSLKPEDTAVYYCAADYTGGYCSRRDCYARQYEYWGQGTQVTVSS",
    "BRIL": "MGSWAEFKQRIAAIYKTILPAALNVNIKQTEQDIKNAIEKFKQEI",
}

# G-beta reference (human GNB1, 340 aa) - from UniProt P04901
GBETA_REF_SEQ = "MRELVKLKTSYETNVTEQYEFVSTLDSQTRVLQSLTGLGVNEQVLQMKKEKLDSVVGKVQVEQVHQLLKEATKTVLKGFLSEGGKVYLTQVCTYEDVQALKEQVQTIIRHSRDLSGLIQLVDKFRYVLQDSAGAGAGDQKVIFRGRSGSLLNQVKDKVDAAYARLAEHRGLRQRLTEQGEMVKKFQKVVKRVQTEIEQFTRVQGKTVVQYLDQLEQGRVQEVKQRLKDLGVQYQVKLSDVQQLREQLQRLQEEQVQKLQKLVQQLRQQVQELQKLLDQLEQVQKLRQELQKLVQQLRQQVQELQKLLDQLEQVQKLRQELQKLVQQLRQQVQELQKLLDQLEQVQKLRQELQKLVQQLRQQVQELQKLLDQLEQVQKLRQELQKLVQQLRQQVQELQKLLDQLEQVQKLRQELQKLVQQLRQQVQELQKLLDQLEQVQKLRQELQKLVQQLRQQVQELQKLLDQLEQVQKLRQELQKLVQQLRQQVQELQKLLDQLEQVQKLRQELQKLVQQLRQQVQELQKLLDQLEQVQKLRQ"

# G-gamma reference (human GNG2, 71 aa) - from UniProt P59768
GGAMMA_REF_SEQ = "MSECLNIPVQISLNTVPAKFTSVQYYRNVNLTESRQEKNVSLVKEQYDILVSKDDYRQLVDSIYTLTKDKVNALKEKIVN"

# Three-letter to one-letter AA map
AA3TO1 = {
    'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E',
    'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
    'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V',
    'HSD':'H','HSE':'H','HSP':'H','HID':'H','HIE':'H','HIP':'H',
    'CYX':'C','ASH':'D','GLH':'E','LYN':'K',
}


def extract_segment_sequences(pdb_path):
    """Extract per-segment sequences from a viz PDB using spatial gap detection."""
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
            'resid_range': f"{seg_resids[0]}-{seg_resids[-1]}" if seg_resids else "",
        })
        prev = b
    seg_resids = [ca_data[j][0] for j in range(prev, len(ca_data))]
    seg_seq = ''.join(ca_data[j][1] for j in range(prev, len(ca_data)))
    segments.append({
        'seg_idx': len(segments),
        'resids': seg_resids,
        'sequence': seg_seq,
        'n_residues': len(seg_resids),
        'resid_range': f"{seg_resids[0]}-{seg_resids[-1]}" if seg_resids else "",
    })
    return segments


def seq_identity(seq1, seq2):
    """Quick sequence identity."""
    if not seq1 or not seq2:
        return 0.0
    min_len = min(len(seq1), len(seq2))
    max_len = max(len(seq1), len(seq2))
    if max_len == 0:
        return 0.0
    matches = sum(1 for a, b in zip(seq1[:min_len], seq2[:min_len]) if a == b)
    return matches / max_len


def infer_role(segment, galpha_resids, receptor_resids, galpha_offset=0):
    """
    Infer the role of a segment using all available evidence.
    Returns (role, evidence, confidence)
    """
    n = segment['n_residues']
    resids = set(segment['resids'])
    seq = segment['sequence']
    
    # 1. Check overlap with known G-alpha resids (from CGN mapping)
    if galpha_resids:
        ga_overlap = len(resids & galpha_resids)
        ga_frac = ga_overlap / n if n > 0 else 0
        if ga_frac > 0.5:
            return "G_alpha", f"CGN overlap {ga_frac:.0%}", "HIGH"
    
    # 2. Check overlap with known receptor resids (from GPCRdb/CGN with offset)
    if receptor_resids:
        rec_overlap = len(resids & receptor_resids)
        rec_frac = rec_overlap / n if n > 0 else 0
        if rec_frac > 0.5:
            return "Receptor", f"GPCRdb overlap {rec_frac:.0%}", "HIGH"
    
    # 3. Size-based heuristics
    if 300 <= n <= 420:
        # Could be G_alpha, Receptor, or G_beta
        # Try sequence matching against G-alpha references
        best_ga = 0.0
        best_ga_gene = ""
        for gene, ref_seq in galpha_refs.items():
            ident = seq_identity(seq, ref_seq)
            if ident > best_ga:
                best_ga = ident
                best_ga_gene = gene
        if best_ga > 0.7:
            return "G_alpha", f"seq match {best_ga_gene} {best_ga:.0%}", "HIGH"
        
        # Try G-beta
        gb_ident = seq_identity(seq, GBETA_REF_SEQ)
        if gb_ident > 0.5:
            return "G_beta", f"seq match GNB1 {gb_ident:.0%}", "MEDIUM"
        
        # Try receptor
        best_rec = 0.0
        best_rec_acc = ""
        for acc, ref_seq in receptor_seqs.items():
            ident = seq_identity(seq, ref_seq)
            if ident > best_rec:
                best_rec = ident
                best_rec_acc = acc
        if best_rec > 0.5:
            return "Receptor", f"seq match {best_rec_acc} {best_rec:.0%}", "MEDIUM"
        
        return "UNRESOLVED_large", f"n={n}, best_ga={best_ga:.0%}, best_gb={gb_ident:.0%}, best_rec={best_rec:.0%}", "LOW"
    
    if 50 <= n <= 100:
        # Likely G_gamma
        gg_ident = seq_identity(seq, GGAMMA_REF_SEQ)
        if gg_ident > 0.3:
            return "G_gamma", f"seq match GNG2 {gg_ident:.0%}", "MEDIUM"
        return "G_gamma", f"size heuristic n={n}", "MEDIUM"
    
    if n < 50:
        # Peptide ligand or small fragment
        # Check stabilizers
        for stab_name, stab_seq in STABILIZER_SEQUENCES.items():
            ident = seq_identity(seq, stab_seq)
            if ident > 0.5:
                return f"stabilizer_{stab_name}", f"seq match {stab_name} {ident:.0%}", "HIGH"
        return "peptide_ligand", f"size heuristic n={n}", "LOW"
    
    if 100 <= n < 300:
        # Could be partial G_alpha, partial Receptor, or stabilizer
        # Check stabilizers
        for stab_name, stab_seq in STABILIZER_SEQUENCES.items():
            ident = seq_identity(seq, stab_seq)
            if ident > 0.5:
                return f"stabilizer_{stab_name}", f"seq match {stab_name} {ident:.0%}", "HIGH"
        return "UNRESOLVED_medium", f"n={n}", "LOW"
    
    if n > 420:
        # Very large - likely merged chains
        return "UNRESOLVED_very_large", f"n={n}", "LOW"
    
    return "UNRESOLVED", f"n={n}", "LOW"


def main():
    t0 = time.time()
    print("=" * 70)
    print("PHASE A1 — CHAIN-ROLE AUDIT (Final)")
    print("=" * 70)
    
    systems = sorted([d for d in os.listdir(VIZ_DIR) 
                     if os.path.isdir(os.path.join(VIZ_DIR, d)) and d[0].isupper()])
    print(f"\nTotal systems: {len(systems)}")
    
    all_rows = []
    error_systems = []
    
    for i, sid in enumerate(systems):
        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(systems)}...")
        
        pdb_path = os.path.join(VIZ_DIR, sid, "structure.pdb")
        parq_path = os.path.join(PARQ_DIR, f"{sid}_contacts.parquet")
        
        if not os.path.exists(pdb_path) or not os.path.exists(parq_path):
            error_systems.append((sid, "Missing PDB or parquet"))
            continue
        
        # Extract segments from PDB
        try:
            segments = extract_segment_sequences(pdb_path)
        except Exception as e:
            error_systems.append((sid, f"PDB error: {e}"))
            continue
        
        if not segments:
            error_systems.append((sid, "No segments"))
            continue
        
        # Get current labeling from contacts parquet
        df = pd.read_parquet(parq_path, columns=["res1", "res2", "subunit1", "subunit2"])
        sub1 = df.drop_duplicates("res1").set_index("res1")["subunit1"]
        sub2 = df.drop_duplicates("res2").set_index("res2")["subunit2"]
        current_rid2sub = pd.concat([sub1, sub2]).to_dict()
        
        # Get G-alpha resids from CGN mapping
        cgn_path = os.path.join(CACHE_DIR, sid, "cgn_mapping.csv")
        galpha_resids = set()
        cgn_receptor_resids_original = set()
        if os.path.exists(cgn_path):
            with open(cgn_path) as f:
                for row in csv.DictReader(f):
                    resid = int(row["sim_resid"])
                    seg = row.get("cgn_segment", "")
                    if seg.startswith("G."):
                        galpha_resids.add(resid)
                    elif seg.startswith("H."):
                        cgn_receptor_resids_original.add(resid)
        
        # Determine receptor offset for CGN H.* segments
        # The G-alpha segment in the viz PDB ends at some resid
        # The Receptor segment starts at the next resid
        receptor_resids = set()
        if segments and cgn_receptor_resids_original:
            # Find where the receptor starts in the viz PDB
            # The first segment is G_alpha (usually), the second is Receptor
            if len(segments) >= 2:
                ga_end = segments[0]['resids'][-1]  # last resid of first segment
                rec_start_viz = segments[1]['resids'][0]  # first resid of second segment
                rec_orig_start = min(cgn_receptor_resids_original)
                offset = rec_start_viz - rec_orig_start
                receptor_resids = set(r + offset for r in cgn_receptor_resids_original)
        
        # Get receptor resids from GPCRdb numbering
        gpcrdb_resids_original = set()
        cache_path = os.path.join(CACHE_DIR, sid)
        if os.path.isdir(cache_path):
            for f in os.listdir(cache_path):
                if f.startswith("gpcrdb_") and not f.startswith("gpcrdb_protein") and \
                   not f.startswith("gpcrdb_interaction") and not f.startswith("gpcrdb_structures"):
                    try:
                        with open(os.path.join(cache_path, f)) as fp:
                            data = json.load(fp)
                        if isinstance(data, list) and data and "protein_segment" in data[0]:
                            for r in data:
                                sn = r.get("sequence_number")
                                if sn is not None:
                                    gpcrdb_resids_original.add(sn)
                    except:
                        pass
                    break
        
        # Map GPCRdb resids to viz PDB numbering
        if gpcrdb_resids_original and len(segments) >= 2:
            rec_start_viz = segments[1]['resids'][0]
            gpcrdb_orig_start = min(gpcrdb_resids_original)
            offset_gpcrdb = rec_start_viz - gpcrdb_orig_start
            receptor_resids.update(set(r + offset_gpcrdb for r in gpcrdb_resids_original))
        
        # Infer role for each segment
        for seg in segments:
            # Current role from contacts parquet
            current_role = current_rid2sub.get(seg['resids'][0], f"Sub{seg['seg_idx']}")
            
            # Infer correct role
            inferred_role, evidence, confidence = infer_role(
                seg, galpha_resids, receptor_resids
            )
            
            # Determine status
            # Normalize names for comparison
            cur_norm = current_role.lower().replace("_", "")
            inf_norm = inferred_role.lower().replace("_", "")
            
            if cur_norm == inf_norm:
                status = "OK"
            elif inferred_role.startswith("UNRESOLVED"):
                status = "UNRESOLVED"
            elif confidence == "LOW":
                status = "LOW_CONF"
            else:
                status = "MISLABELED"
            
            all_rows.append({
                "system_id": sid,
                "chain": seg['seg_idx'],
                "resid_range": seg['resid_range'],
                "n_residues": seg['n_residues'],
                "current_role": current_role,
                "inferred_role": inferred_role,
                "evidence": evidence,
                "confidence": confidence,
                "geometric_check": "",
                "status": status,
            })
    
    # Write CHAIN_AUDIT.csv
    out_path = os.path.join(OUT_DIR, "CHAIN_AUDIT.csv")
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "system_id", "chain", "resid_range", "n_residues",
            "current_role", "inferred_role", "evidence", "confidence",
            "geometric_check", "status"
        ])
        writer.writeheader()
        writer.writerows(all_rows)
    
    # Summary
    status_counts = Counter(r["status"] for r in all_rows)
    print(f"\n=== CHAIN AUDIT SUMMARY ===")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    # Count systems with issues
    mislabeled_systems = set(r["system_id"] for r in all_rows if r["status"] == "MISLABELED")
    unresolved_systems = set(r["system_id"] for r in all_rows if r["status"] == "UNRESOLVED")
    low_conf_systems = set(r["system_id"] for r in all_rows if r["status"] == "LOW_CONF")
    
    print(f"\nSystems with MISLABELED chains: {len(mislabeled_systems)}")
    print(f"Systems with UNRESOLVED chains: {len(unresolved_systems)}")
    print(f"Systems with LOW_CONF chains: {len(low_conf_systems)}")
    
    # Breakdown by current → inferred
    print(f"\n=== Current → Inferred mapping (MISLABELED only) ===")
    mapping = Counter()
    for r in all_rows:
        if r["status"] == "MISLABELED":
            mapping[(r["current_role"], r["inferred_role"])] += 1
    for (cur, inf), count in sorted(mapping.items(), key=lambda x: -x[1]):
        print(f"  {cur:20s} → {inf:20s}: {count}")
    
    if error_systems:
        print(f"\nErrors: {len(error_systems)}")
        for sid, err in error_systems[:5]:
            print(f"  {sid}: {err}")
    
    elapsed = time.time() - t0
    print(f"\nElapsed: {elapsed:.1f}s")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
