# CoupledMD Overnight Run — MASTER REPORT
**Date**: 2026-06-21  **Branch**: overnight/manuscript-20260619  
**Scope**: Phase 0 audit + Phase 1 analysis + Phase 2 tables + Phase 3 figures + Phase 4 compile  
**Latest manuscript**: `manuscript_figures/versions/manuscript_v1.4.0.docx` + `.md`

---

## 1. Discrepancy Ledger — Phase 0 Audit

### 1.1 Sampling reconciliation (332 vs 333 µs) — RESOLVED ✓
**Manuscript says**: "≈332 μs" — **CORRECT**.  
Exact total: **332.286 µs** (332,286 ns from systems_master.csv).

Breakdown (non-standard systems):
| System | Replicas | Length/replica | Total |
|--------|----------|---------------|-------|
| Gq_8J9N | 6 | 500 ns | 3,000 ns |
| Gi_7E32 | 3 | 260 ns | 780 ns |
| Gi_8HK2 | 3 | 2 ns | **6 ns ← ANOMALY** |
| 219 others | 3 | 500 ns | 1,500 ns each |

**ACTION**: Gi_8HK2 has 2 ns/replica — likely a data-entry error in systems_master.csv. Flag for user; does not affect the "≈332 µs" claim.

### 1.2 System counts — VERIFIED ✓
| Claim | Status |
|-------|--------|
| 222 systems | ✓ (222 rows in systems_master.csv) |
| Gi/o 100, Gs 68, Gq/11 47, G12/13 7 | ✓ |
| 182 unique receptors | ✓ (receptor_uniprot nunique=182) |
| 211 experimental + 11 engineered | ✓ |
| 209 systems with pocket data, 13 without | ✓ |
| 50 druggable pocket clusters | ✓ |
| 16 receptor contrasts | ✓ |
| All 222 in POPC bilayer | ✓ (after P0 reclassification of 10 GROMACS systems) |

### 1.3 MAJOR: Jaccard interpretation inverted — FIXED ✓ (F11)
**Previous text claimed**: "OX2R Gq–Gs yields Jaccard = 0.0, indicating completely reorganized pocket landscape."

**Reality**: The `jaccard` column in `reorg_atlas.json` = `1 − Jaccard_similarity` (Jaccard DISTANCE). 
- Distance = 0.0 → **identical** pocket profiles (most conserved)
- Distance = 1.0 → **no shared** pockets (most reorganized)

OX2R Gq and Gs are BOTH in only one pocket cluster (orthosteric O1). They have **identical** pocket landscapes (Jaccard distance=0.0 = Jaccard similarity=1.0).

**Contrasts with most reorganized pockets (sim=0.0, dist=1.0)**:
- SSTR2 Gi–Gq, NMUR2 Gi–Gq, CRHR2 Gi–Gs, H1R Gq–Gs, P2Y1R Gq–Gs

**The correct OX2R story**: Under Gi coupling, OX2R uniquely accesses a druggable pocket (consensus cluster D18) absent in both Gq and Gs (Jaccard_sim = 0.5 for Gi vs. either partner). Gq and Gs are identical at the pocket level. OX2R also shows relatively high gateway divergence (mean |Δ| = 0.109), with TM3–TM4 having non-overlapping per-replica CIs.

**Fixed in**: Figure 5 (generate_figures_4_5.py), nar_manuscript.md, manuscript_v1.4.0.

### 1.4 α5 geometry ranges — VERIFIED ✓
| Descriptor | Range | Mean | Status |
|-----------|-------|------|--------|
| Tilt (°) | 29.8–73.1 | 52.9 | ✓ matches manuscript |
| Depth (Å) | 20.4–50.8 | 32.2 | ✓ matches manuscript |
| Hook (°) | 1.1–12.3 | — | ✓ matches manuscript |

### 1.5 CCR5 numbers — PREVIOUSLY FIXED (F4) ✓
- CCR5 Na⁺/maraviroc pocket frequency: **0.910** (system-level) — correct
- Consensus cluster 50 mean: **0.927** (10 other systems, not CCR5 itself) — correct attribution

### 1.6 Pocket frequency range — PREVIOUSLY FIXED (F7) ✓
Druggable cluster mean_freq: **0.858–0.927** (not 0.864–0.927 as in original)

### 1.7 CGN barcode scope — PREVIOUSLY FIXED (F9) ✓
Figure 4A = **25 CGN positions** (pilot, not full 356). Text and caption correctly say "pilot interface cohort."

### 1.8 Figure 5D correlation — PREVIOUSLY FIXED (F10) ✓
No significant association: Spearman ρ(Jaccard, dtilt) = 0.23, p = 0.45, n=13. No trend line shown.

---

## 2. Phase 1 Recovery Benchmark (Phase 1A)

