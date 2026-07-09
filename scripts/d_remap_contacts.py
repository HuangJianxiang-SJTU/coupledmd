#!/usr/bin/env python3
"""
Phase D — Remap contact subunit labels using corrected chain_roles.json.

For mislabeled-only systems (no PBC issues):
  - Remap subunit1/subunit2 labels in contacts parquet
  - Backup original parquet
  - Write corrected parquet

For PBC-fixed systems:
  - Recompute contacts from corrected trajectory (separate script)
"""
import os, sys, json, time, warnings, shutil
from collections import defaultdict
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

CONTACTS_DIR = "/MDdata/data02/jxhuang/gpcr_g/a/flareplots/cache"
CHAIN_ROLES_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output/chain_roles"
BACKUP_DIR = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/scripts/audit_output/contacts_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

# Systems with PBC issues (need full recompute, not just remap)
PBC_SYSTEMS = {
    "G12_7SF8", "G12_8H8J", "Gi_6PT0", "Gi_7JVR", "Gi_7V68",
    "Gi_7VUG", "Gi_7YK6", "Gi_8J22", "Gi_8X16", "Gi_8YIC",
    "Gq_8Y53", "Gs_7FIG", "Gs_7T9N", "Gs_7TMW", "Gs_7VUH", "Gs_8I2G",
    "Gq_8DPF"
}


CANONICAL_ROLES = {"G_alpha", "Receptor", "G_beta", "G_gamma"}

def build_rid2role(system_id):
    """Build a mapping from residue ID to corrected role.

    Receptor_frag* roles are collapsed to 'Receptor' so the circo plot
    can display them in the correct sector.
    """
    cr_path = os.path.join(CHAIN_ROLES_DIR, f"{system_id}_chain_roles.json")
    if not os.path.exists(cr_path):
        return None

    with open(cr_path) as f:
        data = json.load(f)

    roles = data.get("roles", {})
    rid2role = {}
    for role, info in roles.items():
        rng = info.get("resid_range", "")
        if "-" in rng:
            parts = rng.split("-")
            rmin, rmax = int(parts[0]), int(parts[1])
            # Collapse Receptor_frag* → Receptor so the circo plot works
            canonical = "Receptor" if role.startswith("Receptor") else role
            for r in range(rmin, rmax + 1):
                rid2role[r] = canonical

    return rid2role


def remap_contacts(system_id):
    """Remap subunit labels in contacts parquet using corrected chain_roles."""
    parquet_path = os.path.join(CONTACTS_DIR, f"{system_id}_contacts.parquet")
    if not os.path.exists(parquet_path):
        return None, "No contacts parquet"
    
    # Build residue-to-role mapping
    rid2role = build_rid2role(system_id)
    if rid2role is None:
        return None, "No chain_roles.json"
    
    # Load contacts
    df = pd.read_parquet(parquet_path)
    n_rows = len(df)
    
    # Check if remapping is needed
    # Compare current subunit labels with corrected ones
    old_sub1 = df["subunit1"].values.copy()
    old_sub2 = df["subunit2"].values.copy()
    
    # Remap subunit1 based on res1
    new_sub1 = [rid2role.get(r, "Unknown") for r in df["res1"].values]
    new_sub2 = [rid2role.get(r, "Unknown") for r in df["res2"].values]
    
    # Count changes
    n_changed1 = np.sum(old_sub1 != new_sub1)
    n_changed2 = np.sum(old_sub2 != new_sub2)
    n_changed = n_changed1 + n_changed2
    
    if n_changed == 0:
        return {"system_id": system_id, "n_rows": n_rows, "n_changed": 0, "status": "UNCHANGED"}, None
    
    # Back up original
    backup_path = os.path.join(BACKUP_DIR, f"{system_id}_contacts.parquet.bak")
    if not os.path.exists(backup_path):
        shutil.copy2(parquet_path, backup_path)
    
    # Apply remapping
    df["subunit1"] = new_sub1
    df["subunit2"] = new_sub2
    
    # Write corrected parquet
    df.to_parquet(parquet_path, index=False)
    
    return {
        "system_id": system_id,
        "n_rows": n_rows,
        "n_changed": int(n_changed),
        "n_changed_sub1": int(n_changed1),
        "n_changed_sub2": int(n_changed2),
        "status": "REMAPED",
    }, None


def main():
    t0 = time.time()
    print("=" * 70)
    print("PHASE D — CONTACT LABEL REMAPPING")
    print("=" * 70)
    
    # Get all systems with contacts parquet
    all_systems = []
    for f in sorted(os.listdir(CONTACTS_DIR)):
        if f.endswith("_contacts.parquet"):
            sid = f.replace("_contacts.parquet", "")
            all_systems.append(sid)
    
    print(f"\nTotal systems with contacts: {len(all_systems)}")
    # PBC systems are now included — their contacts have been recomputed with
    # correct sim_resids but may still carry old subunit labels.
    remap_systems = all_systems
    print(f"Systems to remap: {len(remap_systems)}")
    
    results = []
    n_changed_total = 0
    n_unchanged = 0
    
    for i, sid in enumerate(remap_systems):
        result, error = remap_contacts(sid)
        
        if error:
            results.append({"system_id": sid, "status": "ERROR", "error": error})
            continue
        
        if result["n_changed"] == 0:
            n_unchanged += 1
        else:
            n_changed_total += 1
            print(f"  {sid}: {result['n_changed']} labels changed ({result['n_changed_sub1']} sub1, {result['n_changed_sub2']} sub2)")
        
        results.append(result)
    
    # Summary
    print(f"\n=== REMAP SUMMARY ===")
    print(f"  Total processed: {len(remap_systems)}")
    print(f"  Labels changed: {n_changed_total}")
    print(f"  Unchanged: {n_unchanged}")
    print(f"  Errors: {sum(1 for r in results if r.get('status') == 'ERROR')}")
    
    elapsed = time.time() - t0
    print(f"\nElapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
