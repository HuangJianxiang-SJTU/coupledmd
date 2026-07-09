#!/usr/bin/env python3
"""
Phase A2 — PBC Audit for CoupledMD (v4 - correct)

Detection: check CA-CA distances WITHIN each chain segment only.
Inter-segment gaps are expected (different chains) and should not
trigger SPLIT detection.
"""
import os, csv, time, warnings
import numpy as np

warnings.filterwarnings("ignore")

VIZ_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/viz"
OUT_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output"
os.makedirs(OUT_DIR, exist_ok=True)

N_CHECK_FRAMES = 5


def audit_pbc(system_id):
    import MDAnalysis as mda
    
    pdb_path = os.path.join(VIZ_DIR, system_id, "structure.pdb")
    xtc_path = os.path.join(VIZ_DIR, system_id, "traj.xtc")
    
    if not os.path.exists(pdb_path) or not os.path.exists(xtc_path):
        return {"system_id": system_id, "status": "MISSING"}
    
    try:
        u = mda.Universe(pdb_path, xtc_path)
    except:
        return {"system_id": system_id, "status": "LOAD_ERROR"}
    
    n_frames = len(u.trajectory)
    if n_frames == 0:
        return {"system_id": system_id, "status": "NO_FRAMES"}
    
    ca_atoms = u.select_atoms("name CA")
    if len(ca_atoms) == 0:
        return {"system_id": system_id, "status": "NO_CA"}
    
    # Detect segments from first frame
    u.trajectory[0]
    ca_pos = ca_atoms.positions
    n_ca = len(ca_pos)
    
    breaks = []
    for i in range(1, n_ca):
        d = np.linalg.norm(ca_pos[i] - ca_pos[i-1])
        if d > 10.0:
            breaks.append(i)
    
    seg_ranges = []
    prev = 0
    for b in breaks:
        seg_ranges.append((prev, b))
        prev = b
    seg_ranges.append((prev, n_ca))
    
    # Frame indices
    frame_indices = list(range(0, n_frames, max(1, n_frames // N_CHECK_FRAMES)))
    frame_indices = frame_indices[:N_CHECK_FRAMES]
    
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
        
        ca_pos = ca_atoms.positions
        
        # Check WITHIN each segment for split molecules
        frame_split = False
        for start, end in seg_ranges:
            seg_ca = ca_pos[start:end]
            n_seg = len(seg_ca)
            for i in range(1, n_seg):
                d = np.linalg.norm(seg_ca[i] - seg_ca[i-1])
                if d > 0.5 * min_box:
                    frame_split = True
                    break
            if frame_split:
                break
        
        if frame_split:
            split_frames += 1
            continue
        
        # Check inter-segment COM distances
        coms = []
        for start, end in seg_ranges:
            if end > start:
                com = ca_pos[start:end].mean(axis=0)
                coms.append(com)
        
        if len(coms) >= 2:
            coms_arr = np.array(coms)
            frame_separated = False
            for i in range(len(coms_arr)):
                for j in range(i+1, len(coms_arr)):
                    d = np.linalg.norm(coms_arr[i] - coms_arr[j])
                    if d > 0.7 * min_box:
                        frame_separated = True
                        break
                if frame_separated:
                    break
            if frame_separated:
                separation_frames += 1
    
    if not has_box:
        status = "NEEDS-SOURCE"
    elif split_frames > 0:
        status = "SPLIT"
    elif separation_frames > 0:
        status = "SEPARATED"
    else:
        status = "PBC-OK"
    
    return {
        "system_id": system_id,
        "has_box": has_box,
        "n_frames": n_frames,
        "n_segments": len(seg_ranges),
        "split_frames": split_frames,
        "separation_frames": separation_frames,
        "frames_checked": total_checked,
        "status": status,
    }


def main():
    t0 = time.time()
    print("=" * 70)
    print("PHASE A2 — PBC AUDIT (v4)")
    print("=" * 70)
    
    systems = sorted([d for d in os.listdir(VIZ_DIR) 
                     if os.path.isdir(os.path.join(VIZ_DIR, d)) and d[0].isupper()])
    print(f"\nTotal systems: {len(systems)}")
    
    results = []
    for i, sid in enumerate(systems):
        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(systems)}...")
        try:
            result = audit_pbc(sid)
        except Exception as e:
            result = {"system_id": sid, "status": "ERROR"}
        results.append(result)
    
    out_path = os.path.join(OUT_DIR, "PBC_AUDIT.csv")
    fieldnames = ["system_id", "has_box", "n_frames", "n_segments",
                  "split_frames", "separation_frames", "frames_checked", "status"]
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    
    from collections import Counter
    status_counts = Counter(r["status"] for r in results)
    print(f"\n=== PBC AUDIT SUMMARY ===")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    for status in ["SPLIT", "SEPARATED", "NEEDS-SOURCE"]:
        problem = [r for r in results if r["status"] == status]
        if problem:
            print(f"\n  {status} systems ({len(problem)}):")
            for r in problem[:10]:
                print(f"    {r['system_id']}")
            if len(problem) > 10:
                print(f"    ... and {len(problem)-10} more")
    
    elapsed = time.time() - t0
    print(f"\nElapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
