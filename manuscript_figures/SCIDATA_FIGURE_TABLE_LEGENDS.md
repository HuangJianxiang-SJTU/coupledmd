# Draft Scientific Data Figure and Table Legends

## Main Figures

**Figure 1. Clean-v1 dataset composition and construction workflow.**  
(A) Quality-control funnel from the current 222-system inventory to the 208-system clean-v1 release used for the initial Scientific Data submission. Held-back systems are separated because of nonstandard trajectory length, incomplete or temporary source files, nonstandard replica counts, or missing processed outputs. (B) GPCR class distribution in the clean-v1 cohort. (C) Distribution of G-protein coupling families across the clean-v1 cohort. (D) Structural provenance and sampling summary. All clean-v1 systems contain three 500 ns replicas, for 312.0 microseconds of aggregate sampling. (E) Workflow from structure selection and standardized preparation to simulation, trajectory processing, archived records and portal/API access.

**Figure 2. Data records, repository organization and access model.**  
(A) Proposed archival hierarchy for the Scientific Data record, including manifest, metadata, topology, production trajectories, reduced visualization trajectories, processed features, pocket outputs, QC reports, code and API snapshots. (B) Metadata schema linking systems to receptor, G-protein, ligand/state, replica, file and QC records. (C) Archive-first access model. The repository is the stable citable data record, while the web portal and REST API provide interactive and programmatic access layers. (D) Placeholder panel for an annotated portal screenshot showing search, filter, visualization and download functions.

**Figure 3. Technical validation by pocket and binding-site recovery.**  
(A) Clean-v1 orthosteric-site recovery benchmark by G-protein family, summarized among systems with detectable pocket outputs. (B) Distribution of best orthosteric-pocket recovery frequencies among recovered systems. (C) CCR5 Gi_7F1Q worked example showing persistent pocket records from the API. (D) Pocket-output availability across the clean-v1 cohort. These analyses are used as technical validation and reuse examples, not as mechanistic interpretation.

**Figure 4. Global quality-control and completeness summary.**  
(A) Metadata-level completeness checks for the clean-v1 cohort, including intended 3 x 500 ns sampling and trajectory/topology path availability. (B) Reduced-trajectory PBC audit status from the full visualization audit. (C) Reduced visualization trajectory frame-count distribution. (D) Clean-v1 visualization QC flags. These panels support technical validation of the prepared portal/reduced-trajectory layer; final production-archive frame counts and SHA256 checksums should still be reported after archive assembly.

## Supplementary Figures

**Supplementary Figure S3. Portal and API access workflow.**  
(A) User-facing workflow from system search and filtering to per-system metadata, visualization and selected downloads. (B) Programmatic API layers detected from the deployed OpenAPI schema, including status/citation, system metadata, derived records, visualization and consensus endpoints. (C) Archive-first access model for Scientific Data submission, distinguishing the stable archival repository from the web portal and REST API access layers.

## Main Tables

**Table 1. Clean-v1 dataset summary.**  
Summary of the initial Scientific Data clean-v1 cohort by G-protein family, including system counts, unique receptors, aggregate sampling, replica count, per-replica simulation length and inclusion notes.

**Table 2. Repository and data-record structure.**  
Proposed organization of the archival repository, including manifest files, system metadata, topology and trajectory records, reduced visualization files, derived feature tables, pocket outputs, QC reports, code, notebooks and web/API schema snapshots.

**Table 3. Metadata dictionary.**  
Definitions of key metadata fields required for each system, including receptor identifiers, GPCR class, G-protein family/subtype, ligand/state annotation, structure source, replica information, simulation length, file paths, QC status and checksums.

## Supplementary and Source Tables

**Supplementary Table S1. Included clean-v1 systems.**  
Per-system metadata for the 208 systems included in the initial clean-v1 release.

**Supplementary Table S2. Held-back systems.**  
Systems excluded from the initial clean-v1 release, with the reason for holding each system back and the planned verification/rerun status.

**Supplementary Table S3. File manifest and checksum checklist.**  
Checklist of required archive-level file-integrity fields. This checklist should be replaced by the final per-file manifest and checksums after archive assembly.

**Supplementary Table S4. Per-system pocket summary.**  
Clean-v1 per-system pocket-output summary, including total fpocket records, druggable consensus clusters and orthosteric consensus clusters.

**Supplementary Table S5. Per-system gateway summary.**  
Clean-v1 per-system gateway open-fraction and distance summary. These records should be described as reusable derived data and not used for mechanistic claims in Paper 1.

**Supplementary Table S6. Portal/API endpoint inventory.**  
Live REST API endpoints detected from the deployed OpenAPI schema, with each endpoint mapped to its manuscript use.

**Supplementary Table S7. Website feature and submission-gap checklist.**  
Portal capabilities and remaining Scientific Data submission gaps, including archive DOI, reviewer link, final manifest/checksums and full-trajectory download route.

**Supplementary Table S8. Clean-v1 archive manifest from metadata.**  
Production trajectory, topology and available full-system/protein-only trajectory paths for the 208 clean-v1 systems, including current file-size and existence fields from `systems_master.csv`. Final repository SHA256 checksums remain pending and should be generated after archive assembly.

**Supplementary Table S9. Clean-v1 portal file manifest.**  
Current server-side manifest for reduced visualization files, API JSON records, pocket grids, chain-role files and contact files across the 208 clean-v1 systems. Small text/API records include SHA256 checksums; binary or large-file checksums are marked for the final archive pass.

**Manifest Summary Table T6.**  
Summary of archive, portal-file and OpenAPI manifest coverage, including record counts and checksum status.

**Portal File Availability Table T7.**  
Availability summary by record type for clean-v1 portal files, including missing record counts and checksum coverage.

**Visualization PBC Audit Table T8.**  
Clean-v1 subset of the full visualization PBC audit, including reduced trajectory frame counts, atom-count agreement, box agreement and checked-frame PBC flags.

**Visualization PBC Summary Table T8a.**  
Summary of reduced-trajectory PBC audit results used in Figure 4.

**Visualization QC Flags Table T8b.**  
Clean-v1 systems with minor reduced-trajectory visualization QC flags or nonstandard reduced-trajectory frame counts.

**Technical Validation Source Table T4.**  
Per-system clean-v1 pocket and orthosteric-site recovery benchmark used for Figure 3.

**Technical Validation Summary Table T4a.**  
Family-level summary of clean-v1 pocket-output availability and orthosteric-site recovery.

**QC Source Table T5.**  
Metadata-level clean-v1 QC summary used for the draft Figure 4. This table should be extended after frame-count, PBC and stability audits are complete.
