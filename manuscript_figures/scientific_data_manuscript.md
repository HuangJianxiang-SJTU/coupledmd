# Molecular dynamics simulations of 222 G protein-coupled receptor G-protein complexes

## Alternative Scientific Data-compliant titles

1. Molecular dynamics simulations of 222 G protein-coupled receptor G-protein complexes
2. A molecular dynamics dataset for 222 GPCR G-protein complexes
3. Standardized simulations of GPCR G-protein complexes in membrane environments

Preferred title: **Molecular dynamics simulations of 222 G protein-coupled receptor G-protein complexes**.

## Abstract

G protein-coupled receptors (GPCRs) signal through heterotrimeric G proteins, but comparative molecular dynamics data for GPCR-G-protein complexes remain difficult to reuse because published simulations differ in preparation, force fields, membrane composition, trajectory length and annotation. We generated a standardized molecular dynamics dataset for 222 active-state GPCR-G-protein ternary complexes spanning Gi/o, Gs, Gq/11 and G12/13 families. Each system was prepared with a common CHARMM36-family force-field protocol in a POPC membrane environment and was simulated as replicate trajectories, providing approximately 333 microseconds of aggregate sampling. The dataset includes system metadata, receptor and G-protein annotations, trajectory files, reduced visualization trajectories, topology and structure files, GPCRdb-compatible residue mappings, pocket annotations, membrane-gateway measurements, G-protein interface features and summary tables. Technical validation includes trajectory-completeness checks, annotation consistency checks, analysis-availability audits and recovery of known ligand-accessible receptor pockets. The dataset is intended to support reusable benchmarking, method development and future comparative studies of GPCR activation and coupling.

## Background & Summary

G protein-coupled receptors (GPCRs) are a large family of membrane proteins that convert extracellular chemical and sensory inputs into intracellular signalling responses. Active GPCRs engage heterotrimeric G proteins from the Gi/o, Gs, Gq/11 and G12/13 families. Experimental structures have provided many snapshots of active-state GPCR-G-protein complexes, and resources such as GPCRdb provide cross-receptor sequence, structure and generic-numbering annotations. Molecular dynamics (MD) simulations can complement these static structures by sampling receptor, ligand, membrane and G-protein motions, but comparative reuse of GPCR-G-protein trajectories is limited when simulations are generated with heterogeneous force fields, membrane compositions, simulation lengths and analysis workflows.

This Data Descriptor reports a standardized MD dataset for 222 active-state GPCR-G-protein ternary complexes. The dataset was designed as a reusable reference collection rather than as a single mechanistic study. The cohort spans all four major G-protein families and includes 182 unique receptors. Systems were selected from experimentally determined GPCR-G-protein structures and curated into a consistent inventory with receptor names, UniProt identifiers, PDB identifiers, ligand annotations, G-protein family assignments, structural-provenance flags and analysis-availability flags. All systems were prepared with a common CHARMM36-family membrane-simulation protocol and embedded in a POPC lipid bilayer. The nominal simulation design was three independent 500 ns replicas per system; the audited current inventory totals approximately 332.3 microseconds because a small number of systems deviate from the nominal length or replica count, as described under Technical Validation.

The archived data are intended to include complete production trajectories, input structures, topology files, per-system metadata, processed feature tables and derived analyses. A companion web portal provides an interactive access layer for browsing, filtering, visualizing and downloading selected records, but the archival repository is the long-term data record for reproducibility. The web portal and REST API expose system metadata, per-system pocket annotations, GPCRdb-mapped residue labels, membrane-gateway metrics, reduced visualization trajectories and consensus summary tables. This distinction is important: the website improves usability, whereas the archival repository should provide stable downloadable records, manifests, checksums, versioning and a DOI or accession.

### Dataset design requirements

Following the structure used by recent Scientific Data molecular-dynamics Data Descriptors, this dataset was organized around the following design requirements:

- **Targeted coverage of active GPCR-G-protein complexes.** The dataset focuses on active-state ternary complexes and spans the four major G-protein families, allowing users to select systems by receptor, G-protein family, ligand state, structural provenance and analysis availability.
- **Protocol consistency.** Systems were prepared with a common CHARMM36-family membrane-simulation protocol and a shared processing pipeline, reducing protocol heterogeneity during comparative reuse.
- **Reusable molecular records.** The archival record is intended to include structures, topologies, full trajectories, reduced visualization trajectories, metadata, manifests and checksums so that users can reproduce or extend analyses without depending on the live website.
- **GPCR-compatible annotation.** Receptor and pocket features are linked to UniProt, PDB and GPCRdb-compatible residue annotations where available; G-protein features are indexed to CGN labels where available.
- **Derived analysis layers.** Pocket annotations, gateway metrics, G-protein interface features and cohort summary tables are provided as processed records for users who do not need to reprocess the full multi-terabyte trajectory set.
- **Interactive and programmatic access.** A web portal and REST API provide browsing, filtering, visualization and selected downloads, while the archival repository provides the stable citable dataset.
- **Transparent quality flags.** Systems with nonstandard trajectory length, missing processed outputs, incomplete temporary files or pilot-only analyses are flagged so that users can choose inclusion criteria appropriate for their downstream analyses.

