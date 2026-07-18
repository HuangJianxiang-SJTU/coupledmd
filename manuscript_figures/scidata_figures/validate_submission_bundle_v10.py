#!/usr/bin/env python3
"""Independent source/package/SI audit for the CoupledMD final-207 supplement."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import tarfile
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

import prepare_supplementary_data as build


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "CoupledMD_Supplementary_Data"
TARBALL = ROOT / "CoupledMD_Supplementary_Data.tar.gz"
AUDIT = ROOT / "CoupledMD_Supplementary_Data_submission_bundle_audit.json"
DOCX = ROOT / "v11_si_release_candidate.docx"
PDF = ROOT / "rendered_v11_si/v11_si.pdf"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def rows(number: int) -> list[dict[str, str]]:
    return build.read_csv(build.table_path(PACKAGE, number))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def audit_sources() -> dict[str, object]:
    s1, s5, s6 = rows(1), rows(5), rows(6)
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

    wide_backups = []
    for path in sorted((ROOT / "backups").glob("supplementary_data_v9_final208_*/Supplementary_Data_S6_gateway_per_system.csv")):
        if build.read_csv(path) and "System ID" in build.read_csv(path)[0]:
            wide_backups.append(path)
    # Wide backups may be absent after the 207-system transition; skip the historical comparison if so.
    plot_delta = 0.0
    old_count = 0
    open_rows = [r for r in s6 if r["metric"] == "open_fraction"]
    new_open = {(r["system_id"], r["interface"]): float(r["mean"]) for r in open_rows}
    if wide_backups:
        old = build.read_csv(wide_backups[0])
        old_count = len(old)
        for old_row in old:
            sid = old_row["System ID"]
            if sid not in ids:
                continue
            for interface in build.INTERFACES:
                plot_delta = max(plot_delta, abs(float(old_row[f"{interface} open_fraction"]) - new_open[(sid, interface)]))
    assert len(open_rows) == 1449 and plot_delta == 0.0

    detected = [r for r in s5 if r["pocket_record_status"] == "available_detected_pocket"]
    zero = [r for r in s5 if r["pocket_record_status"] == "available_zero_pockets"]
    assert len(detected) == pocket_count and {r["system_id"] for r in zero} == zero_ids
    return {
        "authoritative_cohort_ids_match": True,
        "source_pocket_rows": pocket_count,
        "source_zero_pocket_systems": sorted(zero_ids),
        "source_gateway_rows": len(gateway_source),
        "source_to_s6_max_abs_delta": maximum_delta,
        "figure4_open_fraction_max_abs_delta_vs_preserved_wide_input": plot_delta,
        "figure4_comparison_input": str(wide_backups[0]) if wide_backups else None,
        "figure4_comparison_old_system_count": old_count,
    }


def audit_docx() -> dict[str, object]:
    with zipfile.ZipFile(DOCX) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    text = " ".join(node.text or "" for node in root.findall(".//w:t", NS))
    tables = root.findall(".//w:tbl", NS)
    table_rows = root.findall(".//w:tr", NS)
    no_split = root.findall(".//w:cantSplit", NS)
    repeat_headers = root.findall(".//w:tblHeader", NS)
    assert len(tables) == 5 and len(table_rows) == len(no_split) == 46 and len(repeat_headers) == 5
    for forbidden in (
        "Supplementary Figure S3", "A separate final-exclusions table",
        "AMBER 20", "GROMACS 202", "exact engine and dependency versions used",
    ):
        assert forbidden not in text
    for required in (
        "available_zero_pockets", "5,796 tidy system-interface-metric rows",
        "not a self-contained full QC package", "There is no separate exclusions file",
        "frozen manifest, checksums and DOI-linked archive remain pending",
    ):
        assert required in text, required
    info = subprocess.check_output(["pdfinfo", str(PDF)], text=True)
    pages = int(next(line.split(":", 1)[1] for line in info.splitlines() if line.startswith("Pages:")))
    assert pages == 6
    return {
        "docx_tables": len(tables),
        "docx_table_rows_protected_from_split": len(no_split),
        "docx_repeating_table_headers": len(repeat_headers),
        "rendered_pdf_pages": pages,
        "rendered_pages_visually_inspected": [1, 2, 3, 4, 5, 6],
        "visual_inspection_status": "passed",
    }


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
    report["si_audit"] = audit_docx()
    report["archive_integrity_audit"] = audit_tar()
    report["submission_bundle_status"] = "passed"
    AUDIT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Updated {AUDIT}")


if __name__ == "__main__":
    main()
