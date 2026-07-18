#!/usr/bin/env python3
"""Revise v10_manuscript_updated.docx for the 207-system final cohort."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "v10_manuscript_updated.docx"


REPLACEMENTS = {
    "Molecular dynamics (MD) trajectories of G protein-coupled receptor (GPCR)–G-protein complexes are among the most expensive": (
        "Molecular dynamics (MD) trajectories of G protein-coupled receptor (GPCR)–G-protein complexes are among the most expensive and least reusable data in structural pharmacology, because simulation protocols, molecular representations and annotations differ between studies and are rarely shared in interoperable form. Here we present CoupledMD, a curated cohort of 207 active-state GPCR–G-protein complexes spanning 174 receptors, two GPCR classes (A and B) and all four major G-protein families (Gi/o, Gs, Gq/11 and G12/13). Every complex was simulated in a POPC membrane under a CHARMM36-family force field as three validated 500-ns replicas, yielding 621 production trajectories and 310.5 µs of aggregate sampling—one of the largest uniformly prepared trajectory collections of the receptor–transducer assemblies that dominate the drug-target landscape. CoupledMD adds system metadata, GPCRdb-mapped pocket annotations, transmembrane-gateway records, reduced visualization trajectories and a versioned REST API; a complete DOI-linked archive of primary trajectories, topologies and inputs is in preparation. We built CoupledMD as a shared, extensible foundation the GPCR community can inherit for trajectory-method benchmarking, receptor-aware comparative analysis and reuse of structurally derived annotations."
    ),
    "CoupledMD comprises 208 active-state systems selected from a 222-record working inventory.": (
        "CoupledMD comprises 207 active-state systems selected from a 222-record working inventory. The cohort spans 174 distinct receptor names (173 mapped UniProt accessions) across Class A (181 systems) and Class B (26 systems) GPCRs and all four major G-protein families (95 Gi/o, 65 Gs, 41 Gq/11 and 6 G12/13). Each system contributes three validated 500-ns production replicas simulated under a CHARMM36-family force field in a POPC bilayer, yielding 621 trajectories and 310.5 µs of aggregate sampling. A further thirteen records remain unresolved—owing to periodic-boundary or trajectory-continuity issues, component discontinuity or incomplete-trajectory evidence—and two records (Gq_7E9W and Gq_7DWC) are excluded: Gq_7E9W is a non-GPCR duplicate of Gq_8E9W, and Gq_7DWC is a duplicate source identity of Gq_8DWC (both MRGPRX1, Q96LB2); we document these explicitly, and none contributes to the release counts, derived records or API responses. To our knowledge, this is one of the largest uniformly prepared trajectory collections of the receptor–transducer assemblies that dominate the drug-target landscape, and we built it to be inherited and extended by the broader GPCR community."
    ),
    "Active-state GPCR–G-protein complex structures were collected from the Protein Data Bank (PDB)7": (
        "Active-state GPCR–G-protein complex structures were collected from the Protein Data Bank (PDB)7 by restricting to entries containing both a seven-transmembrane receptor and a heterotrimeric or engineered G-protein assembly in an active or active-like conformation. Receptor chains were cross-referenced to UniProt8, GPCRdb3 and GproteinDb9; G-protein chains were assigned to one of four families (Gi/o, Gs, Gq/11 or G12/13) from the Gα-subtype annotation. Structural provenance was recorded separately from receptor activation state: of the 207 included systems, 197 derive from experimental coordinates and 10 carry an engineered or uncertain provenance flag, so that users may apply stricter inclusion criteria if required."
    ),
    "Complexes were embedded in a homogeneous POPC lipid bilayer using CHARMM-GUI Membrane Builder10,11.": (
        "Complexes were embedded in a homogeneous POPC lipid bilayer using CHARMM-GUI Membrane Builder10,11. Missing residues and side chains in the receptor and G protein were modeled during preparation; protonation states were assigned at pH 7.4. Systems were solvated with TIP3P water leaving at least 15 Å of padding between the protein and the periodic box edge, and neutralized with Na⁺/Cl⁻ ions to an ionic strength of 0.15 M. Ligands retained from the source structure were parameterized with the CHARMM General Force Field (CGenFF)12 where applicable. All 207 systems are annotated as POPC membrane-embedded."
    ),
    "All protocols used NPT conditions at 310 K and 1 bar": (
        "All protocols used NPT conditions at 310 K and 1 bar, a 2-fs integration step, particle-mesh Ewald electrostatics16 and constraints on bonds to hydrogen (SHAKE for AMBER17; LINCS for GROMACS18). Nonbonded interactions used a 12-Å cutoff with force-switching from 10 Å (AMBER) or a 1.2-nm cutoff with switching from 1.0 nm (GROMACS). Coordinates were written every 50 ps. Each system underwent energy minimization followed by multi-stage equilibration with protein and lipid restraints progressively released before production. Each of the three production replicas ran for 500 ns from independently assigned initial velocities, giving 1.5 µs per system and 310.5 µs across the cohort. The three workflow groups share a force-field family and membrane composition but differ in engine, thermostat and barostat implementation; workflow group should therefore be treated as a potential batch variable. Production replicas are computational repeats rather than biological replicates."
    ),
    "Pocket-analysis records were generated for all 208 systems using fpocket19.": (
        "Pocket-analysis records were generated for all 207 systems using fpocket19. Persistent pockets were detected in 206 systems; Gi_7YK6 and Gi_8YIC produced valid zero-pocket records rather than missing analyses. For each system, approximately 200 frames per replica (600 frames across three replicas) were sampled at a stride of 50 stored production frames. Protein coordinates in each frame were aligned to the reference structure by Cα atoms, and fpocket was executed independently per frame. Alpha-sphere occupancy was accumulated on a 1.5-Å Cartesian grid, and grid points occupied in at least 85% of analyzed frames were retained. Retained points were clustered by DBSCAN (ε = 2.85 Å, min_samples = 3), and protein heavy atoms within 4.0 Å of a persistent cluster were assigned as pocket-lining residues. For peptide-ligand systems, a cluster was labelled orthosteric when any retained grid point lay within 5.0 Å of a ligand heavy atom; best_ortho_freq is the maximum mean grid-point frequency among orthosteric clusters."
    ),
    "The CoupledMD product is organized in three tiers.": (
        "The CoupledMD product is organized in three tiers. The planned DOI-linked archive will contain production trajectories, matched topologies and inputs, reduced visualization records, derived annotations, metadata tables, per-replica QC reports, a file-level SHA-256 manifest, code snapshots and licence documentation. The web portal at https://www.coupledmd.cn provides interactive browsing, filtering and per-system visualization with NGL21. The REST API, versioned under /api/v1/, exposes final-cohort system metadata, pocket records, gateway records and visualization assets. It filters system IDs against the 207-system final cohort; unresolved IDs and Gq_7E9W and Gq_7DWC have no release record."
    ),
    "The CoupledMD release comprises 208 GPCR–G-protein systems": (
        "The CoupledMD release comprises 207 GPCR–G-protein systems, 174 distinct receptor names, 173 mapped UniProt accessions and 310.5 µs of aggregate production sampling across 621 trajectories (Table 1; Fig. 1A). By GPCR class it contains 181 Class A and 26 Class B systems; by transducer it contains 95 Gi/o, 65 Gs, 41 Gq/11 and 6 G12/13 systems. Coverage is deliberately broad rather than uniform: it mirrors the composition of the experimental structural record, in which Gi/o- and Gs-coupled complexes are abundant and G12/13 complexes remain rare. Gs_8HTI is a consensus OR52c model without a canonical UniProt mapping and is retained with an explicit null accession. Gq_7E9W and Gq_7DWC are excluded, not flagged as cohort systems."
    ),
    "Figure 1 | Composition of the 208-system CoupledMD dataset.": (
        "Figure 1 | Composition of the 207-system CoupledMD dataset. (A) System counts by GPCR class and G-protein family. (B) Receptors represented with more than one G-protein family. (C) Family-resolved numbers of peptide-eligible systems and systems lacking an orthosteric-defining ligand. (D) Coverage of receptor identifiers: 174 receptor names and 173 mapped UniProt accessions; Gs_8HTI is the single unmapped consensus receptor model. Family colors are Gi/o, green; Gs, blue; Gq/11, orange; and G12/13, purple."
    ),
    "Figure 4 | Transmembrane-gateway opening across the dataset.": (
        "Figure 4 | Transmembrane-gateway opening across the dataset. (A) Open fractions for seven adjacent TM-helix interfaces in 207 systems, ordered by G-protein family. (B) Violin and box-plot summaries of the corresponding interface-specific open-fraction distributions. All 207 systems contain numerical records for all seven interfaces."
    ),
    "Gateway records are complete for all 208 systems": (
        "Gateway records are complete for all 207 systems and contain four metrics for each of seven adjacent helix pairs: penetration, penetration_p90, open_fraction and occupancy, with replica values and confidence intervals. Figure 4 displays open_fraction, whereas Supplementary Figure S2 defines the complete record and its aggregation."
    ),
    "The harmonized receptor-core/interface audit contains 624 replica rows.": (
        "The harmonized receptor-core/interface audit contains 621 replica rows. Figure 5 uses 618 distinct, quantitatively available replicas from 206 systems; the three Gs_8HTI replicas lack the canonical receptor mapping required for this calculation."
    ),
    "The CoupledMD boundary was enforced against the 222-record working inventory.": (
        "The CoupledMD boundary was enforced against the 222-record working inventory. All 207 included systems have three selected 500-ns replicas and final-cohort membership (Fig. 1A,D). Thirteen systems remain unresolved: eight have PBC/trajectory-continuity evidence, four component-continuity evidence and one incomplete-trajectory evidence. Gq_7E9W and Gq_7DWC are separately excluded: Gq_7E9W as a non-GPCR duplicate/mislabel and Gq_7DWC as a duplicate source identity of Gq_8DWC. A programmatic audit confirms 207 unique release IDs, 621 selected replicas, 310,500 ns aggregate sampling and no unresolved or excluded identifier in the final API cohort; record-level evidence is provided in Supplementary Data S2."
    ),
    "The pocket layer was validated using orthosteric-site recovery as a positive control.": (
        "The pocket layer was validated using orthosteric-site recovery as a positive control. All 207 systems have a pocket-analysis record; 205 contain at least one detected pocket and Gi_7YK6 and Gi_8YIC are explicit zero-pocket results. The positive-control denominator is the 58 peptide-ligand systems: 49/58 (84.5%) recover an orthosteric cluster at the 0.85 grid-frequency threshold (Fig. 3A). Family-resolved recovery is 16/18 Gi/o, 15/18 Gs and 18/22 Gq/11; G12/13 has no eligible peptide-defined system and is not applicable. The remaining 150 systems lack the defining positive-control ligand and are not counted as failures. These results validate a derived structural annotation, not druggability or binding mechanism."
    ),
    "For every final system, the seven expected adjacent TM interfaces are present": (
        "For every final system, the seven expected adjacent TM interfaces are present with one numerical value for each of four metrics, three contributing replica summaries and bounded confidence intervals. The open_fraction values lie between 0 and 1 and are complete across the 207 × 7 system-interface matrix shown in Figure 4. Identity keys are fixed by helix pair; missing records, if introduced in a future version, must be encoded as null with a reason rather than as zero."
    ),
    "The structural-validation audit contains one row for each of 624 selected replicas": (
        "The structural-validation audit contains one row for each of 621 selected replicas and uses exactly 1,001 evenly spaced observations for every quantitative record. After excluding the three explicit Gs_8HTI nulls, all 618 plotted records contain finite TM-core RMSD, Gα-interface RMSD and contact-retention summaries (Fig. 5). The distributions therefore report validation coverage and variability without silently converting unavailable or duplicate records into numerical observations."
    ),
    "The reduced visualization tier was audited independently because it is a lossy derivative intended only for inspection.": (
        "The reduced visualization tier was audited independently because it is a lossy derivative intended only for inspection. For all 207 systems, 40 sampled frames per record were checked for topology-trajectory atom-count agreement, blank PDB element fields, box consistency, intra-chain backbone breaks, inter-chain splitting and coordinate scatter. The audit returned 205 systems classified PBC OK and three WARN for minor coordinate scatter only, with seven scatter frames in total and no atom-count, blank-element, box-mismatch or chain-break failures. Frame counts are 2,500 for 205 systems, 2,501 for two systems and 200 for Gs_3SN6. This audit validates sampled reduced frames only and does not validate unsampled reduced frames or replace production-trajectory QC."
    ),
    "The CoupledMD web portal is available at https://www.coupledmd.cn": (
        "The CoupledMD web portal is available at https://www.coupledmd.cn and API documentation at https://www.coupledmd.cn/api/docs. The current public access layer exposes the final 207-system metadata and derived records, including one reduced representative PDB/XTC visualization pair per included system. Complete primary trajectories, matched topologies, inputs, checksums and the frozen file manifest are being prepared for DOI-linked archival deposition. Until that deposition, this manuscript makes no claim of archive completeness, DOI availability, direct raw-trajectory download or public release of all 621 primary trajectories."
    ),
}


def replace_paragraphs(document: Document) -> None:
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        for prefix, replacement in REPLACEMENTS.items():
            if text.startswith(prefix):
                paragraph.text = replacement
                break


def update_tables(document: Document) -> None:
    # Table 1: class/family composition
    table1 = document.tables[1]
    assert table1.rows[0].cells[0].text.strip() == "GPCR class"
    updates = {
        (3, 2): "39",     # Class A Gq/11 systems
        (9, 2): "207",    # Total systems
        (9, 4): "310.5",  # Total sampling
    }
    for (row, col), value in updates.items():
        table1.rows[row].cells[col].text = value

    # Table 2: archive hierarchy
    table2 = document.tables[2]
    assert table2.rows[0].cells[0].text.strip() == "Path"
    for row in table2.rows:
        if "System-level metadata for the 208 included systems" in row.cells[1].text:
            row.cells[1].text = "System-level metadata for the 207 included systems"


def configure_tables(document: Document) -> None:
    for table in document.tables:
        for row_number, row in enumerate(table.rows):
            properties = row._tr.get_or_add_trPr()
            if properties.find(qn("w:cantSplit")) is None:
                properties.append(OxmlElement("w:cantSplit"))
            if row_number == 0 and properties.find(qn("w:tblHeader")) is None:
                header = OxmlElement("w:tblHeader")
                header.set(qn("w:val"), "true")
                properties.append(header)


def validate_text(document: Document) -> None:
    text = "\n".join(p.text for p in document.paragraphs)
    forbidden = [
        "208 active-state systems",
        "208 GPCR–G-protein systems",
        "208 included systems",
        "all 208 systems",
        "All 208 systems",
        "208-system final cohort",
        "208-system CoupledMD dataset",
        "208 systems contain",
        "208 × 7",
        "final 208-system",
        "624 production trajectories",
        "624 trajectories",
        "624 replica rows",
        "624 selected replicas",
        "312.0 µs",
        "312,000 ns",
        "182 Class A",
        "42 Gq/11",
    ]
    for phrase in forbidden:
        assert phrase not in text, f"forbidden phrase found: {phrase!r}"

    required = [
        "207 active-state systems",
        "207 GPCR–G-protein systems",
        "310.5 µs",
        "621 trajectories",
        "181 Class A",
        "41 Gq/11",
        "Gq_7DWC is a duplicate source identity of Gq_8DWC",
        "207 included systems",
        "621 selected replicas",
        "310,500 ns",
        "207 × 7",
        "207-system final cohort",
    ]
    for phrase in required:
        assert phrase in text, f"required phrase missing: {phrase!r}"

    # Table checks
    table1 = document.tables[1]
    assert table1.rows[9].cells[2].text.strip() == "207"
    assert table1.rows[9].cells[4].text.strip() == "310.5"
    assert table1.rows[3].cells[2].text.strip() == "39"


def main() -> None:
    document = Document(DOCX)
    replace_paragraphs(document)
    update_tables(document)
    configure_tables(document)
    document.core_properties.modified = datetime.now(timezone.utc)
    validate_text(document)
    document.save(DOCX)
    print(f"Updated {DOCX}")


if __name__ == "__main__":
    main()
