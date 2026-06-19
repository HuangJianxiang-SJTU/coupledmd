import { useEffect, useState } from 'react'
import { api } from '../api'

const TABS = ['druggable_pockets', 'gateways', 'nominations', 'reorg']
const TAB_LABELS = {
  druggable_pockets: 'Druggable pockets',
  gateways: 'Gateway atlas',
  nominations: 'Nominations',
  reorg: 'Reorganization',
}

export default function AtlasBrowser({ navigate }) {
  const [tab, setTab] = useState('druggable_pockets')
  const [data, setData] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (data[tab]) return
    setLoading(true); setError(null)
    const loaders = {
      druggable_pockets: api.consensusDruggable,
      gateways: () => api.consensusGateways(),
      nominations: api.nominations,
      reorg: api.reorg,
    }
    loaders[tab]()
      .then(d => setData(prev => ({ ...prev, [tab]: d })))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [tab])

  return (
    <div className="page">
      <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 20 }}>Atlas browsers</h1>

      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid var(--rule)', marginBottom: 20 }}>
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{
              padding: '8px 16px', border: 'none', background: 'none', cursor: 'pointer',
              fontWeight: tab === t ? 700 : 400, fontSize: 13,
              borderBottom: tab === t ? '2px solid var(--accent)' : '2px solid transparent',
              color: tab === t ? 'var(--accent)' : 'var(--muted)',
            }}>
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {loading && <div className="loading">Loading...</div>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && tab === 'druggable_pockets' && data[tab] &&
        <DrugPocketTable data={data[tab]} navigate={navigate} />}
      {!loading && !error && tab === 'gateways' && data[tab] &&
        <GatewayAtlas data={data[tab]} />}
      {!loading && !error && tab === 'nominations' && data[tab] &&
        <Nominations data={data[tab]} />}
      {!loading && !error && tab === 'reorg' && data[tab] &&
        <Reorg data={data[tab]} navigate={navigate} />}
    </div>
  )
}

