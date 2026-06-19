# Kickoff prompt — GPCR-G MD web resource (NAR Web Server Issue)

Paste this as the first message of a NEW Claude Code session started in the project root
`/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server`. This folder is the main folder for the web
resource project; all new server code, configuration, and docs live here. The analysis-layer
inputs and the canonical inventory live in the sibling directory
`/MDdata/data02/jxhuang/gpcr_g/a` (referred to below as ANALYSIS_SRC); treat ANALYSIS_SRC as
read-only input to the build. It is a cold-start brief so the new session does not re-derive
what the analysis sessions already established.

---

## ROLE AND CONTEXT

You are implementing a web resource that serves molecular dynamics of active-state
GPCR-G-protein ternary complexes, organized by G-protein family, with a precomputed
analysis layer. Target venue: the NAR Web Server Issue. The resource is the companion to
Paper 1 (a 222-system atlas). The full plan is the canonical reference; read it first:

  /MDdata/data02/jxhuang/gpcr_g/gpcr_g_server/gpcr_g_md_server_plan_revised.html

(Read the _revised version, not gpcr_g_md_server_plan.html. The revised file has the
corrected force-field statement. Sections 3, 5, 6, 7, 10, 12 are the ones that constrain
implementation: scope, per-system pages, architecture/tiering, FAIR/deposition, roadmap,
risks.)

Do not start writing code until you have read the plan, the inventory, and a sample of the
analysis-layer files named below, so the metadata schema matches the real data.

## CANONICAL FACTS (already established; do not re-derive)

- 222 MD systems, 182 unique receptors, 4 G-protein families. Per-family system counts:
  Gi/o 100, Gs 68, Gq/11 47, G12/13 7. G12/13 is underpowered (treat as provisional).
- ~332 microseconds aggregate. Standard protocol 3 replicas x 500 ns (one system has 6).
- FORCE FIELD IS UNIFORM CHARMM36 for all 222 systems. The inventory column force_field
  still mislabels 186 rows as "AMBER (FF unresolved -- check mdout)"; that "AMBER" is the
  ENGINE (pmemd.cuda), not the force field. Fixing this label is a P0 task (see below).
- The only real heterogeneity is TRAJECTORY TYPE: 212 systems are membrane-embedded
  (AMBER pmemd, NetCDF, explicit POPC bilayer, used for gateways + pockets) and 10 are
  protein-only (GROMACS TRR, no bilayer; pockets-on-protein only, excluded from gateways).
- All systems derive from experimental cryo-EM/X-ray ternary structures. No homology or
  AlphaFold-built receptors. Nine systems are flagged for construct engineering or
  identity uncertainty (fusion/BRIL/chimera/recovered-id); list is in paper1_si.
- Generic numbering is GPCRdb. Topologies are chamber-format CHARMM; MDAnalysis cannot
  read them directly, so a water-stripped reference PDB matched to the trajectory is used
  as topology (the now_ref workaround).

## WHERE EVERYTHING LIVES

Project root (all new server code, config, and docs go here):
  /MDdata/data02/jxhuang/gpcr_g/gpcr_g_server   (holds the plan HTML and this prompt)

Analysis-layer source inputs, read-only, referred to as ANALYSIS_SRC:
  /MDdata/data02/jxhuang/gpcr_g/a
All paths below are relative to ANALYSIS_SRC unless stated otherwise.

Canonical inventory:
  inventory_v3_extended.csv   (29 columns; key cols: system_id, pdb_id, receptor_uniprot,
  receptor_gene, g_protein_family, g_alpha_subtype, ligand_chem_id, n_replicas,
  length_per_replica_ns, total_sampling_ns, force_field, lipid_composition,
  has_velocities, has_forces, trajectory_path, topology_path, source_directory,
  full_system_trajectory_path, protein_only_trajectory_path, peptide_ligand_*).

Analysis layer (this is the precomputed product the server exposes; do NOT recompute it):
  paper1_pockets/
    consensus_druggable.{json,csv}, consensus_orthosteric.{json,csv}
    atlas/{sid}_pockets.json           per-system called pockets + orthosteric flag
    atlas/{sid}_pockets_gpcrdb.json    pockets mapped to GPCRdb generics + zone + role_counts
    atlas/{sid}_pocketgrid.npz         occupancy frequency grid (grid_xyz, freq)
    known_site_recovery_{druggable,orthosteric}.{csv,txt}
    reorg_table.csv, reorg_pocket_signed.csv   within-receptor reorganization
    t6_nomination_table.csv, t6_heldout_recovery.csv, figure6_druggable_nominations.{png,pdf}
    figure1..figure7 *.png/.pdf        the manuscript figures
  paper1_gateways/
    atlas/{sid}_gateways.json          per-portal metrics (see schema below)
    gateway_atlas_summary.csv, figure3_gateway_atlas.{png,pdf}
  cache/gateway_pen/{sid}_pen.npz      per-frame penetration arrays (rep{i}_TM{a}-TM{b})
  paper1_si/                           the Tier1/Tier2 audit outputs + results_note_tier1.txt
                                       + claims_to_revise.md + deferred_work.md
  paper1_manuscript.md, paper1_manuscript_revised.md   the companion paper drafts

