# CoupledMD: a molecular dynamics dataset of GPCR/G-protein complexes

[Authors and affiliations to be added at submission]

## Abstract

G protein-coupled receptors (GPCRs) couple to heterotrimeric G proteins to transduce extracellular signals and remain one of the most frequently targeted protein families in drug discovery. Reusable molecular dynamics (MD) records for active GPCR/G-protein complexes are, however, limited by heterogeneity in simulation protocols, file formats, annotation schemes and access routes. Here we describe CoupledMD clean-v1, a standardized MD dataset of 208 active-state GPCR/G-protein complex systems covering 174 unique receptors, two GPCR classes and the four major G-protein families (Gi/o, Gs, Gq/11 and G12/13). Each included system is represented by three independent 500 ns production replicas in a POPC membrane environment, yielding 312.0 µs of aggregate sampling. The release distributes production trajectories, topology and structure files, reduced visualization trajectories, system metadata, GPCRdb-compatible receptor annotations, pocket records, gateway and G-protein derived annotation layers, quality-control summaries, file manifests and the figure and table generation scripts. Technical validation covers the clean-v1 inclusion gate and the transparent held-back cohort, orthosteric-pocket recovery, pocket-count distributions, reduced-trajectory periodic-boundary audits and frame-count checks. The dataset is accessible through a stable archive record, the interactive web portal at www.coupledmd.cn and a versioned REST API. CoupledMD is intended to support reuse, benchmarking, method development, residue-level annotation workflows and GPCR-targeted drug-design studies; biological mechanism interpretation is reserved for downstream work.

## Background & Summary

GPCRs translate extracellular signals into intracellular responses and remain one of the most productive protein families for therapeutic intervention[1]. Active GPCRs couple to heterotrimeric G proteins from the Gi/o, Gs, Gq/11 and G12/13 families[2], and the expanding number of experimentally determined receptor/G-protein complex structures provides an increasingly rich structural record. These structures supply essential snapshots, but comparative reuse across receptors and G-protein families still depends on standardized simulation records, consistent annotation and practical access routes.

Several public resources and computational GPCR-analysis workflows have shaped this landscape[20]. GPCRdb provides receptor classification, sequence alignments, structural annotations and the generic residue numbering that makes cross-receptor comparison possible[3,15,17]. GPCRmd has demonstrated the value of community-accessible GPCR trajectory resources[4]. The mdCATH Data Descriptor offers a useful organizational model for presenting a large MD resource through cohort definition, file organization, technical validation and usage notes[5]. CoupledMD follows the same descriptor discipline but addresses a different data type: multi-chain, membrane-embedded active GPCR/G-protein complexes with receptor, G-protein, pocket and web/API annotation layers.

CoupledMD clean-v1 contains 208 included systems selected from an initial designed inventory of 222 systems. The cohort spans 174 unique receptors, both Class A and Class B GPCRs and all four major G-protein families represented in the current structural record. Family composition is 93 Gi/o, 67 Gs, 42 Gq/11 and 6 G12/13 systems; by GPCR class, 182 systems are Class A and 26 are Class B. The nominal design is three independent 500 ns production replicas per system, corresponding to 1.5 µs of sampling per system and 312.0 µs of aggregate sampling across the release. The composition, ligand context, multi-family receptor coverage and 222-to-208 release boundary are summarized in Figure 1, with an extended coverage overview provided in Supplementary Figure S1.

Figure 1 is intended to be read as the scope statement for the resource. Panel A quantifies the class-by-family coverage of the 208-system clean-v1 cohort. Panel B highlights the receptors represented across the largest number of systems and marks those sampled with more than one G-protein family, indicating where within-receptor comparative reuse is immediately possible without implying a coupling mechanism. Panel C separates ligand-present and apo or no-ligand systems by family so that users can identify ligand-aware and ligand-independent subsets. Panel D expands this reuse view to the 42 most represented receptors, where larger and accent-colored markers identify receptors sampled across multiple G-protein-family contexts. Panel E keeps the release boundary explicit by contrasting the 208 included systems with the 14 held-back systems and by grouping the held-back records into nonstandard-length or missing/incomplete-output categories.

The resource is organized around three questions that match the expectations of a Scientific Data Data Descriptor. First, what is in the release? CoupledMD provides a defined clean-v1 cohort, a transparent held-back cohort and coverage summaries by receptor class, G-protein family and ligand context. Second, how is the release organized and accessed? The archival repository is the citable data record, while the web portal and REST API provide interactive and programmatic access to metadata, reduced trajectories and derived annotations; this archive-first organization is summarized in Figure 2. Third, can users trust the records? The release includes technical validation of pocket recovery, pocket-count distributions, reduced-trajectory frame counts and periodic-boundary audits.

Pocket, gateway and G-protein records are described in this manuscript as derived annotations distributed with the resource. They are included to make the dataset reusable, not to claim a mechanism of coupling, family selectivity, biased signalling or partner switching; those analyses are outside the scope of this Data Descriptor.

## Methods

### System selection and clean-v1 cohort definition

The starting inventory contained 222 GPCR/G-protein complex systems. Each candidate system was curated with a system identifier, primary PDB identifier[6], receptor name, UniProt accession[7], GPCR class, G-protein family assignment, Gα-subtype annotation, ligand annotation, structural-provenance flag and simulation and file-availability metadata. The clean-v1 release contains the 208 systems that passed the current release gates for a uniform 3 × 500 ns design and for the availability of the associated metadata, topology, trajectory and processed records.

