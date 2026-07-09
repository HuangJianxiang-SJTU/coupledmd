#!/usr/bin/env python3
"""
RCSB-backed chain-role audit & fix for ALL 222 CoupledMD systems.

GROUND TRUTH: RCSB PDB entity data (authoritative).
For every system, load the PDB's polymer entity info, map each entity to
its role (Receptor / G_alpha / G_beta / G_gamma / peptide_ligand / stabilizer),
then match each sim segment against the RCSB entities using sliding-window
sequence alignment to determine the correct role.

KEY INSIGHT: Sim segments may be SUBSETS of RCSB entities (e.g. mini-Gs is a
truncated Gα), or CHIMERAS (e.g. Gi2-mini-G13). Simple prefix alignment fails.
We use sliding-window matching: for each sim segment, find the RCSB entity
whose sequence has the best local match.

FALLBACK: When RCSB is ambiguous, use intrinsic sequence signatures:
  - G_alpha: GTPase P-loop GxxxxGK[ST] and/or Switch-II VDVGG
  - G_beta:  conserved N-term ELDQLRQEAEQLK / LRQEAEQLKNQIRD
  - Receptor: matches receptor_uniprot, no GTPase, no G-beta sig
  - G_gamma: ~40-90 aa

USAGE:
  python3 scripts/rcsb_chain_audit.py                    # audit only (dry-run)
  python3 scripts/rcsb_chain_audit.py --apply             # audit + fix
  python3 scripts/rcsb_chain_audit.py --apply G12_7SF7    # fix one system
"""
import os, sys, re, json, csv, time, shutil
from collections import OrderedDict, defaultdict
import numpy as np

# ── PATHS ──
VIZ_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz"
ROLES_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output/chain_roles"
OUT_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output"
MASTER_CSV = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/systems_master.csv"
CACHE_DIR = "/MDdata/data02/jxhuang/gpcr_g/a/cache"

# ── AA MAP ──
AA3TO1 = {
    'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E',
    'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
    'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V',
    'HSD':'H','HSE':'H','HSP':'H','HID':'H','HIE':'H','HIP':'H',
    'CYX':'C','ASH':'D','GLH':'E','LYN':'K',
}

# ── INTRINSIC MOTIFS ──
PLOOP = re.compile(r"G....GK[ST]")
VDVGG = re.compile(r"VDVGG")
GBETA_NTERM = re.compile(r"ELDQLRQEAEQLK|DQLRQEAEQLKNQ|LRQEAEQLKNQIRD")

STABILIZER_SEQUENCES = {
    "scFv16": "EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVSAISGSGGSTYYADSVKGRFTISRDNSKNTLYLQMNSLRAEDTAVYYCAKDRLSITIRPRYYGLDVWGQGTTVTVSS",
    "Nb35":   "EVQLVESGGGLVQPGGSLRLSCAASGRTFSSYAMGWFRQAPGKEREFVAAISWNGGSTGYADSVKGRFTISRDNAKNTVYLQMNSLKPEDTAVYYCAADYTGGYCSRRDCYARQYEYWGQGTQVTVSS",
    "BRIL":   "MGSWAEFKQRIAAIYKTILPAALNVNIKQTEQDIKNAIEKFKQEI",
}


# ═══════════════════════════════════════════════════════════════════
# RCSB ENTITY LOADING (from cache only, no network)
# ═══════════════════════════════════════════════════════════════════

def get_rcsb_entities(pdb_id, sid, cache_dir):
    """Load all polymer entities for a PDB ID from cached RCSB data."""
    entities = []
    entity_cache_dir = os.path.join(cache_dir, sid)
    if not os.path.isdir(entity_cache_dir):
        return None
    entity_files = sorted([f for f in os.listdir(entity_cache_dir)
                           if f.startswith(f"rcsb_{pdb_id}_entity") and f.endswith(".json")])
    if not entity_files:
        return None
    for ef in entity_files:
        with open(os.path.join(entity_cache_dir, ef)) as f:
            data = json.load(f)
        entity_poly = data.get("entity_poly", {})
        rcsb_poly = data.get("rcsb_polymer_entity", {})
        desc = rcsb_poly.get("pdbx_description", "")
        auth_asym = entity_poly.get("pdbx_strand_id", "")
        seq = entity_poly.get("pdbx_seq_one_letter_code_can", "")
        seq = seq.replace("\n", "").replace(" ", "").replace("-", "")
        eid = ef.replace(f"rcsb_{pdb_id}_entity", "").replace(".json", "")
        entity_type = classify_rcsb_entity(desc, seq)
        entities.append({
            "entity_id": eid, "auth_asym": auth_asym, "description": desc,
            "sequence": seq, "entity_type": entity_type, "seq_len": len(seq),
        })
    return entities