The manuscript deliberately restricts interpretation of biological mechanisms. Analyses such as pocket recovery, orthosteric-site recovery, trajectory completeness and annotation consistency are used here as technical validation and examples of reuse. Broader questions about biased signalling, G-protein selectivity, partner switching, structural determinants of coupling and allosteric pathways are reserved for a separate mechanistic paper.

## Methods

### System selection and curation

Active-state GPCR-G-protein ternary-complex structures were collected from the Protein Data Bank and cross-referenced with GPCRdb annotations. The current cohort contains 222 systems representing 182 unique receptors. The systems span Gi/o, Gs, Gq/11 and G12/13 G-protein families, with current counts of 100 Gi/o systems, 68 Gs systems, 47 Gq/11 systems and 7 G12/13 systems. Structural provenance was recorded for each system. In the current inventory, 211 systems are classified as experimental-coordinate derived and 11 are flagged as engineered, chimeric or otherwise uncertain so that users can include or exclude them during reuse.

The selection workflow should be presented explicitly in the final figure set. Starting structures were retained when they represented an active GPCR-G-protein ternary complex, could be assigned to a receptor and G-protein family, and could be processed through the standardized preparation and metadata workflow. Records were flagged, rather than silently removed, when they contained engineered or chimeric features, uncertain recovered identifiers, incomplete annotation, missing GPCRdb pocket mapping or nonstandard trajectory length. This flagging strategy preserves a broad dataset while allowing downstream users to construct stricter subsets.

For each system, the metadata table records the system identifier, PDB identifier, receptor name, receptor UniProt accession, receptor gene where available, G-protein family, G-alpha subtype, ligand name or chemical identifier where available, number of replicas, simulation length, force field, lipid composition, structural provenance, pocket-data availability, gateway-data availability, GPCRdb-mapped pocket availability and notes on file or annotation issues. The primary system identifier follows the pattern `Gfamily_PDBID`, for example `Gi_7F1Q`.

### System preparation and molecular dynamics simulation

Systems were prepared using a CHARMM36-family force-field workflow. Most systems were simulated with AMBER `pmemd` using chamber-converted topologies; a subset was simulated with GROMACS; and 26 class-B receptor systems were prepared via CHARMM-GUI under the same force-field family. All systems in the current curated manuscript inventory are annotated as POPC membrane-embedded systems. The web portal metadata display also records trajectory type, force-field source, velocity availability and force availability where known.

The nominal simulation design was three independent 500 ns replicas per system, corresponding to 1.5 microseconds per system. The current audited inventory contains three deviations that must be confirmed before submission: `Gi_7E32` is listed as three 260 ns replicas, `Gi_8HK2` is listed as three 2 ns replicas and is likely a data-entry or incomplete-trajectory anomaly, and `Gq_8J9N` is listed as six 500 ns replicas. With these entries as currently recorded, the total audited sampling is approximately 332.3 microseconds. If `Gi_8HK2` is corrected or rerun to 500 ns per replica, the final aggregate sampling should be recalculated and updated consistently across the manuscript, data repository, website and metadata tables.

### Trajectory processing and derived data generation

Production trajectories are retained in their native simulation formats for archival reuse. The current inventory records AMBER NetCDF trajectories for most systems and GROMACS TRR trajectories for 10 GROMACS-run systems. A reduced visualization tier was generated for web use by stripping solvent, ions and membrane components and storing protein-only trajectories as XTC files with corresponding reference PDB structures. These reduced trajectories are intended for interactive inspection and lightweight downloads; they are not a substitute for the full archival trajectories.

Derived feature tables were generated from the production trajectories. Pocket analyses were produced with `fpocket` and summarized per system after applying a consensus filter requiring detection in at least two of three replicas where applicable. Pocket-lining residues were mapped to GPCRdb generic positions to support cross-receptor comparison. Membrane-gateway measurements were computed from defined transmembrane-helix portal pairs and summarized as open fractions, mean distances and confidence intervals. G-protein interface metrics were indexed to the Common G-protein Numbering (CGN) scheme where available. The current CGN barcode figure and related table represent a pilot subset of positions and systems; full 356-position coverage across all systems should not be claimed until the corresponding analysis is complete.

### Metadata and annotation

Metadata were harmonized into a master system inventory and SQLite database used by the web portal and API. Key annotation layers include PDB identifiers, UniProt accessions, receptor names, receptor genes where available, G-protein family labels, G-alpha subtype labels, GPCR class labels, ligand identifiers, structural-provenance labels, trajectory type, replica count, sampling length, analysis availability and file availability. GPCRdb-compatible receptor residue numbering is used for pocket-lining residues where mapping is available. G-protein positions are indexed to CGN labels in the processed G-protein feature tables where available.

Several metadata issues remain visible in the current audit and should be resolved or retained as explicit flags in the submitted dataset. These include missing receptor genes in some records, API-name differences relative to earlier local labels, systems lacking GPCRdb-mapped pocket data, systems lacking pocket grids and systems with temporary or incomplete files in the source directory. These issues do not invalidate the dataset, but Scientific Data reviewers will expect transparent flags and, where possible, corrected records.

### Web portal and REST API

