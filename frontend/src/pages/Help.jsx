import { useState } from 'react'

const SECTIONS = [
  {
    id: 'getting-started',
    title: 'Getting started',
    content: (
      <>
        <p>CoupledMD provides open access to molecular dynamics simulation data for
        <strong> 208 validated active-state GPCR&ndash;G-protein ternary complexes</strong> across
        all four major G-protein families (G<sub>i/o</sub>, G<sub>s</sub>, G<sub>q/11</sub>,
        G<sub>12/13</sub>).</p>
        <p>Use the <a href="#/systems">Systems</a> browser to find a receptor of interest.
        The free-text search works on receptor gene name, full receptor name, or PDB ID.
        Click any system row to open its detail page.</p>
      </>
    ),
  },
  {
    id: 'system-detail',
    title: 'Understanding the system detail page',
    content: (
      <>
        <h4>Pockets tab</h4>
        <p>The bar chart shows mean pocket frequency across replicas; higher bars indicate
        more persistent pockets. The table lists each pocket with its zone, GPCRdb generic
        numbers, and per-replica frequencies.</p>
        <h4>Gateways tab</h4>
        <p>Inter-helical distances define bilayer gateways at TM helix interfaces.
        Occupancy is the fraction of frames in which the portal is open to water or lipid
        penetration. Gateway analysis is available only for membrane-embedded systems.</p>
        <h4>G-protein tab</h4>
        <p>A contact-persistence barcode is coloured by CGN (Common G-protein Numbering)
        position. Hover over any bar to see the residue identity and persistence value.</p>
        <h4>3D trajectory viewer</h4>
        <p>A 2500-frame NGL.js viewer (shown above the tabs) renders the protein structure.
        Use the mouse to rotate the view and scroll to zoom. The play/pause button animates
        the trajectory; the slider scrubs to any frame.</p>
      </>
    ),
  },
  {
    id: 'partner-switch',
    title: 'Partner-switching comparison (Compare page)',
    content: (
      <>
        <p>The <a href="#/compare">Compare</a> page lists all receptors with simulation data
        for two or more G-protein partners. Select a receptor to view side-by-side pocket
        frequency bar charts and gateway occupancy for each partner.</p>
        <p><strong>Jaccard similarity</strong> measures overlap between pocket sets. A Jaccard
        index below 0.3 indicates strongly divergent pocket landscapes between the two
        partners.</p>
        <div style={{
          border: '1px solid var(--rule)', borderRadius: 'var(--radius)',
          padding: '12px 16px', marginTop: 12, background: 'var(--panel)',
        }}>
          <strong>Case study:</strong> OX2R couples to Gi, Gq, and Gs. The pocket sets for
        Gq and Gs are completely non-overlapping &mdash; Jaccard(Gq, Gs) = 0.0 &mdash;
        illustrating how the same receptor can present radically different druggable surfaces
        depending on the G-protein partner.
        </div>
      </>
    ),
  },
  {
    id: 'api',
    title: 'Programmatic access (API)',
    content: (
      <>
        <p>All analysis data is available via a RESTful API. Base URL: <code>/api/v1/</code></p>
        <table style={{ fontSize: 12, marginTop: 8, marginBottom: 12 }}>
          <thead>
            <tr>
              <th style={{ padding: '6px 12px', textAlign: 'left' }}>Endpoint</th>
              <th style={{ padding: '6px 12px', textAlign: 'left' }}>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr><td style={{ padding: '4px 12px', fontFamily: 'monospace' }}>GET /api/v1/systems</td><td style={{ padding: '4px 12px' }}>All 208 validated systems</td></tr>
            <tr><td style={{ padding: '4px 12px', fontFamily: 'monospace' }}>GET /api/v1/systems/{'{id}'}</td><td style={{ padding: '4px 12px' }}>Single system metadata</td></tr>
            <tr><td style={{ padding: '4px 12px', fontFamily: 'monospace' }}>GET /api/v1/systems/{'{id}'}/pockets</td><td style={{ padding: '4px 12px' }}>Pocket data</td></tr>
            <tr><td style={{ padding: '4px 12px', fontFamily: 'monospace' }}>GET /api/v1/systems/{'{id}'}/gateways</td><td style={{ padding: '4px 12px' }}>Gateway data</td></tr>
            <tr><td style={{ padding: '4px 12px', fontFamily: 'monospace' }}>GET /api/v1/systems/{'{id}'}/gprotein</td><td style={{ padding: '4px 12px' }}>G-protein barcode</td></tr>
            <tr><td style={{ padding: '4px 12px', fontFamily: 'monospace' }}>GET /api/v1/consensus/coupling</td><td style={{ padding: '4px 12px' }}>Alpha-5 geometry (27 systems)</td></tr>
            <tr><td style={{ padding: '4px 12px', fontFamily: 'monospace' }}>GET /api/v1/consensus/gprotein/barcode</td><td style={{ padding: '4px 12px' }}>CGN reference (356 positions)</td></tr>
          </tbody>
        </table>
        <p>Interactive documentation is available at <a href="/api/docs" target="_blank" rel="noreferrer">/api/docs</a> (Swagger UI).</p>
      </>
    ),
  },
]

export default function Help() {
  const [open, setOpen] = useState('getting-started')

  function toggle(id) {
    setOpen(prev => prev === id ? null : id)
  }

  return (
    <div className="page">
      <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 20 }}>Help &amp; Tutorial</h1>

      <div style={{ maxWidth: 720 }}>
        {SECTIONS.map((s, i) => (
          <div key={s.id} style={{
            borderBottom: '1px solid var(--rule)',
          }}>
            <button
              onClick={() => toggle(s.id)}
              aria-expanded={open === s.id}
              style={{
                width: '100%', padding: '14px 0', border: 'none', background: 'none',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
                textAlign: 'left',
              }}
            >
              <span style={{
                width: 24, height: 24, borderRadius: '50%', background: 'var(--accent)',
                color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 800, fontSize: 12, flexShrink: 0,
              }}>
                {i + 1}
              </span>
              <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--ink)' }}>{s.title}</span>
              <span style={{ marginLeft: 'auto', color: 'var(--faint)', fontSize: 12 }}>
                {open === s.id ? '\u25BC' : '\u25B6'}
              </span>
            </button>
            {open === s.id && (
              <div style={{ paddingLeft: 34, paddingBottom: 16, color: 'var(--muted)', fontSize: 13, lineHeight: 1.7 }}>
                {s.content}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
