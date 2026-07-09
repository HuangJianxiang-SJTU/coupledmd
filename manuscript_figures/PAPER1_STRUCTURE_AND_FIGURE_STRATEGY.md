# Paper 1 Structure and Figure Strategy

> CoupledMD Scientific Data Data Descriptor — paper-internal strategy memo.
> Status: draft for author discussion. All numbers below are taken from the working tracker, contact-sheet inspection, and research-plan extraction already in context. Anything still pending (DOI, SHA256, portal screenshot, benchmark values) is flagged in **Submission Gaps**.

---

## Executive Recommendation

**Recommended main figure set (5 figures):**

| # | Topic | Source asset | Paper 2 risk |
|---|---|---|---|
| Main 1 | Coverage and reuse landscape | `scidata_figure5_community_landscape` | Low |
| Main 2 | Data records and access model | `scidata_figure2_data_records` | Low |
| Main 3 | Technical validation (pocket recovery + benchmark) | `scidata_figure3_validation_ridgeline` | Low–Medium |
| Main 4 | QC and completeness (with held-back transparency) | `scidata_figure4_qc` | Medium (Panel A only) |
| Main 5 | Pocket/gene-annotation atlas as proxy resource | `scidata_figure6_drug_design_pocket_atlas` | Medium |

**Logic flow:** WHAT exists → HOW it is organized → WHETHER it is valid → WHETHER it is complete → HOW the community can reuse it. This is the canonical Scientific Data "dataset → trust → reuse" arc.

**Recommended main tables (3):** T1 (dataset summary), T2 (repository structure), T3 (metadata dictionary).

**Reserve for Paper 2:** Fig 7 (gateway atlas), Fig 8 (CGN barcode dynamics), Fig 9 (partner-switching reuse), and any panel that interprets alpha5, family-selective gateway, or partner-switching mechanism.

**Single most important rule:** Every caption must use only Paper 1-safe verbs (provides, annotates, catalogs, validates, supports, enables). No "reveals," "discovers," "explains," "drives," "determines," "mediates," "controls."

---

## Boundary Between Paper 1 and Paper 2

Paper 1 is a **Data Descriptor**. Its job is to describe what data exist, how they were produced, how they are organized, how they were validated, and how they can be accessed and reused. It is not the place to argue that any biological pattern is meaningful.

Paper 2 will own:

- Coupling mechanism claims (alpha5, gateway, partner switching)
- Family-selective or biased-signaling interpretation
- Allosteric pathway mechanism
- Causal explanation of coupling-state differences
- Druggability or mechanism-based site nomination as a discovery

Paper 1 may describe:

- Dataset composition (counts, families, coverage)
- Simulation protocol (force field, lipid, replicas, length)
- File organization (archive, portal, API)
- Annotation availability (GPCRdb positions, CGN segments, pocket clusters)
- Technical validation (orthosteric recovery, PBC audit, frame counts, held-back)
- Reuse **schematics** that show API or filter workflows without showing a result

Paper 1 may show derived annotations and example filters, but only as "what the resource provides." It must not show a difference plot between families and claim it means anything.

**The firewall test for every figure/table:** if the panel can be removed without losing the answer to "what is in the dataset, is it valid, and how do I reuse it," it is Paper 2 material. Conversely, if a panel only exists to show a biological difference, it does not belong in Paper 1 even if it is visually appealing.

---

## mdCATH Lessons Applied to CoupledMD

The mdCATH Scientific Data paper (Mirarchi, Giorgino, De Fabritiis, *Sci Data* 11, 1299, 2024) is a useful structural reference but is not a template to copy.

**Borrow:**

1. **Transparent exclusion funnel.** mdCATH Fig 1 walks the reader from designed inventory to release. CoupledMD should do the same: 222 designed → 208 clean-v1 → 14 held back, with held-back categories visible (Main Fig 4 Panel D, Supplementary Table S2).
2. **Distributions as technical health evidence.** mdCATH shows atoms/residues/length/RMSD distributions to demonstrate physical sanity. CoupledMD should show: pocket recovery distribution by family, pocket count distribution, reduced-trajectory frame count distribution, PBC audit outcomes. (Main Fig 3, Main Fig 4 Panels B–C.)
3. **Precise Data Records section.** mdCATH's Data Records specify file hierarchy, formats, fields, units, access routes. CoupledMD must do the same. (Main Fig 2, Main Tables T2 and T3.)
4. **Physically expected behavior as validation.** mdCATH validates against expected secondary-structure and compactness behavior. CoupledMD's analog is **orthosteric pocket recovery at 0.85 occupancy** — a known-good geometric feature that must be preserved if the simulation is sane. (Main Fig 3 Panel A.)
5. **Explicit license + access routes.** mdCATH is explicit about CC-BY and access. CoupledMD should match: CC-BY-4.0 for data, MIT for code, archive + portal + API as the three access routes.
6. **Usage examples, not biological conclusions.** mdCATH includes brief reuse examples. CoupledMD may include schematic reuse examples that show filter → download → analyze, but not biological results.