def classify_rcsb_entity(description, sequence):
    """Classify an RCSB entity by its description and sequence."""
    desc_lower = description.lower()

    # Stabilizers first
    if "scfv16" in desc_lower or "scfv" in desc_lower:
        return "stabilizer_scFv16"
    if "nb35" in desc_lower or "nanobody" in desc_lower:
        return "stabilizer_Nb35"
    if "bril" in desc_lower or "apolipoprotein" in desc_lower:
        return "stabilizer_BRIL"

    # G-protein subunits - use specific patterns
    # G_gamma: must have "gamma" AND G-protein context
    if re.search(r'subunit\s+gamma|gamma-\d|g\([^)]*\)\s*subunit\s+gamma|gn[gk]', desc_lower):
        return "G_gamma"
    if "gamma" in desc_lower and any(kw in desc_lower for kw in
            ["g(i)", "g(s)", "g(o)", "g(t)", "g(q)", "g(12)", "g(13)",
             "subunit", "binding protein"]):
        return "G_gamma"

    # G_beta: must have "beta" AND G-protein context
    if re.search(r'subunit\s+beta|beta-\d|g\([^)]*\)\s*subunit\s+beta|gnb', desc_lower):
        return "G_beta"
    if "beta" in desc_lower and any(kw in desc_lower for kw in
            ["g(i)", "g(s)", "g(o)", "g(t)", "g(q)", "g(12)", "g(13)",
             "subunit", "binding protein"]):
        return "G_beta"

    # G_alpha: must have alpha/G-protein context, NOT beta/gamma
    if "beta" not in desc_lower and "gamma" not in desc_lower:
        if re.search(r'subunit\s+alpha|alpha-\d|g\([^)]*\)\s*subunit\s+alpha|gna[sioq]', desc_lower):
            return "G_alpha"
        if any(kw in desc_lower for kw in
               ["g(i)", "g(s)", "g(o)", "g(q)", "g(12)", "g(13)",
                "subunit alpha", "g protein subunit", "mini-g",
                "chimera"]):
            # "chimera" catches "Gi2-mini-G13 chimera" which is G_alpha
            if "beta" not in desc_lower and "gamma" not in desc_lower:
                return "G_alpha"

    # Receptor (GPCR)
    if "receptor" in desc_lower or "gpcr" in desc_lower or "rhodopsin" in desc_lower:
        return "Receptor"
    gpcr_keywords = ["adrenergic", "dopamine", "serotonin", "opioid", "chemokine",
                     "muscarinic", "glucagon", "cannabinoid", "histamine", "purinergic",
                     "endothelin", "angiotensin", "vasopressin", "oxytocin", "thromboxane",
                     "prostaglandin", "leukotriene", "sphingosine", "lysophospholipid",
                     "smoothened", "frizzled", "secretin", "glucagon-like", "pacap",
                     "calcitonin", "parathyroid", "corticotropin", "melanocortin",
                     "tachykinin", "bombesin", "neurotensin", "ghrelin", "motilin",
                     "platelet-activating", "free fatty acid", "bile acid", "succinate",
                     "orphan", "g protein-coupled", "gprotein-coupled", "g-protein-coupled",
                     "adhesion g protein"]
    for kw in gpcr_keywords:
        if kw in desc_lower:
            return "Receptor"

    # Peptide ligand
    if len(sequence) < 50 and "peptide" in desc_lower:
        return "peptide_ligand"

    # Fallback: sequence signatures
    if PLOOP.search(sequence) or VDVGG.search(sequence):
        return "G_alpha"
    if GBETA_NTERM.search(sequence):
        return "G_beta"
    if len(sequence) < 100:
        return "G_gamma"

    return "other"


