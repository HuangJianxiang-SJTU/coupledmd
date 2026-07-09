# Fixing PBC artifacts in viz trajectories (`traj.xtc`)

Several viz-tier trajectories (`data/viz/<system>/traj.xtc`) were built by
decimating an already-PBC-wrapped source with `scripts/p5_build_viz_tier.py`.
When the protein is larger than half the box and the saved frames are far apart
(200 ps stride), the result has atoms scattered across multiple periodic
images — e.g. Gi_8YIC had 321 broken CA-CA bonds at frame 500 and 1000+ at
frame 2500. `gmx trjconv -pbc nojump` / `-pbc whole` cannot recover these
because (a) the decimation destroyed inter-frame continuity, and (b) a bare
`structure.pdb` carries no bond connectivity for GROMACS to reconstruct
molecules with.

This document describes the generalizable fix. It works for **both GROMACS and
AMBER systems** — it only needs the protein+ligand PDB and the full-resolution
source trajectory. It does **not** require a production `.tpr` (AMBER systems
don't have one).

## Method overview

1. Build a **fake TPR** from the PDB: guess bonds with MDAnalysis, **drop bonds
   longer than 2.5 Å** (these are PBC artifacts in the reference PDB itself,
   not real bonds — keeping them corrupts `-pbc whole`), and write a minimal
   GROMACS topology. `gmx grompp` turns this into a fake TPR that carries
   molecule/bond connectivity but no real forcefield parameters.
2. Convert the **full-resolution** source trajectory (every 50 ps frame, NOT
   the decimated xtc) to XTC via MDAnalysis — GROMACS itself can't read AMBER
   `.nc`; MDAnalysis can read anything.
3. `gmx trjconv -pbc cluster` with the fake TPR (separate-molecule topology,
   NOT one-molecule) — reimages each frame so each chain is internally whole.
   (`cluster` is used instead of `whole`/`nojump` because the protein exceeds
   half-box, which makes `whole` fail with "inconsistent shifts" and `nojump`
   accumulate runaway drift.) `cluster` does NOT reliably keep separate chains
   in the same periodic image — that is fixed in step 4.
4. **Multi-pass complex-centroid imaging** (Python/MDAnalysis): for each frame,
   iteratively shift each chain by integer box vectors toward the complex
   centroid until no chain is >half-box from it. This assembles the 4-chain
   complex into one image per frame. (Simpler per-chain reimage to Gα or to the
   reference PDB was tried and is UNSTABLE — it either drifts apart over time
   or flips images between frames. Anchoring on the running complex centroid
   with iteration-to-convergence is the stable method.)
5. **Kabsch-fit** on the α5 helix Cα (residues 330-350 of Gα) to
   `structure.pdb`, so frame 0 matches the reference exactly.
6. **Decimate** stride 4 → 2501 frames (matches the GPCRmd 200 ps/frame
   standard).
7. **Also fix `structure.pdb`** — three things that block NGL playback even when
   the trajectory is correct (these were the *actual* reasons Gi_8YIC did not
   play; the PBC fix alone was not enough):
   - **Reimage the PDB's chains** to the Gα centroid using the **true
     trajectory box** (the PDB's own CRYST1 box is often stale — Gi_8YIC's said
     109.8×158.3 but the true box was 113.2×143.2). Otherwise the first viewer
     snapshot shows Gβ/Gγ detached.
   - **Rewrite the CRYST1 record** to the true trajectory box. NGL uses the PDB
     box to interpret the trajectory; a mismatch can prevent rendering.
   - **Assign an element to every ATOM/HETATM** (cols 77-78). CHARMM lone-pair
     atoms (`LP1` / atom type `LPH`) ship with no element. NGL's
     `colorScheme: 'element'` (used by the `ball+stick` ligand representation)
     **throws on a blank element**, which aborts the structure-load callback
     *before* `NGL.autoLoad(traj)` is reached — so the trajectory never even
     fetches (no `/viz/trajectory` request in the access log, console shows only
     `loaded 'structure'`). Assign `LP*` → `H`; others → guess from atom name.
   - **Preserve clean PDB column formatting.** Do NOT use MDAnalysis's
     `u.atoms.write(pdb)` — it corrupts the element column (leaks the segment-id
     into cols 77-78) and inserts a `HEADER` line. Instead, take a clean-format
     template PDB and replace only the coordinate columns (31-54) per atom,
     leaving the rest of each line byte-identical.

Detect which of these a system needs with `scripts/audit_viz_pbc_full.py` — it
flags `BROKEN_NGL` (blank-element / atom-count), `BROKEN` (true PBC artifacts),
and `WARN` (box mismatch / minor). The cheap `BROKEN_NGL` / `WARN` fixes need
**no trajectory reprocessing** — fix the PDB only (step 7). Only `BROKEN`
systems need the full pipeline (steps 1-6).

## Why each alternative fails (lessons learned)

- **`-pbc whole` / `-pbc nojump` on the bare PDB as topology**: a PDB has no
  bonds, so GROMACS treats every atom as its own molecule and warns
  *"cannot be made whole without you providing a run input file."*
- **`-pbc whole` / `-pbc nojump` with the fake TPR on the decimated xtc**: the
  200 ps frame spacing means atoms move >half-box between saved frames, so
  `nojump` cannot determine which image they jumped to; it accumulates
  runaway drift (frame 2500 spans 7000+ Å). `whole` aborts with
  *"inconsistent shifts ... above half the box length"* because within a
  single molecule some bonded atoms are >half-box apart.
- **`-pbc whole` on the full-resolution source**: same "inconsistent shifts"
  failure — the protein (~90 Å) is bigger than half the box (~56 Å), so a
  single chain can span more than half-box and `whole` cannot choose an image.
- **`-pbc cluster` alone**: keeps each chain internally whole and in one
  cluster, but separate chains land in *different* periodic images (Gβ/Gγ
  ended up 143 Å = one box vector from Gα), giving a "broken complex" look.
  The per-chain reimage step (4) fixes this.
- **PyMOL**: not recommended. Its `align`/`super` do structural superposition
  (outlier rejection), not PBC unwrapping; its `pbc`/`symexp` use the same
  periodic logic that fails when a molecule exceeds half-box.

## Step-by-step: Gi_8YIC worked example

Source files (full-resolution, 10001 frames @ 50 ps = 500 ns):
```
/MDdata/data04/gpcr_g_database/a/a_gi/8YIC/protein.pdb   # protein+ligand, 17007 atoms
/MDdata/data04/gpcr_g_database/a/a_gi/8YIC/traj1.nc      # AMBER NetCDF, 2 GB
```

### A. Build the fake TPR

```bash
SYS=Gi_8YIC
PDB=data/viz/$SYS/structure.pdb
ROLES=scripts/audit_output/chain_roles/${SYS}_chain_roles.json
export GMXLIB=$(pwd)/scripts/audit_output/gmx_top

python3 scripts/fix_viz_pbc_pdb.py build-fake-tpr \
    --pdb $PDB --roles $ROLES --outdir /tmp/${SYS}_fake
gmx grompp -f /tmp/${SYS}_fake/fake.mdp -c /tmp/${SYS}_fake/fake.gro \
    -p /tmp/${SYS}_fake/fake.top -o /tmp/${SYS}_fake/fake.tpr -maxwarn 5
```

`--roles` is needed because the viz PDB uses a single chain id ("A") with
sequential residue numbering; `chain_roles.json` supplies the Gα/Gβ/Gγ/
receptor/ligand residue ranges so each becomes a separate `[ moleculetype ]`.
For PDBs with distinct chain ids, `--roles` is not needed.

### B. Build the α5 index

```bash
python3 scripts/fix_viz_pbc_pdb.py make-ndx --pdb $PDB --out /tmp/${SYS}.ndx
```
This writes `[ alpha5_CA ]` (Gα CA, resid 330:350) and `[ System ]`. If a
system's α5 helix is at different residue numbers, edit the selection in the
script's `cmd_make_ndx` first.

### C. Write full-res XTC, cluster, reimage, fit, decimate

```bash
SRC=/MDdata/data04/gpcr_g_database/a/a_gi/8YIC/traj1.nc   # full-res source

# C1. source (NC/TRR/XTC) → full-res XTC via MDAnalysis (gmx can't read AMBER .nc)
python3 scripts/fix_viz_pbc_pdb.py src-to-xtc --pdb $PDB --src $SRC --out /tmp/${SYS}_fullres.xtc

# C2. -pbc cluster (per-frame assembly; separate-molecule fake TPR)
printf '1\n1\n' | gmx trjconv -s /tmp/${SYS}_fake/fake.tpr \
    -f /tmp/${SYS}_fullres.xtc -n /tmp/${SYS}.ndx \
    -o /tmp/${SYS}_cluster.xtc -pbc cluster

# C3. multi-pass reimage + α5 Kabsch fit + decimate stride 4
#     (use `assemble` for single-chain proteins; `assemble-multipass` for
#      multi-chain complexes — see the script's docstrings for the difference)
python3 scripts/fix_viz_pbc_pdb.py assemble-multipass \
    --pdb $PDB --cluster /tmp/${SYS}_cluster.xtc --roles $ROLES \
    --ndx /tmp/${SYS}.ndx --out data/viz/$SYS/traj.xtc --stride 4
```

### D. Fix structure.pdb (step 7 — do this for EVERY fixed system)

```bash
python3 scripts/fix_viz_pbc_pdb.py fix-structure --pdb $PDB --roles $ROLES
```
This reimages the PDB's chains to the anchor centroid using the true trajectory
box, rewrites CRYST1, assigns elements to blank atoms, and preserves clean
column formatting (with a safety check that aborts if the PDB atom order
doesn't match the trajectory). Backs up to `structure.pdb.pre_chain_fix`.

### E. Update the DB and verify

```bash
python3 scripts/fix_viz_pbc_pdb.py update-db --system $SYS
python3 scripts/audit_viz_pbc_full.py --system $SYS --frames 10   # expect OK or WARN
```

Frame 0 must match `structure.pdb` exactly and every chain must be internally
contiguous at every frame:

```python
import MDAnalysis as mda, numpy as np, warnings; warnings.filterwarnings('ignore')
u_ref = mda.Universe('data/viz/Gi_8YIC/structure.pdb')
u = mda.Universe('data/viz/Gi_8YIC/structure.pdb', 'data/viz/Gi_8YIC/traj.xtc')
u.trajectory[0]
print('frame0 RMSD vs structure.pdb:',
      np.sqrt(((u.atoms.positions-u_ref.atoms.positions)**2).sum(1).mean()))  # ~0.0
print('blank elements:', (u_ref.atoms.elements=='').sum())                    # 0
for fr in [0, 500, 2500]:
    u.trajectory[fr]
    ga = u.select_atoms('name CA and resid 1:354').positions
    d = np.linalg.norm(np.diff(ga,axis=0),axis=1)
    print(fr, 'Gα CA-CA breaks (>8Å):', int((d>8).sum()))   # 0 = good
```

In the browser: hard-refresh (Ctrl+Shift-R); the console should show
`loading file 'trajectory'` after `loaded 'structure'` and the trajectory plays.

### F. Backups

Before overwriting, `fix-structure` preserves `structure.pdb.pre_chain_fix`;
the broken trajectory should be backed up as `traj.xtc.broken_pbc_YYYYMMDD_HHMMSS`
(do this manually before step C3 if you want it — the script overwrites
`traj.xtc` in place). The original pre-fix trajectory is also kept as
`traj_orig.xtc`.

## Refreshing the live web server (10.127.83.59:8000)

The server is gunicorn + uvicorn workers, serving viz files **directly from
disk** via `FileResponse` (`api/main.py:get_viz_trajectory`). There is **no
server-side cache** — replacing `traj.xtc` on disk is picked up immediately.

Two things to do after replacing a `traj.xtc`:

1. **Update the `system_viz_files` DB row** so `/viz/meta` reports accurate
   `file_size_bytes` / `n_frames` (the frontend frame slider reads
   `n_frames`):
   ```bash
   python3 scripts/fix_viz_pbc_pdb.py update-db --system Gi_8YIC
   ```

2. **Browser cache**: the `/viz/trajectory` endpoint now sends
   `Cache-Control: no-cache` (added 2026-06-26), so a normal page load
   re-fetches. If you previously opened the system, do a hard refresh in the
   browser (Ctrl+Shift+R) to be safe.

No gunicorn restart is needed for a file swap. A restart is only needed after
editing `api/main.py`:
```bash
kill -HUP $(cat /tmp/gunicorn.pid)   # graceful worker reload, no downtime
```

## Generalizing to other systems

**First, run the detector across all 222 systems** to triage:
```bash
python3 scripts/audit_viz_pbc_full.py --frames 10
# writes scripts/audit_output/VIZ_PBC_FULL_AUDIT.csv + prints a summary
```
Statuses: `OK` (no action) · `WARN` (minor/box-mismatch — fix PDB only, step D)
· `BROKEN_NGL` (blank-element or atom-count — blocks playback; fix PDB only,
step D, no trajectory reprocessing) · `BROKEN` (true PBC artifacts — full
pipeline A–D) · `NEEDS_SOURCE` (trajectory has no box — must reprocess from a
full-resolution source).

Fix order (cheapest, highest-payoff first):
1. All `BROKEN_NGL` → step D only (assign elements / fix atom count).
2. All `WARN` → step D only (CRYST1 box, minor reimage).
3. All `BROKEN` → full pipeline A–D. Single-chain proteins are easy
   (`assemble`); multi-chain complexes need `assemble-multipass`.
4. Re-run the detector; spot-check 2-3 in the browser.

For each broken system, repeat steps A–F with:
- `--pdb data/viz/<sys>/structure.pdb`
- `--roles scripts/audit_output/chain_roles/<sys>_chain_roles.json` (if the
  PDB has a single chain id)
- the full-resolution source trajectory (locate via `data/systems_master.csv`
  → `pdb_id` + `g_protein_family` → `/MDdata/data04/gpcr_g_database/<sub>/<pdb>/traj1.nc`;
  if absent, the raw GROMACS run dir `/MDdata/data03/jxhuang/gpcr_g/<sub>/<pdb>/`
  has `prod1_now.trr` + `now.tpr`)

The whole pipeline is scripted in `scripts/fix_viz_pbc_pdb.py` (subcommands
`build-fake-tpr`, `make-ndx`, `src-to-xtc`, `assemble`/`assemble-multipass`,
`fix-structure`, `update-db`).

---

# 2026-06-26 — generalizing the remaining 22 "BROKEN" systems

The fake-TPR + `gmx -pbc cluster` + multi-pass method above got Gi_8YIC working
but stalled on the 22 systems flagged `BROKEN` with *intra-chain* breaks. Working
those revealed that **most were not actually broken** and that there is a much
simpler, more reliable reprocessing path for the few that were. Net result: all
22 now audit `OK` with no fake-TPR and no multi-pass imaging.

## Finding 1 — most `BROKEN` flags were a detector false positive

The detector treated **any** CA–CA distance > 8 Å within a chain as "unambiguously
a PBC split". That is wrong: these mini-G constructs have **genuine structural
chain gaps** — a deleted helical-domain linker (or an unresolved loop) that was
renumbered away, leaving two renumbered-consecutive Cα 9–30 Å apart **in a
perfectly imaged frame**. The identical gap is present in the static
`structure.pdb` that the viewer already renders fine, so the matching trajectory
is fine too. 15 of the 22 were nothing but this (single gap, usually at Gα
res ~47–52, present in 100 % of frames, complex otherwise compact, span ≤ box).

**The discriminator is the minimum-image convention.** For a flagged CA–CA break
vector `d`, compute `mi = |d − box·round(d/box)|`. If `mi` collapses to < 8 Å the
two atoms are actually close (true PBC split → fixable). If `mi` stays large it is
a genuine structural gap → ignore. `scripts/audit_viz_pbc_full.py` now applies
this in the intra-chain check, so structural gaps no longer flag `BROKEN`.

Quick triage of "is a `BROKEN` system genuinely scattered, or just a gap?":
sample ~20 frames and compare the raw complex span/box against the span after a
per-frame chain reassembly. If reassembly shrinks the span by > ~0.1 box, chains
are genuinely displaced; if not (and there are 0 min-image-collapsing breaks),
it is a structural gap and the trajectory needs no work.

## Finding 2 — the genuinely scattered ones: cpptraj `autoimage` (AMBER) /
`gmx -pbc whole` + greedy assembly (GROMACS)

Only ~6 systems were truly scattered (a chain/fragment imaged ~½–1 box away;
span ≫ box). The **full-solvated source** (membrane present) is the key — it
gives the imaging tool a stable anchor. Sources live at the paths in
`data/systems_master.csv` (`trajectory_path` / `topology_path`), NOT only in
`gpcr_g_database` (whose protein-only `traj1.nc` is the *already-broken* input the
viz was decimated from). AMBER sources: `now.prmtop` + `prod_now.nc` (Chamber
topology — **MDAnalysis cannot read it; cpptraj can**). GROMACS sources:
`now.tpr` + `prod1_now.trr`.

**AMBER systems — cpptraj `autoimage` (one command does everything):**
```bash
# cpptraj at /opt/softwares/amber24/bin/cpptraj ; export AMBERHOME=/opt/softwares/amber24
cpptraj <<'EOF'
parm   /MDdata/.../<pdb>/now.prmtop
trajin /MDdata/.../<pdb>/prod_now.nc 1 10000 4    # decimate stride 4 → 2500 frames
autoimage                                          # reassembles the membrane complex
strip :POPC,SOD,CLA                                # → protein+ligand (matches viz PDB order)
trajout /tmp/<sys>_assembled.xtc xtc
go
EOF
```
Then per-frame Cα fit to `structure.pdb` (MDAnalysis `align.AlignTraj(..., select='name CA')`)
→ `data/viz/<sys>/traj.xtc`, and `fix_viz_pbc_pdb.py update-db --system <sys>`.
`autoimage` succeeds where every `gmx` mode failed because it images by
**molecule proximity** using the real prmtop molecule definitions, with the
membrane as anchor — no half-box limit. Fixed this way: Gq_7W55 (was span 23×box!),
Gq_7XW9, Gq_7RYC.

**GROMACS systems — two stages (`scripts/fix_viz_gromacs.py`):**
cpptraj cannot read a `.tpr`, and MDAnalysis `unwrap()` runs at ~1 s/frame
(hours). So:
```bash
# STAGE 1: gmx makes molecules whole (real tpr bonds → NO "inconsistent shifts"
#          abort; sequential read of the big trr is fast). Decimate here.
printf 'System\n' | gmx trjconv -s now.tpr -f prod1_now.trr -pbc whole -skip 4 -o whole.xtc
# STAGE 2: cheap chain assembly + Cα fit
python3 scripts/fix_viz_gromacs.py <SYS> now.tpr whole.xtc --stride 1
```
Stage 2's assembly is **greedy proximity**: place the largest chain, then add each
remaining chain in the periodic image that puts its centroid closest to an
already-placed chain. A single global anchor (centroid OR largest-chain) does NOT
work — the complex is elongated (~1.1 box), so end chains sit ~half a box from any
one anchor where `round()` is ambiguous and a chain (e.g. Gβγ, or Gγ relative to
Gα) gets stranded one box away. Greedy proximity walks the binding graph
(receptor→Gα→Gβ→Gγ, ligand→receptor) implicitly because bound partners are in
contact (< half box) in the correct image. Fixed this way: Gi_7JVR, Gi_8X16, Gq_8DPF.

Note: if a system's `structure.pdb` is a different conformation than the source
frame 0 (Gq_8DPF: original frame0 was 26 Å off), the per-frame Cα fit leaves a
large frame-0 RMSD. That is cosmetic (a jump when playback starts), not a PBC
break — sync it by writing trajectory frame 0 back into `structure.pdb` with a
surgical coordinate-column replacement (cols 31–54) + CRYST1 rewrite, preserving
the cleaned element column.

## What this supersedes

For PBC-scattered viz trajectories prefer **cpptraj `autoimage` (AMBER)** or
**`gmx -pbc whole` + greedy proximity assembly (GROMACS)** over the fake-TPR +
`gmx -pbc cluster` + `assemble-multipass` route — both are simpler, faster, and
do not need a hand-built fake topology. And always min-image-check an intra-chain
"break" before treating it as PBC: it may be a real chain gap.

## Addendum 2026-06-26 — a `WARN` "minor scatter" can hide progressive drift

The detector samples only `--frames` evenly-spaced frames (10 by default). Three
systems — **G12_8H8J, Gi_7VUG, Gs_7VUH** — came up `WARN "scatter (1–2/10 frames,
minor)"`, which reads as borderline-but-playable. It is not: scanning **all 2501
frames** showed the scatter is *progressive* — near-zero early, then hundreds of
frames span > 1.6× box in the second half (G12_8H8J: 277 bad frames; the protein
diffuses across a box boundary and the already-PBC-wrapped source never reassembles
it). A 10-frame sample happens to land on only 1–2 of them. **Lesson: for any
non-zero scatter count, scan the full trajectory before dismissing it as minor.**
All three are GROMACS (`now.tpr` + `prod1_now.trr`) and were fixed with the exact
same two-stage pipeline as Finding 2 (`gmx -pbc whole -skip 4` → `scripts/fix_viz_gromacs.py`).
After the fix all three show **0 scatter frames across all 2501** (frame0 RMSD 0.0,
max span/box ≤ 1.24). Backups: `traj.xtc.broken_pbc_backup` per system.
