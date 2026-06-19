import { useEffect, useState } from 'react'
import { api } from '../api'

export default function SystemDetail({ id, navigate }) {
  const [sys, setSys] = useState(null)
  const [pockets, setPockets] = useState(null)
  const [gateways, setGateways] = useState(null)
  const [error, setError] = useState(null)
  const [pocketsError, setPocketsError] = useState(null)
  const [gwError, setGwError] = useState(null)
  const [tab, setTab] = useState('pockets')

  useEffect(() => {
    setSys(null); setPockets(null); setGateways(null)
    setError(null); setPocketsError(null); setGwError(null)

    api.system(id)
      .then(s => {
        setSys(s)
        if (s.analysis_available?.pockets_gpcrdb) {
          api.systemPockets(id, true)
            .then(setPockets)
            .catch(e => setPocketsError(e.message))
        }
        if (s.analysis_available?.gateways) {
          api.systemGateways(id)
            .then(setGateways)
            .catch(e => setGwError(e.message))
        }
      })
      .catch(e => setError(e.message))
  }, [id])

  if (error) return <div className="page"><div className="error">{error}</div></div>
  if (!sys) return <div className="page"><div className="loading">Loading...</div></div>

  const fcolor = { Gi: 'var(--gio)', Gs: 'var(--gs)', Gq: 'var(--gq)', 'G12-13': 'var(--g1213)' }[sys.g_protein_family] || 'var(--accent)'

  return (
    <div className="page">
      <div style={{ marginBottom: 8 }}>
        <a href="#/systems" onClick={e => { e.preventDefault(); navigate('/systems') }}
          style={{ fontSize: 13, color: 'var(--muted)' }}>
          ← Systems
        </a>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 14, marginBottom: 6 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.01em', fontFamily: 'monospace' }}>
          {id}
        </h1>
        <span className="chip" style={{ background: fcolor }}>{sys.g_protein_family}</span>
        <span className={`chip chip-${sys.structural_provenance}`} style={{ fontSize: 10 }}>
          {sys.structural_provenance === 'experimental' ? 'experimental' : 'engineered/uncertain'}
        </span>
      </div>
      <p style={{ color: 'var(--muted)', fontSize: 14, marginBottom: 24 }}>
        {sys.receptor_name} ({sys.receptor_gene}) · {sys.g_alpha_subtype}
      </p>

      <div className="detail-grid">
        <div className="detail-card">
          <h3>Receptor</h3>
          <div className="kv"><span className="k">Name</span><span className="v">{sys.receptor_name}</span></div>
          <div className="kv"><span className="k">Gene</span><span className="v">{sys.receptor_gene}</span></div>
          <div className="kv"><span className="k">UniProt</span><span className="v">
            <a href={`https://www.uniprot.org/uniprot/${sys.receptor_uniprot}`} target="_blank" rel="noreferrer">
              {sys.receptor_uniprot}
            </a>
          </span></div>
          <div className="kv"><span className="k">PDB</span><span className="v">
            <a href={`https://www.rcsb.org/structure/${sys.pdb_id}`} target="_blank" rel="noreferrer">
              {sys.pdb_id}
            </a>
          </span></div>
          <div className="kv"><span className="k">Ligand</span>
            <span className="v">{sys.ligand_chem_id ? `${sys.ligand_chem_id} (${sys.ligand_name})` : sys.ligand_name || '—'}</span>
          </div>
        </div>

        <div className="detail-card">
          <h3>Simulation</h3>
          <div className="kv"><span className="k">Replicas</span><span className="v">{sys.n_replicas}</span></div>
          <div className="kv"><span className="k">Length/replica</span><span className="v">{sys.length_per_replica_ns} ns</span></div>
          <div className="kv"><span className="k">Total sampling</span><span className="v">{(sys.total_sampling_ns/1000).toFixed(2)} μs</span></div>
          <div className="kv"><span className="k">Force field</span><span className="v">{sys.force_field}</span></div>
          <div className="kv"><span className="k">Bilayer</span><span className="v">
            {sys.has_bilayer ? `Yes (${sys.lipid_composition})` : 'No (protein-only)'}</span></div>
          <div className="kv"><span className="k">Trajectory type</span><span className="v">{sys.trajectory_type}</span></div>
          <div className="kv"><span className="k">Velocities</span><span className="v">
            <span className={sys.has_velocities ? 'badge-yes' : 'badge-no'}>
              {sys.has_velocities ? 'retained' : 'not retained'}
            </span>
          </span></div>
          <div className="kv"><span className="k">Forces</span><span className="v">
            <span className={sys.has_forces ? 'badge-yes' : 'badge-no'}>
              {sys.has_forces ? 'retained' : 'not retained'}
            </span>
          </span></div>
          <div className="kv"><span className="k">Traj size</span>
            <span className="v">{sys.traj_size_bytes ? (sys.traj_size_bytes/1e9).toFixed(2) + ' GB' : '—'}</span></div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 4, margin: '24px 0 0', borderBottom: '1px solid var(--rule)' }}>
        {['pockets', 'gateways'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{
              padding: '8px 16px', border: 'none', background: 'none', cursor: 'pointer',
              fontWeight: tab === t ? 700 : 400, fontSize: 13,
              borderBottom: tab === t ? '2px solid var(--accent)' : '2px solid transparent',
              color: tab === t ? 'var(--accent)' : 'var(--muted)',
            }}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'pockets' && (
        <div style={{ marginTop: 16 }}>
          {!sys.analysis_available?.pockets_gpcrdb && (
            <div className="empty">No pocket data available for this system.</div>
          )}
          {pocketsError && <div className="error">{pocketsError}</div>}
          {!pockets && sys.analysis_available?.pockets_gpcrdb && !pocketsError &&
            <div className="loading">Loading pockets...</div>}
          {pockets && <PocketTable pockets={pockets} />}
        </div>
      )}

      {tab === 'gateways' && (
        <div style={{ marginTop: 16 }}>
          {sys.trajectory_type === 'protein_only' && (
            <div className="empty">Gateway analysis requires a membrane-embedded trajectory (bilayer present).</div>
          )}
          {gwError && <div className="error">{gwError}</div>}
          {!gateways && sys.analysis_available?.gateways && !gwError &&
            <div className="loading">Loading gateways...</div>}
          {gateways && <GatewayTable records={gateways.records} />}
        </div>
      )}
    </div>
  )
}