The web portal is an interactive access layer for the dataset. It should be described as a browsing, visualization and programmatic-access interface rather than as the sole archival repository. The production deployment is documented at `https://www.coupledmd.cn`, with a React/Vite frontend, FastAPI backend, SQLite metadata store, Nginx reverse proxy and TLS deployment. The portal supports browsing all 222 systems, filtering by G-protein family and GPCR class, free-text searching by receptor, UniProt accession, PDB identifier, ligand, system identifier and G-alpha subtype, and per-system pages with receptor metadata, simulation metadata, analysis availability, downloadable reduced structures and trajectories, pocket tables, gateway tables, G-protein features and interactive NGL visualization.

The REST API is versioned under `/api/v1/` and provides open endpoints for system lists, per-system metadata, pocket data, gateway data, pocket-grid downloads, reduced visualization structures, reduced visualization trajectories, visualization metadata, consensus pocket tables, gateway summaries, G-protein metrics, coupling-geometry summaries, G-protein barcode summaries, citation metadata and licence information. Interactive Swagger and ReDoc documentation are available at `/api/docs` and `/api/redoc`. Anonymous access is allowed for all data endpoints, with optional API keys used only for higher rate limits. The portal currently documents CC-BY-4.0 terms for data and MIT terms for code.

For Scientific Data submission, the website should link clearly to the archival repository record, DOI or accession, data manifest, code repository, licence files, citation instructions and reviewer-access instructions. Bulk downloads should be routed through the repository or a stable storage service rather than depending on the live web server.

## Data Records

### Access

The dataset should be made available through three complementary routes. First, the stable archival repository should provide the complete downloadable data, including full trajectories, topologies, metadata, processed analyses, manifests and checksums. Second, the REST API should provide programmatic access to selected metadata and processed records. Third, the web portal should provide interactive browsing, filtering, visualization and selected reduced-trajectory downloads. The archival repository is the citable record; the website and API are access layers that improve usability.

Placeholder archival repository: `[repository name, accession or DOI pending]`.  
Placeholder reviewer link: `[private reviewer URL or tokenized repository link pending]`.  
Web portal: `https://www.coupledmd.cn`.

### Organization

The final repository should be organized as a filesystem-like hierarchy with one metadata layer, one system-level layer and one processed-analysis layer. Table 1 gives the recommended organization and the fields that should be documented in the data dictionary. This structure follows the same principle as mdCATH's HDF5 layout: all records needed to interpret a trajectory should be discoverable from a small number of predictable paths and metadata fields.

| Record | Suggested path | Contents | Required status before submission |
| --- | --- | --- | --- |
| System inventory | `metadata/systems_master.csv` | One row per system with identifiers, receptor metadata, G-protein labels, ligand labels, replica count, simulation length, provenance, analysis availability and notes | Required |
| System manifest | `metadata/file_manifest.tsv` | One row per file with system ID, replica ID, file role, file path, format, size, checksum and description | Required |
| Simulation inputs | `systems/{system_id}/input/` | Starting coordinates, topology/parameter files, preparation notes and engine-specific input files | Required where redistribution is permitted |
| Full trajectories | `systems/{system_id}/replicas/{replica_id}/` | Production trajectories in NetCDF or TRR/XTC format, with matching topology/structure files | Required for the primary dataset |
| Reduced trajectories | `systems/{system_id}/visualization/` | Protein-only reference PDB and decimated XTC trajectory used by the web viewer | Recommended |
| Pocket outputs | `analysis/pockets/{system_id}/` | Raw pocket outputs, GPCRdb-mapped pocket JSON, pocket-grid NPZ files and per-system pocket summaries | Required for derived-data reuse |
| Gateway outputs | `analysis/gateways/{system_id}/` | Per-portal distance/open-fraction time series or summary tables with confidence intervals | Required if gateway tables are described |
| G-protein features | `analysis/gprotein/{system_id}/` | CGN-indexed contact, RMSF, order-parameter or barcode features where available | Required if included in manuscript |
| Consensus tables | `analysis/consensus/` | Cross-system pocket clusters, orthosteric-pocket summaries, gateway atlas, partner-contrast summaries and other cohort summaries | Required |
| Web/API export | `web_api_snapshot/` | JSON files served by `/api/v1/`, OpenAPI schema and database schema documentation | Recommended |
| Code and notebooks | `code/` or external repository | Processing scripts, analysis scripts, figure-generation scripts and notebooks | Required through Code Availability |
| Documentation | `README.md`, `DATA_DICTIONARY.md`, `USAGE.md` | Dataset overview, file-format descriptions, column dictionaries, examples and citation instructions | Required |
| Checksums | `checksums/sha256sums.txt` | SHA256 or comparable checksums for repository files | Strongly recommended |
| Licences | `LICENSE`, `LICENSE-CODE` | CC-BY-4.0 for data and MIT or equivalent for code | Required |

**Table 1. Recommended hierarchical organization of the GPCR-G-protein MD dataset.** The final data dictionary should define the path, file role, format, units, dimensions and required metadata for each record type.

