export default function About() {
  return (
    <div className="page">
      <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 20 }}>CoupledMD &mdash; 208 validated GPCR&ndash;G-protein MD simulations</h1>

      <section style={{ marginBottom: 32 }}>
        <h2 className="section-heading">What is CoupledMD?</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7, maxWidth: 720 }}>
          CoupledMD is a web resource providing open access to molecular dynamics (MD) simulation data
          for active-state GPCR&ndash;G-protein ternary complexes. It covers <strong>208 validated systems</strong> across
          all four major G-protein families (G<sub>i/o</sub>, G<sub>s</sub>, G<sub>q/11</sub>, G<sub>12/13</sub>),
          with precomputed analyses of druggable pockets, bilayer gateways, and partner-switching
          reorganization. The resource is designed to support structure-based drug discovery and
          mechanistic studies of GPCR signaling.
        </p>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 className="section-heading">Dataset statistics</h2>
        <div className="stat-grid" style={{ maxWidth: 720 }}>
          <div className="stat-card">
            <div className="num">208</div>
            <div className="label">Systems</div>
          </div>
          <div className="stat-card">
            <div className="num">4</div>
            <div className="label">G-protein families</div>
          </div>
          <div className="stat-card">
            <div className="num">174</div>
            <div className="label">Distinct receptor names</div>
          </div>
          <div className="stat-card">
            <div className="num">312.0 &mu;s</div>
            <div className="label">Aggregate sampling</div>
          </div>
        </div>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 className="section-heading">Simulation Protocol</h2>
        <div className="detail-card" style={{ maxWidth: 720 }}>
          <div className="kv"><span className="k">Systems</span><span className="v">208 validated active-state ternary complexes</span></div>
          <div className="kv"><span className="k">Force field</span><span className="v">CHARMM36</span></div>
          <div className="kv"><span className="k">Replicas</span><span className="v">3 per system (independent trajectories)</span></div>
          <div className="kv"><span className="k">Length</span><span className="v">500 ns per replica (1.5 &mu;s total per system)</span></div>
          <div className="kv"><span className="k">MD engine</span><span className="v">AMBER pmemd (chamber); GROMACS for 10 systems</span></div>
          <div className="kv"><span className="k">Starting structures</span><span className="v">Experimental cryo-EM / X-ray ternary complexes (197); 11 engineered/uncertain</span></div>
          <div className="kv"><span className="k">Receptor identifiers</span><span className="v">174 distinct receptor names; 173 mapped UniProt accessions (one consensus-model system has no UniProt mapping)</span></div>
          <div className="kv"><span className="k">Membrane</span><span className="v">208 membrane-embedded (POPC/POPE mixtures)</span></div>
          <div className="kv"><span className="k">Water model</span><span className="v">TIP3P</span></div>
          <div className="kv"><span className="k">Ionic strength</span><span className="v">0.15 M NaCl</span></div>
          <div className="kv"><span className="k">Temperature</span><span className="v">310 K (Langevin thermostat)</span></div>
          <div className="kv"><span className="k">Pressure</span><span className="v">1 atm (Monte Carlo barostat)</span></div>
          <div className="kv"><span className="k">Constraints</span><span className="v">SHAKE (hydrogen bonds), 2 fs timestep</span></div>
          <div className="kv"><span className="k">Total sampling</span><span className="v">312.0 &mu;s aggregate</span></div>
        </div>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 className="section-heading">Analysis Pipeline</h2>
        <div style={{ maxWidth: 720 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <PipelineStep
              n="1"
              title="Cohort freeze &amp; validation"
              desc="Final validated release inventory of 208 systems with force-field corrections, file integrity checks, and structural provenance classification."
            />
            <PipelineStep
              n="2"
              title="Database ingestion"
              desc="System metadata, file paths, and analysis availability registered in SQLite with full-text search indexes on gene, UniProt, PDB, and family."
            />
            <PipelineStep
              n="3"
              title="Pocket detection &amp; GPCRdb mapping"
              desc="Voxel-based pocket detection on MD trajectories. Each pocket is mapped to GPCRdb generic numbering and classified by zone (orthosteric, extracellular, intracellular, lipid-facing)."
            />
            <PipelineStep
              n="4"
              title="Gateway analysis"
              desc="Bilayer gateway identification at TM helix interfaces. Metrics: water occupancy, lipid penetration depth, and open fraction — computed per replica with 95% confidence intervals."
            />
            <PipelineStep
              n="5"
              title="Consensus &amp; reorganization"
              desc="Cross-system consensus clustering of druggable pockets. Within-receptor partner-switching comparison of pocket sets and gateway metrics between different G-protein partners."
            />
            <PipelineStep
              n="6"
              title="Visualization tier"
              desc="Decimated trajectories (~2500 frames) with stripped membrane/water/ions for web-based NGL viewing. Reference PDB topologies for each system."
            />
          </div>
        </div>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 className="section-heading">Data Tiers</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, maxWidth: 720 }}>
          <div className="detail-card">
            <h3>Full</h3>
            <p style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
              Complete trajectories with membrane, water, and ions. Multi-terabyte scale.
              Available via DOI archive upon publication.
            </p>
          </div>
          <div className="detail-card">
            <h3>Analysis</h3>
            <p style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
              Precomputed JSON: pocket frequencies, GPCRdb mappings, gateway metrics,
              consensus clusters, and reorganization comparisons. Served via the API.
            </p>
          </div>
          <div className="detail-card">
            <h3>Viz</h3>
            <p style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
              Decimated XTC (~2500 frames) with stripped solvent for interactive NGL
              viewing. Reference PDB for topology. Downloadable per system.
            </p>
          </div>
        </div>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 className="section-heading">API Access</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7, maxWidth: 720 }}>
          All analysis data is accessible via a RESTful API. Interactive documentation is
          available at <a href="/api/docs" target="_blank" rel="noreferrer">/api/docs</a> (Swagger)
          and <a href="/api/redoc" target="_blank" rel="noreferrer">/api/redoc</a> (ReDoc).
          Key endpoints:
        </p>
        <div className="detail-card" style={{ maxWidth: 720, marginTop: 12 }}>
          <div className="kv"><span className="k" style={{ fontFamily: 'monospace', fontSize: 12 }}>GET /api/v1/systems</span><span className="v" style={{ fontSize: 12 }}>List systems with filters</span></div>
          <div className="kv"><span className="k" style={{ fontFamily: 'monospace', fontSize: 12 }}>GET /api/v1/systems/{'{sid}'}</span><span className="v" style={{ fontSize: 12 }}>System metadata</span></div>
          <div className="kv"><span className="k" style={{ fontFamily: 'monospace', fontSize: 12 }}>GET /api/v1/systems/{'{sid}'}/pockets</span><span className="v" style={{ fontSize: 12 }}>Pocket data (GPCRdb-mapped)</span></div>
          <div className="kv"><span className="k" style={{ fontFamily: 'monospace', fontSize: 12 }}>GET /api/v1/systems/{'{sid}'}/gateways</span><span className="v" style={{ fontSize: 12 }}>Gateway metrics</span></div>
          <div className="kv"><span className="k" style={{ fontFamily: 'monospace', fontSize: 12 }}>GET /api/v1/consensus/pockets/druggable</span><span className="v" style={{ fontSize: 12 }}>Consensus druggable pockets</span></div>
          <div className="kv"><span className="k" style={{ fontFamily: 'monospace', fontSize: 12 }}>GET /api/v1/consensus/gateways</span><span className="v" style={{ fontSize: 12 }}>Consensus gateway atlas</span></div>
          <div className="kv"><span className="k" style={{ fontFamily: 'monospace', fontSize: 12 }}>GET /api/v1/consensus/nominations</span><span className="v" style={{ fontSize: 12 }}>Druggable pocket nominations</span></div>
          <div className="kv"><span className="k" style={{ fontFamily: 'monospace', fontSize: 12 }}>GET /api/v1/consensus/reorg</span><span className="v" style={{ fontSize: 12 }}>Partner-switching reorganization</span></div>
        </div>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 className="section-heading">Citation</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7, maxWidth: 720 }}>
          If you use CoupledMD, please cite: <strong>Huang J et al., CoupledMD: a web resource for
          GPCR–G-protein molecular dynamics. Citation details to be confirmed
          (pre-publication).</strong>
        </p>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 className="section-heading">Data availability</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7, maxWidth: 720 }}>
          Full trajectory data will be available via a Zenodo archive upon publication
          (DOI pending, pre-publication).
        </p>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 className="section-heading">Contact</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7, maxWidth: 720 }}>
          Jianxiang Huang, <a href="mailto:jxhuang@sjtu.edu.cn">jxhuang@sjtu.edu.cn</a>
        </p>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7, maxWidth: 720, marginTop: 4 }}>
          GitHub: <strong>repository URL pending (pre-publication)</strong>
        </p>
      </section>
    </div>
  )
}

function PipelineStep({ n, title, desc }) {
  return (
    <div style={{ display: 'flex', gap: 12 }}>
      <div style={{
        width: 28, height: 28, borderRadius: '50%', background: 'var(--accent)',
        color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontWeight: 800, fontSize: 13, flexShrink: 0,
      }}>
        {n}
      </div>
      <div>
        <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 2 }}>{title}</div>
        <div style={{ color: 'var(--muted)', fontSize: 12, lineHeight: 1.6 }}>{desc}</div>
      </div>
    </div>
  )
}
