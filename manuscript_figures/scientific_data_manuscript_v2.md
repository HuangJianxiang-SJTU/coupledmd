# CoupledMD, a molecular dynamics dataset of GPCR/G-protein complexes

## Abstract

G protein-coupled receptors (GPCRs) are central drug targets and signal through heterotrimeric G proteins, but reusable molecular dynamics (MD) records for active GPCR/G-protein complexes remain limited by protocol, format, annotation and access heterogeneity. We describe CoupledMD clean-v1, a standardized MD dataset of 208 active-state GPCR/G-protein complex systems spanning 174 receptors, two GPCR classes and the Gi/o, Gs, Gq/11 and G12/13 G-protein families. Each included system follows a 3 x 500 ns production design in a POPC membrane, yielding 312.0 us of aggregate sampling. The release includes production trajectories, topology and structure files, reduced visualization trajectories, system metadata, GPCRdb-compatible receptor annotations, pocket records, G-protein and gateway-derived annotation records, quality-control summaries, manifests and figure/table scripts. Technical validation includes clean-v1 inclusion and held-back reporting, orthosteric-pocket recovery, pocket-count distributions, reduced-trajectory periodic-boundary audits and frame-count checks. CoupledMD is intended to support GPCR community reuse, benchmarking, method development, residue-level annotation workflows and downstream drug-design studies while leaving biological mechanism interpretation to future work.

## Background & Summary

GPCRs translate extracellular signals into intracellular responses and remain one of the most productive families for therapeutic intervention [1]. Active GPCRs couple to heterotrimeric G proteins from the Gi/o, Gs, Gq/11 and G12/13 families [2], and structural biology has produced a rapidly expanding set of receptor/G-protein complex structures. These structures provide critical snapshots, but comparative reuse across receptors and G-protein families requires standardized simulation records, consistent annotation and practical access routes.

Several public resources have shaped the current landscape. GPCRdb provides receptor classification, sequence alignments, structural annotations and generic residue numbering that make cross-receptor comparison possible [3]. GPCRmd established the value of community-accessible GPCR trajectory resources [4]. The mdCATH Data Descriptor provides a useful model for presenting a large MD resource through cohort definition, file organization, technical validation and usage notes [5]. CoupledMD follows the same descriptor discipline but addresses a different data type: multi-chain, membrane-embedded active GPCR/G-protein complexes with receptor, G-protein, pocket and web/API annotation layers.

CoupledMD clean-v1 contains 208 included systems selected from an initial designed inventory of 222 systems. The clean-v1 cohort spans 174 receptors, Class A and Class B GPCRs, and all four major G-protein family groups represented in the current structural record. The included systems comprise 93 Gi/o systems, 67 Gs systems, 42 Gq/11 systems and 6 G12/13 systems. Class A receptors account for 182 systems and Class B receptors account for 26 systems. The nominal design is three independent 500 ns production replicas per system, corresponding to 1.5 us per system and 312.0 us of aggregate sampling across the release.

The dataset is organized around three questions that match the expectations of a Scientific Data descriptor. First, what is in the release? CoupledMD provides a defined clean-v1 cohort, a transparent held-back cohort and coverage summaries by receptor class, G-protein family and ligand context. Second, can users trust the records? The release includes technical validation of pocket recovery, derived pocket-count distributions, reduced-trajectory frame counts and periodic-boundary checks. Third, how can users access and reuse the dataset? The archival repository is the citable data record, while the web portal and REST API provide interactive and programmatic access to selected metadata, reduced trajectories and derived annotations.

This manuscript deliberately avoids biological interpretation of family-resolved differences. Pocket, gateway and G-protein records are described as derived annotations distributed with the resource. They are included to make the dataset reusable, not to claim a mechanism of coupling, selectivity, biased signaling or partner switching. Those analyses are outside the scope of this Data Descriptor.

## Methods

### System selection and clean-v1 cohort definition

The starting inventory contained 222 GPCR/G-protein complex systems. Each candidate system was curated with a system identifier, primary PDB identifier, receptor name, UniProt accession, GPCR class, G-protein family assignment, G-alpha subtype annotation, ligand annotation, structural-provenance flag, simulation design metadata and file-availability metadata. The clean-v1 release contains the 208 systems that passed the current release gates for a uniform 3 x 500 ns dataset and associated metadata, topology, trajectory and processed-record availability.

Fourteen systems were held back from the initial clean-v1 release. The held-back set includes systems with nonstandard trajectory lengths, nonstandard replica counts, temporary or incomplete source-file flags, missing processed pocket/grid outputs or source records requiring verification or rerun. These systems are not silently removed: they are listed in Supplementary Table S2 with exclusion reasons and rerun or verification status. This strategy keeps the released cohort conservative while preserving a record of the full designed inventory.