At present, the project contains a website-ready data layout with `data/api/v1/`, `data/viz/`, `data/chain_roles/`, `data/contacts/`, `data/systems_master.csv`, `db/coupledmd.sqlite`, licence files and citation metadata. The long-term repository deposit and DOI remain placeholders and must be completed before or during review.

### Main metadata table

The primary metadata table is `S1_system_inventory.csv`. It contains 222 rows and records the core identifiers and analysis flags needed to interpret the dataset. Important columns include `system_id`, `pdb_id`, `receptor_name`, `receptor_uniprot`, `receptor_gene`, `g_protein_family`, `g_alpha_subtype`, `ligand_name`, `ligand_class`, `n_replicas`, `length_per_replica_ns`, `total_sampling_ns`, `force_field`, `lipid_composition`, `structural_provenance`, `has_pocket_data`, `has_gateway_data`, `has_gpcrdb_pockets` and `notes`.

### Derived analysis tables

The current manuscript workspace contains main and supplementary tables suitable for repository inclusion. `T1_cohort_summary.csv` summarizes systems, provenance, unique receptors and aggregate sampling by G-protein family. `T2_recovery_benchmark.csv` summarizes orthosteric-pocket recovery by family and ligand class. `T3_partner_switching.csv` summarizes a small set of same-receptor multi-partner contrasts and should be treated as a reuse example rather than a mechanistic result. Supplementary tables include the full system inventory, druggable pocket clusters, alpha5 geometry pilot table, partner-switching pocket-detail table, gateway per-system table and per-system pocket table. These tables should be deposited with data dictionaries defining every column, unit and allowed categorical value.

### Size and descriptive statistics

At the current audit date, the dataset contains 222 GPCR-G-protein systems and approximately 332.3 microseconds of recorded sampling. The nominal design is three 500 ns replicas per system, but the final manuscript must use the audited total after reruns and metadata corrections are complete. The web visualization tier contains 222 reduced reference structures and 222 reduced trajectories, with a reported size of approximately 34-35 GB. The API analysis tier includes per-system JSON records, consensus JSON records, contact parquet files, chain-role files and pocket-grid NPZ files where available.

| Statistic | Current value | Notes |
| --- | ---: | --- |
| Systems | 222 | Active-state GPCR-G-protein complexes |
| Unique receptors | 182 | Based on current UniProt inventory |
| G-protein families | 4 | Gi/o, Gs, Gq/11, G12/13 |
| Gi/o systems | 100 | Current audited table |
| Gs systems | 68 | Current audited table |
| Gq/11 systems | 47 | Current audited table |
| G12/13 systems | 7 | Current audited table |
| Experimental-coordinate derived systems | 211 | 11 additional systems flagged as engineered or uncertain |
| Current audited sampling | 332.3 microseconds | Must be recalculated after reruns/corrections |
| Nominal sampling design | 3 x 500 ns per system | Exceptions are flagged in Technical Validation |
| Systems with pocket data | 209 | 13 systems without detectable or available pocket outputs |
| Systems with gateway data | 222 | Based on current table |
| Reduced visualization structures | 222 | PDB files for web/NGL use |
| Reduced visualization trajectories | 222 | Protein-only XTC files for web/NGL use |
| Pocket-grid files | 219 | Three systems currently missing pocket-grid NPZ files |

**Table 2. Descriptive statistics of the current GPCR-G-protein MD dataset.** Values should be updated after reruns and final repository assembly.

### Web portal and API records

The portal provides an interactive way to inspect and retrieve records. The systems page supports browsing, filtering and free-text search. Per-system pages display receptor metadata, simulation metadata, reduced trajectory downloads, pocket occupancy summaries, gateway summaries, G-protein tabs, NGL visualization and interaction-network visualization. API endpoints expose the same data as JSON and binary downloads for reduced structures, reduced trajectories and pocket grids. The OpenAPI specification at `/api/openapi.json` should be archived with the dataset so programmatic reuse is reproducible even if the live server evolves.

The portal should not be described as the archival record. The manuscript should state that the authoritative archival record is the repository deposit listed in Data Availability, whereas the portal mirrors selected records, provides search and visualization, and may receive later usability updates.

## Technical Validation

### Cohort and metadata audit

The 222-system inventory was audited for system count, G-protein family count, structural provenance, unique receptors, pocket-data availability, gateway-data availability, GPCRdb-mapped pocket availability and aggregate sampling. The current audited counts are 100 Gi/o systems, 68 Gs systems, 47 Gq/11 systems and 7 G12/13 systems. The inventory contains 211 experimental-coordinate derived systems and 11 engineered or uncertain systems. Pocket data are present for 209 systems; 13 systems lack detectable pocket data or pocket-grid outputs in the current analysis tier. Gateway data are present for all 222 systems in the current table.

The audited sampling total is 332.3 microseconds rather than the exact nominal value of 333 microseconds. This difference is explained by nonstandard entries in the inventory: `Gi_7E32` is recorded as three 260 ns replicas, `Gi_8HK2` is recorded as three 2 ns replicas and should be verified or rerun, and `Gq_8J9N` is recorded as six 500 ns replicas. Before submission, these entries should be checked against the source trajectories and the final total should be reported consistently.

### Trajectory and file-completeness checks