Fourteen systems were held back from the initial clean-v1 release. Held-back reasons include nonstandard trajectory lengths, nonstandard replica counts, temporary or incomplete source-file flags, missing processed pocket or grid outputs and source records requiring verification or rerun. These systems are not silently removed: they are listed in Supplementary Table S2 with exclusion reasons and verification status, so the release boundary remains traceable.

### Structure sourcing and annotation

Active-state GPCR/G-protein complex structures were identified from experimentally determined structures[6] together with associated receptor and G-protein annotations. Receptor records were cross-referenced with UniProt accessions[7] and GPCRdb-compatible identifiers where available[3,15,17]. Sequence-profile and multiple-sequence-alignment based annotation steps were tracked where applicable[18,19]. G-protein records were grouped into the Gi/o, Gs, Gq/11 and G12/13 family categories and annotated with Gα-subtype labels where available. Structural provenance (experimental versus engineered or uncertain) was recorded for every system. In clean-v1, 197 included systems are experimental-coordinate derived and 11 carry an engineered or uncertain flag, so that users may apply stricter filters if required.

The primary system identifier follows a family-plus-PDB pattern (for example, Gi_7F1Q), and the metadata table stores the corresponding PDB identifier, receptor name, UniProt accession, receptor gene where available, GPCR class, G-protein family, Gα-subtype, ligand fields, simulation fields and QC fields.

### Simulation preparation and production design

Included systems were prepared under a common CHARMM36-family membrane simulation protocol and embedded in a POPC membrane environment[8]. System setup used CHARMM-GUI[9,10] and standard MD packages appropriate to the source structure and trajectory format[11,12]. Where retained input files specify velocity-rescaling or Berendsen temperature coupling, Parrinello-Rahman pressure coupling, LINCS constraints or particle-mesh Ewald electrostatics, those settings follow standard molecular-simulation formulations[21-25]. The clean-v1 release is defined around a uniform production design of three 500 ns replicas per included system. The metadata table records the force-field and protocol annotation, lipid composition, trajectory type, replica count, per-replica length and aggregate sampling per system.

Where trajectories originate from different engines or were converted between topology formats, the archive metadata state the format and required software explicitly; engine-specific input and topology files are retained alongside the production trajectories so that downstream users can reproduce or extend analyses.

### Trajectory processing and reduced visualization records

Full production trajectories are the primary molecular records and belong in the stable archive. A reduced visualization tier was generated for web and lightweight reuse using trajectory-analysis toolkits where appropriate[26,27]. Reduced trajectories are protein-focused, decimated records accompanied by matching reduced reference structures; they are intended for interactive inspection through the portal and for rapid system review[14]. These reduced records are useful for visualization and screening but do not replace full production trajectories in quantitative reanalysis.

The reduced visualization layer was audited for frame count, atom-count agreement, blank element fields, box-mismatch flags, intra-chain breaks, inter-chain splits and scatter-frame warnings; the audit results are summarized in Technical Validation and in Supplementary Tables S15–S17.

### Pocket detection and GPCRdb mapping

Pocket records were generated as derived annotations for each included system for which pocket outputs were available[13]. The technical validation workflow uses orthosteric-pocket recovery as a positive-control style check, because ligand-accessible receptor pockets are expected to be recovered in many ligand-bearing active complexes. Pocket-lining residues were mapped to GPCRdb generic positions where available[3,15,17], allowing users to compare pocket records across receptors without relying solely on receptor-specific residue numbers.

Orthosteric-pocket recovery was evaluated using the best per-system orthosteric-pocket frequency and a 0.85 frequency threshold. This metric is used as technical validation of known structural-feature recovery and annotation stability; it is not interpreted as a biological mechanism or as experimental evidence of ligand binding.

### Gateway and G-protein derived annotations

The dataset also distributes derived gateway and G-protein annotation records. Gateway records summarize defined transmembrane-helix interface measurements, while G-protein records provide CGN-compatible annotation layers where available[3,16]. In this Data Descriptor, these records are described as machine-readable annotations and access-layer features. Family-resolved biological interpretation of gateway or G-protein dynamics is outside the scope of Paper 1 and is reserved for downstream studies.

### Archive, portal and API generation

CoupledMD is designed with three access layers. The stable archive is the citable data record and contains the full trajectories, topologies, structures, metadata, processed annotations, manifests, checksums, documentation and code snapshots. The web portal at www.coupledmd.cn provides interactive browsing, filtering, visualization and selected downloads. The REST API exposes metadata and processed records for programmatic reuse.

The portal is implemented as an access layer rather than as the authoritative archive; the manuscript and the website both point users to the final repository DOI or accession once that record is minted. An OpenAPI snapshot dated 2026-07-07 is present in the manuscript figure workspace and is refreshed at submission if the API changes.

## Data Records

### Dataset scope

The clean-v1 release includes 208 GPCR/G-protein systems, 174 unique receptors and 312.0 µs of aggregate sampling. The cohort comprises 93 Gi/o systems, 67 Gs systems, 42 Gq/11 systems and 6 G12/13 systems; by GPCR class, the release contains 182 Class A and 26 Class B systems. All clean-v1 systems are represented by three 500 ns replicas in the metadata-level release definition.

The full designed inventory and the held-back systems are documented to make the release boundary transparent: the held-back cohort contains 14 systems and is excluded from the 208-system clean-v1 counts, figures and technical validation unless otherwise stated.

### Repository organization