### Structure sourcing and annotation

Active-state GPCR/G-protein complex structures were identified from experimentally determined structures and associated receptor and G-protein annotations [6]. Receptor records were cross-referenced with UniProt and GPCRdb-compatible identifiers where available [3,7]. G-protein records were grouped into Gi/o, Gs, Gq/11 and G12/13 family categories and annotated with G-alpha subtype labels where available. Structural provenance was recorded for every system. In clean-v1, 197 included systems are experimental-coordinate derived and 11 are flagged as engineered or uncertain so that users can apply stricter filters if required.

The primary system identifier follows a family plus PDB pattern such as `Gi_7F1Q`, while the metadata table stores the corresponding PDB identifier, receptor name, receptor UniProt accession, receptor gene where available, GPCR class, G-protein family, G-alpha subtype, ligand fields, simulation fields and QC fields.

### Simulation preparation and production design

Included systems were prepared under a common CHARMM36-family membrane simulation protocol and embedded in a POPC membrane environment [8,9]. The clean-v1 release is defined around a uniform production design of three 500 ns replicas per included system. The metadata table records the force-field/protocol annotation, lipid composition, trajectory type, replica count, per-replica length and aggregate sampling per system.

The final repository should retain engine-specific input and topology files alongside the production trajectories so that downstream users can reproduce or extend analyses. Where trajectories originate from different engines or converted topology formats, the archive metadata should state the format and required software explicitly.

### Trajectory processing and reduced visualization records

Full production trajectories are the primary molecular records and belong in the stable archive. Simulations and trajectory processing used standard MD software appropriate to the source system and trajectory format [10,11]. A reduced visualization tier was generated for web and lightweight reuse. Reduced trajectories are protein-focused, decimated records with matching reduced reference structures, intended for interactive inspection through the portal and rapid system review. These reduced records are useful for visualization and screening but do not replace full production trajectories for quantitative reanalysis.

The reduced visualization layer was audited for frame count, atom-count agreement, blank element fields, box mismatch flags, intra-chain breaks, inter-chain splits and scatter-frame warnings. These checks are summarized in Technical Validation and Supplementary Tables T8a and T8b.

### Pocket detection and GPCRdb mapping

Pocket records were generated as derived annotations for each included system where pocket outputs were available [12]. The technical validation workflow uses orthosteric-pocket recovery as a positive-control style check because ligand-accessible receptor pockets are expected to be recovered in many ligand-bearing active complexes. Pocket-lining residues were mapped to GPCRdb-compatible generic positions where available [3], allowing users to compare pocket records across receptors without relying only on receptor-specific residue numbers.

Orthosteric-pocket recovery was evaluated using a best per-system orthosteric-pocket frequency and a 0.85 frequency threshold. This metric is used as technical validation of known structural-feature recovery and annotation stability. It is not interpreted as a biological mechanism or as experimental evidence of ligand binding.

### Gateway and G-protein derived annotations

The dataset also distributes derived gateway and G-protein annotation records. Gateway records summarize defined transmembrane-helix interface measurements, while G-protein records provide CGN-compatible annotation layers where available. In this Data Descriptor, these records are described as machine-readable annotations and access-layer features. Family-resolved biological interpretation of gateway or G-protein dynamics is outside the scope of Paper 1 and is reserved for downstream studies.

### Archive, portal and API generation

CoupledMD is designed with three access layers. The stable archive is the citable data record and should contain the full trajectories, topologies, structures, metadata, processed annotations, manifests, checksums, documentation and code snapshots. The web portal at https://www.coupledmd.cn provides interactive browsing, filtering, visualization and selected downloads. The REST API exposes metadata and processed records for programmatic reuse.

The portal is implemented as an access layer rather than the authoritative archive. The manuscript and website should both point users to the final repository DOI or accession once minted. An OpenAPI snapshot dated 2026-07-07 is present in the manuscript figure workspace and should be refreshed at submission if the API changes.

## Data Records

### Dataset scope

The clean-v1 release includes 208 GPCR/G-protein systems, 174 unique receptors and 312.0 us of aggregate sampling. The cohort comprises 93 Gi/o systems, 67 Gs systems, 42 Gq/11 systems and 6 G12/13 systems. By GPCR class, the release contains 182 Class A systems and 26 Class B systems. All clean-v1 systems are represented with three 500 ns replicas in the metadata-level release definition.

The full designed inventory and held-back systems are documented to make the release boundary transparent. The held-back cohort contains 14 systems and is excluded from the 208-system clean-v1 counts, figures and technical validation unless explicitly stated.

