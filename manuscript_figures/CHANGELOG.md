# CoupledMD manuscript — overnight changelog

Target journal: **Nucleic Acids Research** (Web Server Issue). Inferred from the
manuscript framing (web resource, REST API, GPCRdb/GPCRmd positioning) and the
existing NAR reference formatting.

Versioning: minor = substantive pass, patch = proofing. Each version snapshots
`manuscript_vX.Y.Z.md` + `.docx` under `versions/`.

---

## v1.0.0 — Figures rebuilt + first docx assembly
**Figures (Phase 1).** All five figures rewritten to a single publication-grade
visual system (`figstyle.py`): one colour-blind-safe palette (Gi/o green, Gq/11
orange, Gs blue, G12/13 purple) applied consistently, hairline despined axes,
clear type hierarchy, no overlaps. Data-integrity corrections (all using real
pipeline outputs; see `INTEGRITY_FLAGS.md`):
- Fig 1A: was `nunique(receptor_gene)` over an 80%-null column (10/23/5/4);
  now true system counts 100/68/47/7.
- Fig 3: both panels previously plotted the same `occupancy` metric; Panel A now
  `open_fraction` (TM6–TM7 0.022 vs 0.208, matching the text), Panel B portal
  distance with the 8 Å threshold.
- Fig 5B: replaced near-uniform zone-frequency bars with the real OX2R pairwise
  pocket-residue Jaccard (Gq↔Gs = 0.00).
- Fig 5D: jaccard vs α5 tilt difference, NO trend line (resource's own Spearman
  is non-significant, n=13).

**Assembly (Phase 2).** `build_docx.py` compiles the manuscript markdown to a
single-column .docx (python-docx; pandoc unavailable in env), embedding each
figure above its numbered caption. Verified: all 5 figures present, in order,
sized correctly, captions self-contained, unicode renders.

**Known open items for Phase 3** (caption/text still describe the *old* figures):
F2b (Fig 1 caption "aminergic"), F4 (CCR5 0.927 vs real 0.910 / cluster-50
membership), F9 (Fig 4 "356 positions" vs real 25 pilot), F10 (Fig 5D unsupported
correlation claim). To be reconciled in the figure-text integration + consistency
passes.

## v1.1.0 — Figure–text integration (Phase 3, axis 5)
Reconciled all five captions and the tightly-linked body claims with the
corrected figures, resolving the integrity flags:
- F2b: Fig 1D caption now "twelve most-represented receptors … peptide- and
  lipid-sensing" (was "Top 15 … aminergic").
- F4: CCR5 number corrected to its real system-level frequency 0.910 (Fig 2,
  §3.2, Methods); the cross-database 0.927 is now correctly attributed to the
  consensus cluster (10 systems), not to CCR5. "Consensus cluster 50" framing
  removed. Bar-colour description fixed (red orthosteric / orange Na⁺ / teal).