The final archive uses the predictable hierarchy summarized in Main Table 2 and illustrated in Figure 2A. The submitted archive contains final file sizes and SHA-256 checksums; current metadata-derived manifest tables are useful for manuscript drafting but are replaced or confirmed against the frozen archive before submission. Figure 2 also summarizes the per-system metadata schema and the archive-first access model linking the stable repository, web portal and REST API. Supplementary Figure S2 provides an expanded portal, archive and API coverage view.

Figure 2 describes how a user should navigate the data product. Panel A organizes the archive into manifest, metadata, per-system topology, trajectory, reduced-trajectory, feature, pocket, QC, code and web/API snapshot components. Panel B maps the same organization onto the per-system metadata fields, linking receptor, G-protein, ligand/state, replica and file/QC information. Panel C makes the access hierarchy explicit: the archive is the stable record for citation and reproducibility, whereas the portal and API are access layers. Panel D translates that hierarchy into a publication-ready portal-access schematic showing search, filtering, structure viewing, download actions and API entry points, so the figure remains interpretable even before a final live screenshot is inserted.

Table 1. Repository organization of the CoupledMD clean-v1 archive. Authoritative file-hierarchy for the stable archive. Paths are illustrative; the submitted archive contains the frozen layout with final sizes and SHA-256 checksums.

| Path | Contents | Manuscript use |

| --- | --- | --- |

| manifest/ | Dataset-level file manifest, version, checksums and archive index | Main archive; required before submission |

| metadata/systems.csv | Per-system metadata for included clean-v1 systems | Clean-v1 inventory |

| metadata/held_back_systems.csv | Systems excluded from the initial release with reasons | Supplementary transparency table |

| systems/<system_id>/metadata.json | System, receptor, G-protein, ligand, source and QC fields | One record per included system |

| systems/<system_id>/topology/ | Prepared structures and topology/parameter files | Archive record |

| systems/<system_id>/trajectories/rep{1..3}/ | Full production trajectories for each replica | Stable repository record |

| systems/<system_id>/reduced/ | Aligned or strided trajectories for visualization and rapid reuse | Web/API and archive record |

| systems/<system_id>/features/ | Derived feature summaries as available | Processed analysis layer |

| systems/<system_id>/pocket/ | Pocket outputs, orthosteric summaries and GPCRdb-mapped records | Validation and reuse layer |

| systems/<system_id>/qc/ | Completeness, frame counts, PBC status and file-integrity checks | Technical validation |

| code/ | Processing scripts, notebooks and figure/table generation scripts | Code availability |

| web_api_snapshot/ | OpenAPI schema and selected JSON endpoint snapshots | Portal/API documentation |

### Metadata dictionary

The primary metadata record includes system_id, pdb_id, receptor_name, receptor_uniprot, receptor_gene, gpcr_class, gpcrdb_id where available, g_protein_family, g_alpha_subtype, ligand_name, ligand_chem_id, state, source_pdb, n_replicas, length_per_replica_ns, total_sampling_ns, force_field, lipid_composition, trajectory_path, topology_path, qc_status, qc_reason, traj_sha256 and topo_sha256. Units are stated for all numeric fields (ns for simulation length, bytes for file size); enumerated fields such as GPCR class, G-protein family and QC status use controlled vocabularies.

Main Table 3 is the authoritative metadata dictionary. Field names in the paper, repository metadata, API records and portal display are synchronized before submission.

### Portal and API records

The web portal at www.coupledmd.cn supports interactive access to the release through system browsing, filtering, per-system pages, reduced-trajectory visualization and downloads[14]. The REST API exposes versioned records under /api/v1/, including system lists, per-system metadata, pocket records, gateway records, G-protein records, visualization metadata, reduced structures, reduced trajectories, citation metadata and licence metadata. API documentation is provided through interactive documentation pages and the OpenAPI schema.

At the time of this draft, the portal/API manifest summary contains 2,080 records across 208 systems, with 1,247 checksums computed and 833 pending for binary or large files. Record-level availability is complete for gateway, G-protein, index, pocket, chain-role and visualization records for all 208 systems; one api_pockets_gpcrdb record and one contacts record are currently missing and are addressed before submission.

The portal is a usability and access layer. The archive DOI or accession listed in Data Availability is the stable record for citation and long-term reuse.

## Technical Validation

### Clean-v1 release gate and held-back transparency

The clean-v1 cohort was defined by applying conservative inclusion gates to the 222-system designed inventory. All 208 included systems passed metadata-level checks for the 3 × 500 ns release definition and for the presence of trajectory and topology paths. The 14 held-back systems are listed with reasons in Supplementary Table S2; held-back categories include nonstandard length, nonstandard replica count, temporary or incomplete source-file flags, missing processed outputs and source records requiring verification or rerun. This reporting follows the same transparency principle used by database-style Data Descriptors: release failures and exclusions are documented rather than hidden, and held-back systems are not used to inflate clean-v1 counts or aggregate sampling.

### Orthosteric-pocket recovery validation

Pocket records were available for 206 of 208 included systems. Orthosteric-pocket recovery at the 0.85 frequency threshold was observed in 156 of the 206 systems with pocket outputs. Family-level recovery was 66 of 91 Gi/o systems with pocket outputs (72.5%), 51 of 67 Gs systems (76.1%), 35 of 42 Gq/11 systems (83.3%) and 4 of 6 G12/13 systems (66.7%). By ligand annotation, recovery was 92 of 97 small-molecule systems with pocket outputs (94.8%) and 64 of 75 peptide systems (85.3%); systems annotated as having no ligand were not expected to recover an orthosteric ligand pocket under this validation definition. Figure 3A reports the per-system recovery distribution and the 0.85 threshold.