**Do not copy:**

- mdCATH is protein-domain-scale and temperature-series focused. CoupledMD is multi-chain functional complexes. A direct visual parallel would mislead readers.
- mdCATH's "physical sanity" checks are RMSD/Rg-based. CoupledMD's analog is pocket recovery, not whole-protein RMSD — whole-receptor RMSD over 1.5 µs of a multi-chain system is not informative and should not be invented.
- mdCATH's descriptor length and figure density are appropriate for a temperature-series dataset of 5–6k systems. CoupledMD is smaller (208 systems) and richer per system (multi-chain, multi-annotation). The descriptor should be tighter and more annotation-focused, not a copy of mdCATH's structure.

**Adaptation principle:** borrow the *discipline* of mdCATH (funnel, distributions, precise records, validation, license, usage examples) but adapt the *content* to CoupledMD's identity (multi-chain GPCR/G-protein complexes with GPCRdb/CGN annotation).

---

## Recommended Main Figures

### Main Figure 1 — Coverage and Reuse Landscape

- **Source file:** `scidata_figures/scidata_figure5_community_landscape.pdf/png`
- **One-sentence purpose:** Show what the clean-v1 release contains and what it enables for the GPCR community.
- **Panel-level content:**
  - **A.** Class × G-protein family coverage heatmap (Class A vs Class B, Gi/o vs Gs vs Gq/11 vs G12/13).
  - **B.** Receptors represented with more than one G-protein family in clean-v1.
  - **C.** Ligand-bearing vs apo systems by family.
  - **D.** Top receptors by system count, with bubble size encoding G-family breadth.
  - **E.** Release boundary: 208 included / 14 held back, with held-back categories.
- **Why it belongs in Paper 1:** Directly answers "what is in the dataset?" — the first question of any Data Descriptor. Communicates coverage breadth, ligand context, and release discipline in one figure. More readable than the circos.
- **Paper 2 risk:** Low. All panels are compositional/availability information.
- **Caption framing:** "Composition of the CoupledMD clean-v1 release by GPCR class, G-protein family, and ligand context, illustrating coverage breadth and receptor-level reuse opportunities for the GPCR community."
- **Required fixes before submission:**
  - Verify all family/class counts against the latest systems_master snapshot.
  - Ensure held-back categories in Panel E match Supplementary Table S2 exactly.
  - Ensure receptor labels in Panel D are legible at print size.
  - Replace any "promiscuous" wording with "represented in multiple G-protein families" or "multi-family coverage."

### Main Figure 2 — Data Records and Access Model

- **Source file:** `scidata_figures/scidata_figure2_data_records.pdf/png`
- **One-sentence purpose:** Show how CoupledMD is organized, archived, and accessed.
- **Panel-level content:**
  - **A.** Archival repository hierarchy (archive_root/manifest, metadata, systems/<system_id>/topology, trajectories/rep{1..3}, reduced, features, pocket, qc, code, web_api_snapshot).
  - **B.** Metadata schema per system (system, receptor, G protein, ligand/state, replicas, files, QC status).
  - **C.** Archive-first access model (stable archive → web portal → REST API).
  - **D.** Portal access layer screenshot (real PNG, not placeholder).
- **Why it belongs in Paper 1:** This is the canonical Scientific Data figure. Without it, the descriptor fails the "can I find and reuse your data?" test.
- **Paper 2 risk:** Low. Pure infrastructure.
- **Caption framing:** "Repository organization, metadata schema, and three-tier access model of CoupledMD. The archive is the stable citable record; the portal and REST API provide browse, visualization, and programmatic access."
- **Required fixes before submission:**
  - **Blocker:** Replace placeholder portal screenshot with a real PNG showing search, system page, viewer, download, and at least one API response. See Submission Gaps §1.
  - Confirm archive hierarchy in Panel A matches the final archive layout (post-freeze).
  - Confirm metadata field names in Panel B match Main Table T3 exactly.
  - Replace `[repository name, accession or DOI pending]` with the final DOI/accession wording once the archive is minted.

### Main Figure 3 — Technical Validation

- **Source file:** `scidata_figures/scidata_figure3_validation_ridgeline.pdf/png`
- **One-sentence purpose:** Show that the simulations preserve functionally relevant features and produce stable derived annotations.
- **Panel-level content:**
  - **A.** Ridgeline plot of best orthosteric-pocket frequency per system, family-separated, with the 0.85 recovery threshold marked. Family recovery rates (Gi/o 72.5%, Gs 76.1%, Gq/11 83.3%, G12/13 66.7%) annotated.
  - **B.** Pocket count distribution by family (raw points + median + IQR).
  - **C.** Dataset benchmark: CoupledMD systems/aggregate microseconds vs GPCRmd and mdCATH on log scale.
