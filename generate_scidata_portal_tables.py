#!/usr/bin/env python3
"""Generate portal/API tables and a supplemental access-workflow SVG."""

from __future__ import annotations

import csv
import html
import json
import urllib.request
from pathlib import Path


OPENAPI_URL = "https://www.coupledmd.cn/api/openapi.json"


def esc(value: object) -> str:
    return html.escape(str(value))


def svg_text(x, y, text, size=22, weight="400", fill="#1b1f2a", anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}">{esc(text)}</text>'
    )


def rect(x, y, w, h, fill="#fff", stroke="#ccd2da", rx=8):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    )


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_openapi() -> dict:
    with urllib.request.urlopen(OPENAPI_URL, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def endpoint_use(path: str) -> str:
    if path.endswith("/health"):
        return "resource status and system count"
    if "/systems" in path and "/viz/" not in path and all(x not in path for x in ["/pockets", "/gateways", "/gprotein", "/contacts", "/subunit-ranges"]):
        return "system browsing, filtering and metadata retrieval"
    if "/pockets" in path or "/pocketgrid" in path:
        return "pocket validation and derived-data reuse"
    if "/gateways" in path:
        return "derived gateway metrics; use descriptively in Paper 1"
    if "/gprotein" in path or "/coupling" in path or "/barcode" in path:
        return "G-protein annotation/feature layer; avoid mechanistic overclaiming"
    if "/viz/" in path:
        return "interactive visualization and reduced-trajectory access"
    if "/consensus/" in path:
        return "cross-system processed summaries"
    if "/citation" in path:
        return "citation and reuse metadata"
    if "/keys" in path or "/accounts" in path:
        return "optional account/API-key workflow; not required for open access"
    return "portal/API support"


def build_tables(base: Path) -> dict[str, object]:
    tabdir = base / "manuscript_figures" / "tables"
    tabdir.mkdir(exist_ok=True)
    openapi = load_openapi()
    endpoint_rows = []
    for path, ops in sorted(openapi.get("paths", {}).items()):
        for method, spec in sorted(ops.items()):
            if not isinstance(spec, dict):
                continue
            endpoint_rows.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "summary": spec.get("summary", ""),
                    "tags": "; ".join(spec.get("tags", [])),
                    "manuscript_use": endpoint_use(path),
                }
            )
    write_csv(
        tabdir / "scidata_S6_portal_api_endpoints.csv",
        endpoint_rows,
        ["method", "path", "summary", "tags", "manuscript_use"],
    )

    features = [
        ("Browse systems", "supported", "Systems route and /api/v1/systems endpoint", "Show in Fig. 2 or Supp Fig. S3"),
        ("Filter by G-protein family", "supported", "/api/v1/systems supports family; frontend Systems page", "Mention in Data Records/Usage Notes"),
        ("Filter by GPCR class", "supported in frontend/source metadata", "gpcr_class field present, but API docs should expose class filter explicitly if desired", "Consider adding explicit class filter docs before submission"),
        ("Search by receptor/UniProt/PDB/ligand/system ID", "supported", "README and Systems page describe free-text search", "Use in portal-access text"),
        ("Per-system metadata display", "supported", "/api/v1/systems/{system_id}", "Data Records"),
        ("Pocket and GPCRdb-mapped records", "supported", "/pockets and pocketgrid endpoints", "Technical Validation and reuse"),
        ("Gateway/G-protein feature records", "supported", "/gateways, /gprotein, /barcode endpoints", "Keep descriptive for Paper 1"),
        ("Reduced structure/trajectory visualization", "supported", "/viz/structure, /viz/trajectory, /viz/meta", "Portal access layer, not archive replacement"),
        ("API documentation", "supported", "/api/docs, /api/redoc, /api/openapi.json", "Archive OpenAPI JSON with dataset"),
        ("Citation metadata", "supported", "/api/v1/citation and /citation.cff", "Data/code availability"),
        ("Stable archival repository DOI", "missing", "not yet assigned in current manuscript package", "Required before submission or during review"),
        ("Reviewer-accessible private archive link", "missing", "not yet assigned", "Required for Scientific Data review"),
        ("Full archive manifest/checksums", "partial", "checksum checklist exists; final per-file manifest not generated", "Generate after final archive assembly"),
        ("Bulk full-trajectory download route", "missing/unclear", "portal exposes selected/reduced downloads; archival repository must provide full data", "Clarify in Data Records and repository deposit"),
        ("License and reuse terms", "supported in project files", "LICENSE, LICENSE-CODE, CITATION.cff present", "Verify final archive repeats license"),
    ]
    feature_rows = [
        {"feature": f, "status": s, "evidence": e, "submission_action": a}
        for f, s, e, a in features
    ]
    write_csv(
        tabdir / "scidata_S7_website_feature_checklist.csv",
        feature_rows,
        ["feature", "status", "evidence", "submission_action"],
    )
    return {"openapi": openapi, "endpoint_rows": endpoint_rows, "feature_rows": feature_rows}


