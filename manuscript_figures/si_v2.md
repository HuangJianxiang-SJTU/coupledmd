# Supplementary Information for CoupledMD, a molecular dynamics dataset of GPCR/G-protein complexes

## Supplementary Note 1. Clean-v1 cohort definition

The CoupledMD clean-v1 release contains 208 GPCR/G-protein complex systems selected from a 222-system designed inventory. The clean-v1 cohort contains 174 unique receptors and 312.0 us of aggregate sampling, with each included system represented by three 500 ns production replicas in the release metadata. The release includes 93 Gi/o systems, 67 Gs systems, 42 Gq/11 systems and 6 G12/13 systems. By GPCR class, 182 systems are Class A and 26 systems are Class B.

Fourteen systems were held back from the initial clean-v1 release. Held-back reasons include nonstandard trajectory length, nonstandard replica count, temporary or incomplete source-file flags, missing processed pocket/grid outputs, or source records requiring verification or rerun. The held-back systems are listed separately to make the release boundary transparent and are not included in the 208-system clean-v1 counts, figures or aggregate sampling.

## Supplementary Note 2. Derived records and Paper 1 scope

CoupledMD distributes derived pocket, gateway and G-protein annotation records to support reuse of the trajectory dataset. In this Data Descriptor, these records are treated as machine-readable annotations, validation records or access-layer features. They are not used to claim coupling mechanisms, family selectivity, biased signaling, alpha5 rearrangements, allosteric pathways or partner-switching mechanisms. Those interpretations are outside the scope of Paper 1.

Pocket records are used for technical validation through orthosteric-pocket recovery and pocket-count summaries. Gateway and G-protein records are included as descriptive derived data layers. Any family-resolved visualization of these records should be read as annotation coverage or cohort organization unless explicitly tested in a separate mechanistic study.

## Supplementary Note 3. Technical validation summaries

Pocket records were available for 206 of 208 clean-v1 systems. Orthosteric-pocket recovery at the 0.85 frequency threshold was observed in 156 of the 206 systems with pocket outputs. Recovery by family was 66 of 91 Gi/o systems with pocket outputs, 51 of 67 Gs systems, 35 of 42 Gq/11 systems and 4 of 6 G12/13 systems. The corresponding family recovery rates were 72.5%, 76.1%, 83.3% and 66.7%, respectively.

The reduced visualization trajectory audit covered all 208 clean-v1 systems. The audit reported 205 OK systems, 3 WARN systems and 0 hard failures. No atom-count mismatches, blank PDB element fields, PDB/trajectory box mismatches, intra-chain break frames or inter-chain split frames were detected in the summary audit. Reduced-trajectory frame counts were 2500 frames for 205 systems, 2501 frames for 2 systems and 200 frames for 1 system. The short reduced visualization record is `Gs_3SN6`; minor WARN scatter flags were recorded for `Gi_8J22`, `Gq_7XJL` and `Gs_7F4H`.

The current metadata-derived archive manifest contains 650 records across 208 systems. The current portal/API/reduced-file manifest contains 2080 records across 208 systems, with 1247 checksums computed and 833 checksums marked for binary or large-file checksum completion in the final archive pass.

## Supplementary Note 4. Portal and API access

The CoupledMD web portal provides interactive browsing, filtering, per-system pages, reduced-trajectory visualization and selected downloads. The REST API exposes versioned records under `/api/v1/`, including system lists, per-system metadata, pocket records, gateway records, G-protein records, visualization metadata, reduced structures, reduced trajectories, citation metadata and licence metadata.

The stable archive is the citable data record. The web portal and REST API are access layers that improve browsing, visualization and programmatic reuse. Users performing quantitative trajectory analyses should use the archived full production trajectories, topology files, manifests and checksums.

Example API calls:

```bash
curl https://www.coupledmd.cn/api/v1/health
curl "https://www.coupledmd.cn/api/v1/systems?family=Gi&limit=10"
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q/pockets
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q/viz/meta
```

## Supplementary Figures

### Supplementary Figure S1. Receptor-level coupling-topology dendrogram.