- **Why it belongs in Paper 1:** This is the validation that says "you can trust the simulation outputs." Pocket recovery is a known-good geometric sanity check; pocket-count stability shows the pocket-detection pipeline is not noisy.
- **Paper 2 risk:** Low–Medium. Low for panels A–B. Medium for Panel C if benchmark numbers are wrong or if readers infer a comparison claim. The pocket-recovery panel must not be phrased as "pocket dynamics explain receptor function."
- **Caption framing:** "Orthosteric-pocket recovery across the clean-v1 release, shown as best per-system orthosteric-pocket frequency by family (A), per-system pocket count by family (B), and dataset-scale comparison with two related GPCR and general-protein MD resources (C). The 0.85 frequency threshold is used to define recovery."
- **Required fixes before submission:**
  - **Blocker:** Verify GPCRmd and mdCATH aggregate systems and microseconds before publication. If the numbers cannot be confirmed with citations, demote Panel C to Supplementary Fig S2 and keep Main Fig 3 to panels A–B.
  - Add a sentence in the caption that explicitly disclaims any interpretation of pocket dynamics.
  - Ensure pocket-count panel does not show mean or median values that imply family-level mechanism.

### Main Figure 4 — QC and Completeness

- **Source file:** `scidata_figures/scidata_figure4_qc.pdf/png`
- **One-sentence purpose:** Demonstrate transparency about what was held back, what passed PBC audit, and what is complete.
- **Panel-level content:**
  - **A.** TM-gateway open-fraction heatmap, 208 systems × 7 TM helix-pair gateway interfaces, grouped by family.
  - **B.** Reduced-trajectory PBC audit donut (205 OK, 3 WARN, 0 hard failures).
  - **C.** Reduced-trajectory frame count distribution (205 systems at 2500, 2 at 2501, 1 at 200).
  - **D.** Held-back cohort breakdown (14 of 222) and visualization-flag table.
- **Why it belongs in Paper 1:** Scientific Data reviewers reward transparent exclusion reporting. This figure shows the held-back cohort (14/222 = 6.3%) and the reason categories, which is a strength, not a weakness.
- **Paper 2 risk:** Medium because of Panel A. The gateway heatmap, if interpreted mechanistically ("Gi family shows more open TM3-TM4"), becomes a Paper 2 result. The caption must frame it as annotation availability and conformational-range coverage.
- **Caption framing:** "QC and completeness summary of the clean-v1 release. (A) Derived TM-gateway open-fraction annotations are included as machine-readable records across 208 systems; family grouping is shown for organizational convenience. (B) Reduced-trajectory PBC audit outcomes. (C) Reduced-trajectory frame counts. (D) Held-back cohort from the 222 designed systems, with categories of exclusion; see Supplementary Table S2 for the full list. Biological interpretation of panel A is outside the scope of this Data Descriptor."
- **Required fixes before submission:**
  - **Blocker:** Rewrite Panel A caption to make explicit that the gateway panel is record availability, not biological interpretation. The above caption language is acceptable.
  - Confirm family grouping in Panel A uses the same family definitions as Main Fig 1.
  - Ensure the held-back donut in Panel D matches the categories in Supplementary Table S2.
  - Add a one-sentence note in the Methods that gateway annotations are derived records and are not used here as a biological conclusion.

### Main Figure 5 — Pocket/Gene-Annotation Atlas

- **Source file:** `scidata_figures/scidata_figure6_drug_design_pocket_atlas.pdf/png`
- **One-sentence purpose:** Show that CoupledMD provides rich, GPCRdb-anchored pocket annotations useful for downstream drug-design workflows.
- **Panel-level content:**
  - **A.** Consensus druggable pocket clusters by zone (TM-core allosteric, intracellular allosteric, extracellular vestibule).
  - **B.** Pocket-zone cluster-member counts.
  - **C.** Reusable GPCRdb-position anchors appearing in pocket cluster cores.
  - **D.** Orthosteric recovery by family (overlap with Main Fig 3 Panel A, restated as a proxy-resource view).
  - **E.** Example receptor names with high pocket-cluster coverage, framed as "nomination examples" not "discoveries."
