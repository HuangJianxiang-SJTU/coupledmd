# Integrity & data flags — overnight figure/manuscript work

Working log of every data discrepancy found during orientation. Figures are
corrected to show **real** data; manuscript wording issues are flagged for the
user, not silently changed. Cross-referenced in SESSION_REPORT.md.

## Corrected in figures (used real existing data — no fabrication)

- **F1 — Fig 1A data bug.** Original plotted `nunique(receptor_gene)`, but
  `receptor_gene` is null in 179/222 rows → showed 10/23/5/4. Caption says
  *system count per family* (100/68/47/7). Fixed to `groupby(family).size()`
  = Gi 100 / Gs 68 / Gq 47 / G12-13 7 (Σ=222). Real data.
- **F2 — Fig 1D source column.** Original ranked by sparse `receptor_gene`.
  Switched to `receptor_name` (221/222 complete; `receptor_uniprot` nunique=182
  matches the "182 unique receptors" claim). Real data.
- **F3 — Fig 3 metric bug (most serious).** Original Panels A and B plotted the
  *same* `occupancy` metric (= mean portal distance, 2–11 Å); Panel A was
  mislabelled "Occupancy (water/ion count)". The manuscript's key numbers
  (TM6–TM7 Gi 0.022 vs Gq 0.208; TM7–TM1 0.342 vs 0.392) are the `open_fraction`
  metric, which was never plotted. Fixed: Panel A → `open_fraction` (now matches
  the manuscript exactly), Panel B → `occupancy` = mean portal distance (Å) with
  the 8 Å threshold. Real data.
- **F5 — Fig 2 internal label.** Text panel said "600 frames (3 × 200 ns)".
  Analysis tier is 600 frames over 3 replicas (200 frames/replica); replicas are
  500 ns. The "200 ns" was wrong. Corrected to frames, not ns.
- **F6 — Palette unification.** Figs 1–3 used Gi=blue/Gs=gold/Gq=red; Figs 4–5
  used Gi=green/Gs=blue/Gq=orange. Unified ALL five to the brief's canonical,
  colour-blind-safe scheme: Gi/o green #2f8f6b, Gq/11 orange #c0741a,
  Gs blue #2c6fb3, G12/13 purple #8a4aa0.

## Flagged for the user — NOT changed in data (decision needed)

- **F4 — CCR5 number attribution (Fig 2 / Section 3.2 / Methods).** The text says
  CCR5 (Gi_7F1Q) recovers "consensus cluster 50 … mean frequency 0.927". But
  cluster 50's 10 member systems do **not** include Gi_7F1Q; that 0.927 is the
  cross-database cluster-level mean over 10 *other* systems. CCR5's own
  Na⁺/maraviroc pocket (local pocket id 4, zone `tm_core_allosteric`,
  positions 2.50/3.39/7.49) has mean frequency **0.910**. The headline claim
  (MD blind-recovers the maraviroc site in CCR5) is supported; the *number*
  attributed to CCR5 is not. Figure shows CCR5's real 0.910. Recommend the text
  distinguish system-level (0.910) from cluster-level (0.927).
- **F7 — Pocket frequency range.** Manuscript: "0.864 to 0.927". Actual druggable
  cluster mean_freq range: 0.858–0.927. Low end off by ~0.006.
- **F2b — Fig 1D caption claim.** Caption says "Class A aminergic … dominate".
  The actual most-represented receptors are peptide/lipid (orexin, CRF, FFA,
  CCK, endothelin). Recommend the caption say "peptide and lipid receptors".