Source asset: `scidata_figures/new_figureS1_dendrogram.pdf`.

Circular dendrogram of the 174 clean-v1 receptors clustered by presence or absence across the four major G-protein families. Leaf ticks are colored by single-family assignment or by multi-family representation, and each leaf is labeled by a representative four-letter PDB identifier. The figure provides receptor-level coupling-topology context for Figure 1 without implying mechanistic similarity among clustered receptors.

### Supplementary Figure S2. Portal, archive and API coverage.

Source asset: `scidata_figures/new_figure_s2_portal_archive_coverage.pdf`.

Summary of archive, portal and API coverage for the clean-v1 release. Panel A reports portal-file availability by record type, Panel B compares the size of the production archive with the portal/API layer, and Panel C groups the documented REST endpoints by manuscript-relevant use category. The figure supports the Data Records and Usage Notes sections by documenting how operational coverage is distributed across the archive and access layers.

### Supplementary Figure S3. Portal/API access workflow.

Source asset: `scidata_figures/new_figureS3_portal_access.svg`.

Workflow for interactive and programmatic access to CoupledMD. Panel A shows the user-facing route from system search and filtering to per-system metadata, reduced-trajectory visualization and selected downloads, Panel B groups the REST API layers for status/citation records, system metadata, derived records, visualization files and consensus summaries, and Panel C restates the archive-first access model. The stable archive remains the citable data record.

## Supplementary Tables

### Supplementary Table S1. Included clean-v1 systems.

Source file: `tables/scidata_S1_included_systems_clean_v1.csv`.

Per-system metadata for the 208 systems included in the clean-v1 release. Fields include system identifier, PDB identifier, receptor name, UniProt accession, receptor gene where available, GPCR class, G-protein family, G-alpha subtype, ligand fields, replica count, per-replica length, aggregate sampling, force-field/protocol annotation, lipid composition, structural provenance, trajectory type, file-existence fields, checksum fields where available and notes.

### Supplementary Table S2. Held-back systems.

Source file: `tables/scidata_S2_held_back_systems.csv`.

Systems excluded from the clean-v1 release, with receptor and G-protein metadata, simulation metadata, structural provenance, hold reason, rerun or verification status and notes. Held-back systems are excluded from the 208-system clean-v1 counts and aggregate sampling.

### Supplementary Table S3. File manifest and checksum checklist.

Source file: `tables/scidata_S3_file_manifest_checksum_checklist.csv`.

Checklist of file-manifest and checksum fields required for the final archive record. The checklist defines expected fields for paths, file roles, sizes, checksums, system identifiers, replica identifiers and format descriptions. It is intended to support assembly of the final per-file archive manifest.

### Supplementary Table S4. Per-system pocket summary.

Source file: `tables/scidata_S4_per_system_pockets_clean_v1.csv`.

Per-system summary of pocket outputs in the clean-v1 release. The table records pocket-output availability and pocket-derived summary fields used for technical validation and reuse. Pocket records are derived annotations and are not experimental druggability validation.

### Supplementary Table S5. Per-system gateway summary.

Source file: `tables/scidata_S5_gateway_per_system_clean_v1.csv`.

Per-system summary of derived gateway annotation records. These fields are provided as reusable annotations. Biological interpretation of family-resolved gateway differences is outside the scope of Paper 1.

### Supplementary Table S6. Portal/API endpoint inventory.

Source file: `tables/scidata_S6_portal_api_endpoints.csv`.

Inventory of REST API endpoints detected from the deployed OpenAPI schema. Endpoints are grouped by manuscript use, including citation and reuse metadata, system browsing, per-system records, visualization files, pocket records, gateway records, G-protein records and consensus summaries.

### Supplementary Table S7. Website feature and access checklist.

Source file: `tables/scidata_S7_website_feature_checklist.csv`.

Checklist of portal features and access-layer items relevant to Scientific Data submission. The table records support for search, filtering, per-system metadata, visualization, downloads, API documentation, citation metadata and archive-linking features.

### Supplementary Table S8. Clean-v1 archive manifest from metadata.

Source file: `tables/scidata_S8_archive_manifest_clean_v1_from_metadata.csv`.

