#!/usr/bin/env python3
"""Generate draft Scientific Data SVG figures without third-party dependencies."""

from __future__ import annotations

import collections
import csv
import html
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

COLORS = {
    "Gi": "#4C93D9",
    "Gs": "#E8A73A",
    "Gq": "#D95C5C",
    "G12-13": "#8D58B4",
    "A": "#4C93D9",
    "B": "#49A87F",
    "experimental": "#4C93D9",
    "engineered_uncertain": "#A8B0BA",
}


def num(value: str | None) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def svg_text(
    x: float,
    y: float,
    text: str,
    size: int = 24,
    weight: str = "400",
    fill: str = "#1b1f2a",
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}">{html.escape(str(text))}</text>'
    )


def rect(
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str = "#fff",
    stroke: str = "#ccd2da",
    rx: int = 10,
) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    )


def panel_label(x: float, y: float, label: str) -> str:
    return svg_text(x, y, label, 28, "700", "#111827")


def barh(x: float, y: float, w: float, h: float, label: str, n: int, total: int, color: str) -> str:
    bw = w * n / max(total, 1)
    return "".join(
        [
            rect(x, y, w, h, "#eef1f5", "none", 4),
            rect(x, y, bw, h, color, "none", 4),
            svg_text(x + 8, y + h / 2 + 7, f"{label}  {n}", 18, "700", "#111827"),
        ]
    )


def load_systems() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    with open("data/systems_master.csv", newline="", errors="ignore") as handle:
        rows = list(csv.DictReader(handle))
    clean = [row for row in rows if row["system_id"] not in HOLD]
    held = [row for row in rows if row["system_id"] in HOLD]
    return clean, held


