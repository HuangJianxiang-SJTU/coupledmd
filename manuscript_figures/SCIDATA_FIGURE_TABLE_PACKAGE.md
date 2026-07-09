# Scientific Data Figure and Table Package Tracker

Working decision: Paper 1 is a Scientific Data Data Descriptor built around a strict clean-v1 release. The current metadata supports 208 clean-v1 systems after holding back 14 systems with PBC/completeness/file-integrity or nonstandard-length concerns. Clean-v1 totals from `data/systems_master.csv`: 208 systems, 174 unique receptors, 312.0 microseconds, all 3 replicas x 500 ns; family counts are Gi/o 93, Gs 67, Gq/11 42, G12/13 6.

## Current figure assets

| Existing asset | Current content | Paper 1 decision | Required action |
|---|---|---|---|
| `scidata_figures/scidata_figure1_clean_v1_draft.svg` | Clean-v1 composition, QC funnel and workflow draft | Use as Main Fig. 1 starting point | Replace provisional QC gate counts/thresholds after final QC lock |
| `scidata_figures/scidata_figure2_data_records_draft.svg` | Repository hierarchy, metadata schema and access-model schematic | Use as Main Fig. 2 starting point | Insert real portal screenshot and finalize archive/accession wording |
| `scidata_figures/scidata_figure3_validation_draft.svg` | Clean-v1 pocket and orthosteric-site recovery validation | Use as Main Fig. 3 starting point | Add/replace with replica-level agreement if final frame-level outputs are available |
| `scidata_figures/scidata_figure4_qc_draft.svg` | Metadata-level completeness, processed-output availability and held-back summary | Use as Main Fig. 4 placeholder | Replace placeholder QC panels with frame-count, PBC and RMSD/RMSF distributions after final archive audit |
| `scidata_figures/scidata_suppfigS3_portal_access_workflow_draft.svg` | Portal/API access workflow from live OpenAPI schema | Use as Supp Fig. S3 starting point | Pair with or replace one panel using real portal screenshots when available |
| `figure_1.png/.pdf` | 222-system NAR-style overview | Revise into Main Fig. 1 | Recompute clean-v1 counts; add QC funnel and workflow panel |
| `figure_2.png/.pdf` | CCR5 allosteric-site/pocket recovery | Revise into Main Fig. 3 | Use as technical validation or reuse example; soften claims and add cohort context |
| `figure_3.png/.pdf` | FFAR4 gateway reorganisation between Gi and Gq | Reserve or Supplement only | Mechanistic; do not use as main Data Descriptor figure |
| `figure4_gprotein_interface.png/.pdf` | G-protein interface and alpha5 geometry | Reserve for Paper 2 | Too mechanistic for Paper 1 main text |
| `figure5_partner_switching.png/.pdf` | Partner-switching reorganisation | Reserve for Paper 2 | Too close to Paper 2 novelty |

## Required main figures

| Figure | Question answered | Status | Panels to build |
|---|---|---|---|
| Fig. 1 | What is in the dataset and how was it built? | Draft SVG generated | A QC funnel 222 -> 208; B GPCR class distribution; C G-protein family distribution; D provenance/state/source; E simulation-to-data workflow |
| Fig. 2 | How is the dataset organized and accessed? | Draft SVG generated | A archive hierarchy; B metadata schema; C archive/portal/API access model; D portal screenshot |
| Fig. 3 | Are expected structural features preserved? | Draft SVG generated | A orthosteric/pocket recovery benchmark; B frequency distribution; C CCR5 worked example; D pocket-output availability |
| Fig. 4 | Is the dataset technically reliable? | Draft SVG generated, but final QC data still missing | A metadata-level completeness; B processed validation records; C held-back reason summary; D final QC gate checklist |

## Required supplementary figures

| Supplement | Status | Recommendation |
|---|---|---|
| S1 Extended composition | Missing | Generate after clean-v1 lock |
| S2 Full QC distributions | Missing | Needs QC metrics/frame counts/PBC and stability outputs |
| S3 Portal walkthrough | Missing | Capture screenshots for search, filters, viewer, download/API |
| S3 Portal/API workflow | Draft SVG generated | Uses deployed OpenAPI schema; real screenshots still recommended |
| S4 Example reuse workflow | Missing | Optional but useful; show API/notebook workflow |
| S5 Additional pocket examples | Optional | Use only if Fig. 3 needs broader validation |
| S6 Softened mechanism vignettes | Existing source figures | Highest novelty risk; descriptive only or reserve for Paper 2 |
| S7 Excluded/rerun roadmap | Missing | Can generate from held-back table |

## Clean-v1 table files now created