Metadata-derived archive manifest for the 208 clean-v1 systems. The table includes production trajectory, topology and available full-system or protein-only trajectory paths where represented in the current metadata. Final archive-level file sizes and SHA256 checksums should be synchronized with the frozen archive record.

### Supplementary Table S9. Clean-v1 portal file manifest.

Source file: `tables/scidata_S9_portal_file_manifest_clean_v1.csv`.

Current server-side manifest for reduced visualization files, API JSON records, pocket grids, chain-role files and contact files across the 208 clean-v1 systems. Small text and API records include SHA256 checksums where computed; binary or large-file checksum fields are tracked for archive completion.

### Supplementary Table S10. Per-system pocket and orthosteric-site recovery benchmark.

Source file: `tables/scidata_T4_technical_validation_clean_v1.csv`.

Per-system technical-validation table used to evaluate pocket-output availability, orthosteric-pocket recovery, best orthosteric-pocket frequency, orthosteric-pocket count, ligand annotation and structural provenance.

### Supplementary Table S11. Family-level pocket recovery summary.

Source file: `tables/scidata_T4a_recovery_summary_clean_v1.csv`.

Family-level summary of clean-v1 pocket-output availability and orthosteric-site recovery. This table reports the system count, systems with pockets, recovered systems, recovery rate and mean best orthosteric-pocket frequency for Gi/o, Gs, Gq/11, G12/13 and the full clean-v1 cohort.

### Supplementary Table S12. Metadata-level clean-v1 QC summary.

Source file: `tables/scidata_T5_qc_summary_clean_v1.csv`.

Metadata-level QC summary for the clean-v1 release. The table records the designed systems, clean-v1 inclusion gate, 3 x 500 ns metadata gate, trajectory-path presence, topology-path presence and pocket-output availability.

### Supplementary Table S13. Manifest summary.

Source file: `tables/scidata_T6_manifest_summary.csv`.

Summary of archive, portal-file and OpenAPI manifest coverage, including record counts, system counts, checksum counts, checksum-pending counts and explanatory notes.

### Supplementary Table S14. Portal file availability summary.

Source file: `tables/scidata_T7_portal_file_availability_summary.csv`.

Record-type availability summary for clean-v1 portal/API files. The table reports expected systems, present records, missing records, computed checksums and pending checksums by file or record type.

### Supplementary Table S15. Reduced-trajectory PBC audit.

Source file: `tables/scidata_T8_viz_pbc_full_audit_clean_v1.csv`.

Per-system reduced-trajectory PBC and visualization audit. Fields include audit status, reduced-trajectory frame count, atom-count agreement, box agreement, checked-frame PBC flags and warning fields. These records validate the reduced visualization tier and should be distinguished from final full-production archive checksums.

### Supplementary Table S16. Reduced-trajectory PBC audit summary.

Source file: `tables/scidata_T8a_viz_pbc_summary_clean_v1.csv`.

Summary of the reduced-trajectory PBC audit. The table reports 208 audited systems, 205 OK systems, 3 WARN systems, 0 hard failures, 0 atom-count mismatches, 0 blank PDB element-field issues, 0 box mismatches, 0 intra-chain break frames, 7 minor scatter frames, 0 inter-chain split frames and reduced-trajectory frame-count categories.

### Supplementary Table S17. Reduced-trajectory visualization QC flags.

Source file: `tables/scidata_T8b_viz_qc_flags_clean_v1.csv`.

Clean-v1 systems with minor reduced-trajectory visualization warnings or nonstandard reduced-trajectory frame counts. The flagged records are `Gi_8J22`, `Gq_7XJL`, `Gs_3SN6` and `Gs_7F4H`.

## Supplementary Data availability

The supplementary tables are provided as CSV files in the `tables/` directory. Supplementary figures are provided as PDF and PNG files in `scidata_figures/` where available. Draft SVG files are retained only as editable source material and should not supersede the publication-grade matplotlib PDF/PNG outputs.

The full dataset archive DOI/accession and final SHA256 manifest should be cited from the Data Availability section of the main manuscript once the archive is frozen.