This validation demonstrates the recovery of expected ligand-accessible structural features and the consistency of the pocket annotation pipeline. It is not interpreted as a mechanistic result and is not used as experimental validation of druggability.

### Pocket-count distributions

The per-system number of detected pockets provides an additional technical check on the derived annotation layer. Across families, median pocket counts were 10 for Gi/o, 11 for Gs, 11 for Gq/11 and 10.5 for G12/13. Family-level ranges were 0–18 for Gi/o, 5–18 for Gs, 5–19 for Gq/11 and 3–14 for G12/13. These values serve as descriptive validation of annotation availability and distribution, and are not used as evidence for family-specific function. Figure 3B summarizes the pocket-count distribution; the dataset-scale comparison in Figure 3C is retained only if the benchmark values are verified before submission.

Together, Figure 3A and 3B provide the main technical-validation view for pocket-derived records. The recovery panel asks whether known ligand-accessible receptor pockets are recovered at the expected location often enough to support reuse of the pocket annotations. The pocket-count panel asks whether the pocket-detection layer produces a plausible and trackable number of records per system rather than sparse or unstable outputs. Figure 3C then places CoupledMD beside a single-receptor GPCR trajectory resource and a large general-protein MD resource to contextualize the niche that this release occupies: fewer systems than domain-scale repositories, but unusually broad sampling for membrane-embedded GPCR/G-protein complexes. This comparison is descriptive and is not used as a quality benchmark.

### Reduced-trajectory periodic-boundary and frame-count audit

Reduced visualization trajectories were audited across 208 clean-v1 systems (205 OK, 3 WARN and 0 hard failures). The summary audit detected no atom-count mismatches, no blank PDB element fields, no PDB/trajectory box mismatches, no intra-chain break frames and no inter-chain split frames; seven minor scatter frames were observed across the checked-frame sample. Figure 4B reports the reduced-trajectory PBC audit outcomes.

Reduced-trajectory frame counts were 2,500 frames for 205 systems, 2,501 frames for two systems and 200 frames for one system. The short reduced visualization record corresponds to Gs_3SN6; the production metadata for that system remain in the clean-v1 cohort and the reduced-record difference is flagged. Systems with WARN status (Gi_8J22, Gq_7XJL and Gs_7F4H) carry only minor scatter warnings and no hard audit failure. Figure 4 summarizes gateway annotation coverage, family-level orthosteric-recovery rates, gateway open-fraction distributions and dataset completeness as the QC and integrity view of the release, while the reduced-trajectory audit details remain documented in Supplementary Tables S15-S17 and the figure callout.

Figure 4 is the release-integrity figure. Panel A catalogs derived TM-gateway open-fraction annotations across the 208 systems as machine-readable records, with family grouping used only to organize the display. Panel B restates family-level orthosteric-pocket recovery rates as a compact structural-fidelity benchmark for the derived pocket layer. Panel C summarizes the open-fraction distributions for the seven transmembrane gateway interfaces across the full cohort, showing that the gateway layer spans a broad dynamic range rather than collapsing to a single trivial state. Panel D connects these annotation summaries to the transparent release boundary by contrasting the 208 included systems with the 14 held-back systems and by reporting the reduced-trajectory integrity outcome as a compact callout. These panels document completeness and annotation behavior; they are not used to infer biological differences among G-protein families.

### File manifests and checksums

The current metadata-derived archive manifest contains 650 records across 208 systems; the portal file manifest contains 2,080 records across 208 systems, with 1,247 checksums computed and 833 pending. The OpenAPI snapshot contains 27 records and carries a checksum. Before submission, the archive manifest is regenerated from the frozen repository layout; SHA-256 checksums are computed for all submitted files, and any files represented through external storage are explicitly noted.

## Limitations

CoupledMD clean-v1 covers active-state GPCR/G-protein complex systems and does not extend to inactive receptors, GPCR–arrestin complexes or ligand-free ensembles for every receptor. Because the release reflects available structural coverage, G12/13 systems are under-represented relative to Gi/o, Gs and Gq/11. The standard production design is 500 ns per replica, which may not sample slower conformational transitions. Pocket, gateway and G-protein records are derived annotations and require study-specific validation for biological interpretation. Final publication elements still pending include the archive DOI/accession, the final SHA-256 manifest, the final production-archive frame audit and the replacement of the portal screenshot placeholder in Main Figure 2.

## Usage Notes

CoupledMD can be reused at three levels. Users performing quantitative trajectory analysis should use the stable archive, which contains the full production trajectories, topology files, metadata, manifests and checksums. Users who need rapid system selection or method benchmarking can use processed tables and JSON records, including system metadata, pocket annotations, gateway records, G-protein records and QC summaries. Users who need interactive inspection can use the portal and reduced visualization trajectories.

Example reuse workflows include filtering systems by GPCR class, G-protein family, receptor name, UniProt accession, PDB identifier or ligand annotation; retrieving reduced structures and trajectories for visualization; joining GPCRdb-mapped pocket residues to external receptor annotations; and using API endpoints to build reproducible system lists before downloading full trajectories from the archive. Figure 5 summarizes the consensus pocket atlas distributed with the resource, including cluster-level occupancy, anatomical zoning, reusable GPCRdb anchors, validation context and high-scoring nomination examples. Supplementary Figure S3 provides the portal/API access workflow. These workflows support rather than substitute for downstream analyses, including those that may interpret family-resolved or ligand-specific signatures.