The deployment documentation reports 222 reduced visualization structures and 222 reduced visualization trajectories in the web tier, with a total visualization tier of approximately 34 to 35 GB. It also records 219 pocket-grid NPZ files copied into the API data tier; `Gq_7RAN`, `Gq_7RYC` and `Gq_8J9N` currently lack pocket-grid files and correctly return missing-data responses. Several systems have source notes indicating temporary or incomplete `#`-prefixed GROMACS files. These temporary files should be removed from the repository deposit or clearly excluded from the manifest. Systems with retained velocities or forces in TRR files should be labeled explicitly because they affect file size and reuse.

For submission, trajectory validation should include per-replica checks for expected frame count, trajectory duration, topology compatibility, atom count consistency, periodic-boundary handling, coordinate readability and absence of truncated final frames. The repository manifest should include file sizes and checksums so reviewers can verify transfer integrity.

### Annotation consistency

Pocket-lining residues were mapped to GPCRdb generic positions where available. The current system inventory records whether GPCRdb-mapped pocket data are present for each system. The CGN-indexed G-protein features are available for a pilot subset and should remain labeled as a pilot until full 356-position coverage has been computed. Receptor names and UniProt accessions should be checked for records where the audit notes API-name differences or missing receptor genes. These fields are important for reuse because users will filter and join the dataset against GPCRdb, UniProt, PDB and ligand databases.

### Pocket and binding-site validation

Pocket detection provides a technical validation layer because expected ligand-accessible sites should be recovered in many systems with known ligands. Among the 209 systems with detectable pockets, the current benchmark reports orthosteric-site recovery in 158 systems, corresponding to 75.6% of pocket-having systems. Recovery is higher for systems co-crystallized with small-molecule ligands and peptide ligands. These results should be presented as validation of the pocket-detection and annotation workflow, not as evidence for a new biological mechanism.

As a per-system example, the CCR5 system `Gi_7F1Q` recovers a pocket involving GPCRdb positions 2.50, 3.39 and 7.49 with a mean occupancy frequency of 0.910. This site overlaps the known sodium/allosteric region adjacent to the maraviroc binding site. In this manuscript, the CCR5 example should be framed only as a positive-control style validation that the workflow can recover a known ligand-relevant region from the trajectory-derived pocket analysis.

### Replica consistency and processed-feature reproducibility

Pocket calls use a consensus filter requiring recurrence across replicas where applicable. Gateway measurements include confidence intervals across replicate-derived summaries. These design choices help identify features that are reproducible across trajectories rather than idiosyncratic to a single run. For submission, the repository should include the scripts or notebooks used to regenerate the processed tables from source trajectories, together with software versions and parameter files. A small reproducibility example, such as regenerating one system's pocket and gateway summaries from raw trajectories, would strengthen the Data Descriptor.

### Limitations

The dataset is limited to active-state GPCR-G-protein ternary complexes and does not include inactive-state receptors, GPCR-arrestin complexes or ligand-free ensembles for every receptor. Sampling is approximately 500 ns per replica for most systems and may not capture slow conformational transitions. G12/13 systems are under-represented because fewer experimental structures are available. Some analyses are currently complete only for subsets, including the pilot CGN barcode and the alpha5 geometry table. A small number of systems require trajectory-length, PBC, pocket-grid or incomplete-file review before final submission.

## Usage Notes

Users can reuse the dataset at three levels. First, the archival repository should be used for reproducible bulk analyses requiring full trajectories, topology files, file manifests and checksums. Second, the processed tables and JSON files can be used for rapid benchmarking, method development and metadata-driven filtering without reprocessing multi-terabyte trajectories. Third, the website and REST API can be used for interactive inspection, system selection, reduced-trajectory visualization and programmatic retrieval of selected records.

Recommended reuse workflows include selecting systems by receptor, UniProt accession, PDB identifier, GPCR class, G-protein family, ligand annotation, structural provenance or analysis availability; downloading full trajectories from the archival repository for reanalysis; retrieving reduced structures and trajectories from the web portal for visualization; and joining GPCRdb-mapped pocket residues to external receptor annotations. Users should cite both the Scientific Data article and the dataset DOI. If using the codebase or API schema, users should also cite the code repository according to the `CITATION.cff` file.

Example API calls that should be tested and included in the final Usage Notes or Supplementary Information are:

```bash
curl https://www.coupledmd.cn/api/v1/health
curl "https://www.coupledmd.cn/api/v1/systems?family=Gi&limit=10"
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q/pockets
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q/viz/meta
```

The examples included in this manuscript are not intended to provide comprehensive biological conclusions. The dataset may support future analyses of GPCR activation, coupling, ligand recognition, membrane interactions and G-protein interface dynamics, but those analyses require study-specific statistical design and are outside the scope of this Data Descriptor.

## Data Availability

The full dataset will be deposited in a stable public repository before publication.

Placeholder repository record: `[repository name, accession or DOI pending]`.

Placeholder reviewer-access link: `[private reviewer URL or tokenized repository link pending]`.

The web portal is available at `https://www.coupledmd.cn` and provides interactive browsing, filtering, visualization, selected downloads and REST API access. The web portal is an access and visualization layer; the archival repository listed above is the authoritative long-term data record.

