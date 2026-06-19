# Overnight session report — CoupledMD manuscript + figures

**Branch:** `overnight/manuscript-20260619` (8 commits; nothing pushed; web-server
files untouched). **Target journal inferred:** Nucleic Acids Research (Web Server
Issue) — from the resource framing, REST API, and GPCRdb/GPCRmd positioning.

## Final deliverable
- **Latest manuscript:** `manuscript_figures/versions/manuscript_v1.2.1.docx`
  (10 pp; rendered PDF alongside: `manuscript_v1.2.1.pdf`).
- Matching markdown source: `manuscript_figures/nar_manuscript.md` (working copy)
  and the per-version snapshot `versions/manuscript_v1.2.1.md`.
- **Figures (vector PDF + 600-dpi PNG):** `manuscript_figures/figures/`.
- Regenerate everything: `python generate_figures_1_2_3.py && python
  generate_figures_4_5.py && python build_docx.py nar_manuscript.md <version>`
  (uses `figstyle.py`; Python at `/MDdata/data01/jxhuang/miniconda3/bin/python3`).

## What to review first (prioritised)
1. **CCR5 number (F4) — confirm the fix.** I changed CCR5's recovered Na⁺/maraviroc
   frequency from **0.927 → 0.910** everywhere. Reason: cluster 50 (mean 0.927)
   does **not** contain CCR5 (Gi_7F1Q); 0.910 is CCR5's real system-level value,
   0.927 is the cross-database cluster mean over 10 *other* systems. The headline
   (blind recovery of the maraviroc site) is intact. Please confirm this is the
   intended framing.
2. **Fig 4 barcode scope (F9).** Source `pilot_long.csv` has only **25 CGN
   positions** (a pilot), not 356, and no per-system "CCR5–Gi" barcode exists.
   Figure + caption + a new Discussion limitation now say "pilot". **Decision
   needed:** compute the full 356-position / 222-system barcode, or keep the
   pilot framing for submission.
3. **Fig 5D correlation (F10).** The "extreme pocket divergence → larger α5
   geometry difference, suggesting a structural basis" claim is **not supported**
   (your own Spearman: jaccard~dtilt r=+0.23 p=0.45, n=13). I removed it and the
   figure shows no trend line. Confirm, or recompute on a larger set.
4. **Title.** De-overclaimed for journal fit (see changelog v1.2.1). If you prefer
   the punchier original ("…reveals dynamic coupling selectivity"), revert one line.
5. **Placeholders to fill:** `[repository placeholder]`, `[URL]`, `[GitHub URL]`,
   DOI — in Abstract, Methods (Data availability). I could not supply these.

## Version history (rationale)
| Ver | Axis | Change |
|-----|------|--------|
| baseline | — | Snapshot of original 5 figures + manuscript (reversible). |
| 1.0.0 | figures + assembly | All 5 figures rebuilt to one visual system; docx assembled. |
| 1.1.0 | figure–text integration | All captions + linked body claims reconciled with corrected figures (F2b, F4, F8, F9, F10). |
| 1.2.0 | consistency + limitations | Pocket freq range 0.864→0.858; α5 ranges/counts verified; honest barcode-pilot limitation added. |
| 1.2.1 | title + proofreading | Title grammar/journal fit; proofread clean; converged. |

Rubric trend (clarity / rigor / figure quality / journal fit / consistency): every
version held or raised the score; none regressed. Stopped at v1.2.1 — figure work
complete and prose already strong (further rewriting would be churn, not gain).

## Figure-by-figure (before → after)
All figures: unified colour-blind-safe palette (Gi/o green #2f8f6b, Gq/11 orange
#c0741a, Gs blue #2c6fb3, G12/13 purple #8a4aa0), despined hairline axes, type
hierarchy, no overlaps. Before: `git show baseline:manuscript_figures/<file>`.
After: `manuscript_figures/figures/`.

| Fig | Key change | Integrity |
|-----|-----------|-----------|
| 1 | **Panel A data bug fixed**: was `nunique(receptor_gene)` over an 80%-null column (showed 10/23/5/4); now true system counts 100/68/47/7. Panel D uses `receptor_name`. | F1, F2 |
| 2 | Overlapping arrow-labels → clean legend + bubble + summary table; shows CCR5's real values (orthosteric 0.947, Na⁺ 0.910). | F4, F5 |
| 3 | **Metric bug fixed**: both panels plotted the same `occupancy`; Panel A now `open_fraction` (TM6–TM7 0.022 vs 0.208, matching text), Panel B portal distance. | F3 |
| 4 | Palette unified; barcode = real 25 pilot CGN positions; cividis heatmap; OX2R annotated; legends off the bars. | F9, F8 |
| 5 | Panel B now OX2R pairwise pocket-residue Jaccard (Gq↔Gs = 0.00); Panel D jaccard vs α5 tilt diff with **no trend line** (non-significant). | F10 |

Full detail: `INTEGRITY_FLAGS.md`.

## Flags & deferred decisions
- **Corrected in figures using real data (no fabrication):** F1, F2, F3, F5, F6
  (palette). **Flagged, data unchanged:** F4 (CCR5 0.910 vs 0.927), F7 (freq
  range), F8 (OX2R rank tie), F9 (25 vs 356 positions), F10 (unsupported
  correlation), F2b (caption "aminergic"). All addressed in text per `CHANGELOG.md`.
- **`nar_methods.md`** is an earlier standalone Methods draft with `[CITATION:…]`
  and `[N_COMPARE]` placeholders; it is **superseded** by the full Methods inside
  `nar_manuscript.md` (N_COMPARE = 16). Left in place (not deleted). Recommend
  removing it from the submission package to avoid confusion.
- **Not done (out of scope / needs you):** repository DOI + URLs; the full
  356-position barcode computation; any re-analysis on more replicas.

## Toolchain notes
pandoc and LaTeX are **not installed** in this environment. The docx is built with
**python-docx** (`build_docx.py`) — the brief's endorsed fallback, with precise
figure/caption control — and verified by LibreOffice PDF render. If you want a
pandoc/LaTeX pipeline later, install pandoc and a TeX engine; the markdown is
clean and standard.
