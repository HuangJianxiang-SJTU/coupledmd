#!/usr/bin/env python3
"""Audit consistent TM-core and receptor--G-alpha interface selections.

Receptor-role segments are sequence-aligned independently to the canonical
GPCRdb receptor.  Only mapped TM1--TM7 C-alpha atoms are retained, preventing
peptide-sized segments mislabeled as Receptor from entering the calculation.
The G-alpha interface region and initial contacts are then defined geometrically
from the first topology frame using the same cutoffs for every system.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd
from Bio import Align
import MDAnalysis as mda
from scipy.spatial.distance import cdist
from build_final624_replica_qc_v9 import corrected_sources


ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent.parent / "data"
CACHE = ROOT / "v9_figure_inputs/gpcrdb_cache_v9"
INVENTORY = ROOT / "CoupledMD_Supplementary_Data/Supplementary_Data_S1_included_system_inventory.csv"
COMPONENT = ROOT / "trajectory_readiness/component_audit_summary_nc.csv"
MANIFEST = ROOT / "trajectory_readiness/replica_manifest.csv"
OUT = ROOT / "v9_figure_inputs/scidata_T12_final208_structural_selection_audit_v9.csv"

AA3 = {
    "ALA":"A","ARG":"R","ASN":"N","ASP":"D","CYS":"C","GLN":"Q","GLU":"E","GLY":"G",
    "HIS":"H","HSD":"H","HSE":"H","HSP":"H","HID":"H","HIE":"H","HIP":"H",
    "ILE":"I","LEU":"L","LYS":"K","MET":"M","PHE":"F","PRO":"P","SER":"S","THR":"T",
    "TRP":"W","TYR":"Y","VAL":"V","CYX":"C","ASH":"D","GLH":"E","LYN":"K",
}


def parse_range(text):
    start, end = map(int, str(text).split("-"))
    return start, end


def serialize(values):
    return ";".join(str(int(v)) for v in values)


def topology_map():
    manifest = pd.read_csv(MANIFEST)
    paths = {}
    for row in manifest.drop_duplicates("system_id").itertuples(index=False):
        paths[row.system_id] = row.protein_pdb
    # This repaired trajectory has a compact reordered topology.
    paths["Gq_7RAN"] = str(ROOT / "trajectory_readiness/Gq_7RAN_updated_repair/Gq_7RAN/aligned_topology.pdb")
    # The source protein.pdb is solvated; this is the matching protein topology.
    paths["Gi_6D9H"] = str(DATA / "viz/Gi_6D9H/structure.pdb")
    return {sid: Path(path) for sid, path in paths.items()}


def representative_trajectory_map():
    component = pd.read_csv(COMPONENT)
    paths = component.sort_values("replica").drop_duplicates("system_id").set_index("system_id")["aligned_trajectory_path"].to_dict()
    for audit_path, allowed in corrected_sources():
        audit = pd.read_csv(audit_path)
        audit = audit[audit.verdict.eq("GOOD")]
        if allowed is not None:
            audit = audit[audit.system_id.isin(allowed)]
        for row in audit.sort_values("replica").itertuples(index=False):
            paths.setdefault(row.system_id, row.trajectory_path)
            if int(row.replica) == 1:
                paths[row.system_id] = row.trajectory_path
    manifest = pd.read_csv(MANIFEST)
    for row in manifest[manifest.replica.eq(1)].itertuples(index=False):
        paths.setdefault(row.system_id, row.aligned_path)
    result = {}
    for sid, path in paths.items():
        path = Path(path)
        result[sid] = path if path.is_absolute() else ROOT / path
    return result


def galpha_references(family):
    genes = {
        "Gi": ["gnai1","gnai2","gnai3","gnao","gnat1","gnat2","gnat3","gnaz"],
        "Gs": ["gnas2","gnal"],
        "Gq": ["gnaq","gna11","gna14","gna15"],
        "G12-13": ["gna12","gna13"],
    }[family]
    refs = []
    for gene in genes:
        path = Path("/MDdata/data02/jxhuang/gpcr_g/a/cache") / f"cgn_residues_{gene}_human.json"
        if path.exists():
            refs.append(json.loads(path.read_text())["sequence"])
    return refs


def align_segment(canonical, segment):
    aligner = Align.PairwiseAligner(mode="local")
    aligner.match_score = 2.0
    aligner.mismatch_score = -1.0
    aligner.open_gap_score = -5.0
    aligner.extend_gap_score = -0.5
    alignments = aligner.align(canonical, segment)
    if len(alignments) == 0:
        return [], 0.0
    alignment = alignments[0]
    indices = alignment.indices
    paired = [(int(a), int(b)) for a, b in zip(indices[0], indices[1]) if a >= 0 and b >= 0]
    identity = sum(canonical[a] == segment[b] for a, b in paired) / len(paired) if paired else 0.0
    return paired, identity


def audit_one(row, topology, trajectory):
    sid = row.system_id
    base = {
        "system_id": sid, "g_protein_family": row.g_protein_family,
        "receptor_uniprot": row.receptor_uniprot, "topology_path": str(topology), "representative_trajectory_path":str(trajectory),
    }
    if not isinstance(row.receptor_uniprot, str) or not row.receptor_uniprot:
        return {**base, "selection_status":"unavailable", "reason_code":"no_canonical_receptor_accession"}
    protein_path = CACHE / f"{row.receptor_uniprot}_protein.json"
    residues_path = CACHE / f"{row.receptor_uniprot}_extended_residues.json"
    roles_path = DATA / "chain_roles" / f"{sid}_chain_roles.json"
    if not topology.exists() or not trajectory.exists() or not protein_path.exists() or not residues_path.exists() or not roles_path.exists():
        return {**base, "selection_status":"unavailable", "reason_code":"missing_topology_or_mapping_input"}

    universe = mda.Universe(str(topology), str(trajectory))
    roles = json.loads(roles_path.read_text())["roles"]
    receptor_roles = [(name, *parse_range(info["resid_range"])) for name, info in roles.items() if name.startswith("Receptor")]
    if not receptor_roles:
        return {**base, "selection_status":"unavailable", "reason_code":"missing_receptor_or_galpha_role"}

    receptor_sequences = {}
    for name, start, end in receptor_roles:
        receptor_sequences[name] = "".join(AA3.get(res.resname.upper(), "X") for res in universe.residues[start - 1:end])
    # One source identifier is demonstrably wrong in the inherited metadata:
    # 6D9H is the adenosine A1 receptor (P30542).  Preserve the metadata value
    # in the audit, but use the sequence-supported accession for mapping.
    sequence_supported_accession = {
        "Gi_6D9H": "P30542",
    }.get(sid, row.receptor_uniprot)
    if sequence_supported_accession != row.receptor_uniprot:
        protein_path = CACHE / f"{sequence_supported_accession}_protein.json"
        residues_path = CACHE / f"{sequence_supported_accession}_extended_residues.json"
    canonical = json.loads(protein_path.read_text())["sequence"]
    assigned_quality = max((len(pairs), identity) for pairs, identity in (align_segment(canonical, seq) for seq in receptor_sequences.values()))
    mapping_accession = sequence_supported_accession
    if assigned_quality[0] < 50 or assigned_quality[1] < .60:
        best = (assigned_quality[0] * assigned_quality[1], mapping_accession, canonical)
        for candidate_path in CACHE.glob("*_protein.json"):
            candidate = json.loads(candidate_path.read_text())
            quality = max((len(pairs), identity) for pairs, identity in (align_segment(candidate["sequence"], seq) for seq in receptor_sequences.values()))
            score = quality[0] * quality[1]
            if score > best[0]:
                best = (score, candidate["accession"], candidate["sequence"])
        mapping_accession, canonical = best[1], best[2]
        protein_path = CACHE / f"{mapping_accession}_protein.json"
        residues_path = CACHE / f"{mapping_accession}_extended_residues.json"
    residue_records = json.loads(residues_path.read_text())
    tm_by_index = {int(r["sequence_number"]) - 1:r["protein_segment"] for r in residue_records if r.get("protein_segment") in {f"TM{i}" for i in range(1,8)}}
    base["mapping_accession_used"] = mapping_accession
    base["metadata_accession_match"] = mapping_accession == row.receptor_uniprot

    mapped_tm = []
    mapped_receptor = []
    accepted_roles = []
    identities = []
    helix_labels = []
    for name, start, end in receptor_roles:
        residues = universe.residues[start - 1:end]
        sequence = receptor_sequences[name]
        pairs, identity = align_segment(canonical, sequence)
        tm_pairs = [(a, b) for a, b in pairs if a in tm_by_index]
        if len(pairs) >= 20 and identity >= 0.60 and tm_pairs:
            accepted_roles.append(name)
            identities.append(identity)
            for _, segment_index in pairs:
                ordinal = start + segment_index
                ca = universe.residues[ordinal - 1].atoms.select_atoms("name CA")
                if len(ca) == 1:
                    mapped_receptor.append(ordinal)
            for canonical_index, segment_index in tm_pairs:
                ordinal = start + segment_index
                ca = universe.residues[ordinal - 1].atoms.select_atoms("name CA")
                if len(ca) == 1:
                    mapped_tm.append(ordinal)
                    helix_labels.append(tm_by_index[canonical_index])
    mapped_tm = sorted(set(mapped_tm))
    mapped_receptor = sorted(set(mapped_receptor))
    helices = sorted(set(helix_labels))
    if len(mapped_tm) < 100 or helices != [f"TM{i}" for i in range(1, 8)]:
        return {
            **base, "selection_status":"unavailable", "reason_code":"insufficient_tm_core_mapping",
            "accepted_receptor_roles":";".join(accepted_roles), "mapping_identity_min":min(identities) if identities else np.nan,
            "n_tm_core_ca":len(mapped_tm), "n_tm_helices":len(helices), "tm_helices":";".join(helices),
        }

    receptor_atoms = sum((universe.residues[i - 1].atoms.select_atoms("name CA") for i in mapped_receptor), universe.atoms[[]])
    # Source chain-role labels are not reliable for several engineered G-alpha
    # constructs (for example, 7W53 splits G-alpha across roles labelled
    # G_alpha and G_gamma).  Identify G-alpha residues by family-reference
    # sequence alignment across all non-receptor components instead.
    references = galpha_references(row.g_protein_family)
    galpha_roles = []
    galpha_ordinals = []
    for name, info in roles.items():
        if name in accepted_roles or name.startswith("Receptor"):
            continue
        start, end = parse_range(info["resid_range"])
        residues = universe.residues[start - 1:end]
        sequence = "".join(AA3.get(res.resname.upper(), "X") for res in residues)
        if name.startswith("G_alpha"):
            galpha_roles.append((name, start, end))
            for ordinal in range(start, end + 1):
                if len(universe.residues[ordinal - 1].atoms.select_atoms("name CA")) == 1:
                    galpha_ordinals.append(ordinal)
            continue
        if not sequence:
            continue
        candidates = [(*align_segment(reference, sequence), reference) for reference in references]
        pairs, identity, _ = max(candidates, key=lambda item: len(item[0]) * item[1])
        n_identical = len(pairs) * identity
        if len(pairs) < 20 or n_identical < 15:
            continue
        galpha_roles.append((name, start, end))
        for ordinal in range(start, end + 1):
            if len(universe.residues[ordinal - 1].atoms.select_atoms("name CA")) == 1:
                galpha_ordinals.append(ordinal)
    galpha_ordinals = sorted(set(galpha_ordinals))
    if not galpha_roles or not galpha_ordinals:
        return {**base, "selection_status":"unavailable", "reason_code":"missing_receptor_or_galpha_role"}
    ga_atoms = sum((universe.residues[i - 1].atoms.select_atoms("name CA") for i in galpha_ordinals), universe.atoms[[]])
    # Use all sequence-verified receptor residues to define the initial
    # receptor--G-alpha interface.  The mapped TM core remains the independent
    # alignment/RMSD selection.  This retains genuine ICL2/ICL3/H8 contacts
    # without allowing mislabeled peptide-sized receptor segments into either
    # selection.
    distances = cdist(receptor_atoms.positions.astype(float), ga_atoms.positions.astype(float))
    ga_interface_local = np.where((distances <= 12.0).any(axis=0))[0]
    contact_pairs = np.argwhere(distances <= 8.0)
    if len(ga_interface_local) < 5 or len(contact_pairs) < 3:
        return {
            **base, "selection_status":"unavailable", "reason_code":"insufficient_initial_interface",
            "accepted_receptor_roles":";".join(accepted_roles), "mapping_identity_min":min(identities),
            "n_tm_core_ca":len(mapped_tm), "n_tm_helices":7, "tm_helices":";".join(helices),
            "n_galpha_interface_ca":len(ga_interface_local), "n_initial_contacts_8A":len(contact_pairs),
        }
    interface_ordinals = [galpha_ordinals[i] for i in ga_interface_local]
    contact_receptor_ordinals = [mapped_receptor[i] for i in contact_pairs[:, 0]]
    contact_ga_ordinals = [galpha_ordinals[i] for i in contact_pairs[:, 1]]
    return {
        **base, "selection_status":"available", "reason_code":"",
        "accepted_receptor_roles":";".join(accepted_roles), "mapping_identity_min":min(identities),
        "n_tm_core_ca":len(mapped_tm), "n_tm_helices":7, "tm_helices":";".join(helices),
        "tm_core_residue_ordinals":serialize(mapped_tm),
        "verified_receptor_residue_ordinals":serialize(mapped_receptor),
        "accepted_galpha_roles":";".join(x[0] for x in galpha_roles),
        "galpha_candidate_residue_ordinals":serialize(galpha_ordinals),
        "n_galpha_interface_ca":len(interface_ordinals), "galpha_interface_residue_ordinals":serialize(interface_ordinals),
        "n_initial_contacts_8A":len(contact_pairs),
        "contact_receptor_residue_ordinals":serialize(contact_receptor_ordinals),
        "contact_galpha_residue_ordinals":serialize(contact_ga_ordinals),
    }


def main():
    systems = pd.read_csv(INVENTORY)
    paths = topology_map()
    trajectories = representative_trajectory_map()
    rows = []
    for n, row in enumerate(systems.itertuples(index=False), 1):
        topology = paths.get(row.system_id, Path(""))
        trajectory = trajectories.get(row.system_id, Path(""))
        try:
            result = audit_one(row, topology, trajectory)
        except Exception as exc:
            result = {"system_id":row.system_id, "g_protein_family":row.g_protein_family,
                      "receptor_uniprot":row.receptor_uniprot, "topology_path":str(topology), "representative_trajectory_path":str(trajectory),
                      "selection_status":"unavailable", "reason_code":f"audit_error:{type(exc).__name__}:{exc}"}
        rows.append(result)
        if n % 40 == 0:
            print(f"  audited {n}/207 systems")
    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False)
    print(result["selection_status"].value_counts(dropna=False).to_string())
    print("Unavailable selections:")
    print(result.loc[result.selection_status.ne("available"), ["system_id","reason_code","n_tm_core_ca","n_tm_helices","n_galpha_interface_ca","n_initial_contacts_8A"]].to_string(index=False))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