| Table | File | Rows | Status |
|---|---:|---:|---|
| Main Table 1 dataset summary | `tables/scidata_T1_dataset_summary_clean_v1.csv` | 6 | Draft ready |
| Main Table 2 repository structure | `tables/scidata_T2_repository_structure.csv` | 12 | Draft ready |
| Main Table 3 metadata dictionary | `tables/scidata_T3_metadata_dictionary.csv` | 25 | Draft ready |
| Supplementary Table S1 included systems | `tables/scidata_S1_included_systems_clean_v1.csv` | 208 | Draft ready |
| Supplementary Table S2 held-back systems | `tables/scidata_S2_held_back_systems.csv` | 14 | Draft ready |
| Supplementary Table S3 manifest/checksum checklist | `tables/scidata_S3_file_manifest_checksum_checklist.csv` | 8 | Checklist only; final manifest still missing |
| Validation source table | `tables/scidata_T4_technical_validation_clean_v1.csv` | 208 | Draft ready |
| Validation summary table | `tables/scidata_T4a_recovery_summary_clean_v1.csv` | 5 | Draft ready |
| QC summary source table | `tables/scidata_T5_qc_summary_clean_v1.csv` | 6 | Draft ready, metadata-level only |
| Supplementary Table S4 pocket summary | `tables/scidata_S4_per_system_pockets_clean_v1.csv` | 208 | Draft ready |
| Supplementary Table S5 gateway summary | `tables/scidata_S5_gateway_per_system_clean_v1.csv` | 208 | Draft ready, use descriptively only |
| Supplementary Table S6 portal/API endpoints | `tables/scidata_S6_portal_api_endpoints.csv` | 27 | Draft ready from live OpenAPI schema |
| Supplementary Table S7 website feature checklist | `tables/scidata_S7_website_feature_checklist.csv` | 15 | Draft ready; flags repository DOI/checksum/download gaps |
| Supplementary Table S8 archive manifest | `tables/scidata_S8_archive_manifest_clean_v1_from_metadata.csv` | 650 | Draft from metadata; final archive checksums pending |
| Supplementary Table S9 portal file manifest | `tables/scidata_S9_portal_file_manifest_clean_v1.csv` | 2080 | Draft ready for current server tree; binary checksums pending |
| Manifest summary table | `tables/scidata_T6_manifest_summary.csv` | 3 | Draft ready |
| Portal file availability table | `tables/scidata_T7_portal_file_availability_summary.csv` | 10 | Draft ready; flags two missing portal-derived records |
| Visualization PBC audit table | `tables/scidata_T8_viz_pbc_full_audit_clean_v1.csv` | 208 | Draft ready; source for updated Fig. 4 |
| Visualization PBC summary table | `tables/scidata_T8a_viz_pbc_summary_clean_v1.csv` | 12 | Draft ready |
| Visualization QC flags table | `tables/scidata_T8b_viz_qc_flags_clean_v1.csv` | 4 | Draft ready |
| Figure/table tracker | `tables/scidata_figure_table_tracker.csv` | 35 | Draft ready |

## Existing NAR/mechanism tables

| Existing table | Decision | Reason |
|---|---|---|
| `T1_cohort_summary.csv` | Supersede with clean-v1 Table 1 | Currently all-222 NAR framing |
| `T2_recovery_benchmark.csv` | Recompute for clean v1 and use for Technical Validation | Useful but currently all-222 |
| `T3_partner_switching.csv` | Reserve for Paper 2 | Mechanistic partner-switching content |
| `S1_system_inventory.csv` | Supersede with clean-v1 S1 plus held-back S2 | Current version lists all 222 |
| `S2_druggable_pocket_clusters.csv` | Possible SI/validation source | Keep descriptive, not mechanistic |
| `S3_alpha5_geometry.csv` | Reserve for Paper 2 | Alpha5 mechanism risk |
| `S4_partner_switching_pocket_detail.csv` | Reserve for Paper 2 | Partner-switching mechanism risk |
| `S5_gateway_per_system.csv` | Possible QC/SI only | Gateway interpretation risk; can be descriptive only |
| `S6_per_system_pockets.csv` | Useful SI source | Recompute/filter to clean v1 if included |

## Missing items before final figure production

1. Final QC thresholds: PBC pass/fail definition, completeness threshold, file-readability/checksum requirement, stability sanity thresholds, annotation completeness requirement.
2. Final archive layout and DOI/accession target.
3. True per-file manifest and checksums for the clean-v1 archive.
4. Frame-count/completeness table for all included replicas.
5. Stability summaries for Fig. 4: RMSD/RMSF or equivalent technical metrics.
6. Portal screenshots: search/filter page, system page, NGL viewer, download/API access. A schematic/access-workflow supplement now exists, but a real screenshot panel is still recommended for Fig. 2.
7. Clean-v1 recomputation of pocket recovery and per-system pocket tables.
8. Decision on whether any softened FFAR4/OX2R/gateway/alpha5 example is included in SI or fully reserved for Paper 2.

## Current Manifest Findings

The clean-v1 archive manifest from metadata contains 650 production/topology records for 208 systems, but production-archive SHA256 checksums are still pending. The portal/reduced-data manifest contains 2,080 expected records across 208 systems. Current missing portal-derived records are `data/api/v1/systems/Gq_7E9W/pockets_gpcrdb.json` and `data/contacts/Gi_6D9H_contacts.parquet`. Binary or large-file checksums are intentionally marked pending for the final archive pass.

## Current Visualization QC Findings

The full reduced-trajectory PBC audit contains all 208 clean-v1 systems. Results: 205 systems are `OK`, 3 systems have minor `WARN` scatter flags, all 208 have matching PDB/XTC atom counts, non-missing box records, zero blank elements, zero box mismatches, zero intra-chain break frames and zero inter-chain split frames. Reduced trajectory frame counts are 2500 for 205 systems, 2501 for 2 systems and 200 for 1 system (`Gs_3SN6`). These results strengthen Fig. 4 but do not replace the final production-archive checksum and frame-count audit.

## Next production order

1. Freeze the clean-v1 cohort and held-back reasons.
2. Regenerate Table 1/S1/S2 after any final changes.
3. Build Fig. 1 from clean-v1 metadata and QC funnel.
4. Build Fig. 2 from archive layout, metadata schema and portal screenshots.
5. Recompute clean-v1 validation data for Fig. 3.
6. Generate Fig. 4 after frame-count/PBC/stability outputs are assembled.