- **Why it belongs in Paper 1:** This is the panel that sells the GPCR drug-design reuse value. Without it, the descriptor reads as "yet another MD dataset." With it, the descriptor shows unique annotation richness that no other GPCR MD resource currently provides at this scale.
- **Paper 2 risk:** Medium. The risk is that "druggable pocket clusters" reads as a discovery. Mitigation: reframe as "annotation distribution and proxy summary."
- **Caption framing:** "Consensus pocket annotations distributed with CoupledMD, summarized by zone (A), zone membership counts (B), reusable GPCRdb-position anchors (C), and orthosteric recovery as a proxy-validation view (D). Example receptor names with broad pocket-cluster coverage (E) are provided to illustrate reuse potential for prioritization workflows. Pocket clusters and proxy scores are derived annotations; they are not experimental druggability validation. Mechanistic interpretation is outside the scope of this Data Descriptor."
- **Required fixes before submission:**
  - Replace any wording like "druggable sites discovered" with "consensus pocket annotations distributed."
  - Replace "selective" or "family-selective" with "family-resolved."
  - Add a footnote: proxy druggability scores summarize pocket size, occupancy, and lining features; they are not experimental validation.
  - Ensure GPCRdb position numbers in Panel C are correct against GPCRdb generic numbering at the date of submission.

---

## Recommended Supplementary Figures

| Supp Fig | Source asset | Purpose | Paper 2 risk |
|---|---|---|---|
| S1 | `scidata_figure1_overview_circos` | Coupling landscape circos (alt to Main 1) | Low |
| S2 | `scidata_figure10_portal_archive_coverage` (panels A–C) | Portal file availability, two-tier data product, REST surface | Low |
| S3 | Portal walkthrough screenshots | Real screenshots: search, system page, viewer, API JSON example | Low |
| S4 | `scidata_figure4_qc` Panel A extended | Extended gateway annotation coverage (without family interpretation) | Medium |
| S5 | `scidata_figure8_gprotein_barcode` reduced to annotation coverage only | CGN annotation coverage and segment-class distribution, family-dynamics stripped | Medium |
| S6 | Held-back cohort extended view | Per-system reasons and timeline of exclusion | Low |
| S7 | Reduced-trajectory audit extended | Per-system scatter frames and warnings table | Low |

**Supplementary Figure notes:**

- **S1 (circos).** Keep only if Main Fig 1 is the community landscape and the authors want a richer coupling overview in supplement. Strip all mechanistic language.
- **S2 (portal/archive coverage).** Safe infrastructure figure. Verify final archive size and checksum counts before submission.
- **S3 (portal walkthrough).** Critical for "how do I use it?" Replace placeholder with real screenshots. See Submission Gaps §1.
- **S4 (extended gateway).** Include only if stripped of family-level interpretation. Otherwise drop.
- **S5 (CGN barcode).** Include only as annotation-coverage view; drop the dynamics heatmap or reframe it as record-availability. Family-resolved RMSF must not appear.
- **S6, S7.** Pure transparency content. Always safe.

---

## Figures to Reserve for Paper 2

### Reserved: `scidata_figure7_gateway_atlas`

- **Why:** Family-resolved gateway open fractions, per-system gateway distributions, and replica spreads are exactly the kind of analysis Paper 2 needs to make claims about TM-gateway mechanism. Showing this in Paper 1 pre-empts Paper 2.
- **Risk if included in Paper 1:** High.
- **Paper 2 reuse:** Paper 2 should rebuild this figure as a **result figure** with mechanistic framing, and cite CoupledMD as the source.

### Reserved: `scidata_figure8_gprotein_barcode` (full version)

- **Why:** Family-resolved RMSF by CGN segment, contact persistence heatmaps, and the per-position dynamic annotation panel are G-protein mechanism material. CGN segment labels like "selectivity-determining" are mechanistic language.
- **Risk if included in Paper 1:** Medium–High.
- **Paper 2 reuse:** Paper 2 should own the family-dynamic interpretation of CGN segments and any alpha5-related claims.
- **Compromise:** If authors want to demonstrate annotation coverage in Paper 1, include only the per-system CGN-position-coverage histogram from Panel E, stripped of family-resolved dynamics. Do not include Panels A–D.

### Reserved: `scidata_figure9_partner_switching_reuse`

- **Why:** This figure explicitly shows named receptors (NMUR2, FFAR4, P2Y1R, GHSR, OX2R, CCKAR) in a partner-switching geometry comparison. It is the highest-risk figure in the entire package.
- **Risk if included in Paper 1:** Very high. Effectively publishes the headline result of Paper 2.
- **Paper 2 reuse:** This figure should be the central or supporting figure of Paper 2.
- **Compromise:** A generic Usage Notes schematic without data points, receptor names, alpha5 metrics, or tilt comparisons is acceptable in Paper 1 — but it would be a different figure, not Fig 9 as currently drawn.

### Additional reserved material

- Any future alpha5 tilt vs coupling-geometry plot.
- Any family-selective gateway interpretation.
- Any causal claim about coupling-state differences.
- Any "novel druggable site" claim based on the pocket atlas.

---

## Recommended Main Tables

### Main Table 1 — Dataset summary by class/family

