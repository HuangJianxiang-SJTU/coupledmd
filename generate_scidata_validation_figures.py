#!/usr/bin/env python3
"""Generate clean-v1 validation/QC tables and draft SVG figures."""

from __future__ import annotations

import collections
import csv
import html
import json
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

FAMILY_ORDER = ["Gi", "Gs", "Gq", "G12-13"]
FAMILY_LABEL = {"Gi": "Gi/o", "Gs": "Gs", "Gq": "Gq/11", "G12-13": "G12/13"}
COLORS = {"Gi": "#4C93D9", "Gs": "#E8A73A", "Gq": "#D95C5C", "G12-13": "#8D58B4"}


def esc(text: object) -> str:
    return html.escape(str(text))


def num(value: object) -> float:
    try:
        if value in ("", None):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def truth(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


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


def barh(x, y, w, h, label, value, max_value, color, suffix=""):
    bw = w * value / max(max_value, 1)
    return "".join(
        [
            rect(x, y, w, h, "#eef1f5", "none", 4),
            rect(x, y, bw, h, color, "none", 4),
            svg_text(x + 8, y + h / 2 + 7, f"{label} {value}{suffix}", 17, "700", "#111827"),
        ]
    )


def panel_label(x, y, label):
    return svg_text(x, y, label, 28, "700", "#111827")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", errors="ignore") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_validation_tables(base: Path) -> dict[str, object]:
    figdir = base / "manuscript_figures"
    tabdir = figdir / "tables"
    tabdir.mkdir(exist_ok=True)

    systems = read_csv(base / "data" / "systems_master.csv")
    clean_ids = {row["system_id"] for row in systems if row["system_id"] not in HOLD}
    held = [row for row in systems if row["system_id"] in HOLD]
    clean = [row for row in systems if row["system_id"] in clean_ids]
    recovery_all = read_csv(figdir / "phase1_outputs" / "recovery_benchmark.csv")
    recovery = [row for row in recovery_all if row["system_id"] in clean_ids]

    rec_fields = [
        "system_id",
        "g_family",
        "n_pockets",
        "has_pockets",
        "ortho_recovered",
        "best_ortho_freq",
        "n_ortho_pockets",
        "lig_type",
        "structural_provenance",
    ]
    write_csv(tabdir / "scidata_T4_technical_validation_clean_v1.csv", recovery, rec_fields)

    family_rows = []
    for family in FAMILY_ORDER:
        subset = [row for row in recovery if row["g_family"] == family]
        with_pockets = [row for row in subset if truth(row["has_pockets"])]
        recovered = [row for row in with_pockets if truth(row["ortho_recovered"])]
        mean_freq_values = [num(row["best_ortho_freq"]) for row in recovered if num(row["best_ortho_freq"]) > 0]
        family_rows.append(
            {
                "subset": FAMILY_LABEL[family],
                "systems_n": len(subset),
                "systems_with_pockets": len(with_pockets),
                "orthosteric_recovered": len(recovered),
                "recovery_rate_percent": f"{100 * len(recovered) / len(with_pockets):.1f}" if with_pockets else "n/a",
                "mean_best_orthosteric_frequency": f"{sum(mean_freq_values) / len(mean_freq_values):.3f}" if mean_freq_values else "n/a",
            }
        )
    with_pockets = [row for row in recovery if truth(row["has_pockets"])]
    recovered = [row for row in with_pockets if truth(row["ortho_recovered"])]
    mean_freq_values = [num(row["best_ortho_freq"]) for row in recovered if num(row["best_ortho_freq"]) > 0]
    family_rows.append(
        {
            "subset": "All clean-v1",
            "systems_n": len(recovery),
            "systems_with_pockets": len(with_pockets),
            "orthosteric_recovered": len(recovered),
            "recovery_rate_percent": f"{100 * len(recovered) / len(with_pockets):.1f}" if with_pockets else "n/a",
            "mean_best_orthosteric_frequency": f"{sum(mean_freq_values) / len(mean_freq_values):.3f}" if mean_freq_values else "n/a",
        }
    )
    write_csv(
        tabdir / "scidata_T4a_recovery_summary_clean_v1.csv",
        family_rows,
        [
            "subset",
            "systems_n",
            "systems_with_pockets",
            "orthosteric_recovered",
            "recovery_rate_percent",
            "mean_best_orthosteric_frequency",
        ],
    )

    pocket_all = read_csv(figdir / "tables" / "S6_per_system_pockets.csv")
    pocket = [row for row in pocket_all if row["System ID"] in clean_ids]
    write_csv(
        tabdir / "scidata_S4_per_system_pockets_clean_v1.csv",
        pocket,
        [
            "System ID",
            "Receptor",
            "G-protein family",
            "Total pockets (fpocket)",
            "Druggable consensus clusters",
            "N druggable clusters",
            "Orthosteric consensus clusters",
            "N orthosteric clusters",
        ],
    )

    gateway_all = read_csv(figdir / "tables" / "S5_gateway_per_system.csv")
    gateway = [row for row in gateway_all if row["System ID"] in clean_ids]
    write_csv(tabdir / "scidata_S5_gateway_per_system_clean_v1.csv", gateway, list(gateway_all[0].keys()))

    hold_reason_counts = collections.Counter()
    for row in held:
        sid = row["system_id"]
        if sid in {"Gi_7E32", "Gi_8HK2"}:
            hold_reason_counts["nonstandard length"] += 1
        elif sid in {"Gq_7RAN", "Gq_7RYC"}:
            hold_reason_counts["missing processed outputs"] += 1
        elif sid == "Gq_8J9N":
            hold_reason_counts["nonstandard replicas + missing outputs"] += 1
        else:
            hold_reason_counts["temporary/incomplete files"] += 1

    qc_rows = [
        {"gate": "designed systems", "systems_n": len(systems), "passing_n": len(systems), "held_back_n": 0, "notes": "initial current inventory"},
        {"gate": "clean-v1 included", "systems_n": len(systems), "passing_n": len(clean), "held_back_n": len(held), "notes": "strict clean-v1 cohort used for Paper 1 drafts"},
        {"gate": "3 x 500 ns metadata", "systems_n": len(clean), "passing_n": sum(1 for row in clean if row["n_replicas"] == "3" and num(row["length_per_replica_ns"]) == 500), "held_back_n": 0, "notes": "metadata-level completeness check; frame-level audit still needed"},
        {"gate": "trajectory path present", "systems_n": len(clean), "passing_n": sum(1 for row in clean if truth(row.get("traj_exists"))), "held_back_n": 0, "notes": "metadata file-existence flag"},
        {"gate": "topology path present", "systems_n": len(clean), "passing_n": sum(1 for row in clean if truth(row.get("topo_exists"))), "held_back_n": 0, "notes": "metadata file-existence flag"},
        {"gate": "pocket outputs present", "systems_n": len(clean), "passing_n": len([row for row in recovery if truth(row["has_pockets"])]), "held_back_n": len([row for row in recovery if not truth(row["has_pockets"])]), "notes": "fpocket-derived validation data; absence may reflect closed pockets or missing processed output"},
    ]
    write_csv(tabdir / "scidata_T5_qc_summary_clean_v1.csv", qc_rows, ["gate", "systems_n", "passing_n", "held_back_n", "notes"])

    return {
        "systems": systems,
        "clean": clean,
        "held": held,
        "recovery": recovery,
        "family_rows": family_rows,
        "hold_reason_counts": hold_reason_counts,
        "qc_rows": qc_rows,
    }


def make_figure3(base: Path, data: dict[str, object]) -> None:
    outdir = base / "manuscript_figures" / "scidata_figures"
    outdir.mkdir(exist_ok=True)
    recovery = data["recovery"]
    family_rows = data["family_rows"]
    clean_n = len(data["clean"])

    width, height = 1800, 1220
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(70, 70, "Figure 3 draft. Technical validation by pocket and binding-site recovery", 34, "700"),
        svg_text(70, 105, "Draft for Scientific Data; framed as validation and reuse, not mechanism", 18, "400", "#5f6b7a"),
    ]

    parts.extend([panel_label(70, 165, "A"), svg_text(110, 165, "Orthosteric-site recovery by family", 26, "700")])
    y = 215
    max_total = max(int(row["systems_with_pockets"]) for row in family_rows if row["subset"] != "All clean-v1")
    for family, row in zip(FAMILY_ORDER, family_rows[:4]):
        total = int(row["systems_with_pockets"])
        recovered = int(row["orthosteric_recovered"])
        parts.append(rect(110, y, 520, 38, "#eef1f5", "none", 4))
        parts.append(rect(110, y, 520 * total / max_total, 38, "#d8dee7", "none", 4))
        parts.append(rect(110, y, 520 * recovered / max_total, 38, COLORS[family], "none", 4))
        parts.append(svg_text(122, y + 25, f"{row['subset']}: {recovered}/{total} pocket-having systems", 17, "700"))
        y += 58
    all_row = family_rows[-1]
    parts.append(svg_text(110, y + 20, f"All clean-v1: {all_row['orthosteric_recovered']}/{all_row['systems_with_pockets']} recovered ({all_row['recovery_rate_percent']}%)", 20, "700"))

    parts.extend([panel_label(720, 165, "B"), svg_text(760, 165, "Best orthosteric-pocket frequency", 26, "700")])
    recovered_freq = sorted(num(row["best_ortho_freq"]) for row in recovery if truth(row["ortho_recovered"]) and num(row["best_ortho_freq"]) > 0)
    bins = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.85), (0.85, 0.95), (0.95, 1.01)]
    labels = ["0-0.5", "0.5-0.7", "0.7-0.85", "0.85-0.95", "0.95-1.0"]
    counts = [sum(1 for value in recovered_freq if lo <= value < hi) for lo, hi in bins]
    max_count = max(counts) if counts else 1
    x = 770
    for label, count in zip(labels, counts):
        h = 300 * count / max_count
        parts.append(rect(x, 520 - h, 70, h, "#5aa0d8", "none", 4))
        parts.append(svg_text(x + 35, 550, label, 16, "400", "#111827", "middle"))
        parts.append(svg_text(x + 35, 508 - h, count, 16, "700", "#111827", "middle"))
        x += 90
    parts.append(svg_text(760, 600, f"n={len(recovered_freq)} recovered systems with frequency values", 18, "400", "#4b5563"))

    parts.extend([panel_label(1210, 165, "C"), svg_text(1250, 165, "CCR5 worked validation example", 26, "700")])
    ccr5_path = base / "data" / "api" / "v1" / "systems" / "Gi_7F1Q" / "pockets.json"
    if ccr5_path.exists():
        ccr5 = json.load(open(ccr5_path))
        pockets = sorted(ccr5.get("pockets", []), key=lambda item: num(item.get("mean_freq")), reverse=True)[:10]
        y = 215
        max_freq = max((num(item.get("mean_freq")) for item in pockets), default=1)
        for item in pockets:
            freq = num(item.get("mean_freq"))
            label = f"P{item.get('pocket_id')}"
            color = "#D95C5C" if item.get("is_orthosteric") else "#4C93D9"
            parts.append(rect(1250, y, 430, 28, "#eef1f5", "none", 4))
            parts.append(rect(1250, y, 430 * freq / max_freq, 28, color, "none", 4))
            parts.append(svg_text(1260, y + 20, f"{label}  mean frequency {freq:.3f}", 15, "700", "#111827"))
            y += 38
        parts.append(svg_text(1250, y + 10, "CCR5 Gi_7F1Q: persistent pockets summarized from API records", 17, "400", "#4b5563"))
    else:
        parts.append(svg_text(1250, 250, "CCR5 pocket JSON not found", 20, "700", "#b91c1c"))

    parts.extend([panel_label(70, 760, "D"), svg_text(110, 760, "Pocket-output availability in clean-v1", 26, "700")])
    with_pockets = sum(1 for row in recovery if truth(row["has_pockets"]))
    without_pockets = len(recovery) - with_pockets
    recovered = sum(1 for row in recovery if truth(row["ortho_recovered"]))
    values = [("systems", clean_n, "#6b7280"), ("with pockets", with_pockets, "#4C93D9"), ("orthosteric recovered", recovered, "#49A87F"), ("without pockets", without_pockets, "#D95C5C")]
    x = 125
    for label, value, color in values:
        h = 300 * value / clean_n
        parts.append(rect(x, 1090 - h, 130, h, color, "none", 4))
        parts.append(svg_text(x + 65, 1120, label, 16, "700", "#111827", "middle"))
        parts.append(svg_text(x + 65, 1078 - h, value, 20, "700", "#111827", "middle"))
        x += 170
    parts.append(svg_text(780, 850, "Caption guardrail:", 22, "700"))
    parts.append(svg_text(780, 890, "Use recovered / preserved / consistent.", 20, "400", "#374151"))
    parts.append(svg_text(780, 925, "Do not say reveal, explain, or demonstrate a mechanism.", 20, "400", "#374151"))
    parts.append(svg_text(780, 980, "Final version should add replica-level agreement if frame-level outputs are available.", 18, "400", "#5f6b7a"))

    parts.append("</svg>")
    (outdir / "scidata_figure3_validation_draft.svg").write_text("\n".join(parts))