### Repository organization

The final archive should use a predictable hierarchy matching Main Figure 2 and Main Table 2:

| Path or item | Contents | Manuscript use |
| --- | --- | --- |
| `manifest/` | Dataset-level file manifest, version, checksums and archive index | Main archive; required before submission |
| `metadata/systems.csv` | Per-system metadata for included clean-v1 systems | Clean-v1 inventory |
| `metadata/held_back_systems.csv` | Systems excluded from the initial release and exclusion reasons | Supplementary transparency table |
| `systems/<system_id>/metadata.json` | System annotation, receptor, G-protein, ligand, source and QC fields | One record per included system |
| `systems/<system_id>/topology/` | Prepared structures and topology/parameter files | Archive record |
| `systems/<system_id>/trajectories/rep{1..3}/` | Full production trajectories for each replica | Stable repository record |
| `systems/<system_id>/reduced/` | Aligned or strided trajectories for visualization and rapid reuse | Web/API and archive record |
| `systems/<system_id>/features/` | Derived feature summaries as available | Processed analysis layer |
| `systems/<system_id>/pocket/` | Pocket outputs, orthosteric summaries and GPCRdb-mapped records | Validation and reuse layer |
| `systems/<system_id>/qc/` | Completeness, frame counts, PBC status and file-integrity checks | Technical validation |
| `code/` | Processing scripts, notebooks and figure/table-generation scripts | Code availability |
| `web_api_snapshot/` | OpenAPI schema and selected JSON endpoint snapshots | Portal/API documentation |

The submitted archive should include final file sizes and SHA256 checksums. Current manifest tables are useful for manuscript drafting but must be replaced or confirmed against the frozen archive before submission.

### Metadata dictionary

The primary metadata record includes `system_id`, `pdb_id`, `receptor_name`, `receptor_uniprot`, `receptor_gene`, `gpcr_class`, `gpcrdb_id` where available, `g_protein_family`, `g_alpha_subtype`, `ligand_name`, `ligand_chem_id`, `state`, `source_pdb`, `n_replicas`, `length_per_replica_ns`, `total_sampling_ns`, `force_field`, `lipid_composition`, `trajectory_path`, `topology_path`, `qc_status`, `qc_reason`, `traj_sha256` and `topo_sha256`. Units should be stated for all numeric fields, including ns for simulation length and bytes for file size. Enumerated fields such as GPCR class, G-protein family and QC status should use controlled vocabularies.

Main Table 3 should be the authoritative metadata dictionary. Field names in the paper, repository metadata, API records and portal display should be synchronized before submission.

### Portal and API records

The web portal at https://www.coupledmd.cn supports interactive access to the release through system browsing, filtering, per-system pages, reduced-trajectory visualization and downloads [13]. The REST API exposes versioned records under `/api/v1/`, including system lists, per-system metadata, pocket records, gateway records, G-protein records, visualization metadata, reduced structures, reduced trajectories, citation metadata and licence metadata. API documentation is provided through interactive documentation pages and the OpenAPI schema.

At the time of this draft, the portal/API manifest summary contains 2080 records across 208 systems, with 1247 checksums computed and 833 checksums pending for binary or large files. The record-level portal availability table reports complete API gateway, G-protein, index, pocket, chain-role and visualization structure/trajectory coverage for 208 systems, with one missing `api_pockets_gpcrdb` record and one missing `contacts` record. Pocket-grid, contact and visualization binary checksums remain pending for the final archive process.

The portal is a usability and access layer. The archive DOI or accession listed in Data Availability should be treated as the stable record for citation and long-term reuse.

## Technical Validation

### Clean-v1 release gate and held-back transparency

The clean-v1 cohort was defined by applying conservative inclusion gates to the 222-system designed inventory. All 208 included systems passed metadata-level checks for the 3 x 500 ns release definition, trajectory path presence and topology path presence. The 14 held-back systems are listed with reasons in Supplementary Table S2. Held-back reasons include nonstandard length, nonstandard replica count, temporary or incomplete source-file flags, missing processed pocket/grid outputs and source records requiring verification or rerun.

This reporting follows the same transparency principle used by database-style Data Descriptors: release failures and exclusions are documented rather than hidden. The held-back systems are not used to inflate the clean-v1 counts or aggregate sampling.

### Pocket recovery validation