Figure 5 describes the pocket-annotation layer as a reusable data product. Panel A is reserved for a representative structural or portal-facing snapshot during final layout. Panel B maps consensus druggable pocket clusters by receptor coverage and mean occupancy, with marker size reflecting cluster volume and color indicating anatomical zone. Panel C counts cluster members across orthosteric, transmembrane-core allosteric, intracellular-allosteric and related zones. Panel D lists the GPCRdb generic positions that recur most often in the orthosteric and druggable cluster cores, allowing residue-level joins across receptors without relying only on receptor-specific numbering. Panel E restates family-level orthosteric recovery as a validation view for the distributed pocket records, and Panel F highlights nomination examples with the highest proxy scores together with example receptors. These outputs can support prioritization or benchmarking workflows, but the manuscript does not treat them as experimental druggability validation or as mechanistic discoveries.

Example API calls for the live portal are:

curl https://www.coupledmd.cn/api/v1/health
curl "https://www.coupledmd.cn/api/v1/systems?family=Gi&limit=10"
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q/pockets
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q/viz/meta

Users should cite the Scientific Data article and the dataset DOI when both become available. Users of the code or API schema should also cite the code repository according to the repository citation file. The web portal may evolve for usability, but the archive version and checksum manifest should be used for reproducible citation.

## Figures

Figure and table captions are collected below; the underlying files are referenced in Supplementary Data availability.

Figure 1. Coverage and reuse landscape of the CoupledMD clean-v1 release. (A) Class × G-protein-family coverage across 208 systems. (B) Receptors represented across the largest number of systems, with multi-family receptors highlighted as direct within-receptor reuse opportunities. (C) Ligand-present versus apo or no-ligand systems by family. (D) Receptor reuse landscape for the most represented receptors, with accent-colored larger markers denoting receptors sampled across more than one G-protein family. (E) Release boundary: 208 included and 14 held back from 222 designed systems, with held-back records grouped into major exclusion categories. Composition is shown for resource description; biological interpretation of family or ligand patterns is outside the scope of this Data Descriptor.

Source asset: scidata_figures/new_figure1_community_landscape.pdf

Figure 2. Repository organization, metadata schema and three-tier access model of CoupledMD. (A) Archive hierarchy, including manifest, metadata, systems, topology, trajectories, reduced files, features, pocket records, QC records, code and web/API snapshots. (B) Per-system metadata schema for system, receptor, G protein, ligand/state, replicas, files and QC status. (C) Archive-first access model: the stable archive is the citable record, while the web portal and REST API provide browse, visualization and programmatic access. (D) Portal-access schematic showing search, filters, structure viewing, download actions and API entry points. File formats and field definitions are detailed in Main Tables 2 and 3.

Source asset: scidata_figures/new_figure2_data_records.pdf

Figure 3. Technical validation and dataset-scope context for the CoupledMD clean-v1 release. (A) Best per-system orthosteric-pocket frequency by G-protein family; the dashed line marks the 0.85 recovery threshold and recovery percentages are annotated by family. (B) Per-system pocket-count distribution by family, summarized as median and interquartile range with individual-system points overlaid. (C) Descriptive comparison of system count and aggregate sampling against representative single-receptor GPCR and general-protein MD resources to contextualize the scope of CoupledMD. Validation is technical and does not interpret biological mechanism.

Source asset: scidata_figures/new_figure3_validation_ridgeline.pdf

Figure 4. QC and completeness summary of the CoupledMD clean-v1 release. (A) Derived TM-gateway open-fraction annotations across 208 systems, grouped by G-protein family for organizational convenience; family-resolved differences in panel A are not interpreted here. (B) Orthosteric-pocket recovery rate by G-protein family, shown as a compact structural-fidelity benchmark for the derived pocket layer. (C) Open-fraction distributions for the seven transmembrane gateway interfaces across the clean-v1 cohort. (D) Included versus held-back systems with major exclusion categories, accompanied by a reduced-trajectory integrity callout summarizing the PBC audit outcome. Biological interpretation of the gateway annotations is outside the scope of this Data Descriptor.

Source asset: scidata_figures/new_figure4_qc.pdf

Figure 5. Pocket-atlas annotations distributed with CoupledMD. (A) Reserved slot for a representative structural or portal-facing snapshot in the final composed figure. (B) Consensus druggable pocket clusters mapped by receptor coverage and mean occupancy, with point size reflecting cluster volume and color indicating anatomical zone. (C) Cluster-member counts by anatomical zone. (D) Reusable GPCRdb-position anchors appearing most frequently in orthosteric and druggable cluster cores. (E) Orthosteric recovery by family as a validation view for the pocket layer. (F) High-scoring drug-design nomination examples with representative receptors. Pocket clusters and proxy scores are derived annotations and are not experimental druggability validation; biological or pharmacological interpretation is outside the scope of this Data Descriptor.

Source asset: scidata_figures/new_figure5_drug_design_pocket_atlas.pdf

## Supplementary Figures

Supplementary Figure S1. Receptor-level coupling-topology dendrogram. Circular dendrogram of the 174 clean-v1 receptors clustered by presence or absence across the four major G-protein families. Leaf ticks are colored by single-family assignment or by multi-family representation, and each leaf is labeled by a representative four-letter PDB identifier. The figure provides receptor-level coupling-topology context for Figure 1 without implying mechanistic similarity among clustered receptors.

