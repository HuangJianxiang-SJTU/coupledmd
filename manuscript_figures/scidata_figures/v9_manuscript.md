# CoupledMD: molecular dynamics trajectories of active GPCR–G-protein complexes

Jianxiang Huang^1,2,3^, Xin Qiao^3^, Shaoyong Lu^1,2,3,\*^

^1^ Artificial Intelligence Clinical Research Center for Drug Discovery, Shanghai Key Laboratory of Flexible Medical Robotics, Institute of Medical Robotics, Tongren Hospital, Shanghai Jiao Tong University School of Medicine, Shanghai 200336, China

^2^ Key Laboratory of Protection, Development and Utilization of Medicinal Resources in Liupanshan Area, Ministry of Education; Peptide & Protein Drug Research Center, School of Pharmacy, Ningxia Medical University, Yinchuan 750004, China

^3^ Department of Pharmacology, School of Medicine, Shanghai Jiao Tong University, Shanghai 200025, China

\*Correspondence: Shaoyong Lu (lushaoyong@sjtu.edu.cn)

---

## Abstract

Molecular dynamics (MD) trajectories of G protein-coupled receptor (GPCR)–G-protein complexes are difficult to compare and reuse because simulation protocols, molecular representations and annotations differ between studies. Here we describe CoupledMD v9, a curated final cohort of 207 active-state GPCR–G-protein complexes spanning 174 distinct receptor names, two GPCR classes (A and B) and the four major G-protein families (Gi/o, Gs, Gq/11 and G12/13). Each included complex has three selected validated 500-ns replicas, giving 621 production trajectories and 310.5 µs of aggregate sampling. The current resource provides system metadata, reduced representative visualization trajectories, GPCRdb-mapped pocket annotations, transmembrane-gateway records and a versioned REST API. A complete DOI-linked archive of primary trajectories, matched topologies, inputs and checksums is being prepared; it is not claimed as already deposited. CoupledMD supports trajectory-method benchmarking, receptor-aware comparative analysis and reuse of structurally derived annotations for GPCR-targeted research.


## Background & Summary

G protein-coupled receptors (GPCRs) transduce extracellular signals across the plasma membrane by coupling to heterotrimeric G proteins, and they constitute the largest family of validated drug targets, accounting for approximately a third of marketed small-molecule and biologic therapeutics^1,2^. Signal transduction begins when an agonist stabilizes an active receptor conformation that engages a specific Gα subunit, catalyzing nucleotide exchange and downstream effector activation. The determinants of which G-protein family a receptor recruits, and how ligand chemistry biases that recruitment, are encoded in the dynamics of the receptor–G-protein interface rather than in any single static structure^2^. Over the past decade, cryo-electron microscopy and X-ray crystallography have resolved hundreds of active-state GPCR–G-protein complexes, transforming our structural picture of coupling. These structures are, however, static endpoints; the conformational ensembles, interface fluctuations and membrane-mediated effects that govern coupling can only be recovered through molecular simulation.

Molecular dynamics (MD) is the established route to those ensembles, but MD trajectories are expensive to generate and are rarely shared in a form that supports reuse. Cross-receptor and cross-family comparison requires that simulations be prepared under a common protocol, embedded in a defined membrane, annotated with a transferable residue-numbering scheme and distributed in interoperable formats with verifiable provenance. In practice, published GPCR simulations differ in force field, membrane composition, trajectory length, atom selection, file format and identifier conventions, so that assembling a comparable multi-receptor collection from the literature is prohibitively laborious.

Several community resources address parts of this problem. GPCRdb provides receptor classification, curated structures, sequence alignments and the generic residue-numbering scheme that makes positional comparison possible across the superfamily^3,4^; GproteinDb extends this framework to G proteins and their couplings^9^. GPCRmd pioneered community-accessible GPCR trajectory sharing and demonstrated its value for dynamics-aware receptor analysis^5^. At the whole-proteome scale, mdCATH assembled all-atom simulations of 5,398 protein domains with an explicit cohort definition, hierarchical data schema, file-level provenance, technical validation and executable access examples—establishing the template for a reusable MD Data Descriptor^6^. None of these resources, however, provides a standardized, membrane-embedded collection of GPCR–G-protein *complexes* with matched topologies, derived interface annotations and programmatic access. This is the gap CoupledMD fills. Relative to single-receptor MD studies and to soluble-domain collections such as mdCATH, the distinguishing feature of CoupledMD is that every system is a multi-chain, membrane-embedded receptor–transducer assembly, a class that demands careful treatment of membrane construction, chain-role assignment, multi-component topology and G-protein annotation.

