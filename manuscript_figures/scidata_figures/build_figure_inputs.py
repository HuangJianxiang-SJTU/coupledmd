#!/usr/bin/env python3
"""Build the cohort-level v9 plotting inputs from the frozen readiness overlay."""

from pathlib import Path
import json

import pandas as pd


HERE = Path(__file__).resolve().parent
MASTER = HERE.parent.parent / "data" / "systems_master.csv"
OVERLAY = HERE / "trajectory_readiness/versioned_summary/readiness_overlay_20260714_v2.csv"
OUT = HERE / "v9_figure_inputs"
API_SYSTEMS = HERE.parent.parent / "data" / "api" / "v1" / "systems"
SERVER_DATA = HERE.parent.parent / "data"
GATEWAY_READINESS = HERE.parent.parent.parent / "a" / "gateway_readiness.csv"
# Final release decision (2026-07-14): Gq_7E9W is a non-GPCR duplicate/mislabel
# of the separately retained Gq_8E9W system, and Gq_7DWC is a duplicate source
# identity of Gq_8DWC.  Preserve the 209-row readiness overlay unchanged and
# apply the documented exclusions only to v9 outputs.
FINAL_RELEASE_EXCLUSIONS = {
    "Gq_7E9W": "non-GPCR duplicate/mislabel of Gq_8E9W",
    "Gq_7DWC": "duplicate source identity of Gq_8DWC",
}

S1_COLUMNS = [
    "system_id", "pdb_id", "receptor_name", "receptor_uniprot",
    "receptor_gene", "gpcr_class", "g_protein_family", "g_alpha_subtype",
    "ligand_name", "ligand_chem_id", "ligand_class", "n_replicas",
    "length_per_replica_ns", "total_sampling_ns", "force_field",
    "lipid_composition", "structural_provenance", "trajectory_type",
    "has_bilayer", "traj_exists", "topo_exists", "traj_sha256",
    "topo_sha256", "notes",
]


