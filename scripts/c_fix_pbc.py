#!/usr/bin/env python3
"""
Phase C — Fix PBC issues for core-SEPARATED and SPLIT systems.

Uses backbone-connected unwrapping + inter-segment reassembly:
1. For each segment, unwrap CA atoms using consecutive-neighbor minimum image
2. Unwrap all other atoms relative to their segment's unwrapped CA positions
3. Reassemble: bring each segment's COM to the same periodic image as receptor
4. Center the entire complex on the receptor COM
5. Write corrected trajectory
"""
import os, sys, json, time, warnings, shutil
import numpy as np

warnings.filterwarnings("ignore")

VIZ_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz"
CHAIN_ROLES_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output/chain_roles"
BACKUP_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output/pbc_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

CORE_SEPARATED = [
    "G12_7SF8", "G12_8H8J", "Gi_6PT0", "Gi_7JVR", "Gi_7V68",
    "Gi_7VUG", "Gi_7YK6", "Gi_8J22", "Gi_8X16", "Gi_8YIC",
    "Gq_8Y53", "Gs_7FIG", "Gs_7T9N", "Gs_7TMW", "Gs_7VUH", "Gs_8I2G"
]
SPLIT = ["Gq_8DPF"]
ALL_FIX = CORE_SEPARATED + SPLIT


def unwrap_segment_backbone(ca_positions, box):
    """Unwrap CA positions using consecutive-neighbor minimum image."""
    unwrapped = ca_positions.copy()
    for i in range(1, len(unwrapped)):
        delta = unwrapped[i] - unwrapped[i-1]
        delta -= np.round(delta / box) * box
        unwrapped[i] = unwrapped[i-1] + delta
    return unwrapped


def fix_pbc(system_id):
    """Fix PBC issues for a single system."""
    import MDAnalysis as mda
    
    pdb_path = os.path.join(VIZ_DIR, system_id, "structure.pdb")
    xtc_path = os.path.join(VIZ_DIR, system_id, "traj.xtc")
    
    if not os.path.exists(pdb_path) or not os.path.exists(xtc_path):
        return None, "Missing PDB/XTC"
    
    # Get chain roles
    cr_path = os.path.join(CHAIN_ROLES_DIR, f"{system_id}_chain_roles.json")
    if not os.path.exists(cr_path):
        return None, "No chain_roles.json"
    
    with open(cr_path) as f:
        data = json.load(f)
    roles = data.get("roles", {})
    
    # Build segment info
    seg_info = {}
    for role, info in roles.items():
        rng = info.get("resid_range", "")
        if "-" in rng and role not in ("peptide_ligand",) and not role.startswith("UNRESOLVED"):
            parts = rng.split("-")
            seg_info[role] = (int(parts[0]), int(parts[1]))
    
    if "Receptor" not in seg_info:
        return None, "No Receptor in chain_roles"
    
    # Load universe
    try:
        u = mda.Universe(pdb_path, xtc_path)
    except Exception as e:
        return None, f"MDAnalysis error: {e}"
    
    n_frames = len(u.trajectory)
    if n_frames == 0:
        return None, "Zero frames"
    
    # Pre-compute atom indices for each segment
    seg_atoms = {}
    seg_ca_atoms = {}
    for role, (rmin, rmax) in seg_info.items():
        seg_atoms[role] = u.select_atoms(f"resid {rmin}-{rmax}")
        seg_ca_atoms[role] = u.select_atoms(f"name CA and resid {rmin}-{rmax}")
    
    receptor = seg_atoms.get("Receptor")
    if receptor is None or len(receptor) == 0:
        return None, "No receptor atoms"
    
    # Back up original trajectory
    backup_path = os.path.join(BACKUP_DIR, f"{system_id}_traj.xtc.bak")
    if not os.path.exists(backup_path):
        shutil.copy2(xtc_path, backup_path)
        print(f"  Backed up to {backup_path}")
    else:
        # Restore from backup first
        shutil.copy2(backup_path, xtc_path)
        u = mda.Universe(pdb_path, xtc_path)
        seg_atoms = {}
        seg_ca_atoms = {}
        for role, (rmin, rmax) in seg_info.items():
            seg_atoms[role] = u.select_atoms(f"resid {rmin}-{rmax}")
            seg_ca_atoms[role] = u.select_atoms(f"name CA and resid {rmin}-{rmax}")
        receptor = seg_atoms.get("Receptor")
    
    # Apply PBC correction and write corrected trajectory
    corrected_path = xtc_path.replace(".xtc", "_corrected.xtc")
    
    with mda.Writer(corrected_path, n_atoms=len(u.atoms)) as writer:
        for fi in range(n_frames):
            u.trajectory[fi]
            ts = u.trajectory.ts
            
            if ts.dimensions is None or ts.dimensions[0] <= 0:
                writer.write(u.atoms)
                continue
            
            box = ts.dimensions[:3]
            
            # Step 1: Unwrap each segment independently using backbone connectivity
            for role, ca_ag in seg_ca_atoms.items():
                if len(ca_ag) < 2:
                    continue
                
                ca_pos = ca_ag.positions.copy()
                unwrapped_ca = unwrap_segment_backbone(ca_pos, box)
                ca_shift = unwrapped_ca - ca_pos
                
                seg_ag = seg_atoms[role]
                ca_resids = ca_ag.resids
                ca_dict = dict(zip(ca_resids, ca_shift))
                
                for res in seg_ag.residues:
                    if res.resid in ca_dict:
                        shift = ca_dict[res.resid]
                        res.atoms.translate(shift)
            
            # Step 2: Reassemble - bring each segment to the same image as receptor
            rec_com = receptor.center_of_mass()
            for role, seg_ag in seg_atoms.items():
                if role == "Receptor" or len(seg_ag) == 0:
                    continue
                seg_com = seg_ag.center_of_mass()
                delta = seg_com - rec_com
                delta -= np.round(delta / box) * box
                shift = rec_com + delta - seg_com
                seg_ag.translate(shift)
            
            # Step 3: Center on receptor COM
            rec_com = receptor.center_of_mass()
            box_center = box / 2.0
            translation = box_center - rec_com
            u.atoms.translate(translation)
            
            writer.write(u.atoms)
    
    # Replace original with corrected
    os.rename(corrected_path, xtc_path)
    
    return {"system_id": system_id, "n_frames": n_frames, "status": "FIXED"}, None