function DrugPocketTable({ data, navigate }) {
  const clusters = data.clusters || []
  return (
    <section className="atlas-section">
      <h2>Consensus druggable pocket atlas — {clusters.length} clusters</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Cluster</th>
              <th>Systems</th>
              <th>Receptors</th>
              <th>Families</th>
              <th>Zones</th>
              <th>Mean freq</th>
              <th>Core generics</th>
            </tr>
          </thead>
          <tbody>
            {clusters.map(c => {
              const families = typeof c.families === 'string' ? JSON.parse(c.families) : (c.families || {})
              const zones = typeof c.zones === 'string' ? JSON.parse(c.zones) : (c.zones || {})
              const core = c.core_generic_numbers
              return (
                <tr key={c.consensus_id}>
                  <td style={{ fontWeight: 700, fontFamily: 'monospace' }}>{c.consensus_id}</td>
                  <td>{c.n_systems}</td>
                  <td>{c.n_receptors}</td>
                  <td style={{ fontSize: 11 }}>
                    {Object.entries(families).map(([f, n]) => (
                      <span key={f} className="chip" style={{ background: familyColor(f), marginRight: 3 }}>
                        {f}:{n}
                      </span>
                    ))}
                  </td>
                  <td style={{ fontSize: 11, color: 'var(--muted)' }}>
                    {Object.entries(zones).map(([z, n]) => `${z}(${n})`).join(' ')}
                  </td>
                  <td>{(c.mean_freq * 100).toFixed(1)}%</td>
                  <td style={{ fontSize: 10, color: 'var(--muted)', maxWidth: 180,
                               overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                    title={core}>
                    {core?.split(';').slice(0, 4).join('; ')}{core?.split(';').length > 4 ? '…' : ''}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function GatewayAtlas({ data }) {
  const [metric, setMetric] = useState('')
  const [group, setGroup] = useState('')
  const records = (data.records || [])
    .filter(r => !metric || r.metric === metric)
    .filter(r => !group || r.group === group)

  const metrics = [...new Set(data.records?.map(r => r.metric) || [])]
  const groups = [...new Set(data.records?.map(r => r.group) || [])]

  return (
    <section className="atlas-section">
      <h2>Gateway atlas — {data.n_records} records</h2>
      <div className="filter-row">
        <select value={metric} onChange={e => setMetric(e.target.value)}>
          <option value="">All metrics</option>
          {metrics.map(m => <option key={m}>{m}</option>)}
        </select>
        <select value={group} onChange={e => setGroup(e.target.value)}>
          <option value="">All groups</option>
          {groups.map(g => <option key={g}>{g}</option>)}
        </select>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Portal</th><th>Metric</th><th>Group</th><th>N</th><th>Mean</th><th>CI lo</th><th>CI hi</th></tr>
          </thead>
          <tbody>
            {records.map((r, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: 12 }}>{r.pair}</td>
                <td style={{ fontSize: 12 }}>{r.metric}</td>
                <td><span className="chip" style={{ background: familyColor(r.group) }}>{r.group}</span></td>
                <td>{r.n_systems}</td>
                <td>{r.mean?.toFixed(3)}</td>
                <td style={{ color: 'var(--muted)', fontSize: 12 }}>{r.ci_lo?.toFixed(3)}</td>
                <td style={{ color: 'var(--muted)', fontSize: 12 }}>{r.ci_hi?.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function Nominations({ data }) {
  const noms = data.nominations || []
  return (
    <section className="atlas-section">
      <h2>Druggable pocket nominations — {data.n_nominations} pockets</h2>
      <div style={{ background: '#fbf2e6', border: '1px solid #e8c99a', borderRadius: 'var(--radius)',
                    padding: '10px 14px', marginBottom: 16, fontSize: 12, color: '#6b4820' }}>
        {data._caveat}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Cluster</th><th>Zone</th><th>Receptors</th><th>Pockets</th><th>Families</th><th>Core</th><th>Mean freq</th></tr>
          </thead>
          <tbody>
            {noms.map((n, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 700, fontFamily: 'monospace' }}>{n.cid}</td>
                <td><span className="pocket-zone">{n.zone}</span></td>
                <td>{n.n_receptors}</td>
                <td>{n.n_pockets}</td>
                <td style={{ fontSize: 11 }}>
                  {Object.entries(typeof n.families === 'string' ? JSON.parse(n.families) : (n.families || {}))
                    .map(([f, c]) => (
                      <span key={f} className="chip" style={{ background: familyColor(f), marginRight: 3 }}>
                        {f}:{c}
                      </span>
                    ))}
                </td>
                <td style={{ fontSize: 11, color: 'var(--muted)', maxWidth: 160,
                             overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                  title={n.core}>{n.core}</td>
                <td>{(n.mean_freq * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function Reorg({ data, navigate }) {
  const comparisons = data.comparisons || []
  return (
    <section className="atlas-section">
      <h2>Within-receptor partner-switching reorganization — {data.n_comparisons} pairs</h2>
      <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 14 }}>
        Receptors with MD data for more than one G-protein partner, showing pocket and gateway
        reorganization across the partner switch.
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Receptor</th>
              <th>UniProt</th>
              <th>Contrast</th>
              <th>Pockets A</th>
              <th>Pockets B</th>
              <th>Union</th>
            </tr>
          </thead>
          <tbody>
            {comparisons.map((c, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600, fontSize: 12 }}>{c.receptor}</td>
                <td style={{ fontFamily: 'monospace', fontSize: 11 }}>
                  <a href={`https://www.uniprot.org/uniprot/${c.uniprot}`} target="_blank" rel="noreferrer">
                    {c.uniprot}
                  </a>
                </td>
                <td>
                  <span className="chip" style={{ background: familyColor(c.famA), marginRight: 4 }}>{c.famA}</span>
                  vs
                  <span className="chip" style={{ background: familyColor(c.famB), marginLeft: 4 }}>{c.famB}</span>
                </td>
                <td>{c.n_pk_A}</td>
                <td>{c.n_pk_B}</td>
                <td>{c.n_union}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function familyColor(f) {
  return { Gi: 'var(--gio)', Gs: 'var(--gs)', Gq: 'var(--gq)', 'G12-13': 'var(--g1213)' }[f] || 'var(--accent)'
}