## Code Availability

The processing scripts, web-server code, API code, figure-generation scripts and documentation will be made available at `[GitHub or institutional repository URL pending]`. The current project uses a FastAPI backend, React/Vite frontend, SQLite metadata database and Python analysis scripts. Data are intended for release under CC-BY-4.0. Code is intended for release under the MIT licence.

## Acknowledgements

`[Add acknowledgements for computing resources, institutional support, data curation support, GPCRdb/GPCRmd-related discussions if appropriate, and repository/IT support.]`

## Funding

`[Add grant numbers, institutional funding, computing allocations and fellowship support.]`

## Author Contributions

`[Author initials]` conceived the dataset. `[Author initials]` designed and performed molecular dynamics simulations. `[Author initials]` curated the system inventory and annotations. `[Author initials]` developed the analysis pipeline. `[Author initials]` developed the web portal and API. `[Author initials]` generated figures and tables. `[Author initials]` wrote the manuscript with input from all authors. All authors reviewed and approved the final manuscript.

## Competing Interests

The authors declare no competing interests. `[Revise if any financial, advisory, patent, employment or software-related interests apply.]`

## References

1. Hauser, A. S. et al. Trends in GPCR drug discovery: new agents, targets and indications. *Nat. Rev. Drug Discov.* **16**, 829-842 (2017).
2. Flock, T. et al. Selectivity determinants of GPCR-G-protein binding. *Nature* **545**, 317-322 (2017).
3. Weis, W. I. & Kobilka, B. K. The molecular basis of G protein-coupled receptor activation. *Annu. Rev. Biochem.* **87**, 897-919 (2018).
4. Kooistra, A. J. et al. GPCRdb in 2021: integrating GPCR sequence, structure and function. *Nucleic Acids Res.* **49**, D335-D343 (2021).
5. Rodriguez-Espigares, I. et al. GPCRmd uncovers the dynamics of the 3D-GPCRome. *Nat. Methods* **17**, 777-787 (2020).
6. Huang, J. et al. CHARMM36m: an improved force field for folded and intrinsically disordered proteins. *Nat. Methods* **14**, 71-73 (2017).
7. Berman, H. M. et al. The Protein Data Bank. *Nucleic Acids Res.* **28**, 235-242 (2000).
8. Abraham, M. J. et al. GROMACS: High performance molecular simulations through multi-level parallelism from laptops to supercomputers. *SoftwareX* **1-2**, 19-25 (2015).
9. Salomon-Ferrer, R., Goetz, A. W., Poole, D., Le Grand, S. & Walker, R. C. Routine microsecond molecular dynamics simulations with AMBER on GPUs. 2. Explicit solvent particle mesh Ewald. *J. Chem. Theory Comput.* **9**, 3878-3888 (2013).
10. Jo, S., Kim, T., Iyer, V. G. & Im, W. CHARMM-GUI: a web-based graphical user interface for CHARMM. *J. Comput. Chem.* **29**, 1859-1865 (2008).
11. Le Guilloux, V., Schmidtke, P. & Tuffery, P. Fpocket: an open source platform for ligand pocket detection. *BMC Bioinformatics* **10**, 168 (2009).
12. Isberg, V. et al. GPCRdb: an information system for G protein-coupled receptors. *Nucleic Acids Res.* **44**, D356-D364 (2016).
13. Tan, Q. et al. Structure of the CCR5 chemokine receptor-HIV entry inhibitor maraviroc complex. *Science* **341**, 1387-1390 (2013).
14. Liu, W. et al. Structural basis for allosteric regulation of GPCRs by sodium ions. *Science* **337**, 232-236 (2012).
15. Rose, A. S. et al. NGL viewer: web-based molecular graphics for large complexes. *Bioinformatics* **34**, 3755-3758 (2018).

## Figure Legends

**Figure 1. System selection workflow and final dataset composition.**  
Recommended revised main figure, analogous to the exclusion-flow figure in the reference article. Panel A should show the selection and curation workflow from PDB/GPCRdb active-state GPCR-G-protein structures to the final 222-system dataset, including retained, excluded and flagged categories where available. Panel B should summarize system counts by G-protein family. Panel C should show structural provenance and GPCR class distribution. Panel D should summarize unique receptor count, aggregate sampling and explicitly flagged nonstandard systems.

**Figure 2. Dataset size, trajectory completeness and annotation coverage.**  
New or revised figure recommended, analogous to mdCATH's descriptive-distribution figure. Panel A should show total sampling per system or per G-protein family. Panel B should show the distribution of system sizes or trajectory file sizes if available. Panel C should show replica count and trajectory-length distributions, highlighting `Gi_7E32`, `Gi_8HK2` and `Gq_8J9N` until these are corrected. Panel D should show annotation and analysis coverage, including UniProt availability, GPCRdb-mapped pocket availability, pocket-grid availability, gateway availability and reduced visualization availability.

**Figure 3. Data records, repository organization and web/API access.**  
New figure recommended. Panel A should show the archival repository hierarchy, including metadata, system-level files, trajectories, processed analyses, checksums and documentation. Panel B should show how repository files map to website/API records. Panel C should show a small screenshot or schematic of the web portal systems table and per-system page. Panel D should show API access routes for metadata, pockets, gateways, visualization files and citation/licence records. The figure should emphasize that the repository is the stable archive and the portal is an access layer.

