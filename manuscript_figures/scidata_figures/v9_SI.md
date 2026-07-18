# Supplementary Information

## CoupledMD: molecular dynamics trajectories of active GPCR–G-protein complexes

Jianxiang Huang^1,2,3^, Xin Qiao^3^, Shaoyong Lu^1,2,3,\*^

^1^ Artificial Intelligence Clinical Research Center for Drug Discovery, Shanghai Key Laboratory of Flexible Medical Robotics, Institute of Medical Robotics, Tongren Hospital, Shanghai Jiao Tong University School of Medicine, Shanghai 200336, China

^2^ Key Laboratory of Protection, Development and Utilization of Medicinal Resources in Liupanshan Area, Ministry of Education; Peptide & Protein Drug Research Center, School of Pharmacy, Ningxia Medical University, Yinchuan 750004, China

^3^ Department of Pharmacology, School of Medicine, Shanghai Jiao Tong University, Shanghai 200025, China

\*Correspondence: Shaoyong Lu (lushaoyong@sjtu.edu.cn)

---

## Supplementary Note 1. Cohort definition and release controls

The v9 release contains 207 systems selected from a 222-record working inventory: 95 Gi/o, 65 Gs, 42 Gq/11 and 6 G12/13 systems; 182 Class A and 26 Class B. The production design is three selected 500-ns replicas per system, giving 310.5 µs in aggregate. The cohort contains 174 distinct receptor names and 173 mapped UniProt accessions. `Gs_8HTI` is a consensus OR52c model with no canonical UniProt mapping and is retained with explicit null receptor-accession/gene fields.

Thirteen records are unresolved and do not appear in release counts, API responses, derived records or figures. Their categories are PBC/trajectory continuity (8), component continuity (4) and incomplete trajectory evidence (1). `Gq_7E9W` is separately excluded as a non-GPCR duplicate/mislabel of `Gq_8E9W`. Timestamp resets are diagnostic only and are not classified as failures. Record-level evidence is in Supplementary Data S2.

The following release assertions are verified before the archive is frozen:

| Assertion | Required v9 result |
|---|---:|
| Unique system identifiers | 207 |
| Production replicas | 621 |
| Total production sampling | 310,500 ns |
| Systems returned by final API | 207 |
| Unresolved/excluded IDs in final derived files | 0 |
| `Gq_7E9W` in final API | 0 |
| Manifest rows with absolute local paths | Pending archive freeze |
| Manifest rows with more than one physical path | Pending archive freeze |
| Archived files with SHA-256 | Pending archive freeze |
| Manuscript/table/figure count mismatches | 0 |

## Supplementary Note 2. Structure provenance and protocol groups

Each system-level record identifies the PDB biological assembly, retained chains and components, UniProt mapping, ligand annotation, activation-state assignment, structural-provenance flag and retrieval date. Activation state and structural provenance are recorded as separate fields.

The release defines three protocol groups:

| Protocol | Systems | Engine | Current label |
|---|---:|---|---|
| P1 | 180 | AMBER pmemd | `CHARMM36 (chamber, AMBER pmemd)` |
| P2 | 26 | AMBER (CHARMM-GUI) | `CHARMM36 (via AMBER CHARMM-GUI)` |
| P3 | 2 | GROMACS | `CHARMM36 (membrane-embedded, GROMACS)` |

All 207 systems are membrane-embedded in POPC. P1 and P2 input templates specify 310 K, 1 bar, a 2-fs time step, SHAKE constraints on bonds to hydrogen, PME electrostatics, a 12-Å cutoff with switching from 10 Å. P3 templates specify 310 K, 1 bar, a 2-fs step, LINCS constraints, PME, a 1.2-nm cutoff and 1.0–1.2-nm switching. Engine-specific thermostat and barostat algorithms are detailed in the main Methods.

Ligand parameters were generated with CGenFF when available. Water is TIP3P; ions are Na⁺/Cl⁻ at 0.15 M. Protonation was assigned at pH 7.4. Minimization and multi-step equilibration with progressive restraint release preceded production. Engine versions and dependency versions are recorded in the code archive.

## Supplementary Note 3. Production and reduced trajectory records

The file manifest contains one row per physical file. Each production-trajectory row carries: `system_id`, `replica_id`, `protocol_id`, repository-relative path, file role, format, matching-topology identifier, atom selection, atom count, frame count, frame interval (ps), start/end time, byte size and SHA-256. A cell never contains concatenated paths. The roles "production," "water-stripped," "protein-only" and "reduced visualization" are distinct even when derived from the same simulation.

The reduced tier was generated for browser visualization: water, POPC and ions were removed; coordinates were aligned to the protein Cα reference; and frames were decimated to 2,500 frames over 500 ns, written as matched PDB/XTC pairs. The archived processing configuration records the retained atom selection, periodic-boundary reimaging method, alignment reference, stride and XTC precision. Reduced records are not valid for water-, ion- or lipid-dependent analyses.

## Supplementary Note 4. Pocket workflow