def main() -> None:
    master = pd.read_csv(MASTER)
    overlay = pd.read_csv(OVERLAY)
    included = overlay["included_in_209_paper_set"].astype(str).str.lower().eq("true")

    ready_ids = overlay.loc[included, "system_id"]
    ready_ids = ready_ids.loc[~ready_ids.isin(FINAL_RELEASE_EXCLUSIONS)]
    unresolved = overlay.loc[~included].copy()
    s1 = master[master["system_id"].isin(ready_ids)][S1_COLUMNS].copy()
    s1 = s1.sort_values("system_id").reset_index(drop=True)

    # The paper release is explicitly a three-replica, 500-ns-per-replica
    # cohort. The master inventory retains pre-repair values for Gi_7E32 and
    # Gi_8HK2 and all six available replicas for Gq_8J9N; the v9 release uses
    # the three validated 500-ns replicas recorded by the readiness overlay.
    s1["n_replicas"] = 3
    s1["length_per_replica_ns"] = 500.0
    s1["total_sampling_ns"] = 1500.0

    hold_meta = master[master["system_id"].isin(unresolved["system_id"])].copy()
    s2 = hold_meta.merge(
        unresolved[[
            "system_id", "readiness_status", "readiness_action",
            "evidence_group", "evidence_source", "evidence_note",
            "baseline_replica_statuses",
        ]],
        on="system_id", how="inner",
    )
    s2["hold_reason"] = s2["evidence_note"].fillna(s2["readiness_action"])
    s2["rerun_status"] = s2["readiness_status"]
    s2 = s2[[
        "system_id", "pdb_id", "receptor_name", "receptor_uniprot",
        "gpcr_class", "g_protein_family", "g_alpha_subtype", "n_replicas",
        "length_per_replica_ns", "total_sampling_ns", "structural_provenance",
        "hold_reason", "rerun_status", "readiness_action", "evidence_group",
        "evidence_source", "baseline_replica_statuses", "notes",
    ]].sort_values("system_id").reset_index(drop=True)

    # Rebuild the pocket-derived technical-validation table from the current
    # per-system API records, restricted to the frozen 207-system cohort.
    validation_rows = []
    for row in s1.itertuples(index=False):
        pocket_path = API_SYSTEMS / row.system_id / "pockets.json"
        if pocket_path.exists():
            with pocket_path.open() as handle:
                pocket_record = json.load(handle)
            pockets = pocket_record.get("pockets", [])
            orthosteric = [p for p in pockets if p.get("is_orthosteric", False)]
            best_frequency = max(
                (p.get("mean_freq", float("nan")) for p in orthosteric),
                default=float("nan"),
            )
            n_pockets = int(pocket_record.get("n_pockets", 0))
            recovered = bool(pocket_record.get("orthosteric_recovered", False))
            ligand_type = pocket_record.get("ligand_type", "none")
        else:
            n_pockets = 0
            recovered = False
            best_frequency = float("nan")
            orthosteric = []
            ligand_type = "none"
        validation_rows.append({
            "system_id": row.system_id,
            "g_family": row.g_protein_family,
            "n_pockets": n_pockets,
            "has_pockets": n_pockets > 0,
            "ortho_recovered": recovered,
            "best_ortho_freq": best_frequency,
            "n_ortho_pockets": len(orthosteric),
            "lig_type": ligand_type,
            "structural_provenance": row.structural_provenance,
            "pocket_source": str(pocket_path) if pocket_path.exists() else "missing",
        })
    t4 = pd.DataFrame(validation_rows).sort_values("system_id").reset_index(drop=True)

    summary_rows = []
    family_labels = [("Gi/o", "Gi"), ("Gs", "Gs"), ("Gq/11", "Gq"),
                     ("G12/13", "G12-13")]
    for label, family in family_labels + [("All v9", None)]:
        subset = t4 if family is None else t4[t4["g_family"].eq(family)]
        with_pockets = int(subset["has_pockets"].sum())
        recovered = int(subset["ortho_recovered"].sum())
        summary_rows.append({
            "subset": label,
            "systems_n": len(subset),
            "systems_with_pockets": with_pockets,
            "orthosteric_recovered": recovered,
            "recovery_rate_percent": round(100 * recovered / with_pockets, 1)
                if with_pockets else 0.0,
            "mean_best_orthosteric_frequency": round(
                subset["best_ortho_freq"].mean(), 3),
        })
    t4a = pd.DataFrame(summary_rows)

    gateway_pairs = ["TM3-TM4", "TM7-TM1", "TM4-TM5", "TM5-TM6",
                     "TM1-TM2", "TM6-TM7", "TM2-TM3"]
    gateway_rows = []
    for row in s1.itertuples(index=False):
        gateway_path = API_SYSTEMS / row.system_id / "gateways.json"
        output = {"System ID": row.system_id, "gateway_source":
                  str(gateway_path) if gateway_path.exists() else "missing"}
        records = []
        if gateway_path.exists():
            with gateway_path.open() as handle:
                records = json.load(handle).get("records", [])
        for pair in gateway_pairs:
            matches = [r for r in records if r.get("pair") == pair and
                       r.get("metric") == "open_fraction"]
            value = matches[0].get("mean") if len(matches) == 1 else None
            output[f"{pair} open_fraction"] = (
                float(value) if value is not None else float("nan"))
        gateway_rows.append(output)
    s5 = pd.DataFrame(gateway_rows).sort_values("System ID").reset_index(drop=True)

    def readiness_issue(row):
        evidence = " ".join(str(row.get(c, "")) for c in
                            ["evidence_note", "baseline_replica_statuses"]).lower()
        if "incomplete" in evidence or "span" in evidence:
            return "incomplete trajectory"
        if "dissociation" in evidence:
            return "component continuity"
        return "PBC/trajectory continuity"

    qc = overlay.copy()
    qc["cohort_status"] = qc["included_in_209_paper_set"].map(
        {True: "included", False: "unresolved"})
    qc.loc[qc["system_id"].isin(FINAL_RELEASE_EXCLUSIONS), "cohort_status"] = "excluded"
    qc["qc_category"] = "release-ready trajectory set"
    unresolved_mask = ~qc["included_in_209_paper_set"]
    qc.loc[unresolved_mask, "qc_category"] = qc.loc[unresolved_mask].apply(
        readiness_issue, axis=1)
    qc["timestamp_reset_interpretation"] = (
        "diagnostic_only_not_failure")
    qc_summary = qc.groupby(["cohort_status", "qc_category"], sort=False).size().reset_index(
        name="systems_n")

    pocket_rows = []
    pocket_source_rows = []
    for row in s1.itertuples(index=False):
        pocket_path = API_SYSTEMS / row.system_id / "pockets_gpcrdb.json"
        if not pocket_path.exists():
            pocket_source_rows.append({"system_id": row.system_id,
                                       "pocket_record_status": "missing"})
            continue
        with pocket_path.open() as handle:
            record = json.load(handle)
        pockets = record.get("pockets", [])
        pocket_source_rows.append({"system_id": row.system_id,
                                   "pocket_record_status": "available"})
        for pocket in pockets:
            pocket_rows.append({
                "system_id": row.system_id,
                "receptor_name": row.receptor_name,
                "g_family": row.g_protein_family,
                "pocket_id": pocket.get("pocket_id"),
                "n_voxels": pocket.get("n_voxels"),
                "mean_freq": pocket.get("mean_freq"),
                "is_orthosteric": bool(pocket.get("is_orthosteric", False)),
                "location": pocket.get("location", "unknown"),
                "zone": pocket.get("zone", "other"),
                "receptor_generic_numbers": ";".join(
                    pocket.get("receptor_generic_numbers", [])),
            })
    pocket_detail = pd.DataFrame(pocket_rows).sort_values(
        ["system_id", "pocket_id"]).reset_index(drop=True)
    pocket_sources = pd.DataFrame(pocket_source_rows).sort_values(
        "system_id").reset_index(drop=True)

    # Rebuild the v9 archive inventory and portal/API coverage manifest from
    # direct filesystem evidence. These tables describe current source-file
    # availability; they do not imply repository deposition.
    master_by_id = master.set_index("system_id")
    archive_rows = []
    for row in s1.itertuples(index=False):
        source = master_by_id.loc[row.system_id]
        for record_type, column in [
            ("production_trajectory", "trajectory_path"),
            ("topology", "topology_path"),
        ]:
            value = source.get(column)
            path = Path(str(value)) if pd.notna(value) else None
            exists = bool(path and path.exists() and path.is_file())
            archive_rows.append({
                "system_id": row.system_id,
                "record_type": record_type,
                "source_path": str(path) if path else "",
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else 0,
                "release_replicas": "rep1|rep2|rep3",
                "replicas_n": 3,
                "length_per_replica_ns": 500.0,
                "total_sampling_ns": 1500.0,
            })
    archive_manifest = pd.DataFrame(archive_rows)

    portal_specs = {
        "viz_structure": lambda sid: SERVER_DATA / "viz" / sid / "structure.pdb",
        "viz_trajectory": lambda sid: SERVER_DATA / "viz" / sid / "traj.xtc",
        "api_index": lambda sid: API_SYSTEMS / sid / "index.json",
        "api_pockets": lambda sid: API_SYSTEMS / sid / "pockets.json",
        "api_pockets_gpcrdb": lambda sid: API_SYSTEMS / sid / "pockets_gpcrdb.json",
        "api_gateways": lambda sid: API_SYSTEMS / sid / "gateways.json",
        "api_gprotein": lambda sid: API_SYSTEMS / sid / "gprotein_metrics.json",
        "api_pocketgrid": lambda sid: API_SYSTEMS / sid / "pocketgrid.npz",
        "chain_roles": lambda sid: SERVER_DATA / "chain_roles" / f"{sid}_chain_roles.json",
        "contacts": lambda sid: SERVER_DATA / "contacts" / f"{sid}_contacts.parquet",
    }
    gateway_readiness = pd.read_csv(GATEWAY_READINESS).set_index("system_id")
    portal_rows = []
    for row in s1.itertuples(index=False):
        for record_type, path_builder in portal_specs.items():
            path = path_builder(row.system_id)
            exists = path.exists() and path.is_file() and path.stat().st_size > 0
            content_status = "available" if exists else "missing"
            detail = ""
            if exists and record_type == "api_gateways":
                with path.open() as handle:
                    records = json.load(handle).get("records", [])
                values = [r.get("mean") for r in records
                          if r.get("metric") == "open_fraction"]
                if len(values) != 7 or any(v is None for v in values):
                    readiness_status = str(gateway_readiness.loc[row.system_id, "status"])
                    if readiness_status != "gateway_ready":
                        content_status = "not_applicable"
                        detail = ("gateway metric requires lipid-containing full-system "
                                  f"replicas; readiness status is {readiness_status}")
                    else:
                        content_status = "unpopulated"
                        detail = "seven numerical open_fraction means not available"
            portal_rows.append({
                "system_id": row.system_id,
                "record_type": record_type,
                "path": str(path),
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else 0,
                "content_status": content_status,
                "detail": detail,
            })
    portal_manifest = pd.DataFrame(portal_rows)
    portal_summary = portal_manifest.groupby("record_type", sort=False).agg(
        expected_systems=("system_id", "size"),
        files_present=("exists", "sum"),
        records_available=("content_status", lambda s: int(s.eq("available").sum())),
        records_missing=("content_status", lambda s: int(s.eq("missing").sum())),
        records_unpopulated=("content_status", lambda s: int(s.eq("unpopulated").sum())),
        records_not_applicable=("content_status", lambda s: int(s.eq("not_applicable").sum())),
        total_size_bytes=("size_bytes", "sum"),
    ).reset_index()
    gap_ids = (portal_manifest.loc[portal_manifest["content_status"].ne("available")]
               .groupby("record_type")["system_id"].agg(";".join))
    portal_summary["affected_system_ids"] = portal_summary["record_type"].map(
        gap_ids).fillna("")

    manifest_summary = pd.DataFrame([
        {"manifest": "release_cohort_v9_final207", "records": 621, "systems": 207,
         "status": "validated", "notes": "Three selected 500-ns replicas per system; Gq_7E9W and Gq_7DWC excluded as duplicates/mislabels."},
        {"manifest": "archive_source_inventory_v9", "records": len(archive_manifest),
         "systems": int(archive_manifest.loc[archive_manifest["exists"], "system_id"].nunique()),
         "status": "audited", "notes": "Source trajectory and topology inventory; not a repository-deposit claim."},
        {"manifest": "portal_api_file_manifest_v9", "records": len(portal_manifest),
         "systems": int(portal_manifest["system_id"].nunique()), "status": "audited",
         "notes": "Direct file and JSON-content audit of the current server tree."},
        {"manifest": "openapi_snapshot", "records": 27, "systems": pd.NA,
         "status": "documented", "notes": "Frozen OpenAPI schema snapshot."},
    ])

    assert len(s1) == 207, len(s1)
    assert len(s2) == 13, len(s2)
    assert int(s1["n_replicas"].sum()) == 621
    assert float(s1["total_sampling_ns"].sum()) == 310_500.0
    assert s1["g_protein_family"].value_counts().to_dict() == {
        "Gi": 95, "Gs": 65, "Gq": 41, "G12-13": 6,
    }
    assert s1["gpcr_class"].value_counts().to_dict() == {"A": 181, "B": 26}
    assert len(t4) == 207 and t4["system_id"].is_unique
    assert set(t4["system_id"]) == set(s1["system_id"])
    assert int(t4a.loc[t4a["subset"].eq("All v9"), "systems_n"].iloc[0]) == 207
    assert len(s5) == 207 and s5["System ID"].is_unique
    assert len(qc) == 222
    assert qc["cohort_status"].value_counts().to_dict() == {
        "included": 207, "unresolved": 13, "excluded": 2}
    assert len(pocket_sources) == 207
    assert len(archive_manifest) == 414 and archive_manifest["exists"].all()
    assert len(portal_manifest) == 2070
    assert portal_summary["expected_systems"].eq(207).all()

    OUT.mkdir(exist_ok=True)
    s1.to_csv(OUT / "scidata_S1_included_systems_v9.csv", index=False)
    pd.DataFrame([
        {"system_id": sid, "release_status": "excluded",
         "reason": reason,
         "source": "final release decision 2026-07-14"}
        for sid, reason in FINAL_RELEASE_EXCLUSIONS.items()
    ]).to_csv(OUT / "scidata_T0_final_release_exclusions_v9.csv", index=False)
    s2.to_csv(OUT / "scidata_S2_unresolved_systems_v9.csv", index=False)
    t4.to_csv(OUT / "scidata_T4_technical_validation_v9.csv", index=False)
    t4a.to_csv(OUT / "scidata_T4a_recovery_summary_v9.csv", index=False)
    s5.to_csv(OUT / "scidata_S5_gateway_per_system_v9.csv", index=False)
    qc.to_csv(OUT / "scidata_T8_readiness_qc_v9.csv", index=False)
    qc_summary.to_csv(OUT / "scidata_T8a_readiness_qc_summary_v9.csv", index=False)
    pocket_detail.to_csv(OUT / "scidata_S4_per_pocket_v9.csv", index=False)
    pocket_sources.to_csv(OUT / "scidata_S4a_pocket_source_status_v9.csv", index=False)
    archive_manifest.to_csv(OUT / "scidata_S8_archive_source_inventory_v9.csv", index=False)
    portal_manifest.to_csv(OUT / "scidata_S9_portal_api_file_manifest_v9.csv", index=False)
    portal_summary.to_csv(OUT / "scidata_T7_portal_api_availability_summary_v9.csv", index=False)
    manifest_summary.to_csv(OUT / "scidata_T6_manifest_summary_v9.csv", index=False)
    print(f"wrote {len(s1)} final-release systems and {len(s2)} unresolved systems to {OUT}")


if __name__ == "__main__":
    main()