- **File:** `tables/scidata_T1_dataset_summary_clean_v1.csv`
- **Purpose:** Compact at-a-glance numbers: systems, unique receptors, sampling, replicas, length, notes — broken down by class and G-protein family.
- **Paper 2 risk:** Low.
- **Finalization needs:**
  - Confirm all numbers against latest systems_master snapshot.
  - Confirm sampling microseconds (312 µs aggregate).
  - Confirm replica length (3 × 500 ns for standard systems).
  - Note any non-standard-length systems explicitly.

### Main Table 2 — Repository structure

- **File:** `tables/scidata_T2_repository_structure.csv`
- **Purpose:** Authoritative file-hierarchy table for the archive (manifest, metadata, systems, topology, trajectories, reduced, features, pocket, qc, code, web_api_snapshot). Companion to Main Fig 2 Panel A.
- **Paper 2 risk:** Low.
- **Finalization needs:**
  - Update to match final archive layout after archive freeze.
  - Include approximate file counts/sizes per folder if possible.
  - Include format notes (e.g., XTC for trajectories, NPZ for pocketgrids, JSON for gateways/gprotein).

### Main Table 3 — Metadata dictionary

- **File:** `tables/scidata_T3_metadata_dictionary.csv`
- **Purpose:** Field-by-field definition of system metadata: system_id, pdb_id, receptor_name, receptor_uniprot, receptor_gene, gpcr_class, g_protein_family, g_alpha_subtype, ligand fields, replica fields, force field, lipid, provenance, trajectory type, QC/file fields.
- **Paper 2 risk:** Low.
- **Finalization needs:**
  - Fill any missing GPCRdb ID / state / ligand-ID fields.
  - Confirm field names match the per-system JSON keys in the archive.
  - Add units where applicable (ns, Å, K).

---

## Recommended Supplementary Tables

| Supp Table | File | Purpose | Finalization needs |
|---|---|---|---|
| S1 | `scidata_S1_included_systems_clean_v1.csv` | Full 208-system list | Verify against latest snapshot |
| S2 | `scidata_S2_held_back_systems.csv` | 14 held-back systems with reasons | Verify reasons are accurate and publishable |
| S3 | `scidata_S3_file_manifest_checksum_checklist.csv` | Internal manifest/checksum checklist | Replace with true final manifest when archive is frozen |
| S4 | `scidata_S4_per_system_pockets_clean_v1.csv` | Per-system pocket summary | Verify |
| S5 | `scidata_S5_gateway_per_system_clean_v1.csv` | Per-system gateway summary | Mechanism-risk caution; consider reserving |
| S6 | `scidata_S6_portal_api_endpoints.csv` | Live portal/API endpoint inventory | Refresh against current portal at submission |
| S7 | `scidata_S7_website_feature_checklist.csv` | Website feature checklist | Internal — likely not submitted |
| S8 | `scidata_S8_archive_manifest_clean_v1_from_metadata.csv` | Archive manifest | Needs final checksums |
| S9 | `scidata_S9_portal_file_manifest_clean_v1.csv` | Portal/API manifest | Binary checksums pending |

**Notes:**

- **S5 (per-system gateway).** Strongly consider not including in Paper 1 if Paper 2 protection is paramount. If included, the table caption must say "derived records; biological interpretation outside scope."
- **S3, S7.** Internal documents; replace or drop before submission.
- **S8, S9.** Needs final archive checksum freeze before publication.

---

## Manuscript Structure

Scientific Data section skeleton, adapted to CoupledMD.

### Title

- **Key message:** Concise, identifies resource, identifies domain.
- **Recommended:** "CoupledMD: a molecular dynamics dataset of GPCR/G-protein complexes."
- **Alternative:** "A standardized molecular dynamics resource of GPCR/G-protein complexes for community reuse."
- **Avoid:** mechanism, selectivity, bias, allosteric, partner switching, druggable discovery.

### Abstract

- **Structure (≤ 250 words):**
  1. GPCR/G-protein complexes are central to signaling and drug discovery.
  2. Standardized multi-chain MD resources at this scale remain limited.
  3. CoupledMD clean-v1: 208 systems, 174 receptors, 312 µs, 3 × 500 ns replicas, POPC/CHARMM36m.
  4. Records include trajectories, reduced visualization files, metadata, pocket/GPCRdb annotations, gateway records, G-protein CGN records, QC, manifests.
  5. Technical validation: orthosteric pocket recovery, PBC audit, frame-count completeness.
  6. Access: stable archive + www.coupledmd.cn + REST API, open access.
  7. Reuse: benchmarking, method development, GPCR community and drug-design workflows.
- **Avoid:** reveals, discovers, explains, mechanism, selectivity, bias, partner switching.

### Background & Summary

