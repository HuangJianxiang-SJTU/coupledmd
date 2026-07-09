# Feature Notes — F1 & F2 (Feasibility Only, Not Built)

## F1: Interactive "Protein Map" (ESM-Atlas-style)

**Description:** A 2D interactive map of all 222 GPCR–G-protein systems, where each system is a dot positioned by trajectory-derived feature vectors (e.g., pocket frequency profiles, gateway metrics, coupling geometry) or phylogenetic layout. Users can select a system, highlight its partner-switching comparisons, and see drift lines connecting the same receptor with different G-protein partners.

**Data needed:**
- Per-system feature vectors: already available from pocket frequency profiles (50-dim from consensus clusters), gateway metrics (4 metrics × N portals), and coupling geometry (6 features). These can be concatenated or used separately.
- Partner-switching pairs: already in `consensus/reorg` endpoint (N comparisons).
- Phylogenetic tree of receptors: NOT currently in the data pipeline. Would need sequence alignment + tree building, or an external reference (e.g., GPCRdb tree).

**Rough effort:**
- Dimensionality reduction (t-SNE/UMAP) on existing feature vectors: 1–2 days
- Interactive scatter plot with D3/Plotly: 2–3 days
- Partner-switching drift lines + highlight: 1–2 days
- Phylogenetic layout (if desired): 3–5 days additional
- Total: **5–12 days** depending on scope

**Risk to submission timeline:**
- **High risk.** This is a significant new feature with no existing code. The interactive map requires careful UX design (zoom, pan, selection, tooltip, responsive layout). The phylogenetic layout adds dependency on external data. Feature vector quality (are the pockets/gateways discriminative enough for meaningful clustering?) is unknown until tested. Recommend **v2**.

---

## F2: Pocket-as-Object Entry Point

**Description:** Each shared (consensus) pocket becomes its own page/URL, showing: mean size/area, lining residues, involved helices, occurrence frequency across systems, member systems/receptors, representative frame, and preferred Gα family. This is essentially a detail view for each row in the druggable pockets atlas.

**Data needed:**
- Consensus pocket data: already in `consensus/pockets/druggable` endpoint (50 clusters with n_systems, n_receptors, families, zones, mean_freq, core_generic_numbers).
- Per-pocket residue/helix details: partially available from per-system `pockets_gpcrdb.json` (lining_resids, zone, helix assignments). Would need aggregation across member systems.
- Representative frame: would need to select a specific system + frame for each pocket. Not currently computed.
- Pocket size/area: NOT currently in the data. Would need voxel-count or surface-area computation from the pocketgrid NPZ files.

**Rough effort:**
- New route + page component: 1–2 days
- Data aggregation (residues, helices across member systems): 1–2 days
- Representative frame selection logic: 1 day
- Pocket size/area computation: 2–3 days (if needed)
- Total: **3–8 days** depending on scope

**Risk to submission timeline:**
- **Low-to-moderate risk.** The data already exists in the API; this is primarily a frontend feature with a new route and a data-aggregation step. The pocket-atlas data is the most unique and valuable part of the resource, so a detail view would add significant value. The main unknown is whether pocket size/area is needed or if the existing frequency/zone/generic-number data is sufficient. **More feasible than F1** and could be ready for submission if scoped tightly (skip size/area, skip representative frame).

**Recommendation:** F2 is the more feasible of the two. Ship a minimal version (consensus pocket detail page with existing data) for v1, and add size/area + representative frame in v2.
