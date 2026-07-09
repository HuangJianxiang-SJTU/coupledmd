#!/usr/bin/env python3
"""
Pre-fetch all RCSB entity data for 222 systems.
Caches under a/cache/<sid>/rcsb_<pdbid>_entity<n>.json
Run this ONCE before the main audit.
"""
import os, sys, json, csv, time, http.client, ssl

MASTER_CSV = "/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/data/systems_master.csv"
CACHE_BASE = "/MDdata/data02/jxhuang/gpcr_g/a/cache"

_ssl_ctx = ssl._create_unverified_context()

def rcsb_fetch(path, retries=3, delay=2):
    for attempt in range(retries):
        try:
            conn = http.client.HTTPSConnection("data.rcsb.org", 443, timeout=20,
                                               context=_ssl_ctx)
            conn.request("GET", path, headers={"User-Agent": "CoupledMD-Audit/1.0"})
            resp = conn.getresponse()
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                conn.close()
                return data
            elif resp.status == 404:
                conn.close()
                return None
            else:
                conn.close()
                if attempt < retries - 1:
                    time.sleep(delay)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                raise
    return None


def main():
    with open(MASTER_CSV) as f:
        rows = list(csv.DictReader(f))

    print(f"Total systems: {len(rows)}")

    fetched = 0
    cached = 0
    errors = []

    for i, r in enumerate(rows):
        sid = r['system_id']
        pdb_id = r['pdb_id']
        cache_dir = os.path.join(CACHE_BASE, sid)
        os.makedirs(cache_dir, exist_ok=True)

        # Check if already cached
        existing = [f for f in os.listdir(cache_dir) if f.startswith(f"rcsb_{pdb_id}_entity")]
        if existing:
            cached += 1
            continue

        # Fetch entry to get entity list
        entry = rcsb_fetch(f"/rest/v1/core/entry/{pdb_id}")
        if entry is None:
            errors.append((sid, f"No entry for {pdb_id}"))
            continue

        poly_ids = entry.get("rcsb_entry_container_identifiers", {}).get(
            "polymer_entity_ids", [])

        for eid in poly_ids:
            cache_path = os.path.join(cache_dir, f"rcsb_{pdb_id}_entity{eid}.json")
            if os.path.exists(cache_path):
                continue
            data = rcsb_fetch(f"/rest/v1/core/polymer_entity/{pdb_id}/{eid}")
            if data is None:
                errors.append((sid, f"No entity {eid} for {pdb_id}"))
                continue
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            time.sleep(0.3)

        fetched += 1
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{len(rows)} (fetched={fetched}, cached={cached})")

    print(f"\nDone! Fetched: {fetched}, Already cached: {cached}, Errors: {len(errors)}")
    if errors:
        for sid, err in errors[:20]:
            print(f"  {sid}: {err}")


if __name__ == "__main__":
    main()