**Figure 4. Technical validation of pocket annotations.**  
Revised from current Figure 2 and recovery tables. Panel A should show orthosteric-site recovery across all systems with pocket data, stratified by ligand class or G-protein family. Panel B should show the CCR5 positive-control example, framed as recovery of a known ligand-relevant pocket region rather than as a mechanistic discovery. Panel C may show analysis-availability counts for pocket, GPCRdb-mapped pocket and pocket-grid records.

**Figure 5. Web portal and reduced-trajectory visualization example.**  
New or optional main figure, analogous to the reference article's platform-viewer figure. A screenshot-driven workflow should show system search/filtering, a per-system metadata page, reduced trajectory visualization and API documentation. Keep this as a usage/access figure, not a software-server claim.

**Supplementary Figure 1. Gateway and partner-comparison example.**  
Optional. Revised from current FFAR4 and OX2R figures. Language should be limited to "example of a reusable derived feature table" and should avoid claims about mechanisms of selectivity, bias or allostery.

**Supplementary Figure 2. Pilot G-protein interface and alpha5 descriptors.**  
Optional or reserve for Paper 2. If included, clearly label as pilot/subset analysis and avoid broad mechanistic interpretation.

## Supplementary Information

Recommended supplementary tables:

- Table S1. Full system inventory.
- Table S2. File manifest with checksums.
- Table S3. Simulation input and trajectory-format summary.
- Table S4. Pocket-analysis outputs and GPCRdb-mapping availability.
- Table S5. Gateway-analysis outputs.
- Table S6. Reduced visualization file availability.
- Table S7. Data dictionary for all metadata and processed-feature columns.
- Table S8. Known issues, nonstandard systems and recommended exclusion flags.

# Editorial appendix not for submission

## Reference paper structure to emulate

The downloaded Scientific Data reference article is: Mirarchi, Giorgino and De Fabritiis, **mdCATH: A Large-Scale MD Dataset for Data-Driven Computational Biophysics**, *Scientific Data* 11, 1299 (2024), doi:10.1038/s41597-024-04140-z.

Useful structural features to emulate:

- Title is dataset-forward and concise.
- Abstract reports dataset scale, simulation design, recorded fields, accumulated sampling and reuse value without making a mechanistic discovery claim.
- Background & Summary starts with the scientific data gap, then positions existing MD resources, then states what the new dataset contains.
- A **Dataset Requirements** block defines design principles before Methods.
- Figure 1 shows inclusion/exclusion or selection flow.
- Methods gives selection criteria, preparation protocol, simulation protocol and analysis protocol in concrete reproducible detail.
- Data Records starts with access routes, then **Organization**, then **Size**.
- A table defines data-field hierarchy, units and dimensions.
- A second table gives descriptive dataset statistics.
- Technical Validation uses several factual checks and example analyses; it does not become a broad biological discussion.
- Usage Notes include concrete loading/downloading examples and point users to companion code.
- A platform/viewer figure is acceptable when framed as access/visualization, not as the archival record.

## Major changes from the NAR version

- Changed the target from a database/web-server article to a Scientific Data Data Descriptor.
- Removed NAR-style resource positioning and replaced it with dataset provenance, data records, validation and reuse framing.
- Replaced the old Discussion with Usage Notes.
- Distinguished the stable archival repository from the web portal.
- Softened CCR5, FFAR4, OX2R, gateway, partner-switching and alpha5 language.
- Added explicit repository manifest requirements and Scientific Data missing-item checklists.
- Added transparent system-quality flags, especially nonstandard sampling and missing pocket-grid records.

## Current figure and table placement plan

| Current asset | Recommendation | Reason |
| --- | --- | --- |
| Current Figure 1 dataset overview | Keep main, revise | Useful for dataset composition, but add workflow and QC flags for Scientific Data. |
| Current Figure 2 CCR5 pocket recovery | Keep as part of main Figure 3 or supplement | Good technical validation; remove discovery tone. |
| Current Figure 3 FFAR4 gateway example | Move to supplement or reserve | Too close to mechanistic partner-specific interpretation for Paper 1. |
| Current Figure 4 G-protein barcode/alpha5 | Move to supplement or reserve | Pilot subset; mechanistic interpretation risks Paper 2 novelty. |
| Current Figure 5 OX2R partner switching | Move to supplement or reserve | Useful as a usage example but too mechanistic for main Scientific Data narrative. |
| Current T1 cohort summary | Keep main or Data Records table | Supports dataset description. |
| Current T2 recovery benchmark | Keep main or Technical Validation table | Supports validation. |
| Current T3 partner-switching table | Supplement only | Useful for reuse, but avoid central mechanistic framing. |
| Current S1-S6 | Keep supplementary | Add data dictionary, manifest and checksums. |

## Content reserved for Paper 2

