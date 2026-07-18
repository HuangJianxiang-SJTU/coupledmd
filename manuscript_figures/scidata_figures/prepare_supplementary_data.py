#!/usr/bin/env python3
"""Build and validate the CoupledMD Supplementary Data package.

The build is source-driven and staged.  It does not modify trajectories, API
records, systems_master.csv, or the authoritative release cohort.  With
``--replace``, the existing package and tarball are timestamped before the
validated staging directory is installed.

The generated S4, S7, S8, and S9 records describe current source/readiness/API
evidence.  They are not a frozen archive manifest, a DOI deposit, a checksum
manifest, or a self-contained file-level QC package.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import shutil
import sys
import tarfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SERVER = ROOT.parent.parent
DATA = SERVER / "data"
API_SYSTEMS = DATA / "api/v1/systems"
OUT = ROOT / "CoupledMD_Supplementary_Data"
STAGE = ROOT / ".CoupledMD_Supplementary_Data.build"
TARBALL = ROOT / "CoupledMD_Supplementary_Data.tar.gz"
AUDIT = ROOT / "CoupledMD_Supplementary_Data_audit.json"
INPUT = ROOT / "v9_figure_inputs"
COHORT = DATA / "release_cohort_v9_final207.csv"
MASTER = DATA / "systems_master.csv"
SCHEMA_VERSION = "1.0"

EXPECTED_UNRESOLVED = {
    "G12_8H8J", "Gi_7JVR", "Gi_7V68", "Gi_7VUG", "Gi_8J22", "Gi_8X16",
    "Gq_7F9Z", "Gq_7RYC", "Gq_7XJL", "Gq_8DPF", "Gs_7VUH", "Gs_8GY7", "Gs_8HNK",
}
EXCLUDED = {
    "Gq_7E9W": "non-GPCR duplicate/mislabel of Gq_8E9W",
    "Gq_7DWC": "duplicate source identity of Gq_8DWC (both MRGPRX1, Q96LB2)",
}
FAMILIES = {"Gi": 95, "Gs": 65, "Gq": 41, "G12-13": 6}
CLASSES = {"A": 181, "B": 26}
INTERFACES = ["TM1-TM2", "TM2-TM3", "TM3-TM4", "TM4-TM5", "TM5-TM6", "TM6-TM7", "TM7-TM1"]
METRICS = ["penetration", "penetration_p90", "open_fraction", "occupancy"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_record(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def public_zone(raw: str) -> str:
    return {
        "orthosteric": "orthosteric",
        "extracellular_vestibule": "extracellular vestibule",
        "coupling_interface": "intracellular/transducer interface",
        "intracellular_allosteric": "intracellular/transducer interface",
        "tm_core_allosteric": "membrane-facing",
        "other": "other",
    }.get(raw, "other")


def backup_existing() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = ROOT / "backups"
    backup.mkdir(exist_ok=True)
    if OUT.exists():
        target = backup / f"CoupledMD_Supplementary_Data_{stamp}"
        if target.exists():
            raise FileExistsError(target)
        shutil.copytree(OUT, target)
    if TARBALL.exists():
        shutil.copy2(TARBALL, backup / f"CoupledMD_Supplementary_Data_{stamp}.tar.gz")
    return stamp


def build_s1(cohort: list[dict[str, str]]) -> list[dict[str, Any]]:
    master = {row["system_id"]: row for row in read_csv(MASTER)}
    result = []
    for source in cohort:
        sid = source["system_id"]
        row = dict(source)
        index_path = API_SYSTEMS / sid / "index.json"
        index = json_record(index_path).get("metadata", {}) if index_path.exists() else {}
        for field in ("ligand_name", "ligand_chem_id", "ligand_class"):
            candidates = [
                str(row.get(field, "") or "").strip(),
                str(master.get(sid, {}).get(field, "") or "").strip(),
                str(index.get(field, "") or "").strip(),
            ]
            populated = {value for value in candidates if value}
            if len(populated) > 1:
                raise AssertionError(f"conflicting authoritative {field} values for {sid}: {sorted(populated)}")
            row[field] = next(iter(populated), "")
        result.append(row)
    return result


def build_s2(final_ids: set[str]) -> list[dict[str, Any]]:
    unresolved = [row for row in read_csv(INPUT / "scidata_S2_unresolved_systems_v9.csv") if row["system_id"] not in final_ids]
    assert {row["system_id"] for row in unresolved} == EXPECTED_UNRESOLVED
    rows = [{"release_status": "unresolved", **row} for row in unresolved]
    for sid, reason in EXCLUDED.items():
        rows.append({
            "release_status": "excluded", "system_id": sid, "pdb_id": sid.split("_", 1)[1],
            "hold_reason": reason,
            "evidence_source": "release decision 2026-07-14",
        })
    fields = ["release_status"] + list(unresolved[0])
    return [{field: row.get(field, "") for field in fields} for row in rows]


def build_s4(final_ids: set[str]) -> list[dict[str, Any]]:
    sources = [row for row in read_csv(INPUT / "scidata_S8_archive_source_inventory_v9.csv") if row["system_id"] in final_ids]
    rows = []
    for row in sources:
        locator = Path(row["source_path"])
        rows.append({
            "system_id": row["system_id"], "record_type": row["record_type"],
            "source_filename": locator.name, "source_parent": locator.parent.name,
            "source_exists_at_audit": row["exists"], "size_bytes_at_audit": row["size_bytes"],
            "release_replicas": row["release_replicas"], "replicas_n": row["replicas_n"],
            "length_per_replica_ns": row["length_per_replica_ns"],
            "total_sampling_ns": row["total_sampling_ns"],
            "record_scope": "source-inventory evidence; not a deposited file-level manifest",
        })
    return rows


def build_s5(s1_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for sid in sorted(s1_by_id):
        source = json_record(API_SYSTEMS / sid / "pockets_gpcrdb.json")
        assert source.get("system_id") == sid
        pockets = source.get("pockets")
        assert isinstance(pockets, list) and int(source.get("n_pockets")) == len(pockets)
        metadata = s1_by_id[sid]
        if not pockets:
            assert sid in {"Gi_7YK6", "Gi_8YIC"}
            rows.append({
                "system_id": sid, "receptor_name": metadata["receptor_name"],
                "g_protein_family": metadata["g_protein_family"], "pocket_id": "",
                "n_voxels": "", "mean_freq": "", "is_orthosteric": "", "location": "",
                "zone_public_label": "", "receptor_generic_numbers": "",
                "pocket_record_status": "available_zero_pockets",
                "pocket_record_reason": "valid API pocket record with n_pockets=0 and an empty pockets array",
                "schema_version": source.get("_schema_version", SCHEMA_VERSION),
            })
            continue
        for pocket in pockets:
            rows.append({
                "system_id": sid, "receptor_name": metadata["receptor_name"],
                "g_protein_family": metadata["g_protein_family"],
                "pocket_id": pocket.get("pocket_id", ""), "n_voxels": pocket.get("n_voxels", ""),
                "mean_freq": pocket.get("mean_freq", ""),
                "is_orthosteric": pocket.get("is_orthosteric", ""),
                "location": pocket.get("location", ""),
                "zone_public_label": public_zone(str(pocket.get("zone", "other"))),
                "receptor_generic_numbers": ";".join(pocket.get("receptor_generic_numbers") or []),
                "pocket_record_status": "available_detected_pocket", "pocket_record_reason": "",
                "schema_version": source.get("_schema_version", SCHEMA_VERSION),
            })
    return rows


def build_s6(s1_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    units = {
        "penetration": "angstrom", "penetration_p90": "angstrom",
        "open_fraction": "fraction", "occupancy": "lipid_heavy_atoms_per_frame",
    }
    rows = []
    for sid in sorted(s1_by_id):
        source = json_record(API_SYSTEMS / sid / "gateways.json")
        assert source.get("system_id") == sid
        records = source.get("records")
        assert isinstance(records, list) and len(records) == 28
        for record in records:
            values = record.get("replica_values")
            assert isinstance(values, list) and len(values) == 3
            rows.append({
                "system_id": sid, "g_protein_family": s1_by_id[sid]["g_protein_family"],
                "interface": record.get("pair"), "metric": record.get("metric"),
                "mean": record.get("mean"), "ci_lo": record.get("ci_lo"), "ci_hi": record.get("ci_hi"),
                "n_replicas": record.get("n_replicas"),
                "replica_1": values[0], "replica_2": values[1], "replica_3": values[2],
                "unit": units[record.get("metric")],
                "schema_version": source.get("_schema_version", SCHEMA_VERSION),
            })
    return rows


def build_s7(s1: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for system in s1:
        for replica in (1, 2, 3):
            rows.append({
                "system_id": system["system_id"], "replica_id": replica,
                "release_selection_status": "selected_validated", "duration_ns": 500,
                "system_total_sampling_ns": 1500,
                "qc_scope": "release-readiness selection; frozen per-file archival QC pending manifest freeze",
            })
    return rows


def build_s8(final_ids: set[str]) -> list[dict[str, Any]]:
    rows = []
    for source in read_csv(INPUT / "scidata_T8_readiness_qc_v9.csv"):
        if source["system_id"] not in final_ids:
            continue
        row = {key: value for key, value in source.items() if key not in {"included_in_209_paper_set", "cohort_status"}}
        row["included_in_release"] = "True"
        rows.append(row)
    return rows


def portal_specs() -> dict[str, Any]:
    return {
        "viz_structure": lambda sid: DATA / "viz" / sid / "structure.pdb",
        "viz_trajectory": lambda sid: DATA / "viz" / sid / "traj.xtc",
        "api_index": lambda sid: API_SYSTEMS / sid / "index.json",
        "api_pockets": lambda sid: API_SYSTEMS / sid / "pockets.json",
        "api_pockets_gpcrdb": lambda sid: API_SYSTEMS / sid / "pockets_gpcrdb.json",
        "api_gateways": lambda sid: API_SYSTEMS / sid / "gateways.json",
        "api_gprotein": lambda sid: API_SYSTEMS / sid / "gprotein_metrics.json",
        "api_pocketgrid": lambda sid: API_SYSTEMS / sid / "pocketgrid.npz",
        "chain_roles": lambda sid: DATA / "chain_roles" / f"{sid}_chain_roles.json",
        "contacts": lambda sid: DATA / "contacts" / f"{sid}_contacts.parquet",
    }


def content_available(record_type: str, sid: str, path: Path) -> tuple[bool, str]:
    if not path.is_file() or path.stat().st_size == 0:
        return False, "file missing or empty"
    if record_type in {"viz_structure", "viz_trajectory", "api_pocketgrid", "contacts"}:
        return True, "non-empty current server file present; this is not archive-deposition evidence"
    value = json_record(path)
    if record_type == "api_index":
        valid = value.get("system_id") == sid and isinstance(value.get("metadata"), dict)
    elif record_type in {"api_pockets", "api_pockets_gpcrdb"}:
        pockets = value.get("pockets")
        valid = value.get("system_id") == sid and isinstance(pockets, list) and int(value.get("n_pockets", -1)) == len(pockets)
    elif record_type == "api_gateways":
        records = value.get("records")
        keys = {(row.get("pair"), row.get("metric")) for row in records or []}
        valid = value.get("system_id") == sid and keys == {(i, m) for i in INTERFACES for m in METRICS}
    elif record_type == "api_gprotein":
        valid = value.get("system_id") == sid
    elif record_type == "chain_roles":
        valid = value.get("system_id", sid) == sid and isinstance(value.get("roles"), dict)
    else:
        valid = True
    return valid, "valid populated current server record" if valid else "present file failed content validation"


def build_s9(final_ids: set[str]) -> list[dict[str, Any]]:
    semantics = {
        "api_pockets": "Valid JSON requires matching system_id and n_pockets equal to array length; n_pockets=0 is available.",
        "api_pockets_gpcrdb": "Valid mapped-pocket JSON requires matching system_id and n_pockets equal to array length; zero pockets is available.",
        "api_gateways": "Available requires all seven interfaces and all four metrics in valid JSON.",
        "api_index": "Available requires valid JSON, matching system_id, and a metadata object.",
        "api_gprotein": "Available requires valid JSON with matching system_id.",
        "chain_roles": "Available requires valid JSON with a roles object.",
        "viz_structure": "Available means a non-empty current portal structure file is present.",
        "viz_trajectory": "Available means a non-empty current portal visualization trajectory is present.",
        "api_pocketgrid": "Available means a non-empty current API binary pocket-grid file is present.",
        "contacts": "Available means a non-empty current server contact-record file is present.",
    }
    rows = []
    for record_type, builder in portal_specs().items():
        states = []
        total_size = 0
        affected = []
        for sid in sorted(final_ids):
            path = builder(sid)
            present = path.is_file() and path.stat().st_size > 0
            total_size += path.stat().st_size if present else 0
            available, _ = content_available(record_type, sid, path)
            states.append((present, available))
            if not available:
                affected.append(sid)
        rows.append({
            "record_type": record_type, "expected_systems": 207,
            "files_present": sum(present for present, _ in states),
            "records_available": sum(available for _, available in states),
            "records_missing": sum(not present for present, _ in states),
            "records_unpopulated": sum(present and not available for present, available in states),
            "records_not_applicable": 0, "total_size_bytes": total_size,
            "affected_system_ids": ";".join(affected),
            "schema_location": "https://www.coupledmd.cn/api/openapi.json",
            "availability_semantics": semantics[record_type],
            "scope_note": "current included-cohort portal/API coverage; not deposited-archive or frozen-manifest coverage",
            "schema_version": SCHEMA_VERSION,
        })
    return rows


def build_s10() -> list[dict[str, Any]]:
    code = [
        (ROOT / "prepare_supplementary_data.py", "Supplementary Data package builder and validator"),
        (ROOT / "build_figure_inputs.py", "Figure-input builder"),
        (ROOT / "build_structural_selection_audit.py", "Structural-selection audit builder"),
        (ROOT / "build_core_interface_validation.py", "Replica-level technical-validation builder"),
        (ROOT / "build_replica_qc.py", "Replica readiness/QC ledger builder"),
        (ROOT / "plotting_scripts/main_figures.py", "Main Figure 1-6 plotting script"),
        (ROOT / "plotting_scripts/supplementary_s1_plot.py", "Supplementary Figure S1 plotting script"),
        (ROOT / "plotting_scripts/supplementary_s2_plot.py", "Supplementary Figure S2 plotting script"),
        (SERVER / "api/main.py", "Current REST API application and routes"),
        (SERVER / "api/accounts.py", "API account and authentication support"),
        (SERVER / "api/citation.py", "API citation record support"),
        (SERVER / "api/db.py", "API database support"),
        (SERVER / "api/rate_limit.py", "API rate-limiting support"),
        (SERVER / "scripts/p2_serialize.py", "Derived-record serialization utility"),
    ]
    environment_files = [
        (SERVER / "requirements.txt", "Python dependency specification"),
        (SERVER / "frontend/package.json", "Frontend package specification"),
        (SERVER / "frontend/package-lock.json", "Frontend dependency lock file"),
    ]
    rows = []
    python_version = platform.python_version()
    for number, (path, role) in enumerate(code, 1):
        exists = path.is_file()
        rows.append({
            "item_id": f"code_{number:02d}", "item_kind": "code_file",
            "repository_relative_path": str(path.relative_to(SERVER)), "role": role,
            "exists": exists, "size_bytes": path.stat().st_size if exists else "",
            "sha256": sha256(path) if exists else "", "language": "Python",
            "language_version": python_version,
            "software_version": "", "version_authority": "sys.version in the package-build environment",
            "schema_version": SCHEMA_VERSION,
        })
    for number, (path, role) in enumerate(environment_files, 1):
        exists = path.is_file()
        rows.append({
            "item_id": f"environment_file_{number:02d}", "item_kind": "environment_file",
            "repository_relative_path": str(path.relative_to(SERVER)), "role": role,
            "exists": exists, "size_bytes": path.stat().st_size if exists else "",
            "sha256": sha256(path) if exists else "",
            "language": "JSON" if path.suffix == ".json" else "pip requirements",
            "language_version": "", "software_version": "",
            "version_authority": "repository file content", "schema_version": SCHEMA_VERSION,
        })
    dependencies = ["Python", "numpy", "pandas", "scipy", "matplotlib", "MDAnalysis", "python-docx", "reportlab"]
    for number, name in enumerate(dependencies, 1):
        if name == "Python":
            version = python_version
        else:
            try:
                version = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                # Do not list a dependency/version that is unavailable in the
                # active package-build environment.
                continue
        rows.append({
            "item_id": f"build_dependency_{number:02d}", "item_kind": "build_dependency",
            "repository_relative_path": "", "role": "Current package-build environment dependency",
            "exists": True, "size_bytes": "", "sha256": "", "language": name,
            "language_version": version if name == "Python" else "",
            "software_version": "" if name == "Python" else version,
            "version_authority": "runtime/importlib.metadata in the package-build environment; not simulation provenance",
            "schema_version": SCHEMA_VERSION,
        })
    return rows


DEFINITIONS = {
    "system_id": "Release system identifier combining G-protein-family prefix and source-structure identifier.",
    "pdb_id": "Source-structure identifier recorded for the release system.",
    "receptor_name": "Curated receptor name retained independently of accession mapping.",
    "receptor_uniprot": "Mapped receptor UniProt accession; empty when no canonical mapping is available.",
    "receptor_gene": "Mapped receptor gene symbol; nullable with the receptor accession.",
    "gpcr_class": "Release GPCR class.", "g_protein_family": "Release G-protein family.",
    "g_alpha_subtype": "Source metadata label for the G-alpha subtype or construct.",
    "ligand_name": "Ligand name present in systems_master or the per-system API index; empty when unavailable.",
    "ligand_chem_id": "Ligand chemical-component identifier from authoritative system metadata; empty when unavailable.",
    "ligand_class": "Ligand-class annotation; currently empty because no authoritative source value is available.",
    "n_replicas": "Number of selected production replicas represented by the record.",
    "length_per_replica_ns": "Selected production duration per replica.",
    "total_sampling_ns": "Total selected production sampling represented by the system or source record.",
    "force_field": "Force-field/protocol label recorded in included-system metadata; not an exact engine-version claim.",
    "lipid_composition": "Membrane lipid-composition label in included-system metadata.",
    "structural_provenance": "Release label describing experimental or engineered structural provenance.",
    "trajectory_type": "Trajectory content/type label in included-system metadata.",
    "has_bilayer": "Whether the source system metadata records a membrane bilayer.",
    "traj_exists": "Whether a trajectory source was present at the metadata audit.",
    "topo_exists": "Whether a topology source was present at the metadata audit.",
    "traj_sha256": "Trajectory SHA-256; intentionally empty until archive manifest freeze.",
    "topo_sha256": "Topology SHA-256; intentionally empty until archive manifest freeze.",
    "notes": "Curated release or source-metadata note.",
    "release_status": "Release-boundary status for an unresolved or excluded record.",
    "hold_reason": "Recorded reason the system is unresolved or excluded.",
    "rerun_status": "Recorded rerun/recovery status for a release-boundary exception.",
    "readiness_action": "Action recorded by the readiness evidence overlay.",
    "evidence_group": "Readiness-evidence grouping used to support the record.",
    "evidence_source": "Repository-relative pointer to the supporting readiness evidence.",
    "baseline_replica_statuses": "Concatenated human-readable baseline status summary for the three replicas.",
    "field": "Exact serialized CSV field name described by this dictionary row.",
    "entity_level": "Entity or record level at which the field is interpreted.",
    "type": "Serialized logical data type.", "unit": "Measurement unit, or unitless/NA where applicable.",
    "requiredness": "Whether every record requires a value or the field is conditional.",
    "nullable": "Whether an empty CSV value is permitted.",
    "allowed_vocabulary": "Pipe-delimited controlled values when a closed vocabulary applies.",
    "definition": "Reader-facing semantic definition of the serialized field.",
    "example": "Example non-null serialized value from the generated package.",
    "provenance_authority": "Source or computation authoritative for the field.",
    "schema_version": "Schema identifier for the serialized record.",
    "record_type": "Record category; its vocabulary is defined by the containing Supplementary Data table.",
    "source_filename": "Basename of the audited source file; no absolute path is published.",
    "source_parent": "Immediate source-directory name retained as a limited evidence locator.",
    "source_exists_at_audit": "Whether the source file existed and was non-empty at the source audit.",
    "size_bytes_at_audit": "Source-file size observed during the audit.",
    "release_replicas": "Selected replica identifiers represented by the aggregate source evidence row.",
    "replicas_n": "Number of selected replicas represented by the source evidence row.",
    "record_scope": "Explicit interpretation limit for the source-inventory row.",
    "pocket_id": "Pocket identifier within a system; empty only for an explicit zero-pocket system row.",
    "n_voxels": "Number of grid voxels in the detected pocket cluster.",
    "mean_freq": "Mean occupied-frame fraction across voxels in the pocket cluster.",
    "is_orthosteric": "Whether the pocket cluster was annotated as orthosteric by the deposited computational workflow.",
    "location": "Component/location label stored in the pocket API record.",
    "zone_public_label": "Reader-facing anatomical-zone label derived from the stored pocket zone.",
    "receptor_generic_numbers": "Semicolon-delimited GPCRdb generic positions mapped to the pocket.",
    "pocket_record_status": "Distinguishes a detected-pocket row from a valid zero-pocket system record.",
    "pocket_record_reason": "Explanation for the pocket-record status when needed.",
    "interface": "Adjacent TM-helix pair defining a gateway.",
    "metric": "Gateway metric represented by the row.",
    "mean": "Mean of the three replica-level gateway summaries.",
    "ci_lo": "Lower bound of the stored gateway interval.", "ci_hi": "Upper bound of the stored gateway interval.",
    "replica_1": "Gateway summary for selected replica 1.", "replica_2": "Gateway summary for selected replica 2.",
    "replica_3": "Gateway summary for selected replica 3.",
    "replica_id": "Selected production-replica identifier within a system.",
    "release_selection_status": "Release-selection status of the replica.",
    "duration_ns": "Selected production duration represented by the replica row.",
    "system_total_sampling_ns": "Total selected sampling for the replica's system.",
    "qc_scope": "Interpretation limit of the selected-replica ledger.",
    "baseline_n_ready": "Number of replicas classified READY in baseline evidence.",
    "baseline_n_hold": "Number of replicas classified HOLD in baseline evidence.",
    "baseline_n_review": "Number of replicas classified REVIEW in baseline evidence.",
    "baseline_status": "System-level baseline readiness status.",
    "baseline_notes": "Note attached to baseline readiness evidence.",
    "readiness_status": "Current readiness status after evidence overlay.",
    "three_good_ready": "Whether readiness evidence supports three selected good replicas.",
    "evidence_note": "Additional note attached to the selected evidence source.",
    "qc_category": "Reader-facing readiness/QC category.",
    "timestamp_reset_interpretation": "States that timestamp resets are diagnostic rather than automatic failures.",
    "included_in_release": "Whether the row belongs to the authoritative included cohort.",
    "expected_systems": "Number of included systems to which the portal/API record type applies.",
    "files_present": "Number of non-empty current server files present for the record type.",
    "records_available": "Number of records satisfying the stated current-content availability semantics.",
    "records_missing": "Number of expected current server files missing or empty.",
    "records_unpopulated": "Number of present current server files failing content-population validation.",
    "records_not_applicable": "Number of systems for which the record type is explicitly not applicable.",
    "total_size_bytes": "Aggregate byte size of present current server files for the record type.",
    "affected_system_ids": "Semicolon-delimited systems not counted as available.",
    "schema_location": "Location of the current API schema; not a DOI archive locator.",
    "availability_semantics": "Explicit rule used to count a current server record as available.",
    "scope_note": "Interpretation limit separating current server coverage from archive deposition.",
    "item_id": "Stable row identifier within the code/build-environment inventory.",
    "item_kind": "Distinguishes code files, environment files and current build dependencies.",
    "repository_relative_path": "Path relative to the CoupledMD server repository; nullable for runtime dependency rows.",
    "role": "Role of the code or environment item in the current build/server.",
    "exists": "Whether the file exists or the current build dependency is importable.",
    "size_bytes": "Current byte size for a repository file; not applicable to runtime dependency rows.",
    "sha256": "SHA-256 of a repository file; not applicable to runtime dependency rows.",
    "language": "Implementation language, file format or dependency name.",
    "language_version": "Available language/runtime version for the current build environment.",
    "software_version": "Available package version in the current build environment.",
    "version_authority": "How the reported current build version was obtained; never used as simulation-engine provenance.",
}


UNITS = {
    "length_per_replica_ns": "ns", "total_sampling_ns": "ns", "duration_ns": "ns",
    "system_total_sampling_ns": "ns", "size_bytes_at_audit": "byte", "size_bytes": "byte",
    "total_size_bytes": "byte", "mean_freq": "fraction", "ci_lo": "metric-dependent",
    "ci_hi": "metric-dependent", "mean": "metric-dependent", "replica_1": "metric-dependent",
    "replica_2": "metric-dependent", "replica_3": "metric-dependent",
}

VOCABULARIES = {
    "gpcr_class": "A|B", "g_protein_family": "Gi|Gs|Gq|G12-13",
    "release_status": "unresolved|excluded", "pocket_record_status": "available_detected_pocket|available_zero_pockets",
    "interface": "|".join(INTERFACES), "metric": "|".join(METRICS),
    "release_selection_status": "selected_validated", "included_in_release": "True",
    "timestamp_reset_interpretation": "diagnostic_only_not_failure",
    "item_kind": "code_file|environment_file|build_dependency",
}


def infer_type(values: list[str], field: str) -> str:
    if field in {"traj_sha256", "topo_sha256", "sha256"}:
        return "sha256_hex_string"
    nonempty = [str(value).strip() for value in values if str(value).strip()]
    lowered = {value.lower() for value in nonempty}
    if nonempty and lowered <= {"true", "false"}:
        return "boolean"
    try:
        if nonempty and all(float(value).is_integer() for value in nonempty):
            return "integer"
        if nonempty:
            [float(value) for value in nonempty]
            return "number"
    except ValueError:
        pass
    if field in {"receptor_generic_numbers", "affected_system_ids"}:
        return "semicolon_delimited_string"
    return "string"


def build_s3(directory: Path) -> list[dict[str, Any]]:
    values: dict[str, list[str]] = {}
    field_files: dict[str, set[str]] = {}
    for path in sorted(directory.glob("Supplementary_Data_S*.csv")):
        if "_S3_" in path.name:
            continue
        for row in read_csv(path):
            for field, value in row.items():
                values.setdefault(field, []).append(value)
                field_files.setdefault(field, set()).add(path.name.split("_")[2])
    s3_fields = [
        "field", "entity_level", "type", "unit", "requiredness", "nullable",
        "allowed_vocabulary", "definition", "example", "provenance_authority", "schema_version",
    ]
    for field in s3_fields:
        values.setdefault(field, [field if field == "field" else "dictionary metadata"])
        field_files.setdefault(field, set()).add("S3")
    missing_definitions = set(values) - set(DEFINITIONS)
    assert not missing_definitions, f"dictionary definitions missing: {sorted(missing_definitions)}"
    rows = []
    source_groups = {
        "S1": "included cohort, systems_master.csv and per-system index.json",
        "S2": "readiness overlay and release decision",
        "S3": "generated package schema audit",
        "S4": "systems_master.csv paths and source filesystem audit",
        "S5": "per-system pockets_gpcrdb.json",
        "S6": "per-system gateways.json",
        "S7": "included-cohort replica-selection rule",
        "S8": "readiness/QC evidence overlay",
        "S9": "current server filesystem and JSON-content audit",
        "S10": "repository files and current package-build runtime",
    }
    entity_levels = {
        "S1": "system",
        "S2": "release-boundary system",
        "S3": "dictionary field",
        "S4": "system source-inventory record",
        "S5": "pocket or explicit zero-pocket system record",
        "S6": "system/interface/metric gateway record",
        "S7": "system/replica selection record",
        "S8": "system readiness/QC summary",
        "S9": "record-type coverage summary",
        "S10": "code or build-environment inventory item",
    }
    for field in sorted(values):
        field_values = values[field]
        nonempty = [str(value).strip() for value in field_values if str(value).strip()]
        files = sorted(field_files[field])
        rows.append({
            "field": field,
            "entity_level": " / ".join(entity_levels[file] for file in files),
            "type": infer_type(field_values, field), "unit": UNITS.get(field, "unitless_or_not_applicable"),
            "requiredness": "required" if len(nonempty) == len(field_values) else "conditional",
            "nullable": "False" if len(nonempty) == len(field_values) else "True",
            "allowed_vocabulary": VOCABULARIES.get(field, ""), "definition": DEFINITIONS[field],
            "example": nonempty[0] if nonempty else "", "provenance_authority": "; ".join(source_groups[file] for file in files),
            "schema_version": SCHEMA_VERSION,
        })
    assert {row["field"] for row in rows} == set(values)
    return rows


PRIMARY_KEYS = {
    "S1": ["system_id"], "S2": ["system_id"], "S3": ["field"],
    "S4": ["system_id", "record_type"], "S5": ["system_id", "pocket_id"],
    "S6": ["system_id", "interface", "metric"], "S7": ["system_id", "replica_id"],
    "S8": ["system_id"], "S9": ["record_type"], "S10": ["item_id"],
}


def table_path(directory: Path, number: int) -> Path:
    matches = list(directory.glob(f"Supplementary_Data_S{number}_*.csv"))
    assert len(matches) == 1, (number, matches)
    return matches[0]


def validate_package(directory: Path) -> dict[str, Any]:
    tables = {f"S{i}": read_csv(table_path(directory, i)) for i in range(1, 11)}
    for name, rows in tables.items():
        assert rows, f"{name} is empty"
        complete = [tuple(row.items()) for row in rows]
        assert len(complete) == len(set(complete)), f"duplicate complete rows in {name}"
        keys = [tuple(row[field] for field in PRIMARY_KEYS[name]) for row in rows]
        assert len(keys) == len(set(keys)), f"duplicate primary keys in {name}"

    ids = {row["system_id"] for row in tables["S1"]}
    assert len(tables["S1"]) == len(ids) == 207
    assert Counter(row["g_protein_family"] for row in tables["S1"]) == Counter(FAMILIES)
    assert Counter(row["gpcr_class"] for row in tables["S1"]) == Counter(CLASSES)
    assert len({row["receptor_name"] for row in tables["S1"]}) == 174
    assert len({row["receptor_uniprot"] for row in tables["S1"] if row["receptor_uniprot"]}) == 173
    assert sum(float(row["total_sampling_ns"]) for row in tables["S1"]) == 310_500
    assert "Gq_7E9W" not in ids

    s2_ids = {row["system_id"] for row in tables["S2"]}
    assert len(tables["S2"]) == 15 and {row["system_id"] for row in tables["S2"] if row["release_status"] == "unresolved"} == EXPECTED_UNRESOLVED
    assert {row["system_id"] for row in tables["S2"] if row["release_status"] == "excluded"} == set(EXCLUDED)
    assert not ids & s2_ids

    assert len(tables["S4"]) == 414
    assert Counter(row["system_id"] for row in tables["S4"]) == Counter({sid: 2 for sid in ids})
    assert {row["record_type"] for row in tables["S4"]} == {"production_trajectory", "topology"}

    detected = [row for row in tables["S5"] if row["pocket_record_status"] == "available_detected_pocket"]
    zero = [row for row in tables["S5"] if row["pocket_record_status"] == "available_zero_pockets"]
    assert len(detected) == 2149 and len(zero) == 2 and {row["system_id"] for row in zero} == {"Gi_7YK6", "Gi_8YIC"}
    assert {row["system_id"] for row in tables["S5"]} == ids

    assert len(tables["S6"]) == 5796
    assert {row["system_id"] for row in tables["S6"]} == ids
    assert {row["interface"] for row in tables["S6"]} == set(INTERFACES)
    assert {row["metric"] for row in tables["S6"]} == set(METRICS)
    assert Counter(row["system_id"] for row in tables["S6"]) == Counter({sid: 28 for sid in ids})

    assert len(tables["S7"]) == 621 and {row["system_id"] for row in tables["S7"]} == ids
    assert Counter(row["system_id"] for row in tables["S7"]) == Counter({sid: 3 for sid in ids})
    assert sum(float(row["duration_ns"]) for row in tables["S7"]) == 310_500
    assert len(tables["S8"]) == 207 and {row["system_id"] for row in tables["S8"]} == ids
    assert len(tables["S9"]) == 10 and all(row["availability_semantics"] for row in tables["S9"])
    assert all(row["records_available"] == "207" for row in tables["S9"])
    assert all(row["records_missing"] == "0" and row["records_unpopulated"] == "0" for row in tables["S9"])
    assert all("not deposited-archive" in row["scope_note"] for row in tables["S9"])
    assert all(row["item_kind"] in {"code_file", "environment_file", "build_dependency"} for row in tables["S10"])
    assert not any("amber" in row["item_id"].lower() or "gromacs" in row["item_id"].lower() for row in tables["S10"])
    assert all(row["version_authority"] for row in tables["S10"])
    assert all(row["exists"] == "True" for row in tables["S10"])

    final_derived_ids = set()
    for name in ("S4", "S5", "S6", "S7", "S8"):
        current = {row["system_id"] for row in tables[name]}
        assert current == ids, f"{name} cohort mismatch"
        final_derived_ids |= current
    assert not final_derived_ids & (EXPECTED_UNRESOLVED | set(EXCLUDED))

    actual_fields = set()
    for rows in tables.values():
        actual_fields.update(rows[0])
    assert {row["field"] for row in tables["S3"]} == actual_fields

    return {
        "status": "passed", "schema_version": SCHEMA_VERSION,
        "row_counts": {name: len(rows) for name, rows in tables.items()},
        "cohort": {"systems": 207, "families": FAMILIES, "classes": CLASSES,
                   "receptor_names": 174, "mapped_uniprot": 173, "sampling_ns": 310500},
        "s5": {"detected_pocket_rows": 2149, "explicit_zero_pocket_rows": 2,
               "zero_pocket_systems": ["Gi_7YK6", "Gi_8YIC"]},
        "s6": {"rows": 5796, "interfaces": INTERFACES, "metrics": METRICS},
        "pending": [
            "frozen archive manifest", "DOI-linked deposition", "archive file checksums",
            "self-contained per-file QC package", "complete 621-file trajectory manifest freeze",
            "authoritative exact simulation-engine versions",
        ],
    }


def build(directory: Path) -> None:
    cohort = read_csv(COHORT)
    assert len(cohort) == 207 and len({row["system_id"] for row in cohort}) == 207
    final_ids = {row["system_id"] for row in cohort}
    assert not final_ids & (EXPECTED_UNRESOLVED | set(EXCLUDED))

    s1 = build_s1(cohort)
    s1_by_id = {row["system_id"]: row for row in s1}
    outputs = {
        "Supplementary_Data_S1_included_system_inventory.csv": s1,
        "Supplementary_Data_S2_release_boundary_exceptions.csv": build_s2(final_ids),
        "Supplementary_Data_S4_source_inventory.csv": build_s4(final_ids),
        "Supplementary_Data_S5_pocket_summaries_gpcrdb.csv": build_s5(s1_by_id),
        "Supplementary_Data_S6_gateway_per_system.csv": build_s6(s1_by_id),
        "Supplementary_Data_S7_selected_replica_ledger.csv": build_s7(s1),
        "Supplementary_Data_S8_readiness_qc.csv": build_s8(final_ids),
        "Supplementary_Data_S9_api_access_coverage.csv": build_s9(final_ids),
        "Supplementary_Data_S10_code_environment_inventory.csv": build_s10(),
    }
    for filename, rows in outputs.items():
        write_csv(directory / filename, rows)
    s3 = build_s3(directory)
    write_csv(directory / "Supplementary_Data_S3_metadata_dictionary.csv", s3)
    (directory / "README.txt").write_text(
        "CoupledMD Supplementary Data\n\n"
        "S1 is the included-system inventory; S2 combines 13 unresolved and two excluded records.\n"
        "S3 describes every field actually serialized in S1-S10. S4 is source-inventory evidence,\n"
        "S5 contains detected pockets plus two explicit valid zero-pocket records, and S6 contains\n"
        "tidy system/interface/metric gateway summaries. S7 is a selected-replica ledger, S8 is a\n"
        "readiness/QC summary with evidence pointers, and S9 measures current portal/API coverage.\n"
        "This package does not claim a frozen archive, DOI, archive checksum manifest, complete\n"
        "621-file trajectory manifest, or self-contained per-file QC deposit.\n",
        encoding="utf-8",
    )


def write_tarball_and_audit(report: dict[str, Any], backup_stamp: str | None) -> None:
    with tarfile.open(TARBALL, "w:gz") as archive:
        archive.add(OUT, arcname=OUT.name)
    with tarfile.open(TARBALL, "r:gz") as archive:
        members = archive.getmembers()
        file_members = sorted(member.name for member in members if member.isfile())
        expected = sorted(f"{OUT.name}/{path.name}" for path in OUT.iterdir() if path.is_file())
        assert file_members == expected
        for member in members:
            if member.isfile():
                handle = archive.extractfile(member)
                assert handle is not None
                while handle.read(1024 * 1024):
                    pass
    report.update({
        "generated_at": datetime.now().astimezone().isoformat(),
        "package_path": str(OUT), "tarball_path": str(TARBALL),
        "tarball_sha256": sha256(TARBALL), "tarball_size_bytes": TARBALL.stat().st_size,
        "tar_file_members": file_members, "gzip_integrity": "passed",
        "backup_stamp": backup_stamp,
    })
    AUDIT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true", help="Back up and replace the current package/tarball")
    args = parser.parse_args()
    if (OUT.exists() or TARBALL.exists()) and not args.replace:
        raise SystemExit("Current output exists; rerun with --replace to create timestamped backups and rebuild")
    backup_stamp = backup_existing() if args.replace else None
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir()
    try:
        build(STAGE)
        report = validate_package(STAGE)
        if OUT.exists():
            shutil.rmtree(OUT)
        STAGE.rename(OUT)
        write_tarball_and_audit(report, backup_stamp)
    except Exception:
        if STAGE.exists():
            shutil.rmtree(STAGE)
        raise
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Wrote {OUT}")
    print(f"Wrote {TARBALL} sha256={sha256(TARBALL)}")
    print(f"Wrote {AUDIT}")


if __name__ == "__main__":
    main()