def make_figure4(base: Path, data: dict[str, object]) -> None:
    outdir = base / "manuscript_figures" / "scidata_figures"
    outdir.mkdir(exist_ok=True)
    clean = data["clean"]
    held = data["held"]
    recovery = data["recovery"]
    hold_reason_counts = data["hold_reason_counts"]
    qc_rows = data["qc_rows"]

    width, height = 1800, 1220
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(70, 70, "Figure 4 draft. Global QC and completeness summary", 34, "700"),
        svg_text(70, 105, "Draft from current metadata; final version should replace placeholder panels with frame-level trajectory QC", 18, "400", "#5f6b7a"),
    ]

    parts.extend([panel_label(70, 165, "A"), svg_text(110, 165, "Metadata-level trajectory completeness", 26, "700")])
    checks = [
        ("3 x 500 ns", sum(1 for row in clean if row["n_replicas"] == "3" and num(row["length_per_replica_ns"]) == 500)),
        ("trajectory path exists", sum(1 for row in clean if truth(row.get("traj_exists")))),
        ("topology path exists", sum(1 for row in clean if truth(row.get("topo_exists")))),
    ]
    y = 220
    for label, value in checks:
        parts.append(barh(120, y, 560, 42, label, value, len(clean), "#49A87F"))
        y += 62
    parts.append(svg_text(120, y + 20, "Note: frame-count and PBC image checks still need final archive audit.", 18, "700", "#5f6b7a"))

    parts.extend([panel_label(760, 165, "B"), svg_text(800, 165, "Available processed validation records", 26, "700")])
    values = [
        ("recovery rows", len(recovery), "#4C93D9"),
        ("pocket-having", sum(1 for row in recovery if truth(row["has_pockets"])), "#49A87F"),
        ("no pocket record", sum(1 for row in recovery if not truth(row["has_pockets"])), "#D95C5C"),
    ]
    x = 810
    for label, value, color in values:
        h = 300 * value / len(clean)
        parts.append(rect(x, 535 - h, 135, h, color, "none", 4))
        parts.append(svg_text(x + 67, 565, label, 16, "700", "#111827", "middle"))
        parts.append(svg_text(x + 67, 523 - h, value, 20, "700", "#111827", "middle"))
        x += 175

    parts.extend([panel_label(1290, 165, "C"), svg_text(1335, 165, "Held-back systems by reason", 24, "700")])
    y = 220
    for label, value in hold_reason_counts.most_common():
        parts.append(barh(1335, y, 380, 34, label, value, len(held), "#c65f5f"))
        y += 52
    parts.append(svg_text(1335, y + 15, f"Held back: {len(held)} of {len(clean) + len(held)} current systems", 18, "700"))

    parts.extend([panel_label(70, 760, "D"), svg_text(110, 760, "QC gates for final submission figure", 26, "700")])
    y = 815
    for row in qc_rows:
        parts.append(rect(120, y, 1480, 46, "#f7f8fa", "#d1d7e0", 6))
        parts.append(svg_text(140, y + 29, row["gate"], 18, "700"))
        parts.append(svg_text(520, y + 29, f"passing n={row['passing_n']} / {row['systems_n']}", 18, "400"))
        parts.append(svg_text(800, y + 29, row["notes"], 16, "400", "#4b5563"))
        y += 58
    parts.append(svg_text(120, 1165, "Replace this panel with RMSD/RMSF, frame-count and PBC-discontinuity distributions after the final archive audit.", 18, "700", "#5f6b7a"))

    parts.append("</svg>")
    (outdir / "scidata_figure4_qc_draft.svg").write_text("\n".join(parts))


def main() -> None:
    base = Path(".")
    data = build_validation_tables(base)
    make_figure3(base, data)
    make_figure4(base, data)
    figdir = base / "manuscript_figures" / "scidata_figures"
    tabdir = base / "manuscript_figures" / "tables"
    for path in [
        tabdir / "scidata_T4_technical_validation_clean_v1.csv",
        tabdir / "scidata_T4a_recovery_summary_clean_v1.csv",
        tabdir / "scidata_T5_qc_summary_clean_v1.csv",
        tabdir / "scidata_S4_per_system_pockets_clean_v1.csv",
        tabdir / "scidata_S5_gateway_per_system_clean_v1.csv",
        figdir / "scidata_figure3_validation_draft.svg",
        figdir / "scidata_figure4_qc_draft.svg",
    ]:
        print(path)


if __name__ == "__main__":
    main()