def make_portal_figure(base: Path, data: dict[str, object]) -> None:
    outdir = base / "manuscript_figures" / "scidata_figures"
    outdir.mkdir(exist_ok=True)
    width, height = 1800, 1150
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#6b7280"/></marker></defs>',
        svg_text(70, 70, "Supplementary Figure S3 draft. Portal and API access workflow", 34, "700"),
        svg_text(70, 105, "Generated from the deployed OpenAPI schema and project documentation; replace or pair with real screenshots when available", 18, "400", "#5f6b7a"),
    ]

    parts.extend([svg_text(70, 165, "A", 28, "700"), svg_text(110, 165, "User-facing browsing workflow", 26, "700")])
    workflow = [
        ("Search/filter", "receptor, UniProt,\nPDB, ligand,\nfamily, class"),
        ("System page", "metadata,\nreplicas,\nanalysis availability"),
        ("Visualization", "NGL structure\nand reduced trajectory"),
        ("Download", "metadata, reduced\nfiles, processed records"),
    ]
    x = 100
    for idx, (title, body) in enumerate(workflow):
        parts.append(rect(x, 210, 260, 150, "#f4f7fb", "#b8c7d9", 10))
        parts.append(svg_text(x + 130, 252, title, 22, "700", "#1f2937", "middle"))
        for j, line in enumerate(body.split("\n")):
            parts.append(svg_text(x + 130, 290 + j * 24, line, 17, "400", "#374151", "middle"))
        if idx < len(workflow) - 1:
            parts.append(f'<line x1="{x+260}" y1="285" x2="{x+330}" y2="285" stroke="#6b7280" stroke-width="3" marker-end="url(#arrow)"/>')
        x += 330

    parts.extend([svg_text(70, 455, "B", 28, "700"), svg_text(110, 455, "Programmatic API layers", 26, "700")])
    api_groups = [
        ("Status/citation", "/health\n/citation\n/citation.cff", "#eef6ff"),
        ("Systems", "/systems\n/systems/{id}", "#f2fbf3"),
        ("Derived records", "/pockets\n/gateways\n/gprotein\n/contacts", "#fff7e8"),
        ("Visualization", "/viz/structure\n/viz/trajectory\n/viz/meta", "#f5f0ff"),
        ("Consensus", "/consensus/pockets\n/consensus/gateways\n/consensus/reorg", "#fff0f2"),
    ]
    x = 100
    for title, body, fill in api_groups:
        parts.append(rect(x, 505, 290, 160, fill, "#cfd7e3", 10))
        parts.append(svg_text(x + 145, 548, title, 21, "700", "#1f2937", "middle"))
        for j, line in enumerate(body.split("\n")):
            parts.append(svg_text(x + 145, 585 + j * 24, line, 16, "400", "#374151", "middle"))
        x += 320

    parts.extend([svg_text(70, 760, "C", 28, "700"), svg_text(110, 760, "Archive-first access model for Scientific Data", 26, "700")])
    boxes = [
        ("Archival repository", "DOI/accession\nfull trajectories\nmetadata + checksums", 120, "#e7f4ed"),
        ("Web portal", "browse/filter\nvisualize\nselected downloads", 650, "#eef6ff"),
        ("REST API", "metadata JSON\nprocessed records\nOpenAPI schema", 1180, "#fff7e8"),
    ]
    for title, body, x, fill in boxes:
        parts.append(rect(x, 820, 390, 170, fill, "#b8c7d9", 12))
        parts.append(svg_text(x + 195, 868, title, 24, "700", "#1f2937", "middle"))
        for j, line in enumerate(body.split("\n")):
            parts.append(svg_text(x + 195, 910 + j * 26, line, 18, "400", "#374151", "middle"))
    parts.append(f'<line x1="510" y1="905" x2="630" y2="905" stroke="#6b7280" stroke-width="3" marker-end="url(#arrow)"/>')
    parts.append(f'<line x1="1040" y1="905" x2="1160" y2="905" stroke="#6b7280" stroke-width="3" marker-end="url(#arrow)"/>')
    parts.append(svg_text(120, 1055, "Manuscript wording: archive = stable citable data record; portal/API = access and reuse layers.", 22, "700", "#374151"))
    parts.append(svg_text(120, 1090, f"Live OpenAPI paths detected: {len(data['endpoint_rows'])}", 18, "400", "#5f6b7a"))
    parts.append("</svg>")
    (outdir / "scidata_suppfigS3_portal_access_workflow_draft.svg").write_text("\n".join(parts))


def main() -> None:
    base = Path(".")
    data = build_tables(base)
    make_portal_figure(base, data)
    for path in [
        base / "manuscript_figures" / "tables" / "scidata_S6_portal_api_endpoints.csv",
        base / "manuscript_figures" / "tables" / "scidata_S7_website_feature_checklist.csv",
        base / "manuscript_figures" / "scidata_figures" / "scidata_suppfigS3_portal_access_workflow_draft.svg",
    ]:
        print(path)


if __name__ == "__main__":
    main()