def make_figure1(outdir: Path) -> None:
    clean, held = load_systems()
    family = collections.Counter(row["g_protein_family"] for row in clean)
    gpcr_class = collections.Counter(row.get("gpcr_class", "") or "unannotated" for row in clean)
    provenance = collections.Counter(row.get("structural_provenance", "") or "unannotated" for row in clean)

    hold_cat = collections.Counter()
    for row in held:
        sid = row["system_id"]
        if sid in {"Gi_7E32", "Gi_8HK2"}:
            hold_cat["nonstandard length"] += 1
        elif sid in {"Gq_7RAN", "Gq_7RYC"}:
            hold_cat["missing processed outputs"] += 1
        elif sid == "Gq_8J9N":
            hold_cat["nonstandard replicas + missing outputs"] += 1
        else:
            hold_cat["temporary/incomplete files"] += 1

    width, height = 1800, 1220
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#6b7280"/></marker></defs>',
        svg_text(70, 70, "Figure 1 draft. Clean-v1 dataset composition and construction workflow", 34, "700"),
        svg_text(70, 105, "Draft for Scientific Data: update after final QC thresholds are locked", 18, "400", "#5f6b7a"),
    ]

    parts.extend([panel_label(70, 165, "A"), svg_text(110, 165, "QC funnel", 26, "700")])
    steps = [
        ("Designed systems", 222, "#34495e"),
        ("PBC/file screen", 213, "#65768a"),
        ("Completeness screen", 211, "#78909c"),
        ("Processed-output screen", 208, "#3f8f6b"),
        ("Clean v1 release", 208, "#2b7a4b"),
    ]
    x0, y0, maxn = 90, 205, 222
    for i, (label, n, color) in enumerate(steps):
        w = 520 * n / maxn
        x = x0 + (520 - w) / 2
        y = y0 + i * 65
        parts.append(
            f'<polygon points="{x},{y} {x+w},{y} {x+w-25},{y+48} {x+25},{y+48}" '
            f'fill="{color}" opacity="0.92"/>'
        )
        parts.append(svg_text(x0 + 260, y + 31, f"{label}: n={n}", 19, "700", "#ffffff", "middle"))

    parts.append(svg_text(90, 560, "Held back: 14 systems", 20, "700"))
    y = 590
    for label, n in hold_cat.items():
        parts.append(barh(90, y, 520, 28, label, n, 14, "#c65f5f"))
        y += 38

    parts.extend([panel_label(690, 165, "B"), svg_text(730, 165, "GPCR class distribution", 26, "700")])
    y = 210
    for label, n in sorted(gpcr_class.items()):
        parts.append(barh(730, y, 430, 44, "Class " + label, n, len(clean), COLORS.get(label, "#8aa0b4")))
        y += 62
    parts.append(svg_text(730, y + 18, f"Total clean-v1 systems: {len(clean)}", 20, "700"))

    parts.extend([panel_label(1220, 165, "C"), svg_text(1260, 165, "G-protein family distribution", 26, "700")])
    y = 210
    family_label = {"Gi": "Gi/o", "Gs": "Gs", "Gq": "Gq/11", "G12-13": "G12/13"}
    for fam in ["Gi", "Gs", "Gq", "G12-13"]:
        parts.append(barh(1260, y, 430, 44, family_label[fam], family[fam], len(clean), COLORS[fam]))
        y += 62

    parts.extend([panel_label(690, 560, "D"), svg_text(730, 560, "Provenance and sampling", 26, "700")])
    y = 610
    for label, n in provenance.items():
        parts.append(barh(730, y, 430, 40, label.replace("_", "/"), n, len(clean), COLORS.get(label, "#8899aa")))
        y += 55
    total_sampling = sum(num(row.get("total_sampling_ns")) for row in clean) / 1000.0
    unique_receptors = len({row.get("receptor_uniprot", "") for row in clean if row.get("receptor_uniprot", "")})
    parts.append(svg_text(730, y + 10, "All included systems: 3 replicas x 500 ns", 20, "700"))
    parts.append(svg_text(730, y + 42, f"Aggregate clean-v1 sampling: {total_sampling:.1f} microseconds", 20, "700"))
    parts.append(svg_text(730, y + 74, f"Unique receptors: {unique_receptors}", 20, "700"))

    parts.extend([panel_label(70, 820, "E"), svg_text(110, 820, "Build-to-data workflow", 26, "700")])
    workflow = [
        "structure selection",
        "standard preparation",
        "membrane/solvent setup",
        "3 x 500 ns MD",
        "trajectory processing",
        "metadata + archive",
        "portal/API access",
    ]
    x, y = 110, 875
    for i, label in enumerate(workflow):
        parts.append(rect(x, y, 190, 75, "#f5f7fa", "#c9d1dc", 8))
        parts.append(svg_text(x + 95, y + 45, label, 17, "700", "#1b1f2a", "middle"))
        if i < len(workflow) - 1:
            parts.append(
                f'<line x1="{x+190}" y1="{y+37}" x2="{x+235}" y2="{y+37}" '
                'stroke="#6b7280" stroke-width="3" marker-end="url(#arrow)"/>'
            )
        x += 235

    parts.append("</svg>")
    (outdir / "scidata_figure1_clean_v1_draft.svg").write_text("\n".join(parts))