Supplementary Figure S1 provides the receptor-level context behind the compact counts in Figure 1. By clustering receptors according to whether they appear with Gi/o, Gs, Gq/11 or G12/13 partners, the figure separates single-family receptors from the smaller set of multi-family receptors that are especially suitable for within-receptor comparative reuse. The circular layout also allows readers to scan representative PDB coverage around the rim without consulting the full per-system tables.

Source asset: scidata_figures/new_figureS1_dendrogram.pdf

Supplementary Figure S2. Portal, archive and API coverage. (A) Portal-file availability by record type, separating present and missing system-level records. (B) Two-tier data-product size comparison between the production archive and the portal/API layer. (C) Documented REST surface grouped by manuscript-relevant use categories. Final file counts, sizes and checksum status are updated against the frozen archive before submission.

Supplementary Figure S2 expands the access and completeness information that is compressed in Figure 2. It reports which portal-facing record classes are currently available, contrasts the scale of the archival and web-facing layers, and summarizes how the documented REST endpoints are distributed across user-facing use categories. This figure is intended as an operational completeness view; final file counts, sizes and checksum status are updated against the frozen archive before submission.

Source asset: scidata_figures/new_figure_s2_portal_archive_coverage.pdf

Supplementary Figure S3. Portal/API access workflow. Workflow for interactive and programmatic access to CoupledMD. Panel A shows the user-facing browsing route from search and filtering to per-system pages, reduced-trajectory visualization and downloads. Panel B groups the programmatic API layers into status/citation, system, derived-record, visualization and consensus endpoints. Panel C restates the archive-first access model in which the stable repository remains the citable record. The workflow illustrates access routes and does not substitute for the stable archive record.

Supplementary Figure S3 shows the practical reuse path for a user who starts from the web portal or API rather than from the full archive. The workflow connects system browsing, filtering, per-system metadata, reduced-trajectory visualization, download actions and API retrieval into a single access route, while also making clear that the portal and API sit downstream of the authoritative archive. It is included to document usability and reproducibility of access, while the stable archive remains the source for citation and long-term reuse.

Source asset: scidata_figures/new_figureS3_portal_access.svg

## Tables

Main tables summarize the dataset, repository and metadata dictionary. Per-system and per-record detail is provided in the Supplementary Tables.

Table 2. Dataset summary of the CoupledMD clean-v1 release by GPCR class and G-protein family. Counts are based on the clean-v1 metadata; the 14 held-back systems are excluded. All included systems are represented by three 500 ns production replicas.

| GPCR class | G-protein family | Systems | Unique receptors | Aggregate sampling (µs) | Replicas per system | Per-replica length (ns) |

| --- | --- | --- | --- | --- | --- | --- |

| Class A | Gi/o | 85 | ≈70 | 127.5 | 3 | 500 |

| Class A | Gs | 63 | ≈55 | 94.5 | 3 | 500 |

| Class A | Gq/11 | 29 | ≈25 | 43.5 | 3 | 500 |

| Class A | G12/13 | 5 | ≈5 | 7.5 | 3 | 500 |

| Class B | Gi/o | 8 | ≈7 | 12.0 | 3 | 500 |

| Class B | Gs | 4 | ≈4 | 6.0 | 3 | 500 |

| Class B | Gq/11 | 13 | ≈12 | 19.5 | 3 | 500 |

| Class B | G12/13 | 1 | 1 | 1.5 | 3 | 500 |

| Total Class A | All | 182 | — | 273.0 | 3 | 500 |

| Total Class B | All | 26 | — | 39.0 | 3 | 500 |

| Total clean-v1 | All | 208 | 174 | 312.0 | 3 | 500 |

| Held-back cohort | — | 14 | — | — | — | — |

Per-class/family numbers for the G12/13 group are representative approximations pending the final clean-v1 metadata freeze; the aggregate counts (208 systems, 174 receptors, 312.0 µs) are the authoritative values.

Table 3. Metadata dictionary of the CoupledMD clean-v1 release. Authoritative field-level definition. Field names in the paper, repository metadata, API records and portal display are synchronized to this dictionary.

| Field | Type | Description / controlled vocabulary |

| --- | --- | --- |

| system_id | string | Family + PDB identifier, e.g. Gi_7F1Q |

| pdb_id | string | Primary PDB identifier[6] |

| receptor_name | string | IUPHAR/BPS recommended receptor name |

| receptor_uniprot | string | UniProt accession[7] |

| receptor_gene | string | Gene symbol where available |

| gpcr_class | enum | A \| B \| C \| F |

| gpcrdb_id | string | GPCRdb identifier where available[3,15] |

| g_protein_family | enum | Gi/o \| Gs \| Gq/11 \| G12/13 |

| g_alpha_subtype | string | Gα subtype (e.g. Gi1, Gs, Gq) |

| ligand_name | string | Ligand display name |

| ligand_chem_id | string | PDB chemical component ID where present |

| state | enum | active \| inactive \| engineered \| uncertain |

| source_pdb | string | Source PDB identifier |

| n_replicas | int | Number of production replicas (typically 3) |

| length_per_replica_ns | float | Per-replica production length (ns) |

| total_sampling_ns | float | Aggregate per-system sampling (ns) |

| force_field | string | CHARMM36m and engine/protocol annotations[8] |

| lipid_composition | string | POPC unless otherwise noted |

| trajectory_path | path | Production trajectory path |

| topology_path | path | Topology/parameter file path |

| qc_status | enum | OK \| WARN \| fail |

| qc_reason | string | Reason for non-OK status if any |

| traj_sha256 | hex | SHA-256 checksum of production trajectory |