For each standard system, three production trajectories were sampled at a stride of 50 stored frames, yielding approximately 200 frames per replica. Each protein frame was aligned to the reference by Cα atoms. fpocket was executed per frame, and alpha-sphere occupancy was accumulated on a 1.5-Å Cartesian grid. Grid points occupied in ≥85% of analyzed frames were retained. Retained points were clustered by DBSCAN (ε = 2.85 Å, min_samples = 3). Protein heavy atoms within 4.0 Å of a cluster were assigned as lining residues.

Ligand heavy atoms were identified from retained HETATM records after excluding protein, lipid, water and ion residue names. When a small molecule was present, a cluster was labelled orthosteric when any retained grid point lay within 5.0 Å of a ligand heavy atom. The metric `mean_freq` is the mean occupied-frame fraction of grid points within a cluster; `best_ortho_freq` is the maximum `mean_freq` among orthosteric clusters. Ligand-free systems have no ligand-defined positive-control site; they are reported as not evaluable rather than as failed recovery.

GPCRdb mapping used the PDB-specific structure record and a sequence alignment between the receptor model and GPCRdb reference positions. Each deposited pocket record includes receptor-specific residue identifiers, GPCRdb generic positions, unmapped residues and component-role counts (receptor, Gα, Gβ, Gγ).

## Supplementary Note 5. Gateway workflow

Seven adjacent helix pairs define the gateway records: TM1–TM2, TM2–TM3, TM3–TM4, TM4–TM5, TM5–TM6, TM6–TM7 and TM7–TM1. TM residues are assigned from GPCRdb. Each frame is centered on the receptor and wrapped by residue. Lipid heavy atoms within 5.0 Å of both helices and within the central 25th–75th-percentile z-band of TM Cα coordinates are classified as wedged.

For each wedged atom, penetration is its inward radial displacement relative to the nearest helix-pair Cα wall. The system-level metrics are: `penetration` (mean per-frame maximum, Å); `penetration_p90` (90th percentile, Å); `open_fraction` (fraction of sampled frames with penetration ≥0.5 Å); and `occupancy` (mean number of wedged lipid heavy atoms per frame). `occupancy` is dimensionless and is not a distance. System values are means of three replica summaries; 95% intervals are obtained by bootstrap resampling the three replica summaries 1,000 times with a fixed seed.

Missing gateway records are encoded as `null` with a reason code; they are never encoded as zero.

## Supplementary Note 6. Technical validation

### Production-trajectory QC

Every deposited production replica is evaluated against seven criteria:

1. File presence, non-zero size, readability and SHA-256 agreement
2. Exact 500-ns duration, frame count and monotonic timestamps
3. Finite coordinates and valid periodic unit-cell vectors
4. Atom-count and atom-order agreement with the declared topology
5. Periodic-boundary continuity and absence of catastrophic component separation
6. Prespecified thermodynamic indicators (temperature, box volume stability)
7. Structural-integrity thresholds: receptor TM-core RMSD ≤ 5 Å and G-protein Cα centroid distance ≤ 25 Å from starting structure

The planned archival QC package will contain one row per replica with separate `file_status`, `trajectory_status`, `physical_qc_status` and `overall_status` fields. The current release criterion is the readiness-supported selection of three validated replicas per included system; the server must not be described as a complete archived QC package before the final manifest is frozen.

### Reduced-trajectory audit

Reduced browser trajectories are audited separately from primary-production readiness. The v9 figure and tables distinguish included systems from unresolved systems and report current trajectory/PBC and component-continuity categories. Timestamp resets are diagnostic only. The earlier 205-OK/3-WARN reduced-trajectory summary is not reused as a v9 result.

This validation covers sampled reduced frames only; it does not validate every reduced frame or any production-trajectory frame.

## Supplementary Table S1. Canonical metadata dictionary

The deposited machine-readable dictionary contains the following columns for every field: name, entity level, type, unit, requiredness, nullable status, allowed vocabulary, definition, example, provenance authority and schema version. The fields shown below are a representative subset.

| Field | Level | Type / unit | Definition |
|---|---|---|---|
| `dataset_version` | all | string | Final release identifier (`v9-final207`) |
| `system_id` | system | string | Release-stable family/PDB identifier, e.g. `Gi_7F1Q` |
| `pdb_id` | system | PDB ID | Verified starting-structure identifier |
| `receptor_uniprot` | system | UniProt accession, nullable | Mapped receptor accession; missingness reason recorded |
| `receptor_gene` | system | string, nullable | Canonical gene symbol |
| `gpcr_class` | system | enum | Controlled vocabulary: `A`, `B` |
| `g_protein_family` | system | enum | Controlled vocabulary: `Gi/o`, `Gs`, `Gq/11`, `G12/13` |
| `g_alpha_subtype` | system | controlled string | Normalized Gα subtype |
| `activation_state` | system | enum | `active`, `active-like` |
| `structural_provenance` | system | enum | `experimental`, `engineered_uncertain` |
| `ligand_name`, `ligand_chem_id`, `ligand_class` | system | nullable strings / enum | Retained orthosteric ligand annotation |
| `ligand_class` | system | enum | `small_molecule`, `peptide`, `none` |
| `protocol_id` | system | string | Key to creation protocol |
| `replica_id` | replica | integer | `1`, `2` or `3` |
| `random_seed` | replica | integer / string | Engine seed or documented generation rule |
| `trajectory_file_id`, `topology_file_id` | replica | string | Keys to the file manifest |
| `n_atoms`, `n_frames` | file | integer | Stored molecular dimensions |
| `frame_interval_ps`, `duration_ns` | file | numeric | Trajectory time representation |
| `file_size_bytes` | file | integer | Deposited byte count |
| `sha256` | file | 64-character hex | Checksum of deposited bytes |
| `qc_status`, `qc_reason` | relevant level | enum / string | `PASS`, `WARN`, `FAIL` and explanation |

