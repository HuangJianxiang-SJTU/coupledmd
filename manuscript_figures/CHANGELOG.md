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