def make_figure2(outdir: Path) -> None:
    width, height = 1800, 1220
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#6b7280"/></marker></defs>',
        svg_text(70, 70, "Figure 2 draft. Data records, repository organization and access model", 34, "700"),
        svg_text(70, 105, "Draft schematic; replace portal placeholder with a screenshot before submission", 18, "400", "#5f6b7a"),
    ]

    parts.extend([panel_label(70, 165, "A"), svg_text(110, 165, "Archive hierarchy", 26, "700")])
    tree = [
        "archive_root/",
        "  manifest/ checksums + version",
        "  metadata/ systems + held_back + dictionary",
        "  systems/SYSTEM_ID/",
        "    topology/ structures + topology",
        "    trajectories/ rep1 rep2 rep3",
        "    reduced/ aligned strided files",
        "    features/ RMSD RMSF contacts",
        "    pocket/ fpocket + GPCRdb mapping",
        "    qc/ frame PBC stability reports",
        "  code/ scripts notebooks",
        "  web_api_snapshot/ OpenAPI + endpoint examples",
    ]
    y = 205
    for item in tree:
        parts.append(svg_text(100, y, item, 19, "700" if not item.startswith(" ") else "400", "#1f2937"))
        y += 34

    parts.extend([panel_label(690, 165, "B"), svg_text(730, 165, "Metadata schema", 26, "700")])
    boxes = [
        ("system", 850, 220),
        ("receptor", 680, 340),
        ("G protein", 850, 340),
        ("ligand/state", 1020, 340),
        ("replicas", 760, 470),
        ("files", 940, 470),
        ("QC status", 850, 600),
    ]
    for label, x, y in boxes:
        parts.append(rect(x, y, 145, 60, "#f5f7fa", "#b8c2cf", 8))
        parts.append(svg_text(x + 72, y + 38, label, 18, "700", "#111827", "middle"))
    links = [
        ((922, 280), (752, 340)),
        ((922, 280), (922, 340)),
        ((922, 280), (1092, 340)),
        ((922, 400), (832, 470)),
        ((922, 400), (1012, 470)),
        ((922, 530), (922, 600)),
    ]
    for (x1, y1), (x2, y2) in links:
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            'stroke="#6b7280" stroke-width="2" marker-end="url(#arrow)"/>'
        )
    parts.append(svg_text(690, 710, "Keys: system_id, UniProt, GPCRdb numbering, G-protein family,", 16, "400", "#4b5563"))
    parts.append(svg_text(690, 734, "ligand/source, replica IDs, file paths, QC flags and checksums", 16, "400", "#4b5563"))

    parts.extend([panel_label(70, 820, "C"), svg_text(110, 820, "Access model", 26, "700")])
    access = [
        ("Stable archival repository", 110, 880, ("DOI/accession, full trajectories", "metadata, manifests")),
        ("Web portal", 630, 880, ("browse, filter, visualize", "selected downloads")),
        ("REST API", 1150, 880, ("programmatic metadata", "processed records")),
    ]
    for label, x, y, sublines in access:
        parts.append(rect(x, y, 360, 105, "#eef6ff", "#93b9e8", 10))
        parts.append(svg_text(x + 180, y + 40, label, 22, "700", "#14365d", "middle"))
        parts.append(svg_text(x + 180, y + 68, sublines[0], 14, "400", "#14365d", "middle"))
        parts.append(svg_text(x + 180, y + 88, sublines[1], 14, "400", "#14365d", "middle"))
    for x in [470, 990]:
        parts.append(f'<line x1="{x}" y1="932" x2="{x+140}" y2="932" stroke="#6b7280" stroke-width="3" marker-end="url(#arrow)"/>')

    parts.extend([panel_label(1220, 165, "D"), svg_text(1260, 165, "Portal screenshot panel", 26, "700")])
    parts.append(rect(1260, 210, 430, 500, "#f7f7f8", "#c9d1dc", 12))
    parts.append(svg_text(1475, 410, "Insert annotated portal screenshot", 24, "700", "#4b5563", "middle"))
    parts.append(svg_text(1475, 445, "search | filters | viewer | downloads | API", 18, "400", "#6b7280", "middle"))
    parts.append(svg_text(1260, 750, "Use the live portal as the access layer.", 17, "700", "#374151"))
    parts.append(svg_text(1260, 778, "The archive remains the citable data record.", 17, "700", "#374151"))

    parts.append("</svg>")
    (outdir / "scidata_figure2_data_records_draft.svg").write_text("\n".join(parts))


def main() -> None:
    outdir = Path("manuscript_figures/scidata_figures")
    outdir.mkdir(exist_ok=True)
    make_figure1(outdir)
    make_figure2(outdir)
    print(outdir / "scidata_figure1_clean_v1_draft.svg")
    print(outdir / "scidata_figure2_data_records_draft.svg")


if __name__ == "__main__":
    main()