Reusable code (import these; do not reimplement their logic):
  paper1_pocket_consensus.py     collect/cluster/summarize, DRUGGABLE_ZONES, JTHRESH
  paper1_pocket_known_sites.py   KNOWN_SITES, jaccard core matcher, cluster_fingerprint
  paper1_pocket_gpcrdb_map.py    zone assignment, generic mapping
  paper1_gateway_metric.py       gateway metric (only if a cache is missing)

Caches/metadata: pdb_metadata_cache/ (RCSB JSON per PDB), cache/gpcrdb/ (GPCRdb per system).

Python environment (has pandas, numpy, scipy, scikit-learn, MDAnalysis 2.10, python-docx):
  /MDdata/data01/jxhuang/miniconda3/bin/python3

## KEY SCHEMAS (so the metadata model matches reality)

pockets_gpcrdb.json: top-level {system_id, uniprot, family, n_frames, n_replicas,
  lipid_resnames, ligand_type, ligand_resnames, n_ligand_atoms, n_persistent_voxels,
  n_pockets, orthosteric_recovered, pockets:[...]}. Each pocket: {pocket_id, n_voxels,
  mean_freq, max_freq, centroid, dist_to_ligand, is_orthosteric, n_lining, lining_resids,
  role_counts (receptor/galpha/gbeta/...), location, receptor_generic_numbers,
  receptor_segments, zone, axis_frac}.

gateways.json: list of records {system_id, family, pair (e.g. "TM7-TM1"), metric
  (occupancy | penetration | penetration_p90 | open_fraction), mean, ci_lo, ci_hi,
  n_replicas, replica_values}.

consensus_*.csv: consensus_id, n_pockets, n_systems, n_receptors, families (JSON dict),
  zones (JSON dict), mean_freq, core_generic_numbers (";"-joined), member_systems.

## SCOPE FOR THIS SESSION (P0 to P2 only, then STOP for review)

Do P0 to P2 from the roadmap. These are data and backend, no frontend yet. Stop and report
before P3.

P0 — Freeze the cohort and document it.
  - Read the canonical inventory from ANALYSIS_SRC/inventory_v3_extended.csv. Do not edit
    files in ANALYSIS_SRC in place. Write all P0 outputs under the project root (a data/
    subfolder).
  - In the frozen master table, set force_field to "CHARMM36 (chamber, AMBER pmemd)" for the
    186 mislabeled rows and confirm the class B rows read "CHARMM36 (via AMBER CHARMM-GUI)";
    the corrected, uniform CHARMM36 label is the build's source of truth.
  - Separately and optionally, apply the same one-line force_field correction back to the
    canonical ANALYSIS_SRC inventory, but only with a timestamped backup first and in
    coordination with the analysis/manuscript thread, since that file is shared.
  - Derive and record per system: structural provenance (experimental vs the 9
    engineered/uncertain), trajectory type (membrane_embedded vs protein_only), bilayer
    status, and a content checksum of the served files.
  - Emit a single frozen master table under the project root (data/systems_master.csv and
    .parquet) that every later step reads. This is the source of truth for the server.

P1 — Metadata model and ingest.
  - Define a metadata schema keyed on system_id with GPCRdb generic numbering and coupling
    annotations. Start with SQLite for portability; design so a swap to Postgres is trivial.
  - Write an idempotent ingest that loads every system from the frozen master table and the
    analysis-layer files into the DB, with a dry-run mode and a row count report.

P2 — Serialize the analysis layer to stable API-ready files.
  - Write per-system JSON (and a small index) for pockets, gateways, alpha5 geometry, and
    within-receptor reorganization, keyed to system_id, with a versioned schema. Reuse the
    existing JSON/CSV products; repackage, do not recompute.
  - Produce the consensus pocket atlas and gateway atlas as server-ready JSON with
    back-links to contributing systems, and the druggable nomination table as an exportable
    artifact carrying the druggability-proxy and family-selectivity-status caveats.

After P2: report the schema, the row counts, the file sizes, and the proposed storage
tiering, then stop for review before building the API and frontend (P3+).

