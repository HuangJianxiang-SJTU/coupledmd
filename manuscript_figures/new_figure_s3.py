#!/usr/bin/env python3
"""Generate Supplementary Figure S3 — portal and API access workflow (SVG).

Reuses the layout of the original portal-access SVG (panels A/B/C) with the
header subtitle and footer caption removed. Self-contained: no network fetch.
"""

from __future__ import annotations

import html
from pathlib import Path

import cairosvg

HERE = Path(__file__).resolve().parent
OUT = HERE / "scidata_figures"
OUT.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1800, 1150


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


def build_svg() -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" '
        'orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#6b7280"/></marker></defs>',
    ]

    # Panel A — user-facing browsing workflow
    parts.append(svg_text(70, 165, "A", 28, "700"))
    parts.append(svg_text(110, 165, "User-facing browsing workflow", 26, "700"))
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
            parts.append(arrow(x + 260, 285, x + 330, 285))
        x += 330

    # Panel B — programmatic API layers
    parts.append(svg_text(70, 455, "B", 28, "700"))
    parts.append(svg_text(110, 455, "Programmatic API layers", 26, "700"))
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

    # Panel C — archive-first access model
    parts.append(svg_text(70, 760, "C", 28, "700"))
    parts.append(svg_text(110, 760, "Archive-first access model for Scientific Data", 26, "700"))
    boxes = [
        ("Archival repository", "DOI/accession\nfull trajectories\nmetadata + checksums", 120, "#e7f4ed"),
        ("Web portal", "browse/filter\nvisualize\nselected downloads", 650, "#eef6ff"),
        ("REST API", "metadata JSON\nprocessed records\nOpenAPI schema", 1180, "#fff7e8"),
    ]
    for title, body, bx, fill in boxes:
        parts.append(rect(bx, 820, 390, 170, fill, "#b8c7d9", 12))
        parts.append(svg_text(bx + 195, 868, title, 24, "700", "#1f2937", "middle"))
        for j, line in enumerate(body.split("\n")):
            parts.append(svg_text(bx + 195, 910 + j * 26, line, 18, "400", "#374151", "middle"))
    parts.append(arrow(510, 905, 630, 905))
    parts.append(arrow(1040, 905, 1160, 905))

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    svg = build_svg()
    svg_path = OUT / "new_figureS3_portal_access.svg"
    svg_path.write_text(svg)
    png_path = OUT / "new_figureS3_portal_access.png"
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path),
                     output_width=WIDTH * 2, output_height=HEIGHT * 2)
    print(svg_path)
    print(png_path)


if __name__ == "__main__":
    main()