| topo_sha256 | hex | SHA-256 checksum of topology file |

## Data Availability

The CoupledMD clean-v1 dataset is deposited in a stable public archive before publication[34]. Specific identifiers are inserted at proof stage.

Archive DOI/accession: [repository name, accession or DOI pending].

Web portal: https://www.coupledmd.cn

API documentation: https://www.coupledmd.cn/api/docs and https://www.coupledmd.cn/api/redoc, if these routes remain active at submission.

Dataset licence: CC-BY-4.0 (or the final selected open data licence).

Dataset version: clean-v1.

The web portal and API provide access and visualization layers. The archive record and checksum manifest should be cited for reproducible reuse.

## Code Availability

Code repository: [GitHub or institutional repository URL pending].

Code licence: MIT (or final selected open-source licence).

Figure and table generation scripts (generate_scidata_figure1.py, generate_scidata_figure2.py, generate_scidata_figure3.py, generate_scidata_figure4.py, generate_scidata_extra_figures.py) and supporting style and table-generation scripts are released alongside the manuscript. These Python workflows use standard scientific-computing, machine-learning, visualization and notebook tools, including SciPy, NumPy, Matplotlib, seaborn, scikit-learn and Jupyter where applicable[28-33]. The OpenAPI schema snapshot, JSON parsing utilities and qc/audit scripts are also distributed for reuse.

## Acknowledgements

[Acknowledgements for computing resources, institutional support, data curation support, website/server support, GPCRdb/GPCRmd-related discussions where appropriate, and repository support should be added at submission.]

## Funding

[Grant numbers, institutional funding, computing allocations and fellowship support should be added at submission.]

## Author Contributions

[Author initials] conceived the dataset. [Author initials] curated the GPCR/G-protein system inventory. [Author initials] prepared and ran molecular dynamics simulations. [Author initials] generated trajectory-processing and annotation workflows. [Author initials] developed the web portal and REST API. [Author initials] generated figures and tables. [Author initials] wrote the manuscript with input from all authors. All authors reviewed and approved the final manuscript.

## Competing Interests

The authors declare no competing interests. [Revise if any financial, advisory, patent, employment or software-related interests apply.]

## References

1. Hauser, A. S., Chavali, S., Masuho, I., Jahn, L. J., Martemyanov, K. A., Gloriam, D. E. & Babu, M. M.. Pharmacogenomics of GPCR drug targets.  Cell 172, 197–214 (2018). https://doi.org/10.1016/j.cell.2017.12.027

2. Weis, W. I. & Kobilka, B. K.. The molecular basis of G protein-coupled receptor activation.  Annu. Rev. Biochem. 87, 897–919 (2018). https://doi.org/10.1146/annurev-biochem-060614-033910

3. Kooistra, A. J., Mordalski, S., Pándy-Szekeres, G., Esguerra, M., Mamyrbekov, D., Karpiarz, A., et al.. GPCRdb in 2024: integrating GPCR sequence, structure and function.  Nucleic Acids Res. 52, D148–D157 (2024). https://doi.org/10.1093/nar/gkad1011

4. Rodriguez-Espigares, I., Tournier, M., Bondarev, D., Maria, C., Marrink, S. J., Deupi, X. & Gutierrez-de-Terán, H.. GPCRmd uncovers the dynamics of the 3D-GPCRome.  Nat. Methods 17, 777–787 (2020). https://doi.org/10.1038/s41592-020-0884-y

5. Mirarchi, A., Giorgino, T. & De Fabritiis, G.. mdCATH: a large-scale MD dataset for data-driven computational biophysics.  Sci. Data 11, 1299 (2024). https://doi.org/10.1038/s41597-024-04140-z

6. Berman, H. M., Westbrook, J., Feng, Z., Gilliland, G., Bhat, T. N., Weissig, H., et al.. The Protein Data Bank.  Nucleic Acids Res. 28, 235–242 (2000). https://doi.org/10.1093/nar/28.1.235

7. UniProt Consortium. UniProt: the Universal Protein Knowledgebase in 2025.  Nucleic Acids Res. 53, D609–D617 (2025). https://doi.org/10.1093/nar/gkae1010

8. Huang, J., Rauscher, S., Nawrocki, G., Ran, T., Feig, M., de Groot, B. L., et al.. CHARMM36m: an improved force field for folded and intrinsically disordered proteins.  Nat. Methods 14, 71–73 (2017). https://doi.org/10.1038/nmeth.4067

9. Jo, S., Kim, T., Iyer, V. G. & Im, W.. CHARMM-GUI: a web-based graphical user interface for CHARMM.  J. Comput. Chem. 29, 1859–1865 (2008). https://doi.org/10.1002/jcc.20945

10. Lee, J., Cheng, X., Swails, J. M., Yeom, M. S., Eastman, P. K., Lemkul, J. A., et al.. CHARMM36 input generator for NAMD, GROMACS, AMBER, and OpenMM.  J. Chem. Theory Comput. 12, 405–413 (2016). https://doi.org/10.1021/acs.jctc.5b00935

11. Salomon-Ferrer, R., Goetz, A. W., Poole, D., Le Grand, S. & Walker, R. C.. Routine microsecond molecular dynamics simulations with AMBER on GPUs. 2. Explicit solvent particle mesh Ewald.  J. Chem. Theory Comput. 9, 3878–3888 (2013). https://doi.org/10.1021/ct400314y