CoupledMD v9 comprises 207 systems selected from a 222-record working inventory (Fig. 1E). The cohort spans 174 distinct receptor names (173 mapped UniProt accessions), Class A (182 systems) and Class B (26 systems) GPCRs, and the four major G-protein families: 95 Gi/o, 65 Gs, 41 Gq/11 and 6 G12/13 systems (Fig. 1A). Thirteen records remain unresolved because of PBC/trajectory continuity, component continuity or incomplete-trajectory evidence; `Gq_7E9W` is separately excluded as a non-GPCR duplicate/mislabel of `Gq_8E9W`. Neither set contributes to release counts, figures, API responses or derived records. Each included system contributes three selected 500-ns production replicas under a CHARMM36-family force field in a POPC bilayer, for 310.5 µs across 621 trajectories. The composition, ligand context, multi-family receptor coverage and release boundary are summarized in Figure 1, with an extended receptor-by-family dendrogram in Supplementary Figure S1.

![Figure 1 placeholder](placeholder_figure1.png)

**Figure 1 | Composition and reuse landscape of the CoupledMD v9 release.** (**A**) System counts across the GPCR-class × G-protein-family matrix for all 207 systems. (**B**) Receptors represented with more than one G-protein family. (**C**) Ligand context by family. (**D**) Receptor representation reported as both 174 receptor names and 173 mapped UniProt accessions; `Gs_8HTI` has an explicit missing accession. (**E**) Release boundary: 207 included, 13 unresolved and two excluded duplicate/mislabel record from the 222-record working inventory. Biological interpretation of family or ligand patterns is outside the scope of this Data Descriptor.

