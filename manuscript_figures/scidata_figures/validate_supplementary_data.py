#!/usr/bin/env python3
"""Independent source and integrity audit for CoupledMD Supplementary Data."""
from __future__ import annotations

import hashlib
import json
import re
import tarfile
from pathlib import Path

import prepare_supplementary_data as build


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "CoupledMD_Supplementary_Data"
TARBALL = ROOT / "CoupledMD_Supplementary_Data.tar.gz"
AUDIT = ROOT / "CoupledMD_Supplementary_Data_audit.json"


def rows(number: int) -> list[dict[str, str]]:
    return build.read_csv(build.table_path(PACKAGE, number))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def audit_sources() -> dict[str, object]:
    s1, s5, s6, s10 = rows(1), rows(5), rows(6), rows(10)
    ids = {row["system_id"] for row in s1}
    cohort_ids = {row["system_id"] for row in build.read_csv(build.COHORT)}
    assert ids == cohort_ids and len(ids) == 207

    pocket_count = 0
    zero_ids: set[str] = set()
    gateway_source: dict[tuple[str, str, str], dict[str, object]] = {}
    for sid in sorted(ids):
        pocket = build.json_record(build.API_SYSTEMS / sid / "pockets_gpcrdb.json")
        assert int(pocket["n_pockets"]) == len(pocket["pockets"])
        pocket_count += len(pocket["pockets"])
        if not pocket["pockets"]:
            zero_ids.add(sid)
        gateway = build.json_record(build.API_SYSTEMS / sid / "gateways.json")
        assert len(gateway["records"]) == 28
        for record in gateway["records"]:
            key = (sid, record["pair"], record["metric"])
            assert key not in gateway_source
            gateway_source[key] = record
    assert pocket_count == 2149
    assert zero_ids == {"Gi_7YK6", "Gi_8YIC"}
    assert len(gateway_source) == 5796

    csv_gateway = {(r["system_id"], r["interface"], r["metric"]): r for r in s6}
    assert set(csv_gateway) == set(gateway_source)
    maximum_delta = 0.0
    for key, source in gateway_source.items():
        target = csv_gateway[key]
        for field in ("mean", "ci_lo", "ci_hi"):
            maximum_delta = max(maximum_delta, abs(float(target[field]) - float(source[field])))
        assert int(target["n_replicas"]) == int(source["n_replicas"]) == 3
        for index, value in enumerate(source["replica_values"], 1):
            maximum_delta = max(maximum_delta, abs(float(target[f"replica_{index}"]) - float(value)))
    assert maximum_delta == 0.0

    detected = [r for r in s5 if r["pocket_record_status"] == "available_detected_pocket"]
    zero = [r for r in s5 if r["pocket_record_status"] == "available_zero_pockets"]
    assert len(detected) == pocket_count and {r["system_id"] for r in zero} == zero_ids
    inventoried_files = 0
    for record in s10:
        relative = record["repository_relative_path"]
        if not relative:
            continue
        path = build.SERVER / relative
        assert path.is_file() and int(record["size_bytes"]) == path.stat().st_size
        assert record["sha256"] == digest(path)
        inventoried_files += 1
    return {
        "authoritative_cohort_ids_match": True,
        "source_pocket_rows": pocket_count,
        "source_zero_pocket_systems": sorted(zero_ids),
        "source_gateway_rows": len(gateway_source),
        "source_to_s6_max_abs_delta": maximum_delta,
        "s10_repository_files_hash_verified": inventoried_files,
    }


def audit_reader_labels() -> dict[str, object]:
    forbidden = re.compile(r"(?:\bv9\b|v9[_-]|[_-]v9|v9_final|final208|\bfinal\b)", re.I)
    checked = []
    for path in sorted(PACKAGE.iterdir()):
        if not path.is_file():
            continue
        checked.append(path.name)
        assert not forbidden.search(path.name), path.name
        if path.suffix.lower() in {".csv", ".txt"}:
            match = forbidden.search(path.read_text(encoding="utf-8"))
            assert match is None, (path.name, match.group(0))
    assert build.SCHEMA_VERSION == "1.0"
    assert "included_in_release" in rows(8)[0] and "included_in_final208_release" not in rows(8)[0]
    return {"status": "passed", "files_checked": checked, "schema_version": "1.0"}


def audit_tar() -> dict[str, object]:
    with tarfile.open(TARBALL, "r:gz") as archive:
        members = sorted(m.name for m in archive.getmembers() if m.isfile())
        expected = sorted(f"{PACKAGE.name}/{p.name}" for p in PACKAGE.iterdir() if p.is_file())
        assert members == expected
        for member in members:
            stream = archive.extractfile(member)
            assert stream is not None
            while stream.read(1024 * 1024):
                pass
    return {
        "gzip_and_tar_read_integrity": "passed",
        "tar_file_member_count": len(members),
        "tar_file_members": members,
        "tarball_size_bytes": TARBALL.stat().st_size,
        "tarball_sha256": digest(TARBALL),
    }


def main() -> None:
    report = build.validate_package(PACKAGE)
    report["independent_source_audit"] = audit_sources()
    report["reader_facing_label_audit"] = audit_reader_labels()
    report["archive_integrity_audit"] = audit_tar()
    report["supplementary_data_status"] = "passed"
    AUDIT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Updated {AUDIT}")


if __name__ == "__main__":
    main()