# ═══════════════════════════════════════════════════════════════════
# SEQUENCE MATCHING (sliding-window for subset/chimera detection)
# ═══════════════════════════════════════════════════════════════════

def sliding_window_identity(seg_seq, rcsb_seq, window_size=30):
    """
    Find the best local match between a sim segment sequence and an RCSB
    sequence using sliding windows. Returns (best_identity, coverage).

    This handles cases where:
    - The sim segment is a SUBSET of the RCSB entity (e.g. mini-Gs)
    - The sim segment is a CHIMERA (e.g. Gi2-mini-G13)
    - The sim sequence has modified residues shown as 'X'
    """
    if not seg_seq or not rcsb_seq:
        return 0.0, 0.0

    seg_len = len(seg_seq)
    rcsb_len = len(rcsb_seq)

    # For each position in the RCSB sequence, try aligning the segment there
    best_ident = 0.0
    best_coverage = 0.0

    # If segment is shorter than RCSB (typical: mini-G, chimera)
    if seg_len <= rcsb_len:
        for offset in range(rcsb_len - seg_len + 1):
            matches = 0
            valid = 0
            for i in range(seg_len):
                a = seg_seq[i]
                b = rcsb_seq[offset + i]
                if a != 'X' and b != 'X':
                    valid += 1
                    if a == b:
                        matches += 1
            ident = matches / valid if valid > 0 else 0.0
            coverage = seg_len / rcsb_len
            if ident > best_ident:
                best_ident = ident
                best_coverage = coverage
    else:
        # Segment is longer than RCSB (unusual but possible)
        for offset in range(seg_len - rcsb_len + 1):
            matches = 0
            valid = 0
            for i in range(rcsb_len):
                a = seg_seq[offset + i]
                b = rcsb_seq[i]
                if a != 'X' and b != 'X':
                    valid += 1
                    if a == b:
                        matches += 1
            ident = matches / valid if valid > 0 else 0.0
            coverage = rcsb_len / seg_len
            if ident > best_ident:
                best_ident = ident
                best_coverage = coverage

    return best_ident, best_coverage


def match_segment_to_rcsb(seg_sequence, rcsb_entities):
    """
    Find the best-matching RCSB entity for a sim segment.
    Uses sliding-window matching to handle subsets/chimeras.
    Returns (entity_type, entity_id, identity, coverage, description).
    """
    best_type = None
    best_id = None
    best_ident = 0.0
    best_cov = 0.0
    best_desc = ""

    for ent in rcsb_entities:
        ident, cov = sliding_window_identity(seg_sequence, ent["sequence"])
        # Score: prioritize identity, then coverage for tie-breaking
        score = ident * 0.8 + cov * 0.2
        best_score = best_ident * 0.8 + best_cov * 0.2
        if ident > best_ident or (ident == best_ident and cov > best_cov):
            best_ident = ident
            best_cov = cov
            best_type = ent["entity_type"]
            best_id = ent["entity_id"]
            best_desc = ent["description"]

    return best_type, best_id, best_ident, best_cov, best_desc


# ═══════════════════════════════════════════════════════════════════
# SEGMENT EXTRACTION (from viz PDB)
# ═══════════════════════════════════════════════════════════════════

def extract_segments(pdb_path):
    """Spatial segmentation by CA-CA gap > 10 A."""
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
        seg_resids = [ca_data[j][0] for j in range(prev, b)]
        segments.append({
            'seg_idx': len(segments), 'resids': seg_resids,
            'sequence': ''.join(ca_data[j][1] for j in range(prev, b)),
            'n_residues': len(seg_resids),
            'resid_min': seg_resids[0] if seg_resids else 0,
            'resid_max': seg_resids[-1] if seg_resids else 0,
        })
        prev = b
    seg_resids = [ca_data[j][0] for j in range(prev, len(ca_data))]
    segments.append({
        'seg_idx': len(segments), 'resids': seg_resids,
        'sequence': ''.join(ca_data[j][1] for j in range(prev, len(ca_data))),
        'n_residues': len(seg_resids),
        'resid_min': seg_resids[0] if seg_resids else 0,
        'resid_max': seg_resids[-1] if seg_resids else 0,
    })
    return segments