- **Key message:** GPCRs are major drug targets; multi-chain GPCR/G-protein MD is a resource gap; CoupledMD fills it; this is a data descriptor, not a mechanism paper.
- **Required content:**
  - GPCR drug-target landscape (brief).
  - Existing MD resources (GPCRmd; mdCATH as structural inspiration, not competitor).
  - CoupledMD positioning: multi-chain functional complexes with GPCRdb/CGN annotation.
  - Three reuse questions (what is in it / can I trust it / how do I reuse it).
  - Scope statement: descriptor, not mechanistic interpretation.
- **Figures/tables:** Main Fig 1 (referenced for scope statement).
- **Avoid:** claim of novel mechanism, claim of novel selectivity determinants, claim of novel allosteric site.

### Methods

- **Required subsections (each short, descriptive):**
  1. System selection and clean-v1 cohort definition.
  2. Structure sourcing and preparation.
  3. GPCR/G-protein/ligand annotation.
  4. Membrane, solvent, ions, force field.
  5. Equilibration and production protocol.
  6. Trajectory processing and reduced visualization trajectories.
  7. Pocket detection and GPCRdb mapping.
  8. Gateway and derived annotation generation.
  9. G-protein CGN annotation.
  10. QC gates and held-back criteria.
  11. Archive, portal, and API manifest generation.
- **Avoid:** mechanistic interpretation of any derived metric. Methods describes *how* annotations are computed, not *what they mean*.

### Data Records

- **Key message:** Here is exactly what is in the archive, what is in the portal, and how to get both.
- **Required content:**
  - Archive hierarchy (Main Fig 2 Panel A, Main Table T2).
  - Metadata dictionary (Main Table T3).
  - Per-system folder structure.
  - Trajectories + reduced visualization files + derived files (pocket, gateway, gprotein, pocketgrid).
  - Manifests and checksums.
  - Portal/API surface.
  - DOI/accession (placeholder until archive is minted).
- **Figures/tables:** Main Fig 2, Main Tables T2, T3, Supp Tables S1, S8, S9, S6.
- **Avoid:** any statement that a derived annotation "shows" a biological pattern.

### Technical Validation

- **Key message:** The release is honest about what passed and what did not.
- **Required content:**
  - Clean-v1 inclusion criteria and held-back transparency (Supp Table S2).
  - Orthosteric pocket recovery at 0.85 (Main Fig 3 Panel A).
  - Pocket-count distribution stability (Main Fig 3 Panel B).
  - Reduced-trajectory PBC audit (Main Fig 4 Panel B, Supp Table T8).
  - Frame counts (Main Fig 4 Panel C, Supp Table T8b).
  - File availability (Supp Tables S8, S9).
  - Limitations section.
- **Figures/tables:** Main Figs 3 and 4, Supp Tables T4, T4a, T5, T8, T8a, T8b, S2.
- **Avoid:** mechanistic claims from gateway or pocket annotations. Validation is physical/technical, not biological.

### Usage Notes

- **Key message:** Here is how a GPCR researcher or computational chemist would actually use this resource.
- **Required content:**
  - Browse/filter systems (receptor, family, ligand).
  - Select systems for download.
  - Use API for metadata and derived annotations.
  - Use GPCRdb/CGN mappings for residue-level comparison.
  - Cite archive DOI and paper.
  - Living portal vs stable archive distinction.
  - Limitations: 14 held back; binary checksums pending; proxy druggability scores not experimentally validated; mechanistic interpretation outside scope.
- **Safe reuse examples (filter-only, no result):**
  - "Filter all Class A / Gi systems."
  - "Download reduced trajectory for visualization."
  - "Retrieve pocket annotations for a receptor."
  - "Compare metadata availability across families."
  - "Use GPCRdb generic numbers to align pocket-lining residues."
- **Figures/tables:** Main Fig 2 Panel D, Supp Fig S3.
- **Avoid:** any example that produces a result plot. Workflow only.

### Code Availability

- **Required content:**
  - Figure-generation scripts.
  - API schema snapshot (OpenAPI).
  - Notebooks if any.
  - Repository URL.
  - License: MIT (or compatible) for code.

### Data Availability

- **Required content:**
  - Stable archive DOI/accession (pending wording).
  - Web portal URL: www.coupledmd.cn.
  - API docs URL.
  - License: CC-BY-4.0 for data.
  - Versioning: clean-v1.
  - Checksum manifest reference.

### Acknowledgements / Author Contributions / Competing Interests

- Standard Scientific Data boilerplate.
- **Competing interests:** declare or explicitly state none.
- **Author contributions:** use CRediT taxonomy; keep separate from Paper 2.

---

## Safe Language Bank

### Safe verbs

provides, includes, contains, records, annotates, summarizes, catalogs, lists, exposes, distributes, supports, enables, facilitates, benchmarks, validates, documents, reports, allows, retrieves, generates (for derived records only, not for biological findings), derives (for annotation derivation).

### Safe phrases