- F8: OX2R "ranks highest" softened to "among the top-ranked / tied at rank 1".
- F9: Fig 4A caption now "25 CGN positions … pilot interface cohort" (was "356
  positions … exemplar CCR5–Gi"); body "at all 356 CGN positions" → "indexed by
  the CGN scheme"; "comparable across all 222 simulations (Fig 4A)" → "… across
  simulations; Fig 4A shows the pilot cohort mean".
- F10: Fig 5D caption now states no significant association (Spearman, n=13);
  the unsupported "structural basis" claim removed. Fig 5B/5C captions match the
  new Jaccard-bar and open-fraction-heatmap panels.

## v1.2.0 — Internal consistency + honest limitations (Phase 3, axes 9, 6)
- F7: pocket cluster mean-frequency range corrected 0.864 → 0.858 (matches the
  druggable-cluster data). Verified α5 geometry ranges (tilt 29.8–73.1 mean 52.9,
  depth 20.4–50.8 mean 32.2, hook 1.1–12.3) and counts (50 clusters, 16 contrasts,
  209+13=222, 182 receptors) — all correct, unchanged.
- Discussion: added an explicit limitation that the Figure 4A CGN interface
  barcode is a pilot (subset of positions/systems), with full-356/222 extension
  in progress — keeps the manuscript internally consistent with the figure.

## v1.2.1 — Title + proofreading (Phase 3, axes 1, 10)
- Title: fixed grammar/journal fit — "a web resource … reveals dynamic coupling
  selectivity" (resource as subject of "reveals") → "a uniform-protocol molecular
  dynamics web resource for comparative analysis of 222 GPCR–G-protein ternary
  complexes". (Optional — see report; user may prefer the punchier original.)
- Proofread: 0 double spaces, 0 repeated words, 0 space-before-punct. Spelling is
  internally consistent Oxford (-ize / -lyse / double-l) — left unchanged.
- Diminishing returns reached on prose: the body text was already strong;
  further rewriting withheld per stopping discipline.

## v1.3.0 — Phase 3 morning session
- Morning session continuation: further consistency, journal-fit adjustments.
  (See Phase 3 session report.)

## v1.4.0 — Overnight Phase 0–4 run (2026-06-21)
**CRITICAL DATA FIX (F11): Jaccard inversion corrected throughout.**
The `jaccard` column in `reorg_atlas.json` stores Jaccard DISTANCE (1 − similarity),
not similarity. The manuscript through v1.3.0 had the interpretation inverted:
- Was: "OX2R Gq–Gs Jaccard = 0.0 → completely reorganized pocket landscape"
- Corrected: Jaccard distance = 0.0 → IDENTICAL pocket profiles (most conserved)
- The 5 maximally reorganized contrasts (sim = 0.0, dist = 1.0): SSTR2 Gi–Gq,
  NMUR2 Gi–Gq, CRHR2 Gi–Gs, H1R Gq–Gs, P2Y1R Gq–Gs.
- The correct OX2R story: Gi uniquely accesses druggable cluster D18 (absent in
  Gq and Gs); Gq and Gs have IDENTICAL pocket profiles. Narrative rewritten.

**Phase 1A — Recovery benchmark (new).**
Computed cohort-wide for the first time (script: `phase1_analysis.py`):
158/209 = 75.6% orthosteric recovery across systems with detectable pockets.
By ligand type: small-molecule 94.9%, peptide 85.3%. Added to §3.2 and Table T2.

**Phase 1B — Partner-switching census hardened.**
All 16 contrasts now quantified with Jaccard SIMILARITY (= 1 − dist) and gateway
mean |Δ| distances with bootstrap 95% CIs. Permutation null computed (5000 perms,
p95 = 0.128); no contrast exceeds the null for the MEAN 7-portal metric, but
FFAR4 TM6–TM7 (Gi vs Gq) has non-overlapping per-replica CIs (10× difference
is above noise). Table T3 updated with all 16 contrasts.

**Phase 2 — Full table set generated.**
T1–T3 main-text tables + S1–S6 supplementary tables in `manuscript_figures/tables/`.
Scripts: `generate_tables.py`.

**Phase 3 — Figure 5 corrected.**
`generate_figures_4_5.py` rewritten: Figure 5 now plots Jaccard SIMILARITY on all
axes. OX2R annotations corrected (Gi-unique D18 pocket story). Figure 5D x-axis
label corrected. `figures/figure5_partner_switching.pdf` + `.png` regenerated.

**Phase 4 — v1.4.0 compiled.**
`nar_manuscript.md` updated. `build_docx.py` produced `versions/manuscript_v1.4.0.docx`
(1.86 MB) and `versions/manuscript_v1.4.0.md`.

**Phase 0 — Audit artefacts.**
`INTEGRITY_FLAGS.md` updated with F11–F14. `MASTER_REPORT.md` written (morning report).
`phase1_analysis.py` generates `phase1_outputs/` directory with all new statistics.