- Strong claims about GPCR biased signalling mechanisms.
- Claims that partner-specific gateway changes explain coupling selectivity.
- Broad family-level comparisons of Gi/o, Gs, Gq/11 and G12/13 mechanisms.
- Mechanistic interpretation of alpha5 tilt, insertion depth, hook angle or interface barcode features.
- OX2R as a partner-switching mechanistic case study.
- FFAR4 gateway asymmetry as a biological conclusion.
- Cross-system allosteric pathway or druggability claims beyond validation/reuse.
- Any "we reveal", "we discover" or "mechanism" language tied to the derived analyses.

## Website and web portal assessment

Current strengths:

- Public production URL documented as `https://www.coupledmd.cn`.
- Open access model: no login required for data, downloads or API endpoints.
- Optional API keys raise rate limits only.
- Systems page supports browsing, G-protein-family filtering, GPCR-class filtering and free-text search over receptor, UniProt, PDB, ligand, system ID and G-alpha subtype.
- Per-system page displays receptor metadata, simulation metadata, trajectory metadata, pocket summaries, gateway summaries, G-protein data and visualization.
- Download routes exist for reduced PDB and XTC files.
- Pocket-grid NPZ download route exists where files are present.
- API is versioned under `/api/v1/`.
- Swagger and ReDoc documentation exist.
- Citation, licence, privacy and terms pages/endpoints are documented.
- Data licence is CC-BY-4.0 and code licence is MIT.

Website gaps to fix before Scientific Data submission:

- Replace NAR citation text throughout the website with Scientific Data / DOI-pending wording.
- Add the archival repository DOI/accession and reviewer-private link once available.
- Add a visible data-download page explaining full trajectories, reduced trajectories, processed tables and checksums.
- Add a bulk-download route through the archival repository rather than the live web server.
- Add a complete manifest and checksum download link.
- Clarify which files are full archival trajectories and which are reduced visualization trajectories.
- Add or expose a data dictionary for API fields and table columns.
- Mark known missing data explicitly on per-system pages, especially missing pocket-grid records.
- Ensure `Gi_8HK2`, `Gi_7E32`, `Gq_8J9N` and systems with temporary/incomplete files are flagged in both website metadata and repository manifest.
- Add reviewer-access instructions that do not depend on optional accounts.

## Systems requiring review, rerun or explicit flags

High priority:

- `Gi_8HK2`: currently recorded as three 2 ns replicas and total sampling 6 ns. This should be verified immediately. If true, it should be rerun or excluded from the "3 x 500 ns" claim. If it is a metadata error, correct `systems_master.csv`, regenerate tables and update total sampling.
- `Gi_7E32`: currently recorded as three 260 ns replicas. Keep as nonstandard or rerun to 500 ns per replica.
- `Gq_8J9N`: currently recorded as six 500 ns replicas and lacks pocket data/pocketgrid. Verify whether six replicas are intended and whether missing pocket data are due to PBC, trajectory, structure or analysis failure.

PBC/incomplete-file review:

- Systems with notes about `#`-prefixed temporary or incomplete files should be checked before repository deposition: `G12_8H8J`, `Gi_7JVR`, `Gi_7VUG`, `Gi_7YK6`, `Gi_8X16`, `Gi_8YIC`, `Gq_7XXH`, `Gq_8DPF`, `Gs_7VUH`.
- GROMACS TRR systems with velocities and forces should be checked for file-size suitability and whether reduced public formats should be provided alongside full archival files.
- Systems lacking pocket-grid files should be listed explicitly: `Gq_7RAN`, `Gq_7RYC`, `Gq_8J9N`.

## Repository and data-manifest checklist

- Stable repository selected.
- Reviewer-private link generated.
- Public DOI/accession reserved or issued.
- Full trajectories uploaded.
- Topologies and starting structures uploaded.
- Per-system README or metadata available.
- `systems_master.csv` uploaded.
- File manifest includes one row per file.
- Manifest includes system ID, replica ID, role, format, size and checksum.
- SHA256 checksums generated.
- Processed analysis tables uploaded.
- GPCRdb mapping files uploaded.
- Pocket grids uploaded or missingness documented.
- Gateway outputs uploaded.
- G-protein feature outputs uploaded only where complete or clearly marked as pilot.
- Reduced visualization trajectories uploaded.
- API JSON snapshot uploaded.
- OpenAPI schema uploaded.
- Data dictionary uploaded.
- Licence files included.
- Citation instructions included.
- Known-issues table included.

## Final missing-items checklist before submission

- Confirm final exact aggregate simulation time: 332.3 microseconds currently audited versus nominal 333 microseconds.
- Resolve or explicitly flag `Gi_8HK2`.
- Decide whether `Gi_7E32` remains in the dataset as a shorter simulation.
- Resolve or explicitly flag `Gq_8J9N` missing pocket outputs.
- Complete archival repository deposit.
- Add DOI/accession to manuscript, website, `CITATION.cff` and API citation endpoint.
- Add reviewer-access private link.
- Replace NAR wording on website and API description.
- Create Figure 2 data-record/web-access schematic.
- Create Figure 4 QC/completeness summary.
- Add data dictionary and checksum manifest.
- Add author contributions.
- Add competing interests confirmation.
- Add acknowledgements and funding.
- Confirm references and Scientific Data formatting.
- Decide which current mechanistic figures are supplementary versus reserved for Paper 2.