Empty strings, literal `nan`, zero and absent keys are not interchangeable; each serialization defines the null representation.

## Supplementary Table S2. Unresolved and excluded records

Supplementary Data S2 contains the 13 unresolved records and two excluded records with current readiness evidence. A separate final-exclusions table documents only `Gq_7E9W` as a non-GPCR duplicate/mislabel. Neither category contributes to v9 denominators.

## Supplementary Table S3. Molecular-file specification

| File role | Format | Required pairing | Intended use |
|---|---|---|---|
| AMBER production | NetCDF | PRMTOP / PARM7 + input set | Quantitative trajectory analysis |
| GROMACS production | TRR | TPR / TOP + MDP | Quantitative trajectory analysis |
| Reduced reference | PDB | Reduced XTC | Atom names/order, visualization |
| Reduced trajectory | XTC | Reduced PDB | Visualization, lightweight inspection |
| Pocket grid | NPZ | Schema record | Alternative isovalue/reclustering |
| Annotations / QC | JSON / CSV / TSV | Schema version | Machine-readable reuse |

The deposited table also records format version, units, compression/precision, atom selection and recommended reader libraries (MDAnalysis, MDTraj).

## Supplementary Table S4. API and versioning contract

The current OpenAPI 3.0 schema describes the final 207-system API access layer with typed success and error responses, media types for PDB/XTC/NPZ downloads, pagination, error codes and controlled vocabularies. Unresolved IDs and `Gq_7E9W` have no final release record. The portal may evolve; a frozen archival schema will accompany deposition.

## Supplementary Figure S1 | Receptor representation across G-protein families.

Receptors are grouped using a four-element presence/absence vector for Gi/o, Gs, Gq/11 and G12/13. Jaccard distance with average linkage organizes the dendrogram. Branch proximity reflects release coverage only and does not imply sequence, structural or mechanistic similarity.

## Supplementary Figure S2 | Transmembrane gateway definition and aggregation.

**a**, Top view of the seven membrane-facing gateways formed by adjacent transmembrane helix pairs. **b**, Per-frame definition: lipid heavy atoms within 5.0 Å of both helices and within the central 25th–75th-percentile TM Cα z-band are classified as wedged; radial penetration is measured inward from the nearest pair-Cα wall, and a frame is open when the maximum penetration is at least 0.5 Å. **c**, Frame-to-system aggregation. The four gateway metrics are summarized per replica and then averaged across three replicas; 95% confidence intervals use 1,000 replica-level bootstrap resamples. Unavailable results are encoded as null with a reason code, never as zero.

## Supplementary Figure S3 | Portal and API access workflow.

Routes for metadata discovery, reduced visualization, derived records and production-data retrieval. The repository is the version of record; the portal and API are access layers.

## Supplementary Data files

| File | Content | Granularity |
|---|---|---:|
| S1 | v9 included-system inventory | 207 rows |
| S2 | Release-boundary exceptions: 13 unresolved records and two excluded records and one excluded duplicate/mislabel | 14 rows |
| S3 | Canonical metadata dictionary | One row per field |
| S4 | Source inventory for production-trajectory and topology evidence (not an archive manifest) | 414 rows |
| S5 | Pocket summaries with GPCRdb mappings and explicit unavailable records | One row per pocket plus two unavailable-system rows |
| S6 | Current gateway summaries | 207 systems |
| S7 | Selected-replica release ledger (not full archived file QC) | 621 replicas |
| S8 | Final-cohort readiness/QC evidence | 207 rows |
| S9 | Current final-cohort API access coverage | 10 record types |
| S10 | Code and environment inventory | One compact inventory |

## Supplementary reuse cautions

- Split machine-learning datasets by receptor accession, not by replica, to avoid data leakage.
- Treat `protocol_id`, GPCR class, ligand context, construct type and source PDB as potential confounders.
- Do not infer physiological coupling prevalence from this structurally determined cohort.
- Do not use reduced records for lipid, ion, solvent or fast-kinetics analyses.
- `occupancy` is a count of wedged lipid atoms, not a distance; do not label it as Å.
- Cite both the *Scientific Data* article and the exact dataset DOI/version used.

## Supplementary Data Availability

The portal at https://www.coupledmd.cn and API documentation at https://www.coupledmd.cn/api/docs provide the current final-207 access layer. Complete primary trajectories, matched topologies, inputs, file-level checksums and the DOI-linked archive are pending final manifest freeze and deposition. Until then, this supplement makes no archive-completeness, DOI, licensing or direct-download claim.