# ═══════════════════════════════════════════════════════════════════
# INTRINSIC SIGNATURE CHECKS (fallback / cross-check)
# ═══════════════════════════════════════════════════════════════════

def has_gtpase(seq):
    if PLOOP.search(seq) or VDVGG.search(seq):
        return True
    relaxed = re.compile(r"G.{4}GK[ST]")
    return bool(relaxed.search(seq))

def has_gbeta_sig(seq):
    return bool(GBETA_NTERM.search(seq))

def best_stabilizer_match(seq):
    best_name, best_ident = "", 0.0
    for name, ref in STABILIZER_SEQUENCES.items():
        ident, _ = sliding_window_identity(seq, ref)
        if ident > best_ident:
            best_ident, best_name = ident, name
    return best_name, best_ident

def intrinsic_classify(seg):
    """Classify a segment by intrinsic sequence signatures."""
    seq = seg['sequence']
    n = seg['n_residues']
    gtp = has_gtpase(seq)
    gb = has_gbeta_sig(seq)
    stab_name, stab_i = best_stabilizer_match(seq)

    if gtp and 200 <= n <= 420:
        motif = "P-loop" if PLOOP.search(seq) else ("VDVGG" if VDVGG.search(seq) else "relaxed P-loop")
        return "G_alpha", f"GTPase {motif}, n={n}"
    if gb:
        return "G_beta", f"G-beta N-term signature, n={n}"
    if stab_i > 0.5:
        return f"stabilizer_{stab_name}", f"seq identity {stab_i:.0%}, n={n}"
    if n >= 200:
        return "Receptor", f"large non-GTPase non-Gbeta, n={n}"
    if 40 <= n <= 90:
        return "G_gamma", f"size n={n}"
    if n < 40:
        return "peptide_ligand", f"size n={n}"
    return "UNRESOLVED", f"n={n}"


# ═══════════════════════════════════════════════════════════════════
# ROLE ASSIGNMENT (RCSB-backed + intrinsic cross-check)
# ═══════════════════════════════════════════════════════════════════

