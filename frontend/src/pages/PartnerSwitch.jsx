import { useEffect, useState } from 'react'
import { api } from '../api'

const FAM_COLOR = { Gi: 'var(--gio)', Gs: 'var(--gs)', Gq: 'var(--gq)', 'G12-13': 'var(--g1213)' }

export default function PartnerSwitch({ navigate }) {
  const [reorg, setReorg] = useState(null)
  const [selected, setSelected] = useState(null)
  const [dataA, setDataA] = useState(null)
  const [dataB, setDataB] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.reorg().then(d => {
      setReorg(d)
      // Check URL for pre-selected receptor
      const params = new URLSearchParams(window.location.hash.split('?')[1] || '')
      const receptorParam = params.get('receptor')
      if (receptorParam && d.comparisons) {
        const match = d.comparisons.find(c => c.receptor === receptorParam)
        if (match) selectComparison(match)
      }
    }).catch(e => setError(e.message))
  }, [])

  function selectComparison(c) {
    setSelected(c); setDataA(null); setDataB(null); setLoading(true); setError(null)

    // Sync to URL
    const base = '#/compare'
    const params = new URLSearchParams()
    if (c.receptor) params.set('receptor', c.receptor)
    const qs = params.toString()
    const newHash = qs ? `${base}?${qs}` : base
    if (window.location.hash !== newHash) {
      window.history.replaceState(null, '', newHash)
    }

    Promise.all([
      api.systemPockets(c.sid_A, true).catch(() => null),
      api.systemPockets(c.sid_B, true).catch(() => null),
      api.systemGateways(c.sid_A).catch(() => null),
      api.systemGateways(c.sid_B).catch(() => null),
    ]).then(([pkA, pkB, gwA, gwB]) => {
      setDataA({ pockets: pkA, gateways: gwA })
      setDataB({ pockets: pkB, gateways: gwB })
    }).catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  const comparisons = reorg?.comparisons || []

  return (
    <div className="page">
      <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 6 }}>
        Partner-switching comparison
      </h1>
      <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 20 }}>
        Receptors with MD data for multiple G-protein partners. Select a pair to compare
        pocket occupancy and gateway metrics side-by-side.
      </p>

      {error && <div className="error">{error}</div>}

      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>

        {/* Left: receptor list */}
        <div style={{ minWidth: 260, flex: '0 0 260px' }}>
          <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)',
                       textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
            {comparisons.length} receptor contrasts
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {comparisons.map((c, i) => (
              <button key={i}
                onClick={() => selectComparison(c)}
                style={{
                  padding: '10px 12px', textAlign: 'left', border: '1px solid var(--rule)',
                  borderRadius: 8, background: selected === c ? '#f0f7f7' : '#fff',
                  borderColor: selected === c ? 'var(--accent)' : 'var(--rule)',
                  cursor: 'pointer',
                }}>
                <div style={{ fontWeight: 700, fontSize: 13 }}>{c.receptor}</div>
                <div style={{ fontSize: 11, marginTop: 3, display: 'flex', gap: 6 }}>
                  <span className="chip" style={{ background: FAM_COLOR[c.famA] }}>{c.famA}</span>
                  <span style={{ color: 'var(--muted)' }}>vs</span>
                  <span className="chip" style={{ background: FAM_COLOR[c.famB] }}>{c.famB}</span>
                </div>
                <div style={{ fontSize: 10, color: 'var(--muted)', marginTop: 2, fontFamily: 'monospace' }}>
                  {c.sid_A} / {c.sid_B}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right: comparison panels */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selected && !loading && (
            <div className="empty" style={{ marginTop: 40 }}>
              Select a receptor contrast to compare pocket and gateway data.
            </div>
          )}
          {loading && <div className="loading">Loading comparison data…</div>}

          {selected && !loading && (
            <>
              <ComparisonHeader comparison={selected} navigate={navigate} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 }}>
                <PocketPanel label={selected.famA} sid={selected.sid_A}
                             color={FAM_COLOR[selected.famA]} data={dataA} navigate={navigate} />
                <PocketPanel label={selected.famB} sid={selected.sid_B}
                             color={FAM_COLOR[selected.famB]} data={dataB} navigate={navigate} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 }}>
                <GatewayPanel label={selected.famA} color={FAM_COLOR[selected.famA]} data={dataA} />
                <GatewayPanel label={selected.famB} color={FAM_COLOR[selected.famB]} data={dataB} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function ComparisonHeader({ comparison: c, navigate }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
      <div>
        <span style={{ fontWeight: 800, fontSize: '1.1rem' }}>{c.receptor}</span>
        <span style={{ marginLeft: 8, color: 'var(--muted)', fontSize: 13 }}>
          <a href={`https://www.uniprot.org/uniprot/${c.uniprot}`}
             target="_blank" rel="noreferrer" style={{ fontFamily: 'monospace' }}>
            {c.uniprot}
          </a>
        </span>
      </div>
      <span style={{ color: 'var(--muted)', fontSize: 13 }}>
        {c.n_union} total pockets across both partners
      </span>
      <div style={{ display: 'flex', gap: 6, marginLeft: 'auto' }}>
        <a href={`#/systems/${c.sid_A}`} onClick={e => { e.preventDefault(); navigate(`/systems/${c.sid_A}`) }}
          style={{ fontSize: 12, fontFamily: 'monospace' }}>
          {c.sid_A}
        </a>
        <span style={{ color: 'var(--faint)', fontSize: 12 }}>/</span>
        <a href={`#/systems/${c.sid_B}`} onClick={e => { e.preventDefault(); navigate(`/systems/${c.sid_B}`) }}
          style={{ fontSize: 12, fontFamily: 'monospace' }}>
          {c.sid_B}
        </a>
      </div>
    </div>
  )
}