## CONVENTIONS (apply throughout)

- Code discipline: precise, minimal-change, performance-conscious. Use parquet/npy caching,
  KDTree for spatial queries, multiprocessing where embarrassingly parallel. Make ingest
  and serialization idempotent and re-runnable.
- Reuse the existing analysis caches and products. Do NOT rerun fpocket, the gateway frame
  loop, or any MD. The analysis layer is frozen input.
- Stop-and-confirm before any computation over ~30 minutes or touching the full-frame-rate
  trajectory tier; report expected runtime and disk first, and offer the smallest sanity
  check version.
- Reproducibility: every produced artifact comes from a script checked into the repo. No
  one-off shell transforms of the canonical inventory without a backup and a script.
- Writing style for any docs or manuscript text you draft: no em dashes, interconnected
  prose, no bullet lists or bold subheadings in manuscript body, no intensifiers, claims
  bounded to the data. (Internal briefs and READMEs may use lists.)
- Figures, if any: Helvetica 18/16 pt, 600 DPI, no panel titles, top/right spines removed,
  PNG and PDF, matching the existing paper1_figure*.py style.

## PORTABILITY AND MIGRATION (build here, transfer to a university host later)

The build happens on this machine, but the live service will move to a persistent
university host. Build for that move from the first commit so migration is a copy plus a
config change, not a rebuild.

- Containerize from the start. Put the API and the frontend in Docker with a compose file.
  Migration then means pulling an image and mounting data, not reinstalling a stack.
- All host-specific values come from environment variables, never hardcoded: the data
  root, the database connection string, the public base URL, and the port. The same image
  must run here and on the host with only a different .env.
- The frontend uses relative or configurable API URLs. Never hardcode this machine's
  hostname or port; that is the most common thing that breaks on migration.
- Separate code from data. Code lives in git under the project root; data artifacts live
  under a single configurable DATA_ROOT that is bind-mounted. Migration is move DATA_ROOT
  plus pull the image.
- Metadata in SQLite first, behind a thin data layer or ORM so a swap to Postgres on the
  host is a connection-string change, not a rewrite.
- The two small tiers (visualization, analysis) travel with the host; the multi-TB full
  tier never goes on the host but is deposited to a permanent DOI archive, so checksums and
  DOIs must be baked into the metadata at P0/P2. Decide the archive before generating the
  served tiers.
- Anything that depends on the host domain, TLS, uptime, and bandwidth cannot be tested
  here. Build and verify behind localhost; the closed beta, load test, and the
  free-access/uptime checks happen on the real host (roadmap P7).
- Confirm early what the university host provides: a container runtime with a persistent
  volume, or only static hosting, or a shared VM. That choice decides whether the target is
  Docker, a plain Python service, or a static-export frontend with the API hosted elsewhere.

## WHAT NOT TO DO

- Do not stand up live hosting, a CDN, or the DOI deposition. Those are infrastructure
  decisions for Jianxiang and require a persistent host that is not the GPU workstation.
  Build the code and the deposit-ready packaging; flag the infra steps as external.
- Do not finalize the resource name or the public license without confirmation.
- Do not edit paper1_manuscript.md or the original plan HTML. Work on copies.

## OPEN DECISIONS TO SURFACE EARLY (ask before they block you)

1. Resource name. The plan recommends "CoupledMD"; alternatives are listed in section 13.
2. Hosting and persistence. Which persistent host, and which archive for the multi-TB full
   tier and its DOIs. This gates deployment regardless of code progress.
3. Stack confirmation. SQLite-then-Postgres for metadata, an object store for artifacts,
   a REST API, and a JS frontend with a streaming MD viewer (MDsrv-style) plus a WebGL
   viewer (NGL or Mol*). Confirm before P3.
4. Sequencing against Paper 1. The atlas paper should be posted or submitted first or in
   parallel so the server paper can cite it. Confirm Paper 1 is frozen before the showcase
   use cases are wired in.

## FIRST STEPS

1. Read the revised plan HTML in the project root, then the inventory header and one each of
   ANALYSIS_SRC/paper1_pockets/atlas/*_pockets_gpcrdb.json and
   ANALYSIS_SRC/paper1_gateways/atlas/*_gateways.json.
2. Confirm the P0-P2 scope, the portability constraints, and the four open decisions with a
   short plan back to the user.
3. Begin P0: read the canonical inventory from ANALYSIS_SRC, and emit the frozen
   systems_master table under the project root data/ folder with the corrected uniform
   CHARMM36 force field and the provenance, trajectory-type, bilayer, and checksum fields.
   Initialize the project root as a git repository if it is not one already.
