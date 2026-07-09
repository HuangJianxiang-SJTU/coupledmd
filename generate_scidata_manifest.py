#!/usr/bin/env python3
"""Generate clean-v1 manifests from current metadata and local portal files."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import urllib.request
from pathlib import Path


HOLD = {
    "G12_8H8J",
    "Gi_7E32",
    "Gi_7JVR",
    "Gi_7VUG",
    "Gi_7YK6",
    "Gi_8HK2",
    "Gi_8X16",
    "Gi_8YIC",
    "Gq_7RAN",
    "Gq_7RYC",
    "Gq_7XXH",
    "Gq_8DPF",
    "Gq_8J9N",
    "Gs_7VUH",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def should_checksum_now(path: Path) -> bool:
    """Keep this manifest pass fast; final archive checksums are a separate step."""
    if not path.exists():
        return False
    if path.suffix.lower() not in {".json", ".csv", ".cff", ".md", ".txt"}:
        return False
    return path.stat().st_size <= 5 * 1024 * 1024


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def make_manifests(base: Path) -> None:
    tabdir = base / "manuscript_figures" / "tables"
    tabdir.mkdir(exist_ok=True)
    rows = list(csv.DictReader(open(base / "data" / "systems_master.csv", newline="", errors="ignore")))
    clean = [r for r in rows if r["system_id"] not in HOLD]

    archive_rows = []
    for r in clean:
        for record_type, path_field, exists_field, size_field, sha_field in [
            ("production_trajectory", "trajectory_path", "traj_exists", "traj_size_bytes", "traj_sha256"),
            ("topology", "topology_path", "topo_exists", "topo_size_bytes", "topo_sha256"),
            ("protein_only_trajectory", "protein_only_trajectory_path", "traj_exists", "", ""),
            ("full_system_trajectory", "full_system_trajectory_path", "", "", ""),
        ]:
            source_path = r.get(path_field, "")
            if not source_path:
                continue
            archive_rows.append(
                {
                    "system_id": r["system_id"],
                    "record_type": record_type,
                    "source_path": source_path,
                    "exists_flag": r.get(exists_field, "") if exists_field else "not_checked_in_metadata",
                    "size_bytes": r.get(size_field, "") if size_field else "",
                    "sha256": r.get(sha_field, "") if sha_field else "",
                    "checksum_status": "present" if (sha_field and r.get(sha_field)) else "pending_final_archive_checksum",
                    "archive_status": "pending_repository_deposit",
                }
            )
    write_csv(
        tabdir / "scidata_S8_archive_manifest_clean_v1_from_metadata.csv",
        archive_rows,
        ["system_id", "record_type", "source_path", "exists_flag", "size_bytes", "sha256", "checksum_status", "archive_status"],
    )

    portal_rows = []
    for r in clean:
        sid = r["system_id"]
        candidate_files = [
            ("viz_structure", base / "data" / "viz" / sid / "structure.pdb"),
            ("viz_trajectory", base / "data" / "viz" / sid / "traj.xtc"),
            ("api_index", base / "data" / "api" / "v1" / "systems" / sid / "index.json"),
            ("api_pockets", base / "data" / "api" / "v1" / "systems" / sid / "pockets.json"),
            ("api_pockets_gpcrdb", base / "data" / "api" / "v1" / "systems" / sid / "pockets_gpcrdb.json"),
            ("api_gateways", base / "data" / "api" / "v1" / "systems" / sid / "gateways.json"),
            ("api_gprotein", base / "data" / "api" / "v1" / "systems" / sid / "gprotein_metrics.json"),
            ("api_pocketgrid", base / "data" / "api" / "v1" / "systems" / sid / "pocketgrid.npz"),
            ("chain_roles", base / "data" / "chain_roles" / f"{sid}_chain_roles.json"),
            ("contacts", base / "data" / "contacts" / f"{sid}_contacts.parquet"),
        ]
        for record_type, path in candidate_files:
            exists = path.exists()
            compute_now = should_checksum_now(path)
            portal_rows.append(
                {
                    "system_id": sid,
                    "record_type": record_type,
                    "relative_path": str(path.relative_to(base)),
                    "exists": "yes" if exists else "no",
                    "size_bytes": path.stat().st_size if exists else "",
                    "sha256": sha256_file(path) if compute_now else "",
                    "checksum_status": "computed" if compute_now else ("pending_binary_or_large_file" if exists else "missing"),
                }
            )
    write_csv(
        tabdir / "scidata_S9_portal_file_manifest_clean_v1.csv",
        portal_rows,
        ["system_id", "record_type", "relative_path", "exists", "size_bytes", "sha256", "checksum_status"],
    )

    openapi_dir = base / "manuscript_figures" / "scidata_figures" / "api_snapshot"
    openapi_dir.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen("https://www.coupledmd.cn/api/openapi.json", timeout=20) as response:
        openapi = json.loads(response.read().decode("utf-8"))
    openapi_path = openapi_dir / "coupledmd_openapi_2026-07-07.json"
    openapi_path.write_text(json.dumps(openapi, indent=2, sort_keys=True))

    summary_rows = [
        {
            "manifest": "archive_manifest_clean_v1_from_metadata",
            "records": len(archive_rows),
            "systems": len(clean),
            "checksums_present": sum(1 for row in archive_rows if row["checksum_status"] == "present"),
            "checksums_pending": sum(1 for row in archive_rows if row["checksum_status"] != "present"),
            "notes": "Production archive paths/sizes from systems_master; final repository checksums still pending.",
        },
        {
            "manifest": "portal_file_manifest_clean_v1",
            "records": len(portal_rows),
            "systems": len(clean),
            "checksums_present": sum(1 for row in portal_rows if row["checksum_status"] == "computed"),
            "checksums_pending": sum(1 for row in portal_rows if row["checksum_status"] != "computed"),
            "notes": "Portal/API/reduced files under current server tree; binary or large files marked pending_binary_or_large_file.",
        },
        {
            "manifest": "openapi_snapshot",
            "records": len(openapi.get("paths", {})),
            "systems": "",
            "checksums_present": 1,
            "checksums_pending": 0,
            "notes": str(openapi_path.relative_to(base)),
        },
    ]
    write_csv(
        tabdir / "scidata_T6_manifest_summary.csv",
        summary_rows,
        ["manifest", "records", "systems", "checksums_present", "checksums_pending", "notes"],
    )

    availability_rows = []
    for record_type in sorted({row["record_type"] for row in portal_rows}):
        subset = [row for row in portal_rows if row["record_type"] == record_type]
        availability_rows.append(
            {
                "record_type": record_type,
                "expected_systems": len(clean),
                "present": sum(1 for row in subset if row["exists"] == "yes"),
                "missing": sum(1 for row in subset if row["exists"] != "yes"),
                "checksums_computed": sum(1 for row in subset if row["checksum_status"] == "computed"),
                "checksums_pending": sum(1 for row in subset if row["checksum_status"] != "computed"),
            }
        )
    write_csv(
        tabdir / "scidata_T7_portal_file_availability_summary.csv",
        availability_rows,
        ["record_type", "expected_systems", "present", "missing", "checksums_computed", "checksums_pending"],
    )

    print(tabdir / "scidata_S8_archive_manifest_clean_v1_from_metadata.csv")
    print(tabdir / "scidata_S9_portal_file_manifest_clean_v1.csv")
    print(tabdir / "scidata_T6_manifest_summary.csv")
    print(tabdir / "scidata_T7_portal_file_availability_summary.csv")
    print(openapi_path)


if __name__ == "__main__":
    make_manifests(Path("."))