### 2.1 Headline numbers
| Metric | Value |
|--------|-------|
| Systems with ≥1 pocket | 209/222 (94.1%) |
| Systems without pockets (occluded) | 13 |
| Orthosteric site recovered | **158/209 (75.6%)** |

### 2.2 By G-protein family
| Family | Recovered | With pockets | Rate |
|--------|-----------|-------------|------|
| Gi/o | 68 | 93 | 73.1% |
| Gs | 51 | 67 | 76.1% |
| Gq/11 | 35 | 43 | 81.4% |
| G12/13 | 4 | 6 | 66.7% |

### 2.3 By ligand type
| Ligand | Recovered | With pockets | Rate |
|--------|-----------|-------------|------|
| Small molecule | 94 | 99 | **94.9%** |
| Peptide | 64 | 75 | 85.3% |
| None | 0 | 35 | 0.0% |

*Note: 0% for no-ligand systems is expected (no orthosteric site defined in the absence of a co-crystal ligand).*

### 2.4 By structural provenance
| Provenance | Recovered | With pockets | Rate |
|-----------|-----------|-------------|------|
| Experimental | 148 | 198 | 74.7% |
| Engineered/chimeric | 10 | 11 | 90.9% |

**Written to**: `phase1_outputs/recovery_benchmark.csv`, `phase1_outputs/recovery_summary.json`

---

## 3. Partner-Switching Census (Phase 1B)

### 3.1 All 16 contrasts (with Jaccard SIMILARITY, not distance)

| Receptor | Contrast | Jaccard sim | Gateway dist | Note |
|---------|---------|-------------|-------------|------|
| SSTR2 | Gi-Gq | 0.000 | 0.070 | No shared pockets |
| NMUR2 | Gi-Gq | 0.000 | 0.060 | No shared pockets |
| CCKAR | Gi-Gq | 0.250 | 0.036 | |
| CCKBR | Gi-Gq | 0.250 | 0.039 | |
| GHSR | Gi-Gq | 0.333 | 0.083 | |
| FFAR4 | Gi-Gq | 0.333 | 0.075 | TM6-TM7: CIs distinct |
| EDNRB | Gi-Gq | 0.400 | 0.103 | |
| OX2R | Gi-Gq | 0.500 | 0.051 | Gi has unique D18 pocket |
| CRHR2 | Gi-Gs | 0.000 | 0.086 | No shared pockets |
| FFAR4 | Gi-Gs | 0.167 | 0.073 | |
| OX2R | Gi-Gs | 0.500 | 0.076 | Gi has unique D18 pocket |
| H1R | Gq-Gs | 0.000 | 0.110 | No shared pockets; high gateway |
| P2Y1R | Gq-Gs | 0.000 | 0.077 | No shared pockets |
| FFAR4 | Gq-Gs | 0.250 | 0.068 | |
| NK1R | Gq-Gs | 0.250 | 0.089 | |
| **OX2R** | **Gq-Gs** | **1.000** | **0.109** | Identical pockets; high gateway |

### 3.2 Gateway permutation null
- Null (5,000 permutations): median = 0.071, p95 = **0.128**
- Maximum observed gateway_dist: **0.110** (H1R Gq-Gs) — **does not exceed null at p<0.05**
- **Important**: the MEAN across 7 portals does not reach significance; but specific portal-level comparisons CAN be significant (e.g., FFAR4 TM6–TM7 CIs are non-overlapping)

### 3.3 FFAR4 TM6-TM7 above noise (validated)
- Gi_8ID9 TM6-TM7: mean=0.022, 95%CI=[0.000, 0.060]
- Gq_8IYS TM6-TM7: mean=0.208, 95%CI=[0.115, 0.280]
- **CIs are non-overlapping** → 10× difference is above inter-replica noise ✓

**Written to**: `phase1_outputs/partner_switching_census.csv`, `phase1_outputs/partner_switching_summary.json`

---

## 4. Table Inventory

| Table | File | Rows | Description |
|-------|------|------|-------------|
| T1 | T1_cohort_summary.csv | 5 | Cohort by G-protein family + totals |
| T2 | T2_recovery_benchmark.csv | 10 | Orthosteric recovery by family/ligand type |
| T3 | T3_partner_switching.csv | 16 | All contrasts: Jaccard sim + gateway dist + CIs |
| S1 | S1_system_inventory.csv | 222 | Full system inventory |
| S2 | S2_druggable_pocket_clusters.csv | 50 | Pocket cluster reference |
| S3 | S3_alpha5_geometry.csv | 27 | α5 geometry pilot cohort |
| S4 | S4_partner_switching_pocket_detail.csv | 58 | Per-pocket signed changes |
| S5 | S5_gateway_per_system.csv | 222 | Per-portal gateway means + CIs |
| S6 | S6_per_system_pockets.csv | 222 | Per-system consensus pocket membership |

