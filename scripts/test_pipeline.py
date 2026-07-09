#!/usr/bin/env python3
"""Pipeline integration test — verifies P0→P2 output consistency.

Run: python3 scripts/test_pipeline.py
Exit code: 0 if all pass, 1 if any fail.
"""

import csv
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = PROJECT_ROOT / "db" / "coupledmd.sqlite"
CSV_PATH = DATA_DIR / "systems_master.csv"
API_V1 = DATA_DIR / "api" / "v1"
VIZ_DIR = DATA_DIR / "viz"

passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name}  — {detail}")
        failed += 1


def main():
    print("CoupledMD pipeline integration test\n")

    # 1. systems_master.csv
    print("[1] systems_master.csv")
    if CSV_PATH.exists():
        with open(CSV_PATH) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        check("CSV exists and has rows", len(rows) > 0)
        check("CSV has 222 rows", len(rows) == 222, f"got {len(rows)}")
        expected_cols = {"system_id", "pdb_id", "receptor_uniprot", "receptor_gene", "g_protein_family"}
        csv_cols = set(rows[0].keys())
        check("CSV has expected columns", expected_cols.issubset(csv_cols),
              f"missing: {expected_cols - csv_cols}")
        csv_ids = {r["system_id"] for r in rows}
    else:
        check("CSV exists", False, f"not found at {CSV_PATH}")
        csv_ids = set()

    # 2. SQLite database
    print("\n[2] SQLite database")
    if DB_PATH.exists():
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()

        cur.execute("SELECT count(*) FROM systems")
        n_systems = cur.fetchone()[0]
        check("systems table has 222 rows", n_systems == 222, f"got {n_systems}")

        cur.execute("SELECT count(*) FROM system_pocket_files")
        n_pocket = cur.fetchone()[0]
        check("system_pocket_files has ~610 rows", 500 <= n_pocket <= 700, f"got {n_pocket}")

        cur.execute("SELECT count(*) FROM system_gateway_files")
        n_gw = cur.fetchone()[0]
        check("system_gateway_files has ~202 rows", 150 <= n_gw <= 250, f"got {n_gw}")

        cur.execute("SELECT system_id FROM systems")
        db_ids = {r[0] for r in cur.fetchall()}

        if csv_ids:
            check("CSV and DB system_ids match", csv_ids == db_ids,
                  f"CSV-only: {csv_ids - db_ids}, DB-only: {db_ids - csv_ids}")

        con.close()
    else:
        check("DB exists", False, f"not found at {DB_PATH}")
        db_ids = set()

    # 3. API index.json
    print("\n[3] API index.json")
    index_path = API_V1 / "index.json"
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
        check("index.json has n_systems == 222", index.get("n_systems") == 222,
              f"got {index.get('n_systems')}")
    else:
        check("index.json exists", False, f"not found at {index_path}")

    # 4. Per-system index.json
    print("\n[4] Per-system index.json files")
    systems_dir = API_V1 / "systems"
    if systems_dir.exists():
        system_dirs = [d for d in systems_dir.iterdir() if d.is_dir()]
        check("222 system directories exist", len(system_dirs) == 222, f"got {len(system_dirs)}")

        missing = []
        for sid in sorted(db_ids or csv_ids):
            idx = systems_dir / sid / "index.json"
            if not idx.exists():
                missing.append(sid)
        check("Every system_id has index.json", len(missing) == 0,
              f"missing: {missing[:5]}{'...' if len(missing) > 5 else ''}")
    else:
        check("systems directory exists", False, f"not found at {systems_dir}")

    # 5. Reorg atlas
    print("\n[5] Consensus reorg atlas")
    reorg_path = API_V1 / "consensus" / "reorg_atlas.json"
    if reorg_path.exists():
        with open(reorg_path) as f:
            reorg = json.load(f)
        comparisons = reorg.get("comparisons", [])
        check("reorg has comparisons", len(comparisons) > 0)
        null_sids = [c for c in comparisons if not c.get("sid_A") or not c.get("sid_B")]
        check("All comparisons have sid_A and sid_B", len(null_sids) == 0,
              f"{len(null_sids)} comparisons with null sid_A or sid_B")
    else:
        check("reorg_atlas.json exists", False, f"not found at {reorg_path}")

    # 6. Viz tier consistency
    print("\n[6] Viz tier consistency")
    if DB_PATH.exists() and VIZ_DIR.exists():
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT DISTINCT system_id FROM system_viz_files")
        db_viz_sids = {r[0] for r in cur.fetchall()}
        con.close()

        viz_sids = {d.name for d in VIZ_DIR.iterdir() if d.is_dir()}
        check("Viz directories exist", len(viz_sids) > 0)
        check("DB viz entries exist", len(db_viz_sids) > 0)

        viz_only = viz_sids - db_viz_sids
        db_only = db_viz_sids - viz_sids
        check("Viz dirs and DB rows consistent", len(viz_only) == 0 and len(db_only) == 0,
              f"viz-only: {viz_only}, db-only: {db_only}")
    else:
        check("Viz tier check", False, "DB or viz directory missing")

    # Summary
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        print("STATUS: FAIL")
        sys.exit(1)
    else:
        print("STATUS: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
