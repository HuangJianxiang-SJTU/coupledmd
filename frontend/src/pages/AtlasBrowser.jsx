import { useEffect, useState } from 'react'
import { api } from '../api'

const TABS = ['druggable_pockets', 'gateways', 'nominations', 'reorg', 'coupling_geometry']
const TAB_LABELS = {
  druggable_pockets: 'Druggable pockets',
  gateways: 'Gateway atlas',
  nominations: 'Nominations',
  reorg: 'Reorganization',
  coupling_geometry: 'Coupling Geometry',
}

/** Robustly parse a families/zones field that may be:
 *  - a proper JS object already
 *  - a JSON string with double quotes
 *  - a Python dict string with single quotes
 */
function parseDict(val) {
  if (!val) return {}
  if (typeof val === 'object') return val
  if (typeof val === 'string') {
    try { return JSON.parse(val) }
    catch {
      // Python dict with single quotes — convert to valid JSON
      try { return JSON.parse(val.replace(/'/g, '"')) }
      catch { return {} }
    }
  }
  return {}
}

/** Parse core_generic_numbers which may be an array or a semicolon-separated string */
function parseGenerics(val) {
  if (!val) return []
  if (Array.isArray(val)) return val
  if (typeof val === 'string') return val.split(';').map(s => s.trim()).filter(Boolean)
  return []
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
      coupling_geometry: api.couplingGeometry,
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
      {!loading && !error && tab === 'coupling_geometry' && data[tab] &&
        <CouplingAtlas data={data[tab]} />}
    </div>
  )
}

/* ---- CSV export helper ---- */
function exportCSV(filename, rows, headers) {
  const escape = v => {
    const s = v == null ? '' : String(v)
    return s.includes(',') || s.includes('"') || s.includes('\n')
      ? '"' + s.replace(/"/g, '""') + '"'
      : s
  }
  const lines = [headers.map(escape).join(',')]
  rows.forEach(row => {
    lines.push(headers.map(h => escape(row[h])).join(','))
  })
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

/* ---- Export button component ---- */
function ExportButton({ label, onClick }) {
  return (
    <button onClick={onClick}
      style={{
        fontSize: 11, fontWeight: 600, color: 'var(--muted)', background: '#fff',
        border: '1px solid var(--rule)', borderRadius: 4, padding: '3px 10px',
        cursor: 'pointer', marginLeft: 8,
      }}>
      {label || 'Export CSV'}
    </button>
  )
}

/* ---- Horizontal bar chart ---- */
function HBarChart({ items, maxVal, barColor, labelWidth }) {
  if (!items.length) return null
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {items.map(item => {
        const barW = (item.value / maxVal) * 100
        return (
          <div key={item.key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: labelWidth || 70, flexShrink: 0, fontSize: 11, fontFamily: 'monospace',
                           color: 'var(--muted)', textAlign: 'right', overflow: 'hidden',
                           textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
              title={item.label}>
              {item.label}
            </span>
            <div style={{ flex: 1, height: 18, background: 'var(--panel)', borderRadius: 3,
                          position: 'relative', overflow: 'hidden' }}>
              <div style={{
                width: `${barW}%`, height: '100%', borderRadius: 3,
                background: barColor || 'var(--accent)', transition: 'width 0.3s ease',
              }} />
            </div>
            <span style={{
              flexShrink: 0, fontSize: 11, fontWeight: 600, color: 'var(--ink)',
              minWidth: 48, textAlign: 'left',
            }}>
              {item.display}
            </span>
          </div>
        )
      })}
    </div>
  )
}

/* ---- Druggable pockets ---- */
function DrugPocketTable({ data, navigate }) {
  const clustersRaw = data.clusters || []
  // Sort by mean_freq descending
  const clusters = [...clustersRaw].sort((a, b) => b.mean_freq - a.mean_freq)
  const maxFreq = Math.max(...clusters.map(c => c.mean_freq), 0.01)

  return (
    <section className="atlas-section">
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <h2>Consensus druggable pocket atlas &mdash; {clusters.length} clusters</h2>
        <ExportButton label="CSV" onClick={() => exportCSV('druggable_pockets.csv', clusters, [
          'consensus_id', 'n_systems', 'n_receptors', 'families', 'zones',
          'mean_freq', 'core_generic_numbers',
        ])} />
      </div>
      <p style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 12 }}>
        Druggable pockets are cavities on the receptor surface that can accommodate small-molecule ligands.
        Clusters group pockets with shared residue positions across systems.
        <strong>Mean freq</strong> = fraction of systems in the cluster where the pocket is present (0–100%).
        <strong>Core generics</strong> = GPCRdb generic numbers of the most conserved lining residues.
      </p>

      {/* Frequency bar chart */}
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase',
                     letterSpacing: '0.08em', marginBottom: 8 }}>
          Cluster mean frequency
        </h3>
        <HBarChart
          items={clusters.map(c => ({
            key: c.consensus_id,
            label: String(c.consensus_id),
            value: c.mean_freq,
            display: (c.mean_freq * 100).toFixed(1) + '%',
          }))}
          maxVal={maxFreq}
          barColor="var(--accent)"
          labelWidth={90}
        />
      </div>

      <div className="table-wrap">
        <table aria-label="Druggable pocket clusters">
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
              const families = parseDict(c.families)
              const zones = parseDict(c.zones)
              const core = parseGenerics(c.core_generic_numbers)
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
                    title={core.join('; ')}>
                    {core.slice(0, 4).join(', ')}{core.length > 4 ? '…' : ''}
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

/* ---- Gateway atlas ---- */
function GatewayAtlas({ data }) {
  const [metric, setMetric] = useState('')
  const [group, setGroup] = useState('')
  const [pairFilter, setPairFilter] = useState('')

  const allRecords = data.records || []
  const metrics = [...new Set(allRecords.map(r => r.metric))]
  const groups = [...new Set(allRecords.map(r => r.group))]
  const pairs = [...new Set(allRecords.map(r => r.pair))].sort()

  const records = allRecords
    .filter(r => !metric || r.metric === metric)
    .filter(r => !group || r.group === group)
    .filter(r => !pairFilter || r.pair === pairFilter)

  // Build chart data: occupancy by pair, grouped by family
  // Only show chart when a specific metric is selected (not "All metrics")
  const showChart = metric !== '' && metric === 'occupancy'
  const occByPair = {}
  records.filter(r => r.metric === 'occupancy').forEach(r => {
    if (!occByPair[r.pair]) occByPair[r.pair] = []
    occByPair[r.pair].push(r)
  })
  const chartPairs = Object.keys(occByPair).sort()
  const maxOcc = Math.max(...records.filter(r => r.metric === 'occupancy').map(r => r.mean), 0.01)

  return (
    <section className="atlas-section">
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <h2>Gateway atlas &mdash; {data.n_records} records</h2>
        <ExportButton label="CSV" onClick={() => exportCSV('gateways.csv', records, [
          'pair', 'metric', 'group', 'n_systems', 'mean', 'ci_lo', 'ci_hi',
        ])} />
      </div>
      <div className="filter-row">
        <select value={pairFilter} onChange={e => setPairFilter(e.target.value)}>
          <option value="">All portals</option>
          {pairs.map(p => <option key={p}>{p}</option>)}
        </select>
        <select value={metric} onChange={e => setMetric(e.target.value)}>
          <option value="">All metrics</option>
          {metrics.map(m => <option key={m}>{m}</option>)}
        </select>
        <select value={group} onChange={e => setGroup(e.target.value)}>
          <option value="">All groups</option>
          {groups.map(g => <option key={g}>{g}</option>)}
        </select>
        {(metric || group || pairFilter) && (
          <button onClick={() => { setMetric(''); setGroup(''); setPairFilter('') }}
            style={{ fontSize: 12, color: 'var(--muted)', background: 'none', border: 'none',
                     cursor: 'pointer', padding: '4px 6px' }}>
            Clear
          </button>
        )}
      </div>

      {/* Occupancy bar chart — only when occupancy metric is explicitly selected */}
      {showChart && chartPairs.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase',
                       letterSpacing: '0.08em', marginBottom: 8 }}>
            Gateway occupancy by TM portal
          </h3>
          {chartPairs.map(pair => {
            const groupRecords = occByPair[pair]
            return (
              <div key={pair} style={{ marginBottom: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ width: 70, flexShrink: 0, fontSize: 11, fontFamily: 'monospace',
                                 color: 'var(--muted)', textAlign: 'right' }}>
                    {pair}
                  </span>
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {groupRecords.map(r => {
                      const barW = (r.mean / maxOcc) * 100
                      return (
                        <div key={r.group} style={{ height: 14, background: 'var(--panel)', borderRadius: 2,
                                                    position: 'relative', overflow: 'hidden' }}>
                          <div style={{
                            width: `${barW}%`, height: '100%', borderRadius: 2,
                            background: familyColor(r.group), transition: 'width 0.3s ease',
                          }} />
                          <span style={{
                            position: 'absolute', right: 4, top: '50%', transform: 'translateY(-50%)',
                            fontSize: 9, fontWeight: 700, color: barW > 20 ? '#fff' : 'var(--ink)',
                          }}>
                            {r.group} {r.mean?.toFixed(2)}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <p style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 12 }}>
        Bilayer gateways are inter-helical portals at TM interfaces that allow water or lipid penetration.
        <strong>Occupancy</strong> = fraction of frames where the portal is open (0–100%).
        <strong>Open fraction</strong> = mean open time per opening event.
        <strong>Penetration</strong> = mean depth of water/lipid intrusion (Å).
        Values are per-group means with 95% confidence intervals (CI).
      </p>

      <div className="table-wrap">
        <table aria-label="Gateway atlas data">
          <thead>
            <tr><th>Portal</th><th>Metric</th><th>Group</th><th>N systems</th><th>Mean</th><th>CI low</th><th>CI high</th></tr>
          </thead>
          <tbody>
            {records.map((r, i) => {
              const isProportion = r.metric === 'occupancy' || r.metric === 'open_fraction'
              const fmt = v => {
                if (v == null) return '—'
                return isProportion ? `${(v * 100).toFixed(1)}%` : r.metric === 'penetration' || r.metric === 'penetration_p90' ? `${v.toFixed(2)} Å` : v.toFixed(3)
              }
              return (
                <tr key={i}>
                  <td style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: 12 }}>{r.pair}</td>
                  <td style={{ fontSize: 12 }}>{r.metric}</td>
                  <td><span className="chip" style={{ background: familyColor(r.group) }}>{r.group}</span></td>
                  <td>{r.n_systems}</td>
                  <td>{fmt(r.mean)}</td>
                  <td style={{ color: 'var(--muted)', fontSize: 12 }}>{fmt(r.ci_lo)}</td>
                  <td style={{ color: 'var(--muted)', fontSize: 12 }}>{fmt(r.ci_hi)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}

/* ---- Nominations ---- */
function Nominations({ data }) {
  const noms = data.nominations || []
  const maxFreq = Math.max(...noms.map(n => n.mean_freq), 0.01)

  return (
    <section className="atlas-section">
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <h2>Druggable pocket nominations &mdash; {data.n_nominations} pockets</h2>
        <ExportButton label="CSV" onClick={() => exportCSV('nominations.csv', noms, [
          'cid', 'zone', 'n_receptors', 'n_pockets', 'families', 'core', 'mean_freq',
        ])} />
      </div>
      <p style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 12 }}>
        Nominated pockets are the most promising druggable sites, selected by cross-system frequency
        and receptor diversity. Each nomination represents a cluster of pockets sharing a druggable zone.
      </p>
      <div style={{ background: '#fbf2e6', border: '1px solid #e8c99a', borderRadius: 'var(--radius)',
                    padding: '10px 14px', marginBottom: 16, fontSize: 12, color: '#6b4820' }}>
        {data._caveat}
      </div>

      {/* Frequency bar chart */}
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase',
                     letterSpacing: '0.08em', marginBottom: 8 }}>
          Nomination frequency
        </h3>
        <HBarChart
          items={noms.map(n => ({
            key: n.cid,
            label: String(n.cid),
            value: n.mean_freq,
            display: (n.mean_freq * 100).toFixed(1) + '%',
          }))}
          maxVal={maxFreq}
          barColor="var(--gio)"
          labelWidth={90}
        />
      </div>

      <div className="table-wrap">
        <table aria-label="Druggable pocket nominations">
          <thead>
            <tr><th>Cluster</th><th>Zone</th><th>Receptors</th><th>Pockets</th><th>Families</th><th>Core</th><th>Mean freq</th></tr>
          </thead>
          <tbody>
            {noms.map((n, i) => {
              const families = parseDict(n.families)
              return (
                <tr key={i}>
                  <td style={{ fontWeight: 700, fontFamily: 'monospace' }}>{n.cid}</td>
                  <td><span className="pocket-zone">{n.zone}</span></td>
                  <td>{n.n_receptors}</td>
                  <td>{n.n_pockets}</td>
                  <td style={{ fontSize: 11 }}>
                    {Object.entries(families).map(([f, c]) => (
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
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}

/* ---- Reorg ---- */
function Reorg({ data, navigate }) {
  const comparisons = data.comparisons || []
  return (
    <section className="atlas-section">
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <h2>Within-receptor partner-switching reorganization &mdash; {data.n_comparisons} pairs</h2>
        <ExportButton label="CSV" onClick={() => exportCSV('reorg.csv', comparisons, [
          'receptor', 'uniprot', 'famA', 'famB', 'sid_A', 'sid_B', 'n_pk_A', 'n_pk_B', 'n_union',
        ])} />
      </div>
      <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 14 }}>
        Receptors with MD data for more than one G-protein partner, showing pocket and gateway
        reorganization across the partner switch. <strong>Pockets A/B</strong> = number of druggable pockets
        for each partner; <strong>Union</strong> = total unique pockets across both. Click a row to compare on the <a href="#/compare">Compare</a> page.
      </p>
      <div className="table-wrap">
        <table aria-label="Partner-switching reorganization comparisons">
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
              <tr key={i} style={{ cursor: 'pointer' }}
                onClick={() => { window.location.hash = `/compare?receptor=${encodeURIComponent(c.receptor)}` }}>
                <td style={{ fontWeight: 600, fontSize: 12 }}>{c.receptor}</td>
                <td style={{ fontFamily: 'monospace', fontSize: 11 }}>
                  <a href={`https://www.uniprot.org/uniprot/${c.uniprot}`} target="_blank" rel="noreferrer"
                    onClick={e => e.stopPropagation()}>
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

const FAM_COLOR_HEX = { Gi: '#4e9af1', Gs: '#e8a838', Gq: '#e05c5c', 'G12-13': '#9b59b6' }

function CouplingAtlas({ data }) {
  const [hovered, setHovered] = useState(null)
  const records = data.records || []
  const sorted = [...records].sort((a, b) => a.func_rank - b.func_rank)

  const X_MIN = 25, X_MAX = 75, Y_MIN = 15, Y_MAX = 60
  const W = 480, H = 300
  const PAD = { top: 20, right: 20, bottom: 40, left: 50 }
  const plotW = W - PAD.left - PAD.right
  const plotH = H - PAD.top - PAD.bottom

  const xScale = v => PAD.left + ((v - X_MIN) / (X_MAX - X_MIN)) * plotW
  const yScale = v => PAD.top + ((Y_MAX - v) / (Y_MAX - Y_MIN)) * plotH

  const xTicks = [25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75]
  const yTicks = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60]

  return (
    <section className="atlas-section">
      <h2>Coupling geometry atlas &mdash; {data.n_records} systems</h2>

      <div style={{ overflowX: 'auto', marginBottom: 16 }}>
        <svg width={W} height={H} style={{ display: 'block', fontFamily: 'sans-serif' }}>
          {xTicks.map(v => (
            <g key={v}>
              <line x1={xScale(v)} y1={PAD.top} x2={xScale(v)} y2={PAD.top + plotH}
                stroke="#e5e5e5" strokeWidth={1} />
              <text x={xScale(v)} y={PAD.top + plotH + 14} textAnchor="middle"
                fontSize={10} fill="#888">{v}</text>
            </g>
          ))}
          {yTicks.map(v => (
            <g key={v}>
              <line x1={PAD.left} y1={yScale(v)} x2={PAD.left + plotW} y2={yScale(v)}
                stroke="#e5e5e5" strokeWidth={1} />
              <text x={PAD.left - 6} y={yScale(v) + 4} textAnchor="end"
                fontSize={10} fill="#888">{v}</text>
            </g>
          ))}
          <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + plotH}
            stroke="#ccc" strokeWidth={1} />
          <line x1={PAD.left} y1={PAD.top + plotH} x2={PAD.left + plotW} y2={PAD.top + plotH}
            stroke="#ccc" strokeWidth={1} />
          <text x={PAD.left + plotW / 2} y={H - 4} textAnchor="middle" fontSize={11} fill="#555">
            Tilt angle (°)
          </text>
          <text x={12} y={PAD.top + plotH / 2} textAnchor="middle" fontSize={11} fill="#555"
            transform={`rotate(-90, 12, ${PAD.top + plotH / 2})`}>
            Depth (Å)
          </text>
          {records.map(r => (
            <circle
              key={r.system}
              cx={xScale(r.f01_tilt)}
              cy={yScale(r.f06_depth)}
              r={6}
              fill={FAM_COLOR_HEX[r.g_family] || '#888'}
              fillOpacity={hovered === r.system ? 1 : 0.75}
              stroke={hovered === r.system ? '#222' : 'none'}
              strokeWidth={1.5}
              style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHovered(r.system)}
              onMouseLeave={() => setHovered(null)}
            />
          ))}
          {hovered && (() => {
            const r = records.find(x => x.system === hovered)
            if (!r) return null
            const cx = xScale(r.f01_tilt)
            const cy = yScale(r.f06_depth)
            const tx = cx + 10
            const ty = cy - 10
            const label = `${r.receptor} (${r.g_family}) tilt=${r.f01_tilt.toFixed(1)}° depth=${r.f06_depth.toFixed(1)}Å`
            return (
              <g>
                <rect x={tx - 2} y={ty - 12} width={label.length * 5.6 + 8} height={16}
                  fill="rgba(30,30,30,0.85)" rx={3} />
                <text x={tx + 2} y={ty} fontSize={10} fill="#fff">{label}</text>
              </g>
            )
          })()}
        </svg>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        {Object.entries(FAM_COLOR_HEX).map(([f, c]) => (
          <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />
            <span style={{ fontSize: 12, color: 'var(--muted)' }}>{f}</span>
          </div>
        ))}
      </div>

      <div className="table-wrap">
        <table aria-label="Coupling geometry ranked table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Receptor</th>
              <th>Family</th>
              <th>Tilt°</th>
              <th>Depth Å</th>
              <th>SASA</th>
              <th>Hook°</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(r => (
              <tr key={r.system}>
                <td style={{ fontWeight: 700 }}>{r.func_rank}</td>
                <td style={{ fontWeight: 600 }}>{r.receptor}</td>
                <td>
                  <span className="chip" style={{ background: familyColor(r.g_family) }}>{r.g_family}</span>
                </td>
                <td>{r.f01_tilt?.toFixed(1)}</td>
                <td>{r.f06_depth?.toFixed(1)}</td>
                <td>{r.f04_sasa?.toFixed(3)}</td>
                <td>{r.f02_hook?.toFixed(1)}</td>
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