function PocketTable({ pockets }) {
  const ps = pockets.pockets || []
  if (!ps.length) return <div className="empty">No pockets detected.</div>
  return (
    <div className="table-wrap">
      <p style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>
        {ps.length} pockets · {pockets.n_frames || '?'} frames · {pockets.n_replicas} replicas
      </p>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Zone</th>
            <th>Mean freq</th>
            <th>Max freq</th>
            <th>Orthosteric</th>
            <th>Voxels</th>
            <th>GPCRdb numbers</th>
          </tr>
        </thead>
        <tbody>
          {ps.map(p => (
            <tr key={p.pocket_id}>
              <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{p.pocket_id}</td>
              <td><span className="pocket-zone">{p.zone || '—'}</span></td>
              <td>{(p.mean_freq * 100).toFixed(1)}%</td>
              <td>{(p.max_freq * 100).toFixed(1)}%</td>
              <td><span className={p.is_orthosteric ? 'badge-yes' : 'badge-no'}>
                {p.is_orthosteric ? 'yes' : '—'}</span></td>
              <td>{p.n_voxels}</td>
              <td style={{ fontSize: 11, color: 'var(--muted)', maxWidth: 200,
                           overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                title={(p.receptor_generic_numbers || []).join('; ')}>
                {(p.receptor_generic_numbers || []).slice(0, 4).join(', ')}
                {(p.receptor_generic_numbers || []).length > 4 ? '…' : ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function GatewayTable({ records }) {
  if (!records?.length) return <div className="empty">No gateway data.</div>
  const byPair = {}
  records.forEach(r => {
    if (!byPair[r.pair]) byPair[r.pair] = []
    byPair[r.pair].push(r)
  })
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Portal</th>
            <th>Metric</th>
            <th>Mean</th>
            <th>95% CI</th>
            <th>Replicas</th>
          </tr>
        </thead>
        <tbody>
          {records.map((r, i) => (
            <tr key={i}>
              <td style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: 12 }}>{r.pair}</td>
              <td style={{ fontSize: 12, color: 'var(--muted)' }}>{r.metric}</td>
              <td>{r.mean?.toFixed(3)}</td>
              <td style={{ fontSize: 12, color: 'var(--muted)' }}>
                [{r.ci_lo?.toFixed(3)}, {r.ci_hi?.toFixed(3)}]</td>
              <td>{r.n_replicas}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