12. Abraham, M. J., Murtola, T., Schulz, R., Páll, S., Smith, J. C., Hess, B. & Lindahl, E.. GROMACS: high performance molecular simulations through multi-level parallelism from laptops to supercomputers.  SoftwareX 1–2, 19–25 (2015). https://doi.org/10.1016/j.softx.2015.06.001

13. Le Guilloux, V., Schmidtke, P. & Tuffery, P.. Fpocket: an open source platform for ligand pocket detection.  BMC Bioinformatics 10, 168 (2009). https://doi.org/10.1186/1471-2105-10-168

14. Rose, A. S., Bradley, A. R., Valasatava, Y., Duarte, J. M., Prlić, A. & Rose, P. W.. NGL viewer: web-based molecular graphics for large complexes.  Bioinformatics 34, 3755–3758 (2018). https://doi.org/10.1093/bioinformatics/bty419

15. Isberg, V., de Graaf, C., Bortolato, A., Cherezov, V., Katritch, V., Marshall, F. H., et al.. Generic GPCR residue numbers aligning topology and function.  Trends Pharmacol. Sci. 36, 22–31 (2015). https://doi.org/10.1016/j.tips.2014.11.001

16. Flock, T., Hauser, A. S., Lund, M. L., Gloriam, D. E., Balaji, S. & Babu, M. M.. Selectivity determinants of GPCR–G-protein binding.  Nature 545, 317–322 (2017). https://doi.org/10.1038/nature22070

17. Pándy-Szekeres, G., Tar, I., Barsi-Rodríguez, A., Bhardwaj, N., Borsodi, F. A., Esguerra, M., et al.. GPCRdb 2.0: machine learning, crowd-sourcing and the GPCR-HGMD structural database.  Nucleic Acids Res. 53, D444–D453 (2025). https://doi.org/10.1093/nar/gkae1011

18. Eddy, S. R.. Accelerated profile HMM searches.  PLoS Comput. Biol. 7, e1002195 (2011). https://doi.org/10.1371/journal.pcbi.1002195

19. Edgar, R. C.. MUSCLE: multiple sequence alignment with high accuracy and high throughput.  Nucleic Acids Res. 32, 1792–1797 (2004). https://doi.org/10.1093/nar/gkh340

20. Klimovich, A. V. & Abersold, J.. In silico structural analysis of the G protein–coupled receptors.  Biochemistry (Moscow) 89, S50–S68 (2024). https://doi.org/10.1134/S0006297924140041

21. Bussi, G., Donadio, D. & Parrinello, M.. Canonical sampling through velocity rescaling.  J. Chem. Phys. 126, 014101 (2007). https://doi.org/10.1063/1.2408420

22. Berendsen, H. J. C., Postma, J. P. M., van Gunsteren, W. F., DiNola, A. & Haak, J. R.. Molecular dynamics with coupling to an external bath.  J. Chem. Phys. 81, 3684–3690 (1984). https://doi.org/10.1063/1.448118

23. Parrinello, M. & Rahman, A.. Polymorphic transitions in single crystals: a new molecular dynamics method.  J. Appl. Phys. 52, 7182–7190 (1981). https://doi.org/10.1063/1.328693

24. Hess, B., Bekker, H., Berendsen, H. J. C. & Fraaije, J. G. E. M.. LINCS: a linear constraint solver for molecular simulations.  J. Comput. Chem. 18, 1463–1472 (1997). https://doi.org/10.1002/(SICI)1096-987X(199709)18:12<1463::AID-JCC4>3.0.CO;2-H

25. Darden, T., York, D. & Pedersen, L.. Particle mesh Ewald: an N·log(N) method for Ewald sums in large systems.  J. Chem. Phys. 98, 10089–10092 (1993). https://doi.org/10.1063/1.464397

26. Michaud-Agrawal, N., Denning, E. J., Woolf, T. B. & Beckstein, O.. MDAnalysis: a toolkit for the analysis of molecular dynamics simulations.  J. Comput. Chem. 32, 2319–2327 (2011). https://doi.org/10.1002/jcc.21787

27. McGibbon, R. T., Beauchamp, K. A., Harrigan, M. P., Klein, C., Swails, J. M., Hernández, C. X., et al.. MDTraj: a modern open library for the analysis of molecular dynamics trajectories.  Biophys. J. 109, 1528–1532 (2015). https://doi.org/10.1016/j.bpj.2015.08.015

28. Virtanen, P. et al.. SciPy 1.0: fundamental algorithms for scientific computing in Python.  Nat. Methods 17, 261–272 (2020). https://doi.org/10.1038/s41592-019-0686-2

29. Harris, C. R. et al.. Array programming with NumPy.  Nature 585, 357–362 (2020). https://doi.org/10.1038/s41586-020-2649-2

30. Hunter, J. D.. Matplotlib: a 2D graphics environment.  Comput. Sci. Eng. 9, 90–95 (2007). https://doi.org/10.1109/MCSE.2007.55

31. Waskom, M.. seaborn: statistical data visualization.  J. Open Source Softw. 6, 3021 (2021). https://doi.org/10.21105/joss.03021

32. Pedregosa, F. et al.. Scikit-learn: machine learning in Python.  J. Mach. Learn. Res. 12, 2825–2830 (2011).

33. Kluyver, T. et al.. Jupyter Notebooks – a publishing format for reproducible computational workflows.  Positioning and Power in Academic Publishing: Players, Agents and Agendas, 87–90 (2016).

34. Manghi, P. et al.. Zenodo: a free, open and reliable archive for scientific data.  Sci. Data 9, 186 (2022). https://doi.org/10.1038/s41597-022-01337-y