Pocket records were available for 206 of 208 included systems. Orthosteric-pocket recovery at the 0.85 frequency threshold was observed in 156 of the 206 systems with pocket outputs. Family-level recovery was 66 of 91 Gi/o systems with pocket outputs (72.5%), 51 of 67 Gs systems (76.1%), 35 of 42 Gq/11 systems (83.3%) and 4 of 6 G12/13 systems (66.7%). By ligand annotation in the validation table, recovery was 92 of 97 small-molecule systems with pocket outputs (94.8%) and 64 of 75 peptide systems (85.3%); systems annotated as having no ligand were not expected to recover an orthosteric ligand pocket under this validation definition.

This validation demonstrates recovery of expected ligand-accessible structural features and consistency of the pocket annotation pipeline. It should not be interpreted as a mechanistic result or as experimental validation of druggability.

### Pocket-count distributions

The per-system number of detected pockets provides an additional technical check on the derived annotation layer. Across families, median pocket counts were 10 for Gi/o, 11 for Gs, 11 for Gq/11 and 10.5 for G12/13. Family-level ranges were 0 to 18 for Gi/o, 5 to 18 for Gs, 5 to 19 for Gq/11 and 3 to 14 for G12/13. These values are used as descriptive validation of annotation availability and distribution, not as evidence for family-specific function.

### Reduced-trajectory PBC and frame-count audit

The reduced visualization trajectories were audited across 208 clean-v1 systems. The audit reported 205 OK systems, 3 WARN systems and 0 hard failures. No atom-count mismatches, blank PDB element fields, PDB/trajectory box mismatches, intra-chain break frames or inter-chain split frames were detected in the summary audit. Seven minor scatter frames were observed across the checked-frame sample.

Reduced-trajectory frame counts were 2500 frames for 205 systems, 2501 frames for 2 systems and 200 frames for 1 system. The short reduced visualization record is `Gs_3SN6`; the production metadata for the system remains in the clean-v1 cohort and the reduced-record difference is flagged. Systems with WARN status were `Gi_8J22`, `Gq_7XJL` and `Gs_7F4H`, each with minor scatter warnings and no hard audit failure.

### File manifests and checksums

The current archive manifest derived from metadata contains 650 records across 208 systems, with final production-archive checksums pending. The portal file manifest contains 2080 records across 208 systems, with 1247 checksums computed and 833 pending. The OpenAPI snapshot contains 27 records and has a checksum. Before submission, the archive manifest should be regenerated from the frozen repository layout, with SHA256 checksums for all submitted files and clear notes for any files omitted or represented through external storage.

### Limitations

CoupledMD clean-v1 is limited to active-state GPCR/G-protein complex systems and does not attempt to cover inactive receptors, GPCR-arrestin complexes or ligand-free ensembles for every receptor. The release is shaped by available structures, so G12/13 systems are under-represented relative to Gi/o, Gs and Gq/11. The standard production design is 500 ns per replica and may not sample slower conformational transitions. Pocket, gateway and G-protein records are derived annotations and require study-specific validation for biological interpretation. Some final publication elements remain pending, including the archive DOI/accession, final SHA256 manifest, final production-archive frame audit and replacement of the portal screenshot placeholder in Main Figure 2.

## Usage Notes

CoupledMD can be reused at three levels. First, users performing quantitative trajectory analysis should use the stable archive because it contains the full production trajectories, topology files, metadata, manifests and checksums. Second, users who need rapid system selection or method benchmarking can use processed tables and JSON records, including system metadata, pocket annotations, gateway records, G-protein records and QC summaries. Third, users who need interactive inspection can use the portal and reduced visualization trajectories.

Example reuse workflows include filtering systems by GPCR class, G-protein family, receptor name, UniProt accession, PDB identifier or ligand annotation; retrieving reduced structures and trajectories for visualization; joining GPCRdb-mapped pocket residues to external receptor annotations; and using API endpoints to build reproducible system lists before downloading full trajectories from the archive.

Example API calls for the live portal are:

```bash
curl https://www.coupledmd.cn/api/v1/health
curl "https://www.coupledmd.cn/api/v1/systems?family=Gi&limit=10"
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q/pockets
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q/viz/meta
```

Users should cite the Scientific Data article and the dataset DOI once available. Users of the code or API schema should also cite the code repository according to the repository citation file. The web portal may evolve for usability, but the archive version and checksum manifest should be used for reproducible citation.

## Data Availability

The CoupledMD clean-v1 dataset will be deposited in a stable public archive before publication.

Archive DOI/accession: `[repository name, accession or DOI pending]`.  
Reviewer access link: `[private reviewer URL or tokenized repository link pending]`.  
Web portal: https://www.coupledmd.cn.  
API documentation: `https://www.coupledmd.cn/api/docs` and `https://www.coupledmd.cn/api/redoc` if these routes remain active at submission.  
Dataset licence: CC-BY-4.0 or final selected open data licence.  
Dataset version: clean-v1.