- "technical validation"
- "derived annotation"
- "annotation availability"
- "annotation coverage"
- "machine-readable record"
- "proxy metric"
- "not experimentally validated"
- "hypothesis-generating"
- "outside the scope of this Data Descriptor"
- "for downstream mechanistic studies"
- "for future analyses"
- "reproduces expected geometric features"
- "preserves known structural features"
- "clean-v1 release"
- "transparent held-back cohort"
- "the resource provides"
- "the dataset enables"
- "the annotation summarizes"
- "as an illustration of reuse"
- "as a workflow example"

### Safe figure/table language

- "Coverage of clean-v1 systems by class and family."
- "Family-resolved distribution of derived pocket-recovery frequency."
- "Per-system pocket count distribution, family-grouped."
- "Repository hierarchy, metadata schema, and access model."
- "Reduced-trajectory PBC audit outcomes."
- "Frame-count completeness across clean-v1."
- "Held-back cohort and exclusion categories from the 222 designed systems."
- "Consensus pocket annotations distributed with the resource."
- "GPCRdb-position anchors reused across pocket cluster cores."

---

## Unsafe Language Bank (Reserve for Paper 2)

### Verbs to avoid

reveals, discovers, explains, demonstrates mechanism, drives, determines, mediates, controls, encodes, governs, underlies, causes, produces (in a biological sense — fine for "produces a record").

### Noun phrases to avoid

- "selectivity mechanism"
- "bias mechanism"
- "partner-switching mechanism"
- "allosteric pathway"
- "family-specific mechanism"
- "novel druggable site discovered"
- "selectivity-determining pocket/residue/position"
- "alpha5 rearrangement explains"
- "gateway opening explains"
- "coupling-geometry determinant"
- "allosteric mediator"
- "functional consequence"
- "causal role"

### Sentence frames to avoid

- "These data reveal that..."
- "We show that X drives Y..."
- "This pocket mediates..."
- "This gateway controls..."
- "The CGN barcode identifies selectivity-determining positions..."
- "Multi-family receptors exhibit promiscuous coupling..."
- "Partner switching is driven by..."

### If a phrase sounds mechanistic, it is Paper 2.

Apply this test to every caption and every result sentence. If the phrase is mechanistic, move it to Paper 2.

---

## Safe Caption Templates

Use these as the starting point for each main figure caption. Adapt to final numbers but keep the verbs.

### Main Figure 1 — Coverage and Reuse Landscape

> **Figure 1. Coverage and reuse landscape of the CoupledMD clean-v1 release.** (A) Class × G-protein family coverage across 208 systems. (B) Receptors represented with more than one G-protein family in clean-v1. (C) Ligand-bearing vs apo systems by family. (D) Top receptors by system count, with bubble size encoding G-protein-family breadth. (E) Release boundary: 208 included / 14 held back of 222 designed systems; held-back categories are detailed in Supplementary Table S2. Composition is shown for resource description; biological interpretation of family or ligand patterns is outside the scope of this Data Descriptor.

### Main Figure 2 — Data Records and Access Model

> **Figure 2. Repository organization, metadata schema, and three-tier access model of CoupledMD.** (A) Archive hierarchy (manifest, metadata, systems, topology, trajectories, reduced, features, pocket, qc, code, web_api_snapshot). (B) Per-system metadata schema (system, receptor, G protein, ligand/state, replicas, files, QC status). (C) Archive-first access model: stable archive is the citable record; web portal (www.coupledmd.cn) and REST API provide browse, visualization, and programmatic access. (D) Portal access layer showing system browse, viewer, download, and API endpoints. File formats and field definitions are detailed in Main Tables T2 and T3.

### Main Figure 3 — Technical Validation

> **Figure 3. Technical validation of the CoupledMD clean-v1 release.** (A) Best per-system orthosteric-pocket frequency by G-protein family; the dashed line marks the 0.85 recovery threshold. (B) Per-system pocket count distribution by family (points: individual systems; box: median and interquartile range). (C) Dataset-scale comparison of systems and aggregate sampling against two related GPCR and general-protein MD resources (numbers to be verified at submission; see Supplementary Fig S2 if demoted). Validation is technical — it demonstrates preservation of known structural features and stability of derived annotations — and does not interpret biological mechanism.

### Main Figure 4 — QC and Completeness

> **Figure 4. QC and completeness summary of the CoupledMD clean-v1 release.** (A) Derived TM-gateway open-fraction annotations across 208 systems, grouped by G-protein family for organizational convenience; family-resolved differences in panel A are not interpreted here. (B) Reduced-trajectory PBC audit outcomes (205 OK, 3 WARN, 0 hard failures). (C) Reduced-trajectory frame counts (205 systems at 2500 frames, 2 at 2501 frames, 1 at 200 frames). (D) Held-back cohort (14 of 222 designed systems) and visualization-flag table; full reasons are listed in Supplementary Table S2. Biological interpretation of the gateway annotation is outside the scope of this Data Descriptor.

