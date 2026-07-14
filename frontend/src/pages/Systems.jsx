import { useEffect, useState, useCallback, useMemo } from 'react'
import { api } from '../api'

const PAGE_SIZE = 500
const FAMILIES = ['Gi', 'Gs', 'Gq', 'G12-13']
const GPCR_CLASSES = ['A', 'B']

export default function Systems({ navigate }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  // Filters — synced to URL hash query params
  const [family, setFamily] = useState(null)
  const [search, setSearch] = useState('')
  const [gpcrClass, setGpcrClass] = useState('')
  const [sortKey, setSortKey] = useState('system_id')
  const [sortAsc, setSortAsc] = useState(true)

  // Read initial state from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.split('?')[1] || '')
    if (params.get('family')) setFamily(params.get('family'))
    if (params.get('q')) setSearch(params.get('q'))
    if (params.get('class')) setGpcrClass(params.get('class'))
  }, [])

  // Sync filters to URL
  useEffect(() => {
    const base = '#/systems'
    const params = new URLSearchParams()
    if (family) params.set('family', family)
    if (search) params.set('q', search)
    if (gpcrClass) params.set('class', gpcrClass)
    const qs = params.toString()
    const newHash = qs ? `${base}?${qs}` : base
    if (window.location.hash !== newHash) {
      window.history.replaceState(null, '', newHash)
    }
  }, [family, search, gpcrClass])

  // Fetch all final-release systems in one batch (208 systems; 500 gives headroom).
  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    api.systems({
      family: family || undefined,
      gpcr_class: gpcrClass || undefined,
      limit: PAGE_SIZE,
      offset: 0,
    })
      .then(d => setData(d))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [family, gpcrClass])

  useEffect(() => { load() }, [load])

  function setFilter(key, val) {
    if (key === 'family') setFamily(val)
    if (key === 'search') setSearch(val)
    if (key === 'gpcrClass') setGpcrClass(val)
  }

  function toggleSort(key) {
    if (sortKey === key) {
      setSortAsc(prev => !prev)
    } else {
      setSortKey(key)
      setSortAsc(true)
    }
  }

  const allSystems = data?.systems ?? []
  const total = data?.total ?? 0

  // Client-side free-text search across gene, receptor_name, pdb_id, system_id, ligand
  const filtered = useMemo(() => {
    if (!search) return allSystems
    const q = search.toLowerCase()
    return allSystems.filter(s =>
      (s.receptor_gene || '').toLowerCase().includes(q) ||
      (s.receptor_uniprot || '').toLowerCase().includes(q) ||
      (s.receptor_name || '').toLowerCase().includes(q) ||
      (s.pdb_id || '').toLowerCase().includes(q) ||
      (s.system_id || '').toLowerCase().includes(q) ||
      (s.ligand_name || '').toLowerCase().includes(q) ||
      (s.ligand_chem_id || '').toLowerCase().includes(q) ||
      (s.g_alpha_subtype || '').toLowerCase().includes(q)
    )
  }, [allSystems, search])

  // Client-side sort
  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      let va = a[sortKey], vb = b[sortKey]
      if (typeof va === 'string') va = va.toLowerCase()
      if (typeof vb === 'string') vb = vb.toLowerCase()
      if (va < vb) return sortAsc ? -1 : 1
      if (va > vb) return sortAsc ? 1 : -1
      return 0
    })
  }, [filtered, sortKey, sortAsc])

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
        <span style={{ marginLeft: 8, borderLeft: '1px solid var(--rule)', paddingLeft: 8 }}>
          {GPCR_CLASSES.map(c => (
            <span key={c} className={`family-pill${gpcrClass === c ? ' active' : ''}`}
              onClick={() => setFilter('gpcrClass', gpcrClass === c ? '' : c)}
              style={{ display: 'inline-block', padding: '4px 10px', cursor: 'pointer',
                        fontWeight: gpcrClass === c ? 700 : 400, fontSize: 12 }}>
              Class {c}
            </span>
          ))}
        </span>
      </div>

      <div className="filter-row">
        <input
          placeholder="Search gene, receptor, PDB ID, ligand…"
          value={search}
          onChange={e => setFilter('search', e.target.value)}
          style={{ width: 280 }}
        />
        <select value={gpcrClass} onChange={e => setFilter('gpcrClass', e.target.value)}>
          <option value="">All GPCR classes</option>
          {GPCR_CLASSES.map(c => <option key={c} value={c}>Class {c}</option>)}
        </select>
        {(search || gpcrClass) &&
          <button onClick={() => { setFilter('search', ''); setFilter('gpcrClass', '') }}
            style={{ fontSize: 12, color: 'var(--muted)', background: 'none', border: 'none',
                     cursor: 'pointer', padding: '4px 6px' }}>
            Clear
          </button>
        }
      </div>

      {search && !loading && (
        <p style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>
          {sorted.length} result{sorted.length !== 1 ? 's' : ''} matching "{search}"
        </p>
      )}

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading...</div>}

      {!loading && sorted.length === 0 && <div className="empty">No systems match these filters.</div>}

      {!loading && sorted.length > 0 && (
        <div className="table-wrap">
          <table aria-label="MD systems list">
            <thead>
              <tr>
                <SortHeader col="system_id" sortKey={sortKey} sortAsc={sortAsc} onSort={toggleSort}>System</SortHeader>
                <SortHeader col="pdb_id" sortKey={sortKey} sortAsc={sortAsc} onSort={toggleSort}>PDB</SortHeader>
                <th>Receptor</th>
                <th>UniProt</th>
                <th>Family</th>
                <th>Class</th>
                <th>Ligand</th>
                <SortHeader col="total_sampling_ns" sortKey={sortKey} sortAsc={sortAsc} onSort={toggleSort}>Sampling</SortHeader>
                <th>Provenance</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map(s => (
                <tr key={s.system_id} style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/systems/${s.system_id}`)}>
                  <td><a href={`#/systems/${s.system_id}`} onClick={e => e.preventDefault()}
                    style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: 12 }}>
                    {s.system_id}
                  </a></td>
                  <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{s.pdb_id}</td>
                  <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis',
                               whiteSpace: 'nowrap', fontSize: 12 }}
                    title={s.receptor_name}>{s.receptor_name}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--muted)' }}>
                    {s.receptor_uniprot || '—'}</td>
                  <td><span className="chip" style={{ background: familyColor(s.g_protein_family) }}>
                    {s.g_protein_family}</span></td>
                  <td style={{ fontSize: 11, color: 'var(--muted)' }}>
                    Class {s.gpcr_class || '—'}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--muted)' }}>
                    {s.ligand_chem_id || '—'}</td>
                  <td style={{ whiteSpace: 'nowrap', fontSize: 12 }}>
                    {(s.total_sampling_ns / 1000).toFixed(1)} μs</td>
                  <td><span className={`chip chip-${s.structural_provenance}`} style={{ fontSize: 10 }}>
                    {s.structural_provenance === 'experimental' ? 'exp' : 'eng'}
                  </span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function SortHeader({ col, sortKey, sortAsc, onSort, children }) {
  const active = sortKey === col
  return (
    <th style={{ cursor: 'pointer', userSelect: 'none' }} onClick={() => onSort(col)}>
      {children}
      {active && <span style={{ marginLeft: 4, fontSize: 10 }}>
        {sortAsc ? ' \u25B2' : ' \u25BC'}
      </span>}
    </th>
  )
}

function familyColor(f) {
  return { Gi: 'var(--gio)', Gs: 'var(--gs)', Gq: 'var(--gq)', 'G12-13': 'var(--g1213)' }[f] || 'var(--accent)'
}