def assign_roles_rcsb(segments, rcsb_entities, receptor_uniprot="",
                      peptide_ligand_info=None):
    """
    Assign roles to segments using RCSB entity matching as ground truth,
    with intrinsic signatures as cross-check.

    Strategy:
    1. Match each segment to its best RCSB entity (sliding-window)
    2. Use intrinsic signatures as cross-check / tie-breaker
    3. Assign core roles (G_alpha, G_beta, Receptor, G_gamma) first
    4. Assign remaining segments (peptide_ligand, stabilizer, UNRESOLVED)

    Returns: (assigned_roles, audit_rows)
    """
    assigned = OrderedDict()
    used = set()

    # Step 1: Match each segment to RCSB entities
    seg_matches = []
    for seg in segments:
        rcsb_type, rcsb_eid, rcsb_ident, rcsb_cov, rcsb_desc = \
            match_segment_to_rcsb(seg['sequence'], rcsb_entities)
        intr_role, intr_ev = intrinsic_classify(seg)
        seg_matches.append({
            'seg': seg,
            'rcsb_type': rcsb_type,
            'rcsb_eid': rcsb_eid,
            'rcsb_ident': rcsb_ident,
            'rcsb_cov': rcsb_cov,
            'rcsb_desc': rcsb_desc,
            'intr_role': intr_role,
            'intr_ev': intr_ev,
        })

    # Step 2: Assign core roles
    # For each core role, find the best-matching unassigned segment.
    # Use RCSB match as primary, intrinsic as tie-breaker.

    def assign_core_role(role_name, rcsb_type, intr_role, min_ident=0.3):
        """Assign a core role to the best-matching unassigned segment."""
        candidates = []
        for m in seg_matches:
            if m['seg']['seg_idx'] in used:
                continue
            # Primary: RCSB entity type match
            if m['rcsb_type'] == rcsb_type and m['rcsb_ident'] >= min_ident:
                candidates.append((m, m['rcsb_ident'], 'rcsb'))
            # Fallback: intrinsic signature match
            elif m['intr_role'] == intr_role:
                candidates.append((m, 0.0, 'intrinsic'))

        if not candidates:
            return None

        # Sort by: RCSB match first (higher identity), then intrinsic
        candidates.sort(key=lambda x: (x[2] == 'rcsb', x[1]), reverse=True)
        best_m = candidates[0][0]
        seg = best_m['seg']
        assigned[role_name] = seg
        used.add(seg['seg_idx'])
        return best_m

    # Assign in priority order: G_alpha > G_beta > Receptor > G_gamma
    assign_core_role("G_alpha", "G_alpha", "G_alpha")
    assign_core_role("G_beta", "G_beta", "G_beta")
    assign_core_role("Receptor", "Receptor", "Receptor")
    assign_core_role("G_gamma", "G_gamma", "G_gamma")

    # Step 3: Assign remaining segments
    for m in seg_matches:
        seg = m['seg']
        if seg['seg_idx'] in used:
            continue

        rcsb_type = m['rcsb_type']
        intr_role = m['intr_role']
        n = seg['n_residues']

        # Stabilizer
        if rcsb_type and rcsb_type.startswith('stabilizer_'):
            assigned[rcsb_type] = seg
            used.add(seg['seg_idx'])
            continue
        stab_name, stab_i = best_stabilizer_match(seg['sequence'])
        if stab_i > 0.5:
            assigned[f"stabilizer_{stab_name}"] = seg
            used.add(seg['seg_idx'])
            continue

        # Peptide ligand
        if rcsb_type == 'peptide_ligand':
            assigned["peptide_ligand"] = seg
            used.add(seg['seg_idx'])
            continue
        if peptide_ligand_info and n < 50 and n > 0:
            assigned["peptide_ligand"] = seg
            used.add(seg['seg_idx'])
            continue

        # Receptor fragment (split by loop gaps)
        if rcsb_type == 'Receptor' or (intr_role == 'Receptor' and n >= 30):
            if "Receptor" not in assigned:
                assigned["Receptor"] = seg
            else:
                n_frags = sum(1 for r in assigned if r.startswith("Receptor_frag"))
                assigned[f"Receptor_frag{n_frags}"] = seg
            used.add(seg['seg_idx'])
            continue

        # G_alpha fragment
        if rcsb_type == 'G_alpha' or intr_role == 'G_alpha':
            if "G_alpha" not in assigned:
                assigned["G_alpha"] = seg
            else:
                assigned[f"UNRESOLVED_seg{seg['seg_idx']}"] = seg
            used.add(seg['seg_idx'])
            continue

        # G_beta fragment
        if rcsb_type == 'G_beta' or intr_role == 'G_beta':
            if "G_beta" not in assigned:
                assigned["G_beta"] = seg
            else:
                assigned[f"UNRESOLVED_seg{seg['seg_idx']}"] = seg
            used.add(seg['seg_idx'])
            continue

        # G_gamma (second one, or mislabeled)
        if rcsb_type == 'G_gamma' or (intr_role == 'G_gamma' and 40 <= n <= 90):
            if "G_gamma" not in assigned:
                assigned["G_gamma"] = seg
            else:
                assigned[f"UNRESOLVED_seg{seg['seg_idx']}"] = seg
            used.add(seg['seg_idx'])
            continue

        # Default: UNRESOLVED
        assigned[f"UNRESOLVED_seg{seg['seg_idx']}"] = seg
        used.add(seg['seg_idx'])

    # Build audit rows
    audit_rows = []
    for m in seg_matches:
        seg = m['seg']
        correct_role = None
        for role, a_seg in assigned.items():
            if a_seg['seg_idx'] == seg['seg_idx']:
                correct_role = role
                break

        # Determine confidence
        if m['rcsb_ident'] >= 0.7:
            confidence = "HIGH"
        elif m['rcsb_ident'] >= 0.4:
            confidence = "MEDIUM"
        elif m['intr_role'] in ("G_alpha", "G_beta"):
            confidence = "MEDIUM"  # intrinsic motifs are reliable
        else:
            confidence = "LOW"

        audit_rows.append({
            'system_id': '',
            'sim_resid_range': f"{seg['resid_min']}-{seg['resid_max']}",
            'n_residues': seg['n_residues'],
            'current_role': '',
            'rcsb_chain': m['rcsb_desc'][:60] if m['rcsb_desc'] else '',
            'rcsb_entity_type': m['rcsb_type'] or 'N/A',
            'rcsb_identity': f"{m['rcsb_ident']:.1%}",
            'intrinsic_role': m['intr_role'],
            'CORRECT_role': correct_role or 'UNRESOLVED',
            'confidence': confidence,
            'evidence': f"RCSB:{m['rcsb_type']}({m['rcsb_ident']:.0%},cov={m['rcsb_cov']:.0%}) Intrinsic:{m['intr_ev']}",
            'needs_fix': '',
        })

    return assigned, audit_rows


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def load_master():
    with open(MASTER_CSV) as f:
        rows = list(csv.DictReader(f))
    return {r['system_id']: r for r in rows}