function PocketPanel({ label, sid, color, data, navigate }) {
  const pockets = data?.pockets?.pockets || []
  const maxFreq = pockets.length ? Math.max(...pockets.map(p => p.mean_freq), 0.01) : 0

  return (
    <div style={{ border: '1px solid var(--rule)', borderRadius: 8, padding: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="chip" style={{ background: color }}>{label}</span>
          <a href={`#/systems/${sid}`} onClick={e => { e.preventDefault(); navigate(`/systems/${sid}`) }}
            style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--muted)' }}>
            {sid}
          </a>
        </div>
      </div>
      <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>
        {pockets.length} pockets
      </div>
      {!data && <div className="loading" style={{ fontSize: 12 }}>Loading…</div>}
      {data && !pockets.length && <div className="empty" style={{ fontSize: 12 }}>No pocket data.</div>}

      {/* Mini bar chart */}
      {pockets.length > 0 && (
        <div style={{ marginBottom: 10 }}>
          {pockets.slice(0, 8).map(p => {
            const barW = (p.mean_freq / maxFreq) * 100
            return (
              <div key={p.pocket_id} style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 2 }}>
                <span className="pocket-zone" style={{ width: 60, textAlign: 'center', fontSize: 10 }}>
                  {p.zone || '—'}
                </span>
                <div style={{ flex: 1, height: 12, background: 'var(--panel)', borderRadius: 2,
                              overflow: 'hidden' }}>
                  <div style={{
                    width: `${barW}%`, height: '100%', borderRadius: 2,
                    background: color, transition: 'width 0.3s ease',
                  }} />
                </div>
                <span style={{ flexShrink: 0, width: 34, textAlign: 'right', fontSize: 9,
                               fontWeight: 700, color: 'var(--ink)' }}>
                  {(p.mean_freq * 100).toFixed(0)}%
                </span>
              </div>
            )
          })}
        </div>
      )}

      {pockets.length > 8 && (
        <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 8 }}>
          +{pockets.length - 8} more pockets
        </div>
      )}
    </div>
  )
}

function GatewayPanel({ label, color, data }) {
  const records = data?.gateways?.records || []
  const byPair = {}
  records.forEach(r => {
    if (!byPair[r.pair]) byPair[r.pair] = {}
    byPair[r.pair][r.metric] = r
  })
  const pairs = Object.keys(byPair).sort()

  // Get occupancy for mini chart
  const occRecords = records.filter(r => r.metric === 'occupancy')
  const maxOcc = occRecords.length ? Math.max(...occRecords.map(r => r.mean), 0.01) : 0

  return (
    <div style={{ border: '1px solid var(--rule)', borderRadius: 8, padding: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span className="chip" style={{ background: color }}>{label}</span>
        <span style={{ fontSize: 12, color: 'var(--muted)' }}>Gateways</span>
      </div>
      {!data && <div className="loading" style={{ fontSize: 12 }}>Loading…</div>}
      {data && !pairs.length && (
        <div className="empty" style={{ fontSize: 12 }}>No gateway data available.</div>
      )}

      {/* Mini bar chart */}
      {occRecords.length > 0 && (
        <div style={{ marginBottom: 10 }}>
          {occRecords.slice(0, 8).map(r => {
            const barW = (r.mean / maxOcc) * 100
            return (
              <div key={r.pair} style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 2 }}>
                <span style={{ width: 60, flexShrink: 0, fontSize: 10, fontFamily: 'monospace',
                               color: 'var(--muted)', textAlign: 'right' }}>
                  {r.pair}
                </span>
                <div style={{ flex: 1, height: 12, background: 'var(--panel)', borderRadius: 2,
                              overflow: 'hidden' }}>
                  <div style={{
                    width: `${barW}%`, height: '100%', borderRadius: 2,
                    background: color, transition: 'width 0.3s ease',
                  }} />
                </div>
                <span style={{ flexShrink: 0, width: 34, textAlign: 'right', fontSize: 9,
                               fontWeight: 700, color: 'var(--ink)' }}>
                  {r.mean?.toFixed(2)}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
