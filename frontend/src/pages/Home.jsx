import { useEffect, useState } from 'react'
import { api } from '../api'

const FAMILY_COLORS = { Gi: 'var(--gio)', Gs: 'var(--gs)', Gq: 'var(--gq)', 'G12-13': 'var(--g1213)' }

export default function Home({ navigate }) {
  const [families, setFamilies] = useState(null)
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([api.families(), api.health()])
      .then(([f, h]) => { setFamilies(f.families); setHealth(h) })
      .catch(e => setError(e.message))
  }, [])

  const totalNs = families ? families.reduce((s, f) => s + (f.total_sampling_ns || 0), 0) : 0
  const totalUs = (totalNs / 1000).toFixed(1)

  return (
    <div className="page">
      <div style={{ maxWidth: 640, marginBottom: 32 }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1.1, marginBottom: 12 }}>
          The coupled state, in motion.
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '1.05rem', lineHeight: 1.65 }}>
          Molecular dynamics of active-state GPCR-G-protein ternary complexes, organized by
          G-protein family, with a precomputed pocket, gateway, and reorganization analysis layer.
        </p>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="stat-grid">
        <div className="stat-card">
          <div className="num">{health?.n_systems ?? '—'}</div>
          <div className="label">MD systems</div>
          <div className="sub">207 validated ternary complexes</div>
        </div>
        <div className="stat-card">
          <div className="num">{totalUs > 0 ? `${totalUs}` : '—'}<span style={{ fontSize: '1rem' }}> μs</span></div>
          <div className="label">Aggregate sampling</div>
          <div className="sub">207 systems · standard 3 × 500 ns</div>
        </div>
        <div className="stat-card">
          <div className="num">4</div>
          <div className="label">G-protein families</div>
          <div className="sub">Gi/o · Gs · Gq/11 · G12/13</div>
        </div>
        <div className="stat-card">
          <div className="num">CHARMM36</div>
          <div className="label">Force field</div>
          <div className="sub">Uniform across all systems</div>
        </div>
      </div>

      {families && (
        <div style={{ margin: '28px 0' }}>
          <h2 style={{ fontSize: '0.9rem', fontWeight: 700, letterSpacing: '0.1em',
                       textTransform: 'uppercase', color: 'var(--faint)', marginBottom: 14 }}>
            Systems by G-protein family
          </h2>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {families.map(f => (
              <div key={f.family}
                style={{ border: '1px solid var(--rule)', borderRadius: 'var(--radius)',
                         padding: '16px 20px', minWidth: 160, cursor: 'pointer',
                         borderTop: `4px solid ${FAMILY_COLORS[f.family] || 'var(--accent)'}` }}
                onClick={() => navigate('/systems')}>
                <div style={{ fontWeight: 800, fontSize: '1.4rem', color: FAMILY_COLORS[f.family] }}>
                  {f.n_systems}
                </div>
                <div style={{ fontWeight: 700, fontSize: 13, marginTop: 2 }}>{f.family}</div>
                <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 3 }}>
                  {f.n_receptors} receptors · {(f.total_sampling_ns / 1000).toFixed(0)} μs
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 12, marginTop: 28 }}>
        <button
          onClick={() => navigate('/systems')}
          style={{ background: 'var(--accent)', color: '#fff', border: 'none',
                   borderRadius: 'var(--radius)', padding: '9px 20px', fontWeight: 700,
                   fontSize: 13, cursor: 'pointer' }}>
          Browse systems
        </button>
        <button
          onClick={() => navigate('/atlas')}
          style={{ background: '#fff', color: 'var(--ink)', border: '1px solid var(--rule)',
                   borderRadius: 'var(--radius)', padding: '9px 20px', fontWeight: 600,
                   fontSize: 13, cursor: 'pointer' }}>
          Explore atlas
        </button>
      </div>

      {/* How to cite */}
      <div style={{ marginTop: 36, padding: 20, background: 'var(--panel)', borderRadius: 'var(--radius)',
                    border: '1px solid var(--rule)' }}>
        <h3 style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase',
                     letterSpacing: '0.08em', color: 'var(--faint)', marginBottom: 8 }}>
          How to cite
        </h3>
        <p style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--muted)', margin: 0 }}>
          Huang J et al., CoupledMD: a web resource for GPCR–G-protein molecular dynamics.
          Citation details to be confirmed (pre-publication).
        </p>
        <p style={{ fontSize: 11, color: 'var(--faint)', marginTop: 8, marginBottom: 0 }}>
          Data: CC-BY-4.0 &middot; Code: MIT &middot; Zenodo DOI 10.5281/zenodo.21395292
        </p>
      </div>

      <div style={{ marginTop: 24, padding: '20px 0', borderTop: '1px solid var(--rule)',
                    color: 'var(--faint)', fontSize: 12 }}>
        Force field: CHARMM36-based simulation protocols across the final release cohort.
        Structures from experimental cryo-EM/X-ray ternary complexes (197), plus 10
        engineered/uncertain models.
      </div>
    </div>
  )
}