def load_current_roles(sid):
    path = os.path.join(ROLES_DIR, f"{sid}_chain_roles.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f, object_pairs_hook=OrderedDict)

def get_current_role_for_range(jr, rmin, rmax):
    for role, info in jr.get("roles", {}).items():
        lo, hi = map(int, info["resid_range"].split("-"))
        if lo == rmin and hi == rmax:
            return role
        if not (rmax < lo or rmin > hi):
            return role
    return None


def main():
    apply_mode = "--apply" in sys.argv
    target_systems = [a for a in sys.argv[1:] if not a.startswith("--")]

    print("=" * 70)
    print(f"RCSB-BACKED CHAIN-ROLE AUDIT {'(APPLY MODE)' if apply_mode else '(DRY-RUN)'}")
    print("=" * 70)

    master = load_master()
    systems = sorted(target_systems) if target_systems else sorted(master.keys())
    print(f"Systems to audit: {len(systems)}")

    all_audit_rows = []
    fix_log = []
    n_fixed = 0
    n_errors = 0
    n_unchanged = 0

    for i, sid in enumerate(systems):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(systems)}...")

        info = master.get(sid)
        if info is None:
            n_errors += 1
            continue

        pdb_id = info['pdb_id']
        receptor_uniprot = info.get('receptor_uniprot', '')
        peptide_chain = info.get('peptide_ligand_chain', '').strip()
        peptide_seq = info.get('peptide_ligand_sequence', '').strip()
        peptide_len = info.get('peptide_ligand_length', '').strip()
        peptide_info = None
        if peptide_chain:
            peptide_info = {"chain": peptide_chain, "sequence": peptide_seq, "length": peptide_len}

        # 1. Load RCSB entities
        try:
            rcsb_entities = get_rcsb_entities(pdb_id, sid, CACHE_DIR)
        except Exception as e:
            print(f"  {sid}: RCSB load error: {e}")
            n_errors += 1
            continue
        if rcsb_entities is None:
            print(f"  {sid}: no RCSB data for {pdb_id}")
            n_errors += 1
            continue

        # 2. Extract segments
        pdb_path = os.path.join(VIZ_DIR, sid, "structure.pdb")
        if not os.path.exists(pdb_path):
            n_errors += 1
            continue
        try:
            segments = extract_segments(pdb_path)
        except Exception as e:
            print(f"  {sid}: segment extraction error: {e}")
            n_errors += 1
            continue

        # 3. Load current roles
        current_jr = load_current_roles(sid)
        if current_jr is None:
            n_errors += 1
            continue

        # 4. Assign roles
        assigned, audit_rows = assign_roles_rcsb(
            segments, rcsb_entities, receptor_uniprot, peptide_info)

        # 5. Fill in current_role and needs_fix
        for row in audit_rows:
            row['system_id'] = sid
            rmin, rmax = map(int, row['sim_resid_range'].split("-"))
            row['current_role'] = get_current_role_for_range(current_jr, rmin, rmax) or "N/A"
            cur = row['current_role']
            cor = row['CORRECT_role']
            cur_canon = "Receptor" if (cur or "").startswith("Receptor") else cur
            cor_canon = "Receptor" if cor.startswith("Receptor") else cor
            row['needs_fix'] = "TRUE" if cur_canon != cor_canon else "FALSE"

        all_audit_rows.extend(audit_rows)

        # 6. Check if any roles need fixing
        needs_fix = False
        changes = []
        for role, seg in assigned.items():
            if role.startswith("UNRESOLVED") or role.startswith("Receptor_frag"):
                continue
            rmin, rmax = seg['resid_min'], seg['resid_max']
            old_role = get_current_role_for_range(current_jr, rmin, rmax)
            if old_role != role:
                needs_fix = True
                changes.append((f"{rmin}-{rmax}", old_role, role))

        if not needs_fix:
            n_unchanged += 1
            continue

        # 7. Apply fix
        n_fixed += 1
        fix_entry = {
            "system_id": sid, "pdb_id": pdb_id, "changes": changes,
            "new_roles": {role: f"{seg['resid_min']}-{seg['resid_max']}" for role, seg in assigned.items()},
        }

        if apply_mode:
            jr_path = os.path.join(ROLES_DIR, f"{sid}_chain_roles.json")
            bak_path = jr_path + ".bak"
            if not os.path.exists(bak_path):
                shutil.copy2(jr_path, bak_path)

            new_roles_dict = OrderedDict()
            for role, seg in assigned.items():
                new_roles_dict[role] = OrderedDict([
                    ("resid_range", f"{seg['resid_min']}-{seg['resid_max']}"),
                    ("n_residues", seg['n_residues']),
                ])
            out = OrderedDict([
                ("system_id", sid),
                ("n_segments", len(segments)),
                ("roles", new_roles_dict),
            ])
            with open(jr_path, 'w') as f:
                json.dump(out, f, indent=2)

        fix_log.append(fix_entry)
        if len(changes) <= 5:
            change_str = "; ".join(f"{rng}: {old}->{new}" for rng, old, new in changes)
        else:
            change_str = f"{len(changes)} changes"
        print(f"  {sid}: {'FIXED' if apply_mode else 'NEEDS FIX'} - {change_str}")

    # ── Write CHAIN_AUDIT_FINAL.csv ──
    os.makedirs(OUT_DIR, exist_ok=True)
    audit_path = os.path.join(OUT_DIR, "CHAIN_AUDIT_FINAL.csv")
    with open(audit_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            "system_id", "sim_resid_range", "n_residues", "current_role",
            "rcsb_chain", "rcsb_entity_type", "rcsb_identity",
            "intrinsic_role", "CORRECT_role", "confidence", "evidence", "needs_fix"])
        w.writeheader()
        w.writerows(all_audit_rows)

    # ── Summary ──
    n_needs_fix = sum(1 for r in all_audit_rows if r['needs_fix'] == 'TRUE')
    fix_systems = sorted(set(r['system_id'] for r in all_audit_rows if r['needs_fix'] == 'TRUE'))

    print(f"\n{'='*70}")
    print(f"AUDIT SUMMARY")
    print(f"{'='*70}")
    print(f"  Systems processed: {len(systems)}")
    print(f"  Systems needing fix: {len(fix_systems)}")
    print(f"  Systems unchanged: {n_unchanged}")
    print(f"  Systems with errors: {n_errors}")
    print(f"  Segments needing fix: {n_needs_fix}")
    if apply_mode:
        print(f"  Systems FIXED: {n_fixed}")
    print(f"\n  Audit CSV: {audit_path}")

    if fix_systems:
        print(f"\n  Systems needing fix ({len(fix_systems)}):")
        for sid in fix_systems:
            print(f"    {sid}")

    return fix_log, all_audit_rows


if __name__ == "__main__":
    main()
