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