- **F9 — Fig 4A barcode is a 25-position pilot, not 356 (MAJOR).** The caption
  and Methods describe the "356-position CGN" barcode for "an exemplar system
  (CCR5–Gi)". The actual source (`a/stage2_outputs/pilot_long.csv`) covers only
  **25 CGN positions** across a pilot subset, with just two flock classes present
  (selectivity-determining 95, conserved 62 rows; no paralog-specific/neutral).
  The figure plots the real 25 positions (cross-system mean). The full 356-position
  barcode and the per-system "CCR5–Gi exemplar" do not exist in the analysis layer
  yet. Caption/Methods must be revised to describe the pilot, OR the full barcode
  computed. Not fabricated. (`reorg_atlas.json` note confirms "no per-system
  alpha5 geometry files exist in the current analysis layer".)
- **F10 — Fig 5D / caption correlation claim is unsupported (MAJOR).** Caption 5D:
  "Systems with extreme pocket divergence also tend to show larger α5 geometry
  differences, suggesting a structural basis." The resource's own Spearman stats
  (`reorg_atlas.json → alpha5_reorg_correlations`, n=13) show jaccard vs dtilt
  r=+0.23 p=0.45, jaccard vs composite r=+0.09 p=0.77 — weak, non-significant,
  and the positive sign is opposite to the claimed trend. Figure plots the real
  jaccard-vs-dtilt scatter with NO trend line and NO causal claim; caption claim
  should be removed or softened to "no significant association (n=13)".
- **F8 — Fig 4B "OX2R ranks highest".** OX2R (7L1V, Gs) has func_rank=1, but
  func_rank=1 is shared by several systems (SSTR2, H1R, P2Y1R, FFAR4 …). "Ranks
  highest" is true only as "tied for top". Soften wording.

## New flags (overnight Phase 0, 2026-06-21)

- **F11 — MAJOR: Jaccard interpretation inverted throughout (Fig 5, Section 3.2,
  Methods, Discussion).** The `jaccard` column in `reorg_atlas.json` (source:
  `paper1_reorg_build.py` line 127: `jac = 1 - len(inter) / len(union)`) is
  Jaccard **DISTANCE** (dissimilarity), NOT Jaccard similarity.
  - jaccard_dist = 0.0 → identical pocket profiles (no reorganization)
  - jaccard_dist = 1.0 → completely non-overlapping pockets (maximum reorganization)
  
  The manuscript INCORRECTLY says: "OX2R Gq–Gs yields Jaccard = 0.0, indicating
  that the intracellular pocket landscape is entirely reorganized."  
  **Truth**: OX2R Gq–Gs has Jaccard_distance = 0.0 = IDENTICAL pocket profiles
  (both Gq_7SR8 and Gs_7L1V belong ONLY to orthosteric cluster O1). This is the
  MOST CONSERVED contrast in the dataset.
  
  **Truth about pocket reorganization**: The MOST reorganized contrasts (Jaccard
  distance = 1.0, Jaccard similarity = 0.0) are: SSTR2 Gi–Gq, NMUR2 Gi–Gq,
  CRHR2 Gi–Gs, H1R Gq–Gs, P2Y1R Gq–Gs (all with zero shared pockets).
  
  **What IS special about OX2R**: Under Gi coupling, OX2R uniquely accesses a
  druggable pocket (consensus cluster D18) absent in both Gq and Gs complexes
  (Jaccard_dist Gi–Gq = 0.5, Gi–Gs = 0.5). Gq and Gs are identical (dist = 0.0).
  OX2R Gq–Gs also shows relatively high gateway divergence (mean |Δopen| = 0.109),
  though only TM3–TM4 has non-overlapping per-replica 95% CIs.
  
  **Required fix**: Convert figure and text to use Jaccard SIMILARITY (= 1 − dist)
  throughout, OR label explicitly as Jaccard DISTANCE. Correct the OX2R narrative.
  Figure 5B bars should show: Gi↔Gq = 0.5 (sim), Gi↔Gs = 0.5 (sim), Gq↔Gs = 1.0
  (sim; identical), annotated correctly. Update Section 3.2, Methods, Discussion.

- **F12 — 332 vs 333 µs reconciled (not an error, but document it).** "≈332 µs"
  in the manuscript is correct. The exact aggregate is 332.286 µs, not 333 µs.
  Discrepancy from naive 222×3×500 = 333 µs because:
  • Gi_7E32: 3 × 260 ns = 780 ns (short trajectory)
  • Gi_8HK2: 3 × 2 ns = 6 ns (likely a data-entry anomaly; flag for user)
  • Gq_8J9N: 6 × 500 ns = 3000 ns (6 replicas instead of 3)
  Text value "≈332 µs" is accurate; no change needed. Recommend flagging Gi_8HK2
  (2 ns/replica) as a possible data-entry error in the systems_master.csv.

- **F13 — Orthosteric recovery benchmark (new Phase 1A result).** Cohort-wide
  orthosteric site recovery: 158/209 systems with pockets recover the orthosteric
  site (75.6%). By G-family: Gi 73.1%, Gs 76.1%, Gq 81.4%, G12 66.7%.
  13 systems have no pockets detected (intracellular cavity occluded). This is
  a new headline number for Section 3.2 and Table T2.

- **F14 — Gateway permutation null: no contrast exceeds null at p95.** The
  permutation null for mean gateway distance (7 portals, 5000 permutations) has
  p95 = 0.128. The maximum observed gateway_dist is 0.110 (H1R Gq–Gs), which
  does NOT exceed the null. HOWEVER, specific portal-level comparisons CAN be
  above noise: FFAR4 TM6–TM7 (Gi=0.022 vs Gq=0.208) has non-overlapping per-
  replica 95% CIs, supporting the "~10×" claim for that single portal.
  Implication: the summary MEAN across 7 portals does not reach significance, but
  INDIVIDUAL portals (especially TM6–TM7 in FFAR4) show above-noise differences.
  The manuscript currently describes only the named portal differences for FFAR4,
  which IS supported. The summary Jaccard-vs-gateway scatter should note the
  non-significant association across contrasts.
