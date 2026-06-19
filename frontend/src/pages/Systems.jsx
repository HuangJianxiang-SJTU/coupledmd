import { useEffect, useState, useCallback } from 'react'
import { api } from '../api'

const PAGE_SIZE = 50

const FAMILIES = ['Gi', 'Gs', 'Gq', 'G12-13']

export default function Systems({ navigate }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [family, setFamily] = useState(null)
  const [gene, setGene] = useState('')
  const [trajType, setTrajType] = useState('')
  const [page, setPage] = useState(0)

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    api.systems({
      family: family || undefined,
      gene: gene || undefined,
      trajectory_type: trajType || undefined,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
    })
      .then(d => setData(d))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [family, gene, trajType, page])

  useEffect(() => { load() }, [load])

  function setFilter(key, val) {
    setPage(0)
    if (key === 'family') setFamily(val)
    if (key === 'gene') setGene(val)
    if (key === 'trajType') setTrajType(val)
  }

  const systems = data?.systems ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="page">
      <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 20 }}>Systems</h1>

      <div className="family-row">
        <div className={`family-pill${!family ? ' active' : ''}`} onClick={() => setFilter('family', null)}>
          All <strong>{!data ? '' : total}</strong>
        </div>
        {FAMILIES.map(f => (
          <div key={f} className={`family-pill${family === f ? ' active' : ''}`}
            onClick={() => setFilter('family', family === f ? null : f)}>
            <span className="chip" style={{ background: familyColor(f) }}>{f}</span>
          </div>
        ))}
      </div>

      <div className="filter-row">
        <input
          placeholder="Gene name (e.g. ADRB2)"
          value={gene}
          onChange={e => setFilter('gene', e.target.value)}
          style={{ width: 200 }}
        />
        <select value={trajType} onChange={e => setFilter('trajType', e.target.value)}>
          <option value="">All trajectory types</option>
          <option value="membrane_embedded">Membrane-embedded</option>
          <option value="protein_only">Protein-only</option>
        </select>
        {(gene || trajType) &&
          <button onClick={() => { setFilter('gene', ''); setFilter('trajType', '') }}
            style={{ fontSize: 12, color: 'var(--muted)', background: 'none', border: 'none',
                     cursor: 'pointer', padding: '4px 6px' }}>
            Clear
          </button>
        }
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading...</div>}

      {!loading && systems.length === 0 && <div className="empty">No systems match these filters.</div>}

      {!loading && systems.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>System</th>
                <th>PDB</th>
                <th>Receptor</th>
                <th>Gene</th>
                <th>Family</th>
                <th>Ligand</th>
                <th>Sampling</th>
                <th>Type</th>
                <th>Provenance</th>
              </tr>
            </thead>
            <tbody>
              {systems.map(s => (
                <tr key={s.system_id} style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/systems/${s.system_id}`)}>
                  <td><a href={`#/systems/${s.system_id}`} onClick={e => e.preventDefault()}
                    style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: 12 }}>
                    {s.system_id}
                  </a></td>
                  <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{s.pdb_id}</td>
                  <td style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis',
                               whiteSpace: 'nowrap', fontSize: 12 }}
                    title={s.receptor_name}>{s.receptor_name}</td>
                  <td style={{ fontWeight: 600, fontSize: 12 }}>{s.receptor_gene}</td>
                  <td><span className="chip" style={{ background: familyColor(s.g_protein_family) }}>
                    {s.g_protein_family}</span></td>
                  <td style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--muted)' }}>
                    {s.ligand_chem_id || '—'}</td>
                  <td style={{ whiteSpace: 'nowrap', fontSize: 12 }}>
                    {(s.total_sampling_ns / 1000).toFixed(1)} μs</td>
                  <td style={{ fontSize: 11, color: 'var(--muted)' }}>
                    {s.trajectory_type === 'membrane_embedded' ? 'bilayer' : 'protein'}</td>
                  <td><span className={`chip chip-${s.structural_provenance}`} style={{ fontSize: 10 }}>
                    {s.structural_provenance === 'experimental' ? 'exp' : 'eng'}
                  </span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="pager">
          <button disabled={page === 0} onClick={() => setPage(p => p - 1)}>Prev</button>
          <span className="info">Page {page + 1} of {totalPages} ({total} systems)</span>
          <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}>Next</button>
        </div>
      )}
    </div>
  )
}

function familyColor(f) {
  return { Gi: 'var(--gio)', Gs: 'var(--gs)', Gq: 'var(--gq)', 'G12-13': 'var(--g1213)' }[f] || 'var(--accent)'
}