def validate_pbc(system_id):
    """Re-run PBC check on the corrected trajectory."""
    import MDAnalysis as mda
    
    pdb_path = os.path.join(VIZ_DIR, system_id, "structure.pdb")
    xtc_path = os.path.join(VIZ_DIR, system_id, "traj.xtc")
    
    u = mda.Universe(pdb_path, xtc_path)
    
    n_frames = len(u.trajectory)
    frame_indices = list(range(0, n_frames, max(1, n_frames // 5)))[:5]
    
    # Use spatial-gap heuristic for segment detection
    u.trajectory[0]
    ca_pos0 = []
    for res in u.residues:
        ca = res.atoms.select_atoms("name CA")
        if len(ca) == 1:
            ca_pos0.append(ca.positions[0])
    ca_pos0 = np.array(ca_pos0)
    
    breaks = [i for i in range(1, len(ca_pos0))
              if np.linalg.norm(ca_pos0[i] - ca_pos0[i-1]) > 10.0]
    bounds = []
    prev = 0
    for b in breaks:
        bounds.append((prev, b))
        prev = b
    bounds.append((prev, len(ca_pos0)))
    
    has_box = False
    split_frames = 0
    separation_frames = 0
    total_checked = 0
    
    for fi in frame_indices:
        u.trajectory[fi]
        ts = u.trajectory.ts
        
        if ts.dimensions is None or ts.dimensions[0] <= 0:
            continue
        
        has_box = True
        min_box = min(ts.dimensions[:3])
        total_checked += 1
        
        ca_pos = []
        for res in u.residues:
            ca = res.atoms.select_atoms("name CA")
            if len(ca) == 1:
                ca_pos.append(ca.positions[0])
        ca_pos = np.array(ca_pos)
        
        frame_split = False
        for si, (s, e) in enumerate(bounds):
            if e - s < 2:
                continue
            seg_pos = ca_pos[s:e]
            diffs = np.linalg.norm(np.diff(seg_pos, axis=0), axis=1)
            if np.any(diffs > 0.5 * min_box):
                frame_split = True
                break
        
        if frame_split:
            split_frames += 1
            continue
        
        coms = []
        for si, (s, e) in enumerate(bounds):
            if e - s < 2:
                continue
            seg_pos = ca_pos[s:e]
            coms.append(np.mean(seg_pos, axis=0))
        
        if len(coms) >= 2:
            coms = np.array(coms)
            for i in range(len(coms)):
                for j in range(i+1, len(coms)):
                    d = np.linalg.norm(coms[i] - coms[j])
                    if d > 0.7 * min_box:
                        separation_frames += 1
                        break
                else:
                    continue
                break
    
    if not has_box:
        return "NEEDS-SOURCE"
    elif split_frames > 0:
        return f"SPLIT ({split_frames}/{total_checked})"
    elif separation_frames > 0:
        return f"SEPARATED ({separation_frames}/{total_checked})"
    else:
        return "PBC-OK"


def main():
    t0 = time.time()
    print("=" * 70)
    print("PHASE C — PBC FIX (backbone + reassembly)")
    print("=" * 70)
    
    print(f"\nSystems to fix: {len(ALL_FIX)}")
    
    results = []
    for i, sid in enumerate(ALL_FIX):
        print(f"\n[{i+1}/{len(ALL_FIX)}] {sid}...")
        t1 = time.time()
        
        result, error = fix_pbc(sid)
        t2 = time.time()
        
        if error:
            print(f"  ERROR: {error}")
            results.append({"system_id": sid, "status": "ERROR", "error": error})
            continue
        
        # Validate
        print(f"  Validating...")
        validation = validate_pbc(sid)
        t3 = time.time()
        print(f"  Validation: {validation} (fix: {t2-t1:.1f}s, validate: {t3-t2:.1f}s)")
        
        results.append({
            "system_id": sid,
            "status": result["status"],
            "validation": validation,
        })
    
    # Summary
    print(f"\n=== PBC FIX SUMMARY ===")
    for r in results:
        print(f"  {r['system_id']}: {r['status']} → validation: {r.get('validation', 'N/A')}")
    
    elapsed = time.time() - t0
    print(f"\nElapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