### Main Figure 5 — Pocket/Gene-Annotation Atlas

> **Figure 5. Consensus pocket annotations distributed with CoupledMD.** (A) Consensus pocket clusters summarized by zone (TM-core allosteric, intracellular allosteric, extracellular vestibule). (B) Cluster-member counts by zone. (C) Reusable GPCRdb-position anchors appearing in pocket cluster cores. (D) Orthosteric recovery as a proxy-validation view. (E) Example receptors with broad pocket-cluster coverage, shown as workflow illustrations. Pocket clusters and proxy scores are derived annotations and are not experimental druggability validation; biological or pharmacological interpretation is outside the scope of this Data Descriptor.

---

## Submission Gaps

### Hard blockers (must be resolved before submission)

1. **Portal screenshot for Main Fig 2 Panel D.**
   The current figure has a placeholder. A real PNG must be produced showing search/filter, system page, NGL viewer, download UI, and at least one API JSON response.
   *Owner action:* capture screenshots from www.coupledmd.cn and embed; record screenshot date.

2. **DOI / accession wording.**
   The Data Availability section and the Methods "Data Records" subsection still contain `[repository name, accession or DOI pending]`.
   *Owner action:* mint or reserve DOI; replace placeholder with final string.

3. **Production archive frame counts.**
   Final per-system reduced-trajectory frame counts and any non-standard counts must be confirmed against the production archive, not against the metadata snapshot.
   *Owner action:* run the freeze audit; update Supplementary Table T8 and Main Fig 4 Panel C.

4. **SHA256 checksums.**
   Final per-file checksums for the production archive and the binary/large portal files are pending. Current T6 / S8 / S9 are metadata-derived.
   *Owner action:* compute and publish final SHA256 manifest; embed in archive root.

5. **Final archive manifest.**
   Current S8 is from metadata. Replace with the true final archive manifest (file paths, sizes, checksums) once the archive is frozen.
   *Owner action:* freeze archive layout; regenerate manifest.

6. **Benchmark numbers in Main Fig 3 Panel C.**
   GPCRmd and mdCATH system counts and aggregate microseconds must be verified against current public resources with citations. If not verifiable, demote Panel C to Supplementary Fig S2 and keep Main Fig 3 to panels A–B.

### Soft gaps (should be resolved; non-blocking if noted)

7. **Live portal/API confirmation.**
   Confirm www.coupledmd.cn status and capture OpenAPI snapshot date before submission.

8. **Missing portal files.**
   Resolve any known missing derived outputs (e.g., Gq_7E9W pockets_gpcrdb, Gi_6D9H contacts). Either regenerate or document the gap in Supplementary Table S7/S9.

9. **Caption rewrite pass.**
   Every figure and table caption must be rewritten to use only Safe Language Bank verbs. Especially Main Fig 4 Panel A and Main Fig 5 caption.

10. **Held-back reasons verification.**
    Confirm Supplementary Table S2 reasons are accurate and publishable (no internal jargon, no unfinished work).

11. **GPCRdb generic numbering currency.**
    Confirm GPCRdb generic numbers used in Main Fig 5 Panel C and metadata dictionary match GPCRdb at the date of submission.

12. **Reconciliation of cohort numbers.**
    Some internal documents still cite 222 systems / 332.3 µs; the clean-v1 release is 208 systems / 312 µs. All captions, tables, and the abstract must be reconciled to 208 / 312 before submission.

### Internal-only (do not submit)

- Supplementary Table S3 (file manifest checklist, internal).
- Supplementary Table S7 (website feature checklist, internal).
- All draft SVGs and unsynchronized figure variants in `scidata_figures/`.

---

## Final Recommendation Summary

- **Main figures (5):** Fig 5 community landscape, Fig 2 data records, Fig 3 validation, Fig 4 QC, Fig 6 pocket atlas (with strict caption discipline).
- **Main tables (3):** T1 dataset summary, T2 repository structure, T3 metadata dictionary.
- **Supplementary figures:** circos (Fig 1) as alt to Main 1; portal/archive (Fig 10) split into Supp S2 and S3; reduced gateway (Fig 7) and reduced CGN (Fig 8) only if stripped of dynamics; held-back and audit tables extended to S6 and S7.
- **Reserve for Paper 2:** Fig 7 full, Fig 8 full, Fig 9 in entirety, any alpha5 / partner-switching / family-selective gateway panel.
- **Hard blockers:** portal screenshot, DOI/accession, production archive frame counts, SHA256 checksums, final archive manifest, benchmark number verification.
- **Single most important rule:** every caption must pass the firewall test (no mechanism language). Apply this test to every figure/table before submission.

---

*End of strategy memo. All numbers and asset references are taken from the working context; verification actions are listed in Submission Gaps.*