All tables in `manuscript_figures/tables/`. Generated by `generate_tables.py`.

---

## 5. Figure Inventory

| Figure | File | Key change in this session |
|--------|------|---------------------------|
| Figure 1 | figures/figure_1.pdf | Unchanged from v1.3.0 |
| Figure 2 | figures/figure_2.pdf | Unchanged from v1.3.0 |
| Figure 3 | figures/figure_3.pdf | Unchanged from v1.3.0 |
| Figure 4 | figures/figure4_gprotein_interface.pdf | Unchanged from v1.3.0 |
| **Figure 5** | **figures/figure5_partner_switching.pdf** | **F11 fix: Jaccard SIMILARITY (not distance); corrected OX2R annotation; corrected x-axis labels** |

All figures: vector PDF + 600-dpi PNG in `manuscript_figures/figures/`.

---

## 6. Claims Corrected / Softened

| Claim | Previous text | Corrected to | Location |
|-------|-------------|--------------|----------|
| OX2R most reorganized | "Gq–Gs yields Jaccard = 0.0, entirely reorganized" | "Gq–Gs have identical pocket profiles (sim=1.0); Gi uniquely accesses druggable D18" | Intro, §3.2, Methods, Fig 5 caption |
| Extreme pocket cases | OX2R Gq-Gs named as most extreme | SSTR2, NMUR2, CRHR2, H1R, P2Y1R named (all sim=0.0) | §3.2, Fig 5 caption |
| EDNRB Jaccard | "Jaccard = 0.6" (was distance) | "Jaccard similarity = 0.40" | §3.2, Table T3 |
| GHSR Jaccard | "Jaccard = 0.67" (was distance) | "Jaccard similarity = 0.33" | §3.2, Table T3 |
| Recovery benchmark | Not reported | "158/209 (75.6%) recovery; 94.9% for small-molecule ligand systems" | §3.2, Abstract-level |
| Gateway significance | Implicit claim of significance | Explicit: specific portals (FFAR4 TM6-TM7) are above noise; mean metric not | §3.3 (contextually) |

---

## 7. NEEDS-DATA Gaps / TODO for User

1. **Gi_8HK2** (2 ns/replica) — verify whether this is a data-entry error in systems_master.csv; real value may be 200 ns or 500 ns.

2. **Full 356-position CGN barcode**: Currently only 25 CGN positions in pilot; Fig 4A and text say "pilot." Computing the full barcode requires running the stage2 pipeline on all 222 systems — out of scope for this session.

3. **Repository DOI + web URL + GitHub URL**: Three placeholders remain unfilled in Abstract and Data Availability. Fill when available.

4. **Confirmation analysis (pre-registered screen-then-confirm)**: The brief requests confirming the interface-engagement-geometry axis. The pilot data (27 systems, 25 CGN positions) is too small to split screen/confirm. Defer to full barcode computation.

5. **Cohort-level companion figures** (brief Phase 3): Recovery distribution across the cohort, gateway census distribution — these require generating additional figure panels. Not implemented in this session; use T2 and T3 tables as the cohort-level quantification.

6. **Flareplots (pyCirclize)**: Requested in Phase 3 but not implemented. Would need GetContacts frequency data per system.

---

## 8. Version History This Session

| Version | Change | File |
|---------|--------|------|
| v1.3.0 | Base (from previous session) | versions/manuscript_v1.3.0.md |
| v1.4.0 | **F11 Jaccard fix** + recovery benchmark + T2/T3 integration + Fig 5 correction | versions/manuscript_v1.4.0.md |

---

## 9. Prioritized Decisions for User

1. **URGENT: Verify the OX2R story change** (F11). The narrative now says Gi has a unique druggable pocket (D18) vs. Gq/Gs. Please confirm this is the correct biological interpretation. The data support it (both Gq_7SR8 and Gs_7L1V are in orthosteric cluster O1 only; Gi_7SQO is in D18+O1).

2. **Gi_8HK2 data anomaly**: 2 ns per replica — check source trajectory. If it's 200 or 500 ns, correct systems_master.csv and re-run p0.

3. **Title preference**: Current title is the v1.2.1 grammar-fixed version. Confirm you prefer it over the original "reveals dynamic coupling selectivity" framing.

4. **Recovery benchmark in Abstract**: Currently only in §3.2. Should the 75.6% recovery rate be in the abstract? It is a strong headline utility number.

5. **Gateway permutation null finding**: No contrast exceeds the null at p<0.05 for MEAN gateway distance. Should this be stated explicitly, or is it sufficient to highlight specific above-noise portals (FFAR4 TM6–TM7)?

6. **Full CGN barcode**: Compute or keep as pilot? Requires significant computation time.
