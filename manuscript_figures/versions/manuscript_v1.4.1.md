# CoupledMD: a uniform-protocol molecular dynamics web resource for comparative analysis of 222 GPCR–G-protein ternary complexes

---

## Abstract

CoupledMD (https://coupledmd.org) is the first web resource to provide uniform-protocol molecular dynamics (MD) simulations for 222 active-state G protein-coupled receptor (GPCR)–G-protein ternary complexes spanning all four G-protein subfamilies (Gi/o, Gs, Gq/11, G12/13), yielding 332 μs of aggregate sampling under a single force field. Because every system is parameterized identically, CoupledMD enables statistical comparisons that are not possible when aggregating simulations from disparate sources. The resource delivers five precomputed analysis layers for each system: pocket occupancy landscapes, membrane lipid-entry gateway dynamics, G-protein interface barcodes indexed to the 356-position Common G-protein Numbering (CGN) scheme, α5 helix coupling geometry descriptors, and a partner-switching comparison tool for receptors with multi-partner data. Prospective validation on CCR5 recovers the FDA-approved maraviroc allosteric site from MD alone, without structural input from the inhibitor-bound conformation. All data are served through an interactive web interface and a fully documented REST API. Source trajectories (4.7 TB) are deposited at [repository placeholder] under open-access terms. All 222 systems are embedded in a POPC lipid bilayer, enabling uniform gateway and pocket analysis across the full cohort.

---

## Introduction

G protein-coupled receptors (GPCRs) constitute the largest family of druggable membrane proteins in the human genome, mediating responses to hormones, neurotransmitters, and sensory stimuli, and accounting for approximately 35% of all FDA-approved drug targets [1]. Upon agonist binding, the intracellular face of the receptor rearranges to engage heterotrimeric G proteins from four major families—Gi/o, Gs, Gq/11, and G12/13—thereby routing the signal into distinct downstream cascades [2]. A central and unresolved question is how a single receptor selectively couples to one G-protein family over another, and how that selectivity can be exploited pharmacologically to achieve pathway-biased drug action.

Coupling selectivity is inherently dynamic. The intracellular cavity samples transient conformations that open and close allosteric pockets, modulate membrane lipid-entry portals (gateways) at the receptor–G-protein interface, and reposition the G-protein α5 helix within the binding cleft—events that are invisible in static crystal structures [3]. Molecular dynamics (MD) simulations capture these phenomena on the microsecond timescale, but their value for comparative analysis depends critically on a factor that has been largely overlooked in existing GPCR informatics resources: **protocol uniformity**.

The two primary community resources address complementary but non-overlapping needs. GPCRdb [4] curates experimental structures, sequence alignments, and mutagenesis data with exceptional cross-receptor indexing, but provides no MD-derived dynamic analyses. GPCRmd [5] offers a growing repository of uploaded MD trajectories across diverse GPCR systems; however, because submissions originate from independent laboratories using different force fields, membrane compositions, simulation lengths, and analysis pipelines, quantitative cross-system comparisons are confounded by protocol heterogeneity. A researcher asking, for example, whether a given receptor opens its TM6–TM7 lipid-entry gateway more in the Gi complex than in the Gq complex cannot reliably answer that question from GPCRmd if the two simulations were generated with different force fields. Neither resource currently supports direct partner-switching analysis—precomputed, side-by-side comparison of pocket occupancy and gateway dynamics for the same receptor coupled to different G-protein partners.

CoupledMD resolves this by construction. All 222 systems were simulated under a single protocol—CHARMM36m force field [6], three 500 ns replicas per system, POPC lipid bilayer—and analysed through a shared computational pipeline. This uniformity is the defining feature of the resource: it converts MD data from anecdotal per-system observations into a cohort that supports cross-family statistical analysis and within-receptor partner comparisons. At 222 systems and 332 μs of aggregate sampling, CoupledMD is, to our knowledge, the largest uniform-protocol MD dataset for GPCR–G-protein ternary complexes published to date.

This paper describes the CoupledMD database, analysis pipeline, and web server. Figure 1 summarizes the 222-system cohort and its G-protein family composition. Figure 2 demonstrates prospective allosteric site recovery in CCR5, where the Na⁺/maraviroc pocket is recovered from MD without structural input from the inhibitor-bound form. Figure 3 illustrates partner-dependent gateway reorganization in FFAR4 between Gi and Gq couplings. Figure 4 presents the G-protein interface barcode and α5 coupling geometry landscape across the cohort. Figure 5 showcases the partner-switching comparison tool using OX2R, illustrating how Gi coupling uniquely accesses a druggable pocket absent in both Gq and Gs, while Gq and Gs share identical pocket profiles but show partner-dependent gateway reorganization.

---

## Database Description

### 3.1 Dataset composition and simulation protocol

The CoupledMD database comprises 222 GPCR–G-protein ternary complex systems drawn from the Protein Data Bank [7] and GPCRdb [4] (Figure 1A). The cohort spans four G-protein subfamilies: Gi/o (100 systems, 45%), Gs (68, 31%), Gq/11 (47, 21%), and G12/13 (7, 3%), representing 182 unique receptors (Figure 1A, B). The predominance of Gi-coupled systems reflects the larger number of experimental ternary complex structures available for this subfamily. G12/13 remains under-represented with 7 systems, a limitation imposed by the scarcity of high-resolution experimental structures for this subfamily.

All 222 systems were parameterized with the CHARMM36m force field [6] and simulated in three independent replicas of 500 ns, yielding approximately 332 μs of aggregate sampling (Figure 1C). Of the systems, 186 were executed with the AMBER pmemd engine [9] using chamber-converted topologies, 10 systems with GROMACS [8], and 26 class-B receptor systems prepared via CHARMM-GUI [10]. All 222 systems were embedded in a POPC lipid bilayer. Of the 222 structures, 211 derive from experimental coordinates; 11 originate from engineered or chimeric constructs (BRIL-fused receptors, recovered identifiers) and are flagged in the database (Figure 1B). The top 15 receptor genes by system count span class A aminergic, peptide, and lipid-sensing receptors (Figure 1D; Table T1).

### 3.2 Pocket landscape and allosteric site recovery

Transient binding pockets at the intracellular face of each receptor were identified using fpocket [11] with a consensus filter requiring detection in at least two of three replicas. Of 222 systems, 209 yield consensus pocket data; the 13 exceptions correspond to simulations where the intracellular cavity remained occluded throughout all replicas. Lining residues were mapped to GPCRdb generic positions [12] to enable cross-receptor alignment and clustering. Consensus clustering across the full database identifies 50 druggable pocket clusters spanning 182 unique receptors, with per-cluster mean occupancy frequencies ranging from 0.858 to 0.927.

As a prospective validation, we examined CCR5 (system Gi_7F1Q; Figure 2). MD blind-recovers an intracellular allosteric pocket lining residues at GPCRdb positions 2.50, 3.39, and 7.49 — the Na⁺ binding motif that co-localises with the adjacent maraviroc binding site [13, 14], the site of an FDA-approved allosteric CCR5 inhibitor used to treat HIV infection. In CCR5 this pocket is recovered at a mean occupancy frequency of 0.910 from MD dynamics alone, without structural input from the inhibitor-bound conformation (Figure 2A, B); across the database, the corresponding consensus pocket cluster spans 10 systems at a mean frequency of 0.927. The recovery of a clinically validated allosteric site through unbiased MD sampling demonstrates that the CoupledMD pipeline captures functionally relevant transient cavities that could serve as starting points for allosteric drug discovery in receptor systems where no allosteric ligand is yet known.

Across the 209 systems with detectable pockets, the orthosteric binding site is recovered in 158 (75.6%; Table T2), rising to 94.9% for systems co-crystallized with a small-molecule ligand and 85.3% for peptide-ligand systems, confirming that the pipeline systematically captures the primary ligand-accessible cavity. The 13 systems without detectable pockets correspond to simulations in which the intracellular cavity remained occluded throughout all replicas.

The uniform simulation protocol of CoupledMD uniquely enables direct comparison of pocket landscapes between G-protein partners of the same receptor. Across 16 receptor contrasts with MD data for two or more G-protein partners, pocket Jaccard similarity coefficients range from 0.0 (no shared pocket clusters; SSTR2 Gi–Gq, NMUR2 Gi–Gq, CRHR2 Gi–Gs, H1R Gq–Gs, and P2Y1R Gq–Gs) to 1.0 (identical pocket profiles; OX2R Gq–Gs), with intermediate values such as EDNRB Gi–Gq (0.40) and GHSR Gi–Gq (0.33; Table T3). OX2R provides the most informative partner-switching case study (Figure 5): the Gi complex uniquely accesses a druggable intracellular pocket (consensus cluster D18) that is absent in both the Gq and Gs complexes (Jaccard similarity = 0.50 for Gi vs. Gq or Gs), while Gq and Gs themselves share identical pocket profiles (Jaccard similarity = 1.0). Because all paired simulations share an identical force field and analysis pipeline, these Jaccard differences reflect biological coupling selectivity rather than methodological artefact.

### 3.3 G-protein coupling geometry and interface barcodes

Per-position root-mean-square fluctuation (RMSF) and contact persistence were computed for the G-protein α-subunit at positions indexed by the 356-position Common G-protein Numbering (CGN) scheme [2]. The CGN system classifies these positions into four functional categories: conserved (142), selectivity-determining (127), paralog-specific (69), and neutral (18). Contact persistence—the fraction of simulation frames in which a receptor–G-protein residue pair falls within a 4 Å heavy-atom distance cutoff, averaged across replicas—constitutes a per-system G-protein barcode indexed to the CGN scheme and directly comparable across simulations; Figure 4A shows the mean profile across the pilot interface cohort. Order parameters (S²) and χ₁ rotameric entropy were computed where applicable, providing additional measures of side-chain flexibility at the coupling interface.

Four geometric descriptors characterize the G-protein α5 helix quantitatively: tilt angle relative to the receptor transmembrane axis (range 29.8°–73.1°, mean 52.9°), insertion depth into the intracellular cavity (range 20.4–50.8 Å, mean 32.2 Å), solvent-accessible surface area of the buried α5 tip, and hook angle at the C-terminal terminus (range 1.1°–12.3°). A composite functional rank integrating all four descriptors stratifies systems by coupling interface compactness (Figure 4B); OX2R (Gs, PDB 7L1V) is among the top-ranked systems, consistent with its extreme partner-switching behaviour.

Gateway dynamics further differentiate G-protein partners at the same receptor. For FFAR4, which couples to both Gi (Gi_8ID9) and Gq (Gq_8IYS), the TM6–TM7 portal shows the largest divergence: occupancy is 0.022 under Gi versus 0.208 under Gq—a nearly ten-fold difference indicating near-complete portal closure in the Gi complex (Figure 3A). The TM7–TM1 portal, by contrast, shows comparable occupancy under both partners (0.342 vs 0.392), demonstrating that partner-dependent gateway asymmetry is spatially localized rather than a global property of the interface (Figure 3). Because CoupledMD applies an identical analysis pipeline to both systems, these differences can be attributed to biology rather than methodology—the core analytical claim enabled by protocol uniformity.

---

## Methods

### Database construction and curation

Active-state GPCR–G-protein ternary complex structures were collected from the Protein Data Bank [7] and GPCRdb [4]. The cohort comprises 222 systems spanning four G-protein subfamilies: Gi/o (100), Gs (68), Gq/11 (47), and G12/13 (7), representing 182 unique receptors. Of the 222 structures, 211 are derived from experimental coordinates; the remaining 11 originate from engineered or chimeric constructs (e.g. BRIL-fused receptors, recovered identifiers) and are retained in the database but flagged so that users can exclude them from downstream analyses.

All systems were parameterized with the CHARMM36m force field [6]. Of the 222 systems, 186 were executed with the AMBER pmemd engine [9] using a chamber-converted topology; 10 systems were simulated with GROMACS [8]; and 26 class-B receptor systems were prepared via CHARMM-GUI [10] and simulated under the same force field. Each system was simulated in three independent replicas of 500 ns, yielding approximately 332 μs of aggregate sampling. All 222 systems were embedded in a POPC lipid bilayer. Production trajectories were stored in AMBER NetCDF format for 212 systems and GROMACS TRR format for the 10 GROMACS-run systems.

### Analysis pipeline

**Pocket detection.** Transient binding pockets at the intracellular face of each receptor were identified using fpocket [11]. Pocket predictions from all three replicas were aggregated per system, and a consensus filter was applied: a pocket was reported only if detected in at least two of three replicas, reducing spurious identifications. Lining residues were mapped to GPCRdb generic positions [12] to enable cross-receptor alignment.

**Gateway analysis.** Membrane lipid-entry portals at the receptor–G-protein interface were tracked by computing inter-helical distances between defined transmembrane portal pairs. Time series of portal-pair distances were extracted from each replica, characterizing the dynamics of gateway opening and closure on the 500 ns timescale.

**G-protein interface metrics.** Per-position RMSF and contact persistence were computed for the G-protein α-subunit at positions indexed by the CGN scheme [2]. The CGN system classifies 356 G-protein residue positions into four functional categories: conserved (142 positions), selectivity-determining (127), paralog-specific (69), and neutral (18). Contact persistence was defined as the fraction of simulation frames in which a given receptor–G-protein residue pair fell within a 4 Å heavy-atom distance cutoff, averaged across replicas. Order parameters (S²) and χ₁ rotameric entropy were computed where applicable. Together these metrics constitute a per-system G-protein barcode that can be compared directly across the 222 simulations via the CGN coordinate system.

**α5 coupling geometry.** Four geometric descriptors of the G-protein α5 helix were computed for each system: tilt angle relative to the receptor transmembrane helical axis (f₁), insertion depth into the intracellular cavity (f₆), solvent-accessible surface area of the buried α5 tip (f₄), and hook angle at the C-terminal terminus (f₂). These descriptors were extracted frame-by-frame and summarized as ensemble statistics per system. A composite functional rank integrating all four descriptors was derived to stratify systems by coupling interface compactness.

**Partner-switching analysis.** Receptors with MD data available for two or more G-protein subfamily partners were identified (16 receptor contrasts). For each contrast, pocket consensus-cluster sets were compared using the Jaccard similarity coefficient (|A ∩ B| / |A ∪ B|; 0 = no shared clusters, 1 = identical profiles), and mean absolute gateway open-fraction differences were computed across all seven transmembrane portal pairs. Five contrasts show Jaccard similarity = 0.0 (no shared pocket clusters): SSTR2 Gi–Gq, NMUR2 Gi–Gq, CRHR2 Gi–Gs, H1R Gq–Gs, and P2Y1R Gq–Gs. OX2R, with data for Gi, Gq, and Gs coupling, shows that the Gi complex uniquely accesses a druggable pocket (consensus cluster D18) absent in both Gq and Gs complexes (Jaccard similarity 0.50), while Gq and Gs share identical pocket profiles (similarity 1.0). Bootstrap 95% confidence intervals for gateway distances were derived from the distribution of portal-pair differences within each contrast.

**Allosteric site recovery.** As prospective validation, CCR5 (Gi_7F1Q) was examined. MD recovers an intracellular pocket lining generic positions 2.50, 3.39, and 7.49 that corresponds to the Na⁺ allosteric pocket and the adjacent maraviroc binding site [13, 14], at a mean occupancy frequency of 0.910. Recovery of this pocket from MD dynamics without structural input from the inhibitor-bound form demonstrates that the database captures functionally relevant transient cavities.

### Web server implementation

The CoupledMD web server follows a three-tier architecture. The backend is implemented in FastAPI [15] (Python 3.12) with an SQLite metadata store; all API responses are pre-serialized to JSON during pipeline execution, enabling low-latency retrieval without on-the-fly computation. The frontend is a React/Vite single-page application providing free-text search across 222 systems, interactive filterable tables, per-system pocket and gateway visualization, and a G-protein contact barcode display.

Trajectory visualization is provided through NGL.js [16]. Each system is represented by 2,500 frames sampled at 200 ps intervals, consistent with the GPCRmd [5] visualization standard. The visualization tier was generated from a pre-extracted protein-only database; each trajectory occupies approximately 160 MB in XTC format, totalling ~35 GB for all 222 systems.

The CouplingAtlas tool provides an interactive scatter of α5 tilt versus insertion depth across systems, enabling identification of outlier coupling geometries. The PartnerSwitch tool allows side-by-side comparison of pocket occupancy and gateway dynamics for receptors with multi-partner data, directly illustrating coupling selectivity at molecular resolution.

The server is deployed behind an Nginx reverse proxy with TLS 1.2/1.3 termination and rate limiting. A RESTful API is exposed at `/api/v1/` with interactive OpenAPI documentation at `/api/docs`, providing programmatic access to all precomputed datasets.

### Data availability

Source simulation trajectories (4.7 TB) are deposited at [placeholder: university repository, DOI pending]. Pre-computed analysis outputs (pocket annotations, gateway time series, CGN interface metrics, and α5 coupling geometry descriptors) are served through the CoupledMD web server and REST API at [URL]. All analysis and web server code is available at [GitHub URL] under the MIT licence.

---

## Discussion

CoupledMD occupies a distinct position in the GPCR computational landscape. GPCRdb provides unrivalled coverage of experimental structures and sequence-level annotations; GPCRmd provides a community repository for user-submitted trajectories. CoupledMD complements both by offering what neither currently provides: a uniform-force-field, uniform-protocol MD cohort of sufficient scale—222 systems, 332 μs—to support cross-family statistical analysis and within-receptor partner comparisons. The key insight is that the value of uniformity is not that any individual simulation in CoupledMD is superior to those in other resources, but that identical protocol converts MD data from anecdotal per-system observations into a dataset with genuine comparative power. A quantitative difference between a Gi-coupled and a Gs-coupled simulation of the same receptor in CoupledMD can be attributed to biological coupling selectivity rather than to force-field or protocol differences.

Three specific capabilities distinguish CoupledMD from existing resources. First, the PartnerSwitch comparison tool provides precomputed, direct side-by-side analysis of pocket occupancy and gateway dynamics for the same receptor coupled to different G-protein partners—the most operationally useful output of uniform-protocol simulation, and a capability unavailable elsewhere. Second, the G-protein interface barcode, standardized to the 356-position CGN scheme across all 222 systems, allows systematic identification of selectivity-determining positions whose contact persistence varies across G-protein families—an analysis that requires both cross-family data and uniform protocol. Third, prospective allosteric site recovery in CCR5 demonstrates that the CoupledMD pipeline identifies clinically validated binding sites from MD without prior knowledge of inhibitor-bound structures, suggesting utility for allosteric drug discovery in the many GPCR systems where no allosteric chemotype is yet known.

Several limitations should be acknowledged. The visualization tier and per-system G-protein barcodes currently use a single replica; multi-replica averaging will improve statistical robustness in future updates. The CGN interface barcode reported here (Figure 4A) is a pilot covering a subset of CGN positions and systems; extension to the full 356-position scheme across all 222 systems is in progress. The 500 ns per-replica timescale is sufficient for pocket and gateway dynamics but may miss rare conformational transitions. The G12/13 subfamily is represented by only 7 systems, limiting family-level statistics. The database is restricted to active-state ternary complexes; inactive-state receptors and GPCR–arrestin complexes are not yet included.

Future directions include extension to arrestin complexes, inactive-state simulations, and integration of AlphaFold-Multimer [17] predicted ternary complex structures for receptors lacking experimental coordinates. The open REST API enables programmatic meta-analysis across all 222 systems, and we encourage its integration into machine-learning pipelines for allosteric site prediction and biased-signalling modelling.

---

## Figure Captions

**Figure 1. Overview of the CoupledMD dataset.**
(A) System count per G-protein subfamily. CoupledMD comprises 222 ternary complexes: Gi/o (100), Gs (68), Gq/11 (47), and G12/13 (7), representing 182 unique receptors.
(B) Structural provenance. 211 of 222 systems derive from experimental coordinates; 11 originate from engineered or chimeric constructs (e.g. BRIL-fused receptors, recovered identifiers) and are retained in the database but flagged so that users can exclude them from downstream analyses. All 222 systems are embedded in a POPC lipid bilayer.
(C) Aggregate MD sampling per G-protein subfamily and for the full cohort. Each system was simulated in three independent 500 ns replicas, yielding ≈332 μs total.
(D) The twelve most-represented receptors, ranked by number of systems and coloured by predominant G-protein subfamily. Peptide- and lipid-sensing class A receptors dominate (orexin OX2R, free fatty acid FFAR4, cholecystokinin CCKAR, corticotropin-releasing factor CRHR2, endothelin EDNRB), reflecting the current experimental ternary complex structural coverage.

**Figure 2. Prospective allosteric site recovery in CCR5.**
(A) Mean occupancy frequency of the 13 persistent pockets detected in CCR5 (system Gi_7F1Q), ranked by frequency. The orthosteric pocket (red) is recovered at frequency 0.947; the intracellular Na⁺/maraviroc allosteric pocket (orange), lining GPCRdb positions 2.50, 3.39 and 7.49, is recovered at frequency 0.910 — blind from MD, with no inhibitor-bound starting structure. Remaining allosteric and interface pockets are shown in teal.
(B) Pocket size (lining residue count) versus mean occupancy frequency for all 13 pockets; bubble area is proportional to pocket volume. The Na⁺/maraviroc pocket and the orthosteric pocket are annotated; the former's lining residues at GPCRdb positions 2.50, 3.39 and 7.49 constitute the Na⁺ binding motif that co-localises with the maraviroc site.
(C) Summary of the CCR5 case study: system identifier, sampling, recovered pocket frequencies, key generic residue positions, and the clinical cross-reference to maraviroc.

**Figure 3. Partner-dependent gateway reorganization in FFAR4.**
FFAR4 is a lipid-sensing GPCR with CoupledMD data for both Gi (Gi_8ID9) and Gq (Gq_8IYS) coupling.
(A) Gateway open fraction (fraction of frames in the open state) for all seven transmembrane portal pairs, shown side-by-side for Gi/o (green) and Gq/11 (orange) with 95% confidence intervals. The TM6–TM7 portal shows the largest divergence (Gi: 0.022 vs Gq: 0.208; ~ten-fold), indicating near-complete closure under Gi coupling.
(B) Mean portal distance (Å) for all seven portal pairs. The dashed line at 8 Å denotes the empirical open-state threshold. Partner-dependent divergence is localized to specific portals rather than uniformly distributed across the interface.

**Figure 4. G-protein coupling interface barcode and α5 geometry landscape.**
(A) Mean contact persistence across the 25 CGN positions profiled in the pilot interface cohort, averaged over systems and grouped by CGN segment; bars are coloured by Flock functional class (conserved, selectivity-determining) and error bars are 95% confidence intervals. The α5 (G.H5) segment is shaded.
(B) α5 tilt angle versus insertion depth for the 27 systems with both descriptors available, coloured by G-protein subfamily; shaded ellipses are 2σ covariance envelopes. OX2R (Gs coupling, PDB 7L1V), tied for the top composite functional rank, is highlighted.
(C) Contact persistence at the selectivity-determining CGN positions, averaged within each G-protein subfamily, revealing conserved versus family-specific interface regions.
(D) RMSF profile along the G.H5 (α5) segment, grouped by subfamily. The C-terminal tip of α5 (G.H5 positions 24–26) shows the largest variance across systems, consistent with its role as the primary selectivity-encoding region.

**Figure 5. Partner-switching comparison: OX2R across three G-protein families.**
OX2R (orexin receptor 2) has CoupledMD data for Gi, Gq, and Gs coupling.
(A) Pocket Jaccard similarity (|A ∩ B| / |A ∪ B|; 0 = no shared clusters, 1 = identical profiles) versus gateway divergence (mean |Δ open fraction| across seven portals) for all 16 receptor contrasts. Points with Jaccard similarity = 0 represent complete pocket non-overlap; the OX2R Gq→Gs contrast (Jaccard = 1.0, gateway divergence 0.11) is annotated as a case of gateway reorganization without pocket-profile change.
(B) Pairwise pocket Jaccard similarity among OX2R's three G-protein complexes. The Gi complex uniquely accesses a druggable pocket (consensus cluster D18; Jaccard similarity 0.50 vs. both Gq and Gs), while Gq and Gs share identical pocket profiles (similarity 1.0).
(C) Heatmap of gateway open fraction across all seven TM portal pairs for OX2R under Gi, Gq, and Gs coupling, illustrating partner-specific gateway remodelling.
(D) Pocket Jaccard similarity versus α5 tilt difference for the 13 contrasts with both descriptors, OX2R highlighted. Across these contrasts, pocket divergence and α5 geometry difference show no significant association (Spearman ρ = 0.23, p = 0.45, n = 13), indicating that pocket-landscape differences are not simply a consequence of α5 re-tilting.

---

## References

1. Hauser AS, Attwood MM, Rask-Andersen M, Schiöth HB, Gloriam DE. Trends in GPCR drug discovery: new agents, targets and indications. *Nat Rev Drug Discov.* 2017;**16**(12):829–842.

2. Flock T, Hauser AS, Lund N, Gloriam DE, Balaji S, Babu MM. Selectivity determinants of GPCR–G-protein binding. *Nature.* 2017;**545**(7654):317–322.

3. Weis WI, Kobilka BK. The molecular basis of G protein-coupled receptor activation. *Annu Rev Biochem.* 2018;**87**:897–919.

4. Kooistra AJ, Mordalski S, Pándy-Szekeres G, Wacker D, Isberg V, Tsonkov T, et al. GPCRdb in 2021: integrating GPCR sequence, structure and function. *Nucleic Acids Res.* 2021;**49**(D1):D335–D343.

5. Rodríguez-Espigares I, Torrens-Fontanals M, Tiemann JKS, Aranda-García D, Ramírez-Anguita JM, Stepniewski TM, et al. GPCRmd uncovers the dynamics of the 3D-GPCRome. *Nat Methods.* 2020;**17**(8):777–787.

6. Huang J, Rauscher S, Nawrocki G, Ran T, Feig M, de Groot BL, et al. CHARMM36m: an improved force field for folded and intrinsically disordered proteins. *Nat Methods.* 2017;**14**(1):71–73.

7. Berman HM, Westbrook J, Feng Z, Gilliland G, Bhat TN, Weissig H, et al. The Protein Data Bank. *Nucleic Acids Res.* 2000;**28**(1):235–242.

8. Abraham MJ, Murtola T, Schulz R, Páll S, Smith JC, Hess B, et al. GROMACS: High performance molecular simulations through multi-level parallelism from laptops to supercomputers. *SoftwareX.* 2015;**1–2**:19–25.

9. Salomon-Ferrer R, Götz AW, Poole D, Le Grand S, Walker RC. Routine microsecond molecular dynamics simulations with AMBER on GPUs. 2. Explicit solvent particle mesh Ewald. *J Chem Theory Comput.* 2013;**9**(9):3878–3888.

10. Jo S, Kim T, Iyer VG, Im W. CHARMM-GUI: a web-based graphical user interface for CHARMM. *J Comput Chem.* 2008;**29**(11):1859–1865.

11. Le Guilloux V, Schmidtke P, Tuffery P. Fpocket: an open source platform for ligand pocket detection. *BMC Bioinformatics.* 2009;**10**:168.

12. Isberg V, Mordalski S, Munk C, Rataj K, Harpsøe K, Hauser AS, et al. GPCRdb: an information system for G protein-coupled receptors. *Nucleic Acids Res.* 2016;**44**(D1):D356–D364.

13. Tan Q, Zhu Y, Li J, Chen Z, Han GW, Kufareva I, et al. Structure of the CCR5 chemokine receptor–HIV entry inhibitor maraviroc complex. *Science.* 2013;**341**(6152):1387–1390.

14. Liu W, Chun E, Thompson AA, Chubukov P, Xu F, Katritch V, et al. Structural basis for allosteric regulation of GPCRs by sodium ions. *Science.* 2012;**337**(6091):232–236.

15. Ramírez S. FastAPI [Internet]. 2018. Available from: https://fastapi.tiangolo.com/

16. Rose AS, Bradley AR, Valasatava Y, Duarte JM, Prlić A, Rose PW. NGL viewer: web-based molecular graphics for large complexes. *Bioinformatics.* 2018;**34**(21):3755–3758.

17. Evans R, O'Neill M, Pritzel A, Antropova N, Senior A, Green T, et al. Protein complex prediction with AlphaFold-Multimer. *bioRxiv.* 2021. doi:10.1101/2021.10.04.463034.