The web portal and API provide access and visualization layers. The archive record and checksum manifest should be cited for reproducible reuse.

## Code Availability

Processing scripts, figure-generation scripts, table-generation scripts, API schema snapshots and website/API code should be released through a public code repository or archived code snapshot before publication.

Code repository: `[GitHub or institutional repository URL pending]`.  
Code licence: MIT or final selected open-source licence.  
Figure scripts: `generate_scidata_figure1.py`, `generate_scidata_figure2.py`, `generate_scidata_figure3.py`, `generate_scidata_figure4.py`, `generate_scidata_extra_figures.py` and supporting style/table-generation scripts.

## Acknowledgements

`[Add acknowledgements for computing resources, institutional support, data curation support, website/server support, GPCRdb/GPCRmd-related discussions if appropriate and repository support.]`

## Funding

`[Add grant numbers, institutional funding, computing allocations and fellowship support.]`

## Author Contributions

`[Author initials]` conceived the dataset. `[Author initials]` curated the GPCR/G-protein system inventory. `[Author initials]` prepared and ran molecular dynamics simulations. `[Author initials]` generated trajectory-processing and annotation workflows. `[Author initials]` developed the web portal and REST API. `[Author initials]` generated figures and tables. `[Author initials]` wrote the manuscript with input from all authors. All authors reviewed and approved the final manuscript.

## Competing Interests

The authors declare no competing interests. `[Revise if any financial, advisory, patent, employment or software-related interests apply.]`

## References

[1] Hauser, A. S. et al. Trends in GPCR drug discovery: new agents, targets and indications. *Nat. Rev. Drug Discov.* **16**, 829-842 (2017). https://doi.org/10.1038/nrd.2017.178

[2] Weis, W. I. & Kobilka, B. K. The molecular basis of G protein-coupled receptor activation. *Annu. Rev. Biochem.* **87**, 897-919 (2018). https://doi.org/10.1146/annurev-biochem-060614-033910

[3] Kooistra, A. J. et al. GPCRdb in 2021: integrating GPCR sequence, structure and function. *Nucleic Acids Res.* **49**, D335-D343 (2021). https://doi.org/10.1093/nar/gkaa1080

[4] Rodriguez-Espigares, I. et al. GPCRmd uncovers the dynamics of the 3D-GPCRome. *Nat. Methods* **17**, 777-787 (2020). https://doi.org/10.1038/s41592-020-0884-y

[5] Mirarchi, A., Giorgino, T. & De Fabritiis, G. mdCATH, a large-scale MD dataset for data-driven computational biophysics. *Sci. Data* **11**, 1299 (2024). https://doi.org/10.1038/s41597-024-04164-8

[6] Berman, H. M. et al. The Protein Data Bank. *Nucleic Acids Res.* **28**, 235-242 (2000). https://doi.org/10.1093/nar/28.1.235

[7] UniProt Consortium. UniProt: the Universal Protein Knowledgebase in 2023. *Nucleic Acids Res.* **51**, D523-D531 (2023). https://doi.org/10.1093/nar/gkac1052

[8] Huang, J. et al. CHARMM36m: an improved force field for folded and intrinsically disordered proteins. *Nat. Methods* **14**, 71-73 (2017). https://doi.org/10.1038/nmeth.4067

[9] Jo, S., Kim, T., Iyer, V. G. & Im, W. CHARMM-GUI: a web-based graphical user interface for CHARMM. *J. Comput. Chem.* **29**, 1859-1865 (2008). https://doi.org/10.1002/jcc.20945

[10] Salomon-Ferrer, R., Goetz, A. W., Poole, D., Le Grand, S. & Walker, R. C. Routine microsecond molecular dynamics simulations with AMBER on GPUs. 2. Explicit solvent particle mesh Ewald. *J. Chem. Theory Comput.* **9**, 3878-3888 (2013). https://doi.org/10.1021/ct400314y

[11] Abraham, M. J. et al. GROMACS: High performance molecular simulations through multi-level parallelism from laptops to supercomputers. *SoftwareX* **1-2**, 19-25 (2015). https://doi.org/10.1016/j.softx.2015.06.001

[12] Le Guilloux, V., Schmidtke, P. & Tuffery, P. Fpocket: an open source platform for ligand pocket detection. *BMC Bioinformatics* **10**, 168 (2009). https://doi.org/10.1186/1471-2105-10-168

[13] Rose, A. S. et al. NGL viewer: web-based molecular graphics for large complexes. *Bioinformatics* **34**, 3755-3758 (2018). https://doi.org/10.1093/bioinformatics/bty419