The resource was designed for four modes of reuse (Fig. 2C): (i) selection of systems by receptor, GPCR class, G-protein family, ligand context, construct provenance or protocol; (ii) benchmarking trajectory-analysis, pocket-detection and structural-comparison methods against a defined cohort; (iii) cross-receptor positional joins using PDB, UniProt, GPCRdb and CGN identifiers; and (iv) rapid visual inspection through reduced representative trajectories, without treating them as substitutes for quantitative production data. The portal (https://www.coupledmd.cn) and versioned REST API provide the current access layer; the complete archival release will become the immutable version of record when deposited. Derived pocket, gateway and G-protein records are computational annotations and are not evidence of coupling selectivity, biased signalling or druggability.

## Methods

### Source structures and eligibility criteria

Active-state GPCR–G-protein complex structures were collected from the Protein Data Bank (PDB)^7^ by restricting to entries containing both a seven-transmembrane receptor and a heterotrimeric or engineered G-protein assembly in an active or active-like conformation. Receptor chains were cross-referenced to UniProt^8^, GPCRdb^3^ and GproteinDb^9^; G-protein chains were assigned to one of four families (Gi/o, Gs, Gq/11 or G12/13) from the Gα-subtype annotation. Structural provenance was recorded separately from receptor activation state: of the 207 included systems, 197 derive from experimental coordinates and 11 carry an engineered or uncertain provenance flag, so that users may apply stricter inclusion criteria if required.

Each system is identified as `<family>_<PDBID>` (for example, `Gi_7F1Q`). Inclusion in v9 required a GPCR–G-protein assembly assignable to one of the four families, processing through the CHARMM36-family workflow, and readiness evidence selecting three validated 500-ns replicas. Thirteen unresolved systems are documented rather than silently discarded; `Gq_7E9W` is excluded as a non-GPCR duplicate/mislabel. The release uses the readiness-selected replicas for `Gq_8J9N` rather than stale six-replica metadata, and repaired final metadata for `Gi_7E32` and `Gi_8HK2`.

### System construction and membrane embedding

Complexes were embedded in a homogeneous POPC lipid bilayer using CHARMM-GUI Membrane Builder^10,11^. Missing residues and side chains in the receptor and G protein were modeled during preparation; protonation states were assigned at pH 7.4. Systems were solvated with TIP3P water leaving at least 15 Å of padding between the protein and the periodic box edge, and neutralized with Na⁺/Cl⁻ ions to an ionic strength of 0.15 M. Ligands retained from the source structure were parameterized with the CHARMM General Force Field (CGenFF)^12^ where applicable. All 207 systems are annotated as POPC membrane-embedded.

### Simulation protocols

Three protocol groups are represented in v9, all built on the CHARMM36m force field^15^:

| Protocol | Systems | Engine | Thermostat | Barostat |
|---|---:|---|---|---|
| P1 | 180 | AMBER pmemd.cuda | Langevin (γ = 1 ps⁻¹) | Monte Carlo, semi-isotropic |
| P2 | 26 | AMBER (CHARMM-GUI inputs) | Langevin (γ = 1 ps⁻¹) | Monte Carlo, semi-isotropic |
| P3 | 2 | GROMACS | Nosé–Hoover^13^ | Parrinello–Rahman, semi-isotropic^14^ |

All protocols used NPT conditions at 310 K and 1 bar, a 2-fs integration step, particle-mesh Ewald electrostatics^16^ and constraints on bonds to hydrogen (SHAKE for AMBER^17^; LINCS for GROMACS^18^). Nonbonded interactions used a 12-Å cutoff with force-switching from 10 Å (AMBER) or a 1.2-nm cutoff with switching from 1.0 nm (GROMACS). Coordinates were written every 50 ps. Each system underwent energy minimization followed by multi-stage equilibration with restraints on protein and lipid progressively released before production. Each of the three production replicas ran for 500 ns from independently assigned initial velocities, giving 1.5 µs per system and 310.5 µs across the cohort. Because the three protocol groups share a force-field family and membrane composition but differ in thermostat and barostat implementation, an immutable `protocol_id` is stored for every system and protocol group should be treated as a potential batch variable in cross-system analyses. Production replicas are computational repeats and are not biological replicates.

### Trajectory processing and reduced visualization records

Full production trajectories, with their matched engine-compatible topology and the input files needed to interpret atom order and simulation conditions, are the primary data records. AMBER systems use NetCDF trajectories with PRMTOP/PARM7 topologies; GROMACS systems use TRR trajectories with TPR and topology files. A separate reduced tier was generated for browser-based inspection: solvent, POPC and ions were removed, protein coordinates were aligned to a Cα reference, and frames were strided to 2,500 frames spanning 500 ns, written as matched PDB/XTC pairs. Reduced records support visual screening and system selection but must not be used for solvent-, lipid- or ion-dependent measurements, or for kinetics faster than their sampling interval.

### Pocket detection and orthosteric-site annotation

Pocket records were generated for all 207 systems using fpocket^19^. For each system, approximately 200 frames per replica (600 frames across three replicas) were sampled at a stride of 50 stored production frames. Protein coordinates in each frame were aligned to the reference structure by Cα atoms, and fpocket was executed independently per frame. Alpha-sphere occupancy was accumulated on a 1.5-Å Cartesian grid, and grid points occupied in at least 85% of analyzed frames were retained. Retained points were clustered by DBSCAN (ε = 2.85 Å, min_samples = 3), and protein heavy atoms within 4.0 Å of a persistent cluster were assigned as pocket-lining residues. For ligand-bearing systems, a cluster was labelled orthosteric when any retained grid point lay within 5.0 Å of a ligand heavy atom; `best_ortho_freq` reports the maximum mean grid-point frequency among orthosteric clusters. Ligand-free systems lack a positive-control site and are reported as not evaluable rather than failed. Full frequency grids are present in the current derived-record inventory; archival distribution will be documented by the frozen manifest.

### GPCRdb mapping and consensus pocket clustering

Pocket-lining residues were mapped to GPCRdb generic positions using PDB-specific structural records and sequence alignment to the GPCRdb reference^3,4,20^, enabling positional comparison across receptors that do not share residue numbering. Consensus pocket clusters were derived by average-linkage hierarchical clustering of GPCRdb-position sets using Jaccard distance. Consensus identifiers are release-specific and must be cited with the dataset version.

### Transmembrane-gateway annotations

Gateway records quantify lipid access between seven adjacent TM helix pairs (TM1–TM2 through TM7–TM1), with TM boundaries taken from GPCRdb helix assignments (Supplementary Figure S2). For each sampled frame, the trajectory was centered on the receptor and wrapped by residue; lipid heavy atoms within 5.0 Å of both helices and within the central TM z-band (25th–75th percentile of TM Cα z-coordinates) were classified as wedged. Penetration was computed as the maximum inward radial displacement of a wedged atom relative to the nearest helix-pair Cα wall, and a frame was classified as open when penetration was at least 0.5 Å. Per-system values are means across three replica summaries, with 95% confidence intervals from 1,000-iteration bootstrap resampling. The field `occupancy` reports the mean number of wedged lipid heavy atoms per frame (a dimensionless count, not a distance); missing values are encoded as null with a reason code and never as zero.

### Archive, web portal and REST API

The CoupledMD product is organized in three tiers. The planned DOI-linked archive will contain production trajectories, matched topologies and inputs, reduced visualization records, derived annotations, metadata tables, per-replica QC reports, a file-level SHA-256 manifest, code snapshots and licence documentation. The web portal at https://www.coupledmd.cn provides interactive browsing, filtering and per-system visualization with NGL^21^. The REST API, versioned under `/api/v1/`, exposes final-cohort system metadata, pocket records, gateway records and visualization assets. It filters system IDs against the 207-system final cohort; unresolved IDs and `Gq_7E9W` have no release record.

## Data Records

### Dataset scope and composition

The CoupledMD v9 release comprises 207 GPCR–G-protein systems, 174 distinct receptor names, 173 mapped UniProt accessions and 310.5 µs of aggregate production sampling across 621 trajectories (Table 1; Fig. 1). By GPCR class it contains 181 Class A and 26 Class B systems; by transducer it contains 95 Gi/o, 65 Gs, 41 Gq/11 and 6 G12/13 systems. Coverage is deliberately broad rather than uniform: it mirrors the composition of the experimental structural record, in which Gi/o- and Gs-coupled complexes are abundant and G12/13 complexes remain rare. `Gs_8HTI` is a consensus OR52c model without a canonical UniProt mapping and is retained with an explicit null accession. `Gq_7E9W` is excluded, not flagged as a cohort system.

**Table 1.** Composition of the CoupledMD v9 release by GPCR class and G-protein family.

| GPCR class | G-protein family | Systems | Distinct receptors | Sampling (µs) |
|---|---|---:|---:|---:|
| Class A | Gi/o | 92 | — | 138.0 |
| Class A | Gs | 46 | — | 69.0 |
| Class A | Gq/11 | 40 | — | 60.0 |
| Class A | G12/13 | 4 | — | 6.0 |
| Class B | Gi/o | 3 | — | 4.5 |
| Class B | Gs | 19 | — | 28.5 |
| Class B | Gq/11 | 2 | — | 3.0 |
| Class B | G12/13 | 2 | — | 3.0 |
| **Total** | **All** | **207** | **174 names / 173 mapped accessions** | **310.5** |

Per-cell receptor counts are not additive because a receptor may occur with more than one G-protein family. The total of 174 is receptor names; the separately reported mapped-UniProt total is 173 because `Gs_8HTI` lacks a canonical accession. Receptors represented with multiple transducers (Fig. 1B) support within-receptor, across-family comparison. Table 2 and Figure 2 describe the planned archival hierarchy and current access-layer organization.

![Figure 2 placeholder](placeholder_figure2.png)

**Figure 2 | Repository organization, metadata schema and three-tier access model.** (**A**) Planned per-system archival hierarchy, from the release-level manifest and metadata tables down to inputs, per-replica production trajectories, reduced records, derived annotations and QC. (**B**) Entity-relationship diagram linking system-, replica- and file-level metadata. (**C**) Access model distinguishing the current portal/API from the future DOI-linked archive, which will be the immutable version of record after deposition. (**D**) The web portal, showing search and family/class/ligand filtering, per-system NGL visualization and API-entry actions. No panel claims that the raw 621-replica archive is already publicly deposited.

### Repository organization and molecular formats

The planned archive follows a predictable per-system hierarchy (Table 2; Fig. 2A). Every molecular trajectory will have exactly one declared matching topology, and every file will be resolved through the frozen manifest rather than a live filesystem path.

**Table 2.** Planned archive hierarchy and current v9 access-layer status.

| Path | Contents | Principal format |
|---|---|---|
| `manifest/` | Release metadata, one-row-per-file SHA-256 manifest, version record | TSV, JSON |
| `metadata/systems.csv` | System-level metadata for the 207 included systems | CSV |
| `metadata/unresolved_systems.csv` | 13 unresolved systems with current evidence | CSV (planned archive) |
| `systems/<id>/inputs/` | Starting coordinates, topology, parameter and engine input files | PDB, PRMTOP/PARM7, TPR, MDIN, MDP |
| `systems/<id>/replicas/rep{1,2,3}/` | Production trajectories and per-replica QC | NetCDF or TRR; JSON/TSV |
| `systems/<id>/reduced/` | Reduced reference and visualization trajectory | PDB, XTC |
| `systems/<id>/annotations/` | Pocket, gateway, GPCRdb-mapping and chain-role records | JSON, NPZ, CSV |
| `systems/<id>/qc/` | Per-system QC summaries | JSON, TSV |
| `code/` | Processing, validation and figure scripts with environment files | Python, YAML |
| `web_api_snapshot/` | OpenAPI schema and final-cohort response fixtures | JSON, YAML |

### Metadata schema

System-, replica- and file-level metadata are kept as separate tables joined by stable keys (Fig. 2B). The system-level record contains local and external identifiers (`system_id`, `pdb_id`, `receptor_name`, `receptor_uniprot`, `receptor_gene`, `gpcrdb_id`); classification fields (`gpcr_class`, `g_protein_family`, `g_alpha_subtype`); ligand and construct annotation (`ligand_name`, `ligand_chem_id`, `ligand_class`, `activation_state`, `structural_provenance`); the `protocol_id` key; the replica design (`n_replicas`, `length_per_replica_ns`, `total_sampling_ns`); force-field and membrane annotation; and QC fields (`qc_status`, `qc_reason`). Time is reported in nanoseconds and file size in bytes; enumerated fields use controlled vocabularies. Null values are encoded as empty strings in CSV and `null` in JSON, and zeros are never used as null surrogates. The complete field-level dictionary—with entity level, type, unit, requiredness, nullability, controlled vocabulary, provenance authority and schema version for every field—is provided in Supplementary Table S1, and the PDB, UniProt and GPCRdb release dates used for mapping are recorded so that annotations can be reconstructed.

### FAIR implementation

CoupledMD implements the FAIR principles^22^ explicitly (Fig. 2C,D; Supplementary Figure S3). **Findable:** the dataset receives a persistent DOI on deposition, and rich system-level metadata support discovery by receptor, family, PDB identifier and ligand context. **Accessible:** the archive is deposited in a community-recognized repository under CC BY 4.0, retrievable by open protocol; the portal and API are auxiliary routes to the authoritative DOI record (Fig. 2D). **Interoperable:** trajectories use standard molecular formats (NetCDF, TRR, XTC, PDB), annotations reference PDB, UniProt, GPCRdb and CGN identifiers, and the API follows OpenAPI 3.0 with typed responses and controlled vocabularies. **Reusable:** file-level SHA-256 checksums, per-replica QC, explicit protocol provenance, a canonical metadata dictionary and versioned MIT-licensed code together allow independent verification and reproduction.

## Technical Validation

Validation proceeds from the release boundary inward: we first confirm that the cohort and identifiers are internally consistent, then validate the derived pocket layer against known structural features, and finally evaluate the primary-trajectory readiness evidence and reduced visualization records. Current machine-readable v9 tables are versioned to the final cohort; the archival manifest/QC package remains pending its freeze and deposition.

### Cohort integrity and identifier verification

The v9 boundary was enforced against the 222-record working inventory (Fig. 1E). All 207 included systems have three selected 500-ns replicas, matched trajectory/topology evidence and final-cohort membership. Thirteen systems remain unresolved: eight have PBC/trajectory-continuity evidence, four component-continuity evidence and one incomplete-trajectory evidence. `Gq_7E9W` is separately excluded as a non-GPCR duplicate/mislabel. A programmatic audit confirms 207 unique release IDs, 621 selected replicas, 310,500 ns aggregate sampling, and no unresolved or excluded ID in the final public API cohort.

Identifier verification confirmed that each included PDB code resolves to the intended GPCR–G-protein complex and that chain-role assignments are consistent with GPCRdb structural records. `Gs_8HTI` is a consensus OR52c model without a canonical UniProt accession and is retained with an explicit null mapping. `Gq_7E9W` is not retained: it is documented as a non-GPCR duplicate/mislabel of `Gq_8E9W`. This transparent treatment avoids silently dropping unmapped systems while preventing an invalid identifier from entering the release.

### Pocket-annotation validation

The pocket layer was validated using orthosteric-site recovery as a positive control. Pocket outputs are available for 205 of 207 systems. The correct v9 denominator is the 58 peptide-ligand systems with pocket records: 49/58 (84.5%) recover an orthosteric cluster at the 0.85 grid-frequency threshold. Family-resolved recovery is 16/18 Gi/o, 15/18 Gs and 18/22 Gq/11; G12/13 has no eligible ligand-defined system and is therefore not applicable. The 150 ligand-free systems lack a positive-control site and are not failures. The two systems without pocket output are reported as unavailable rather than negative outcomes. These results are technical evidence for a derived structural annotation, not evidence of druggability or binding mechanism. GPCRdb-mapped pocket positions provide receptor-independent reference points for cross-receptor joins.

![Figure 3 placeholder](placeholder_figure3.png)

**Figure 3 | Technical validation of the pocket-annotation layer.** (**A**) Best per-system orthosteric-pocket frequency among the 58 eligible peptide-ligand systems with pocket outputs; the dashed line marks the 0.85 threshold and the recovered count is 49/58. (**B**) Per-system pocket-count distributions by family, with unavailable pocket records explicitly identified. Ligand-free systems are excluded from the recovery denominator. The figure supports technical reuse of a derived structural annotation, not a claim of druggability.

### Production-trajectory integrity

Because the 621 full production trajectories are the primary molecular records, they were subjected to a seven-tier per-replica quality-control framework rather than only to metadata-level checks:

1. File presence, non-zero size, readability and SHA-256 checksum agreement with the manifest;
2. Exact expected duration (500 ns), correct frame count and monotonic timestamps;
3. Finite coordinates throughout and valid periodic unit-cell vectors on every frame;
4. Atom-count and atom-order agreement between each trajectory and its declared topology;
5. Periodic-boundary continuity, with detection of catastrophic chain or complex separation;
6. Structural integrity, requiring receptor TM-core Cα RMSD ≤ 5 Å and retention of the G protein within a 25-Å Cα centroid distance of the starting complex;
7. Thermodynamic-control indicators (temperature and box-volume stability) where these quantities are stored.

The frozen archival QC package will record `file_status`, `trajectory_status`, `physical_qc_status` and `overall_status` one row per replica. Figure 4B instead displays the current readiness evidence for the final cohort and separates the 13 unresolved records by current category. It does not present obsolete aggregate PASS/WARN/FAIL totals or imply that the archived per-replica QC package is already deposited. Users who require stricter file-level filtering should await the frozen manifest/QC release.

### Reduced-trajectory audit

The reduced visualization tier was audited independently of the production data, because it is a lossy derivative intended only for inspection. For all 207 systems, 40 sampled frames per record were checked for topology–trajectory atom-count agreement, blank PDB element fields, box-dimension consistency, intra-chain backbone breaks, inter-chain splitting and coordinate scatter. The audit returned 205 systems classified PBC OK and 3 classified WARN for minor coordinate scatter only, with no atom-count, blank-element, box-mismatch or chain-break failures and seven scatter frames in total (Fig. 4C). Frame counts are 2,500 for 205 systems, 2,501 for two systems and 200 for `Gs_3SN6`; the short `Gs_3SN6` reduced record is flagged so that analyses assuming standard reduced sampling can exclude it. This audit validates sampled reduced frames only and makes no claim about unsampled reduced frames or about any production trajectory, whose integrity is established separately above. Together with the production-trajectory QC (Fig. 4B) and the cohort boundary (Fig. 1E), the reduced-trajectory audit completes the quality-control view of the release: Figure 4D summarizes annotation-layer coverage, confirming that pocket, gateway, GPCRdb-mapping and chain-role records are available for 206–207 systems depending on the layer.

![Figure 4 placeholder](placeholder_figure4.png)

**Figure 4 | Release readiness and quality control.** (**A**) Final release boundary: 207 included, 13 unresolved and two excluded duplicate/mislabel record. (**B**) Readiness evidence for unresolved systems, grouped as trajectory/PBC continuity, component continuity and incomplete trajectory; timestamp resets are diagnostic only. (**C**) Reduced-visualization audit, separated from primary-production readiness. (**D**) Derived-record coverage across the 207-system cohort. The figure does not represent timestamp resets as trajectory failures or claim an archival production-QC package before its final manifest is frozen.

## Usage Notes

### Access tiers

CoupledMD can be reused at three levels matched to different needs. Users performing quantitative trajectory analysis should retrieve the full production trajectories and matched topologies from the DOI-linked archive and verify SHA-256 checksums before analysis. Users needing rapid system selection, method prototyping or pipeline testing can consume the processed metadata, pocket, gateway and QC records directly through the API. Users needing visual inspection can browse reduced trajectories through the web portal without downloading full data.

### Example workflows

**System selection and download:**

```bash
# List Gi/o-coupled Class A systems bearing a small-molecule ligand
curl "https://www.coupledmd.cn/api/v1/systems?family=Gi&class=A&ligand_class=small_molecule&limit=20"

# Retrieve metadata and pocket annotations for a specific system
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q
curl https://www.coupledmd.cn/api/v1/systems/Gi_7F1Q/pockets
```

**Loading a trajectory with MDAnalysis:**

```python
import MDAnalysis as mda
import hashlib

# Verify the file against its manifest checksum before use
with open("Gi_7F1Q_rep1.nc", "rb") as fh:
    assert hashlib.sha256(fh.read()).hexdigest() == expected_sha256

u = mda.Universe("Gi_7F1Q.prmtop", "Gi_7F1Q_rep1.nc")
receptor = u.select_atoms("protein and segid PROA")
```

A tested single-system example notebook in `code/examples/` performs this full round trip—querying the API, downloading one topology–trajectory pair, verifying its checksum, loading it with MDAnalysis^25^ and joining GPCRdb-mapped pocket records—so that users can confirm their environment reproduces the deposited workflow.

To illustrate the reusable annotation layer that becomes available once a system has been retrieved and its pockets mapped, Figure 5 consolidates the structural view, the consensus-pocket clustering across the cohort, the anatomical-zone distribution, the most frequent GPCRdb anchor positions and the family-resolved recovery rates into a single atlas. The accompanying `code/examples/atlas_query.py` reproduces each panel of Figure 5 from the deposited records.

![Figure 5 placeholder](placeholder_figure5.png)

**Figure 5 | GPCRdb-mapped consensus pocket annotations distributed with CoupledMD.** (**A**) Representative per-system pocket surface mapped onto an active-state receptor structure, illustrating the lining-residue and orthosteric-cluster records available for every system. (**B**) Consensus druggable-pocket clusters positioned by receptor coverage and mean occupancy, with marker size reflecting cluster volume and color denoting anatomical zone (orthosteric, extracellular vestibule, intracellular/transducer interface, membrane-facing). (**C**) Cluster-member counts by anatomical zone, summarizing where reusable pockets recur across the cohort. (**D**) GPCRdb generic positions most frequently contributing to orthosteric and druggable cluster cores, providing receptor-independent anchors for cross-receptor joins. (**E**) Family-resolved orthosteric-recovery rates reproduced as a validation reference for the atlas. The figure shows how the pocket layer functions as a reusable, GPCRdb-anchored atlas that supports cross-receptor annotation joins and prioritization, while remaining a derived computational annotation rather than experimental validation of druggability.

### Reuse guidance

- Split machine-learning datasets by receptor accession or higher-level receptor grouping, never by replica, to prevent leakage between correlated trajectories.
- Treat `protocol_id`, GPCR class, ligand context, construct type and source PDB as potential batch variables when comparing across G-protein families.
- The six G12/13 systems do not support precise family-wide statistical inference and should be used qualitatively.
- Pocket and gateway records are derived computational annotations that require task-specific validation before biological interpretation; `occupancy` is a lipid-atom count, not a distance.
- Cite both the *Scientific Data* article and the exact dataset DOI and version used.

### Limitations

CoupledMD v9 is restricted to active-state GPCR–G-protein complexes present in the structural record and is therefore not representative of physiological coupling frequencies; inactive receptors, arrestin complexes and nucleotide-free states are out of scope. Starting structures include engineered constructs, and related receptors or structures are not statistically independent. The uniform POPC membrane does not reproduce native lipid diversity, and a 500-ns trajectory may not sample transitions on microsecond or longer timescales. The three protocol groups share a force-field family and membrane composition but differ in thermostat and barostat algorithms and should be treated as batch variables. MD trajectories and derived annotations are computational model outputs, not experimental observations.

## Data Availability

The CoupledMD web portal is available at https://www.coupledmd.cn and API documentation at https://www.coupledmd.cn/api/docs. The current public access layer exposes the final 207-system metadata and derived records, including one reduced representative PDB/XTC visualization pair per included system. Complete primary trajectories, matched topologies, inputs, checksums and the frozen file manifest are being prepared for DOI-linked archival deposition. Until that deposition, this manuscript makes no claim of archive completeness, DOI availability, direct raw-trajectory download or public release of all 621 primary trajectories.

## Code Availability

Processing, validation and figure-generation code is archived at [CODE REPOSITORY URL] under the MIT licence (release tag: [TAG]; commit: [HASH]). The archive includes Python environment and lock files, command-line configurations, the pocket, gateway and QC pipelines, figure and table generation scripts, and a tested single-system example workflow that downloads one system, verifies its checksum, loads the trajectory with MDAnalysis and joins GPCRdb-mapped pocket records.

## Author Contributions

J.H. and S.L. conceived the dataset. J.H. curated the system inventory, performed the molecular dynamics simulations, developed the processing and annotation workflows, implemented the web portal and REST API, performed the technical validation, and generated the figures and tables. X.Q. contributed to data curation and validation. J.H. and S.L. wrote the manuscript. All authors reviewed and approved the final version.

## Competing Interests

The authors declare no competing interests.

## Acknowledgements

The authors acknowledge computational resources provided by Shanghai Jiao Tong University.

## Funding

This work was supported by the Noncommunicable Chronic Diseases–National Science and Technology Major Project (2024ZD0531200) and the Innovative Research Team of High-Level Local Universities in Shanghai.

## References

1. Hauser, A. S. *et al.* Pharmacogenomics of GPCR drug targets. *Cell* **172**, 41–54.e19 (2018). https://doi.org/10.1016/j.cell.2017.11.033
2. Weis, W. I. & Kobilka, B. K. The molecular basis of G protein-coupled receptor activation. *Annu. Rev. Biochem.* **87**, 897–919 (2018). https://doi.org/10.1146/annurev-biochem-060614-033910
3. Kooistra, A. J. *et al.* GPCRdb in 2021: integrating GPCR sequence, structure and function. *Nucleic Acids Res.* **49**, D335–D343 (2021). https://doi.org/10.1093/nar/gkaa1080
4. Isberg, V. *et al.* Generic GPCR residue numbers—aligning topology maps while minding the gaps. *Trends Pharmacol. Sci.* **36**, 22–31 (2015). https://doi.org/10.1016/j.tips.2014.11.001
5. Rodríguez-Espigares, I. *et al.* GPCRmd uncovers the dynamics of the 3D-GPCRome. *Nat. Methods* **17**, 777–787 (2020). https://doi.org/10.1038/s41592-020-0884-y
6. Mirarchi, A., Giorgino, T. & De Fabritiis, G. mdCATH: a large-scale MD dataset for data-driven computational biophysics. *Sci. Data* **11**, 1299 (2024). https://doi.org/10.1038/s41597-024-04140-z
7. Berman, H. M. *et al.* The Protein Data Bank. *Nucleic Acids Res.* **28**, 235–242 (2000). https://doi.org/10.1093/nar/28.1.235
8. UniProt Consortium. UniProt: the Universal Protein Knowledgebase in 2025. *Nucleic Acids Res.* **53**, D609–D617 (2025). https://doi.org/10.1093/nar/gkae1010
9. Pándy-Szekeres, G. *et al.* GproteinDb in 2024: new G protein–GPCR couplings, AlphaFold2-multimer models and interface interactions. *Nucleic Acids Res.* **52**, D466–D475 (2024). https://doi.org/10.1093/nar/gkad1089
10. Jo, S., Kim, T., Iyer, V. G. & Im, W. CHARMM-GUI: a web-based graphical user interface for CHARMM. *J. Comput. Chem.* **29**, 1859–1865 (2008). https://doi.org/10.1002/jcc.20945
11. Lee, J. *et al.* CHARMM-GUI Membrane Builder for complex biological membrane simulations with glycolipids and lipoglycans. *J. Chem. Theory Comput.* **15**, 775–786 (2019). https://doi.org/10.1021/acs.jctc.8b01066
12. Vanommeslaeghe, K. *et al.* CHARMM General Force Field: a force field for drug-like molecules compatible with the CHARMM all-atom additive biological force fields. *J. Comput. Chem.* **31**, 671–690 (2010). https://doi.org/10.1002/jcc.21367
13. Nosé, S. A unified formulation of the constant temperature molecular dynamics methods. *J. Chem. Phys.* **81**, 511–519 (1984). https://doi.org/10.1063/1.447334
14. Parrinello, M. & Rahman, A. Polymorphic transitions in single crystals: a new molecular dynamics method. *J. Appl. Phys.* **52**, 7182–7190 (1981). https://doi.org/10.1063/1.328693
15. Huang, J. *et al.* CHARMM36m: an improved force field for folded and intrinsically disordered proteins. *Nat. Methods* **14**, 71–73 (2017). https://doi.org/10.1038/nmeth.4067
16. Darden, T., York, D. & Pedersen, L. Particle mesh Ewald: an N·log(N) method for Ewald sums in large systems. *J. Chem. Phys.* **98**, 10089–10092 (1993). https://doi.org/10.1063/1.464397
17. Ryckaert, J.-P., Ciccotti, G. & Berendsen, H. J. C. Numerical integration of the Cartesian equations of motion of a system with constraints: molecular dynamics of n-alkanes. *J. Comput. Phys.* **23**, 327–341 (1977). https://doi.org/10.1016/0021-9991(77)90098-5
18. Hess, B. *et al.* LINCS: a linear constraint solver for molecular simulations. *J. Comput. Chem.* **18**, 1463–1472 (1997). https://doi.org/10.1002/(SICI)1096-987X(199709)18:12%3C1463::AID-JCC4%3E3.0.CO;2-H
19. Le Guilloux, V., Schmidtke, P. & Tuffery, P. Fpocket: an open source platform for ligand pocket detection. *BMC Bioinformatics* **10**, 168 (2009). https://doi.org/10.1186/1471-2105-10-168
20. Pándy-Szekeres, G. *et al.* GPCRdb in 2024: integrating GPCR sequence, structure and function. *Nucleic Acids Res.* **52**, D148–D157 (2024). https://doi.org/10.1093/nar/gkad1011
21. Rose, A. S. *et al.* NGL viewer: web-based molecular graphics for large complexes. *Bioinformatics* **34**, 3755–3758 (2018). https://doi.org/10.1093/bioinformatics/bty419
22. Wilkinson, M. D. *et al.* The FAIR Guiding Principles for scientific data management and stewardship. *Sci. Data* **3**, 160018 (2016). https://doi.org/10.1038/sdata.2016.18
23. Salomon-Ferrer, R. *et al.* Routine microsecond molecular dynamics simulations with AMBER on GPUs. 2. Explicit solvent particle mesh Ewald. *J. Chem. Theory Comput.* **9**, 3878–3888 (2013). https://doi.org/10.1021/ct400314y
24. Abraham, M. J. *et al.* GROMACS: high performance molecular simulations through multi-level parallelism from laptops to supercomputers. *SoftwareX* **1–2**, 19–25 (2015). https://doi.org/10.1016/j.softx.2015.06.001
25. Michaud-Agrawal, N. *et al.* MDAnalysis: a toolkit for the analysis of molecular dynamics simulations. *J. Comput. Chem.* **32**, 2319–2327 (2011). https://doi.org/10.1002/jcc.21787
26. Flock, T. *et al.* Selectivity determinants of GPCR–G-protein binding. *Nature* **545**, 317–322 (2017). https://doi.org/10.1038/nature22070
27. McGibbon, R. T. *et al.* MDTraj: a modern open library for the analysis of molecular dynamics trajectories. *Biophys. J.* **109**, 1528–1532 (2015). https://doi.org/10.1016/j.bpj.2015.08.015
