#!/usr/bin/env python3
"""Generate Supplementary Figure S3 — portal and API access (SVG).

Panels A and B use frozen real portal and API screenshots. Panel C retains the
archive-first access model. Self-contained: no network fetch.
"""

from __future__ import annotations

import base64
import csv
import html
from pathlib import Path

import cairosvg

HERE = Path(__file__).resolve().parent
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1800, 1150
PORTAL_SCREENSHOT_DIR = OUT / "portal_screenshots"
API_SCREENSHOT_DIR = OUT / "api_snapshot"
MANIFEST_SUMMARY = OUT / "v9_figure_inputs" / "scidata_T6_manifest_summary_v9.csv"


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


def arrow(x0, y0, x1, y1):
    return (
        f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" '
        f'stroke="#6b7280" stroke-width="3" marker-end="url(#arrow)"/>'
    )


def find_snapshot(directory: Path) -> Path:
    """Return the single PNG snapshot in *directory*."""
    snapshots = sorted(directory.glob("*.png"))
    if not snapshots:
        raise FileNotFoundError(f"No PNG snapshot found in {directory}")
    if len(snapshots) > 1:
        raise RuntimeError(
            f"Expected one PNG snapshot in {directory}, found {len(snapshots)}"
        )
    return snapshots[0]


def png_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def snapshot_panel(x, y, w, h, path: Path) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
        f'fill="#ffffff" stroke="#ccd2da" stroke-width="2"/>'
        f'<image x="{x + 2}" y="{y + 2}" width="{w - 4}" height="{h - 4}" '
        f'href="{png_data_uri(path)}" preserveAspectRatio="xMidYMid meet"/>'
    )


def build_svg() -> str:
    with MANIFEST_SUMMARY.open(newline="") as handle:
        manifests = {row["manifest"]: row for row in csv.DictReader(handle)}
    assert manifests["release_cohort_v9_final208"]["systems"] == "208"
    assert manifests["release_cohort_v9_final208"]["records"] == "624"
    assert manifests["archive_source_inventory_v9"]["status"] == "audited"
    assert manifests["portal_api_file_manifest_v9"]["status"] == "audited"
    portal_snapshot = find_snapshot(PORTAL_SCREENSHOT_DIR)
    api_snapshot = find_snapshot(API_SCREENSHOT_DIR)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" '
        'orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#6b7280"/></marker></defs>',
    ]

    # Panels A/B — frozen real browser captures.
    parts.append(svg_text(70, 80, "A", 28, "700"))
    parts.append(svg_text(110, 80, "Web portal: system browsing and filters", 26, "700"))
    parts.append(snapshot_panel(100, 105, 760, 475, portal_snapshot))
    parts.append(svg_text(480, 608, "Legacy 222-system interface snapshot; v9 files audited separately",
                          18, "700", "#c0741a", "middle"))

    parts.append(svg_text(930, 80, "B", 28, "700"))
    parts.append(svg_text(970, 80, "REST API: interactive OpenAPI documentation", 26, "700"))
    parts.append(snapshot_panel(960, 105, 760, 475, api_snapshot))
    parts.append(svg_text(1340, 608, "OpenAPI schema snapshot; current v9 records audited separately",
                          18, "700", "#c0741a", "middle"))

    # Panel C — archive-first access model
    parts.append(svg_text(70, 690, "C", 28, "700"))
    parts.append(svg_text(110, 690, "Archive-first access model for Scientific Data", 26, "700"))
    boxes = [
        ("Archival repository", "DOI/accession\nfull trajectories\nmetadata + checksums", 120, "#e7f4ed"),
        ("Web portal", "browse/filter\nvisualize\nselected downloads", 650, "#eef6ff"),
        ("REST API", "metadata JSON\nprocessed records\nOpenAPI schema", 1180, "#fff7e8"),
    ]
    for title, body, bx, fill in boxes:
        parts.append(rect(bx, 750, 390, 170, fill, "#b8c7d9", 12))
        parts.append(svg_text(bx + 195, 798, title, 24, "700", "#1f2937", "middle"))
        for j, line in enumerate(body.split("\n")):
            parts.append(svg_text(bx + 195, 840 + j * 26, line, 18, "400", "#374151", "middle"))
    parts.append(arrow(510, 835, 630, 835))
    parts.append(arrow(1040, 835, 1160, 835))
    parts.append(svg_text(900, 995, "Validated release scope: 208 systems · 624 trajectories · 312.0 µs",
                          22, "700", "#155e63", "middle"))
    parts.append(svg_text(900, 1035, "Archive source inventory and portal/API file manifest: audited",
                          20, "700", "#155e63", "middle"))

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    svg = build_svg()
    svg_path = OUT / "v9_figureS3_portal_access.svg"
    svg_path.write_text(svg)
    png_path = OUT / "v9_figureS3_portal_access.png"
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path),
                     output_width=WIDTH * 2, output_height=HEIGHT * 2)
    pdf_path = OUT / "v9_figureS3_portal_access.pdf"
    cairosvg.svg2pdf(bytestring=svg.encode("utf-8"), write_to=str(pdf_path))
    print(svg_path)
    print(png_path)
    print(pdf_path)


if __name__ == "__main__":
    main()
