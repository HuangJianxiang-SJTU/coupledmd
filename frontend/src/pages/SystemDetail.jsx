import { useEffect, useState } from 'react'
import { api } from '../api'
import TrajectoryViewer from '../components/TrajectoryViewer'
import Flareplot from '../components/Flareplot'

const BASE = import.meta.env.VITE_API_BASE || ''

export default function SystemDetail({ id, navigate }) {
  const [sys, setSys] = useState(null)
  const [pockets, setPockets] = useState(null)
  const [gateways, setGateways] = useState(null)
  const [gprotein, setGprotein] = useState(null)
  const [vizMeta, setVizMeta] = useState(null)
  const [error, setError] = useState(null)
  const [pocketsError, setPocketsError] = useState(null)
  const [gwError, setGwError] = useState(null)
  const [gpError, setGpError] = useState(null)
  const [tab, setTab] = useState('pockets')
  const [highlightPocket, setHighlightPocket] = useState(null)
  const [highlightGprotein, setHighlightGprotein] = useState(null)
  const [highlightResidue, setHighlightResidue] = useState(null)
  const [subunitRanges, setSubunitRanges] = useState(null)

  useEffect(() => {
    setSys(null); setPockets(null); setGateways(null); setGprotein(null); setVizMeta(null)
    setError(null); setPocketsError(null); setGwError(null); setGpError(null)
    setSubunitRanges(null)
    setHighlightPocket(null); setHighlightGprotein(null); setHighlightResidue(null)

    api.system(id)
      .then(s => {
        setSys(s)
        if (s.analysis_available?.pockets_gpcrdb || s.analysis_available?.pockets) {
          api.systemPockets(id, !!s.analysis_available?.pockets_gpcrdb)
            .then(setPockets)
            .catch(e => setPocketsError(e.message))
        }
        if (s.analysis_available?.gateways) {
          api.systemGateways(id)
            .then(setGateways)
            .catch(e => setGwError(e.message))
        }
        api.vizMeta(id).then(setVizMeta).catch(() => {})
        // Fetch subunit ranges for NGL coloring (lightweight endpoint)
        api.systemSubunitRanges(id)
          .then(data => {
            if (data.subunit_ranges && Object.keys(data.subunit_ranges).length > 0) {
              setSubunitRanges(data.subunit_ranges)
            }
          })
          .catch(() => {})
      })
      .catch(e => setError(e.message))
  }, [id])

  useEffect(() => {
    if (tab !== 'gprotein' || gprotein || gpError) return
    api.systemGprotein(id)
      .then(setGprotein)
      .catch(e => setGpError(e.message))
  }, [tab, id])

  if (error) return <div className="page-wide"><div className="error">{error}</div></div>
  if (!sys) return <div className="page-wide"><div className="loading">Loading...</div></div>

  const fcolor = { Gi: 'var(--gio)', Gs: 'var(--gs)', Gq: 'var(--gq)', 'G12-13': 'var(--g1213)' }[sys.g_protein_family] || 'var(--accent)'

  const nPockets = pockets?.pockets?.length ?? null
  const nGateways = gateways?.records?.length ?? null
  const nFrames = vizMeta?.viz_files?.traj_xtc?.n_frames ?? null
  const nAtoms = vizMeta?.viz_files?.structure_pdb?.n_atoms ?? null

  return (
    <div className="page-wide">
      <div style={{ marginBottom: 8 }}>
        <a href="#/systems" onClick={e => { e.preventDefault(); navigate('/systems') }}
          style={{ fontSize: 13, color: 'var(--muted)' }}>
          &larr; Systems
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
        {[
          sys.receptor_name,
          sys.receptor_gene ? `(${sys.receptor_gene})` : null,
          sys.g_alpha_subtype,
        ].filter(Boolean).join(' · ')}
      </p>

      {/* Summary stats bar */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
        <SummaryPill label="Sampling" value={`${(sys.total_sampling_ns/1000).toFixed(1)} μs`} />
        <SummaryPill label="Replicas" value={sys.n_replicas} />
        <SummaryPill label="Force field" value="CHARMM36" />
        <SummaryPill label="Type" value="Bilayer" />
        {nPockets !== null && <SummaryPill label="Pockets" value={nPockets} />}
        {nGateways !== null && <SummaryPill label="Gateways" value={nGateways} />}
        {nFrames !== null && <SummaryPill label="Frames" value={nFrames} />}
        {nAtoms !== null && <SummaryPill label="Atoms" value={nAtoms?.toLocaleString()} />}
      </div>

      <div className="detail-grid">
        <div className="detail-card">
          <h3>Receptor</h3>
          <div className="kv"><span className="k">Name</span><span className="v">{sys.receptor_name || '—'}</span></div>
          <div className="kv"><span className="k">Gene</span><span className="v">{sys.receptor_gene || '—'}</span></div>
          <div className="kv"><span className="k">UniProt</span><span className="v">
            {sys.receptor_uniprot
              ? <a href={`https://www.uniprot.org/uniprot/${sys.receptor_uniprot}`} target="_blank" rel="noreferrer">
                  {sys.receptor_uniprot}
                </a>
              : '—'}
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
            {sys.lipid_composition || 'Yes'}</span></div>
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

      {/* Download buttons */}
      {vizMeta && (
        <div style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <DownloadButton
              label="Structure (PDB)"
              href={`${BASE}/api/v1/systems/${id}/viz/structure`}
              filename={`${id}_structure.pdb`}
            />
            <DownloadButton
              label="Trajectory (XTC)"
              href={`${BASE}/api/v1/systems/${id}/viz/trajectory`}
              filename={`${id}_traj.xtc`}
              sizeMB={vizMeta.viz_files?.traj_xtc?.size_bytes
                ? (vizMeta.viz_files.traj_xtc.size_bytes / 1e6).toFixed(1) : null}
            />
          </div>
          <p style={{ fontSize: 10, color: 'var(--faint)', marginTop: 6 }}>
            Data: CC-BY-4.0 &middot; Please cite: Huang J et al., CoupledMD: a web resource for GPCR–G-protein molecular dynamics. Citation details to be confirmed (pre-publication)
          </p>
        </div>
      )}

      {/* 3D structure viewer + Flareplot — side by side, full width */}
      <div style={{ marginTop: 16, display: 'flex', gap: 16, alignItems: 'stretch' }}>
        <div style={{ flex: '1 1 50%', minWidth: 0 }}>
          <TrajectoryViewer systemId={id} highlightPocket={highlightPocket} highlightGprotein={highlightGprotein} highlightResidue={highlightResidue} family={sys.g_protein_family} subunitRanges={subunitRanges} />
        </div>
        <div style={{ flex: '1 1 50%', border: '1px solid var(--rule)', borderRadius: 8, padding: 12, background: 'var(--panel)' }}>
          <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase',
                       letterSpacing: '0.08em', marginBottom: 8 }}>
            Interaction Network
          </h3>
          <Flareplot systemId={id} family={sys.g_protein_family} onResidueClick={(rid) => setHighlightResidue(rid)} />
        </div>
      </div>

      <div style={{ display: 'flex', gap: 4, margin: '24px 0 0', borderBottom: '1px solid var(--rule)' }}>
        {[['pockets', 'Pockets'], ['gateways', 'Gateways'], ['gprotein', 'G-protein']].map(([t, label]) => (
          <button key={t} onClick={() => setTab(t)}
            style={{
              padding: '8px 16px', border: 'none', background: 'none', cursor: 'pointer',
              fontWeight: tab === t ? 700 : 400, fontSize: 13,
              borderBottom: tab === t ? '2px solid var(--accent)' : '2px solid transparent',
              color: tab === t ? 'var(--accent)' : 'var(--muted)',
            }}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'pockets' && (
        <div style={{ marginTop: 16 }}>
          {!(sys.analysis_available?.pockets_gpcrdb || sys.analysis_available?.pockets) && (
            <div className="empty">No pocket data available for this system.</div>
          )}
          {pocketsError && <div className="error">{pocketsError}</div>}
          {!pockets && (sys.analysis_available?.pockets_gpcrdb || sys.analysis_available?.pockets) && !pocketsError &&
            <div className="loading">Loading pockets...</div>}
          {pockets && <PocketSection pockets={pockets} onHighlight={setHighlightPocket} highlightPocket={highlightPocket} />}
        </div>
      )}

      {tab === 'gateways' && (
        <div style={{ marginTop: 16 }}>
          {!sys.analysis_available?.gateways && (
            <div className="empty">Gateway analysis not yet computed for this system.</div>
          )}
          {gwError && <div className="error">{gwError}</div>}
          {!gateways && sys.analysis_available?.gateways && !gwError &&
            <div className="loading">Loading gateways...</div>}
          {gateways && <GatewaySection records={gateways.records} />}
        </div>
      )}

      {tab === 'gprotein' && (
        <div style={{ marginTop: 16 }}>
          {gpError && <div className="error">{gpError}</div>}
          {!gprotein && !gpError && <div className="loading">Loading G-protein data...</div>}
          {gprotein && <GproteinSection data={gprotein} highlightGprotein={highlightGprotein} onHighlight={setHighlightGprotein} />}
        </div>
      )}
    </div>
  )
}

function SummaryPill({ label, value }) {
  return (
    <div style={{
      border: '1px solid var(--rule)', borderRadius: 6, padding: '6px 12px',
      display: 'flex', alignItems: 'baseline', gap: 6,
    }}>
      <span style={{ fontSize: 11, color: 'var(--faint)', fontWeight: 600, textTransform: 'uppercase',
                     letterSpacing: '0.05em' }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--ink)' }}>{value}</span>
    </div>
  )
}

function DownloadButton({ label, href, filename, sizeMB }) {
  return (
    <a href={href} download={filename}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '6px 14px', borderRadius: 6, border: '1px solid var(--rule)',
        background: '#fff', color: 'var(--ink)', fontSize: 12, fontWeight: 600,
        textDecoration: 'none', cursor: 'pointer',
      }}>
      <span style={{ fontSize: 14 }}>&#8595;</span>
      {label}
      {sizeMB && <span style={{ color: 'var(--faint)', fontWeight: 400 }}>{sizeMB} MB</span>}
    </a>
  )
}

/* ---- Pocket section with frequency bar chart + table ---- */
function PocketSection({ pockets, onHighlight, highlightPocket }) {
  const ps = pockets.pockets || []
  if (!ps.length) return <div className="empty">No pockets detected.</div>

  const maxFreq = Math.max(...ps.map(p => p.mean_freq), 0.01)

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>
        {ps.length} pockets &middot; {pockets.n_frames || '?'} frames &middot; {pockets.n_replicas} replicas
        {highlightPocket != null && (
          <span style={{ marginLeft: 12 }}>
            Pocket {highlightPocket} highlighted —{' '}
            <a href="#/systems" onClick={e => { e.preventDefault(); onHighlight(null) }}
              style={{ color: 'var(--accent)', cursor: 'pointer' }}>clear</a>
          </span>
        )}
      </p>

      {/* Frequency bar chart */}
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase',
                     letterSpacing: '0.08em', marginBottom: 8 }}>
          Pocket occupancy frequency
          <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: 'normal',
                         marginLeft: 8, fontSize: 11 }}>
            Click a pocket to highlight on 3D structure
          </span>
        </h3>
        {/* Location legend */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 6 }}>
          {[...new Set(ps.map(pocketLabel).filter(Boolean))].sort().map(lbl => (
            <span key={lbl} style={{ fontSize: 10, color: 'var(--muted)', display: 'inline-flex', alignItems: 'center', gap: 3 }}>
              <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: zoneBarColor(pocketLabelToZone(lbl)) }} />
              {lbl}
            </span>
          ))}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 3, maxWidth: 460 }}>
          {ps.map(p => {
            const pct = p.mean_freq * 100
            const barW = (p.mean_freq / maxFreq) * 100
            const zoneColor = zoneBarColor(p.zone)
            const lbl = pocketLabel(p)
            return (
              <div key={p.pocket_id}
                onClick={() => onHighlight(highlightPocket === p.pocket_id ? null : p.pocket_id)}
                style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer',
                         background: highlightPocket === p.pocket_id ? 'var(--panel)' : 'transparent',
                         borderRadius: 3, padding: '1px 4px' }}>
                <span style={{ width: 40, flexShrink: 0, fontSize: 11, fontFamily: 'monospace',
                               color: 'var(--muted)', textAlign: 'right' }}>
                  {p.pocket_id}
                </span>
                <div style={{ flex: 1, height: 16, background: 'var(--panel)', borderRadius: 3,
                              position: 'relative', overflow: 'hidden' }}>
                  <div style={{
                    width: `${barW}%`, height: '100%', borderRadius: 3,
                    background: zoneColor, transition: 'width 0.3s ease',
                  }} />
                </div>
                <span style={{ flexShrink: 0, width: 56, textAlign: 'right', fontSize: 10,
                               fontWeight: 700, color: 'var(--ink)' }}>
                  {pct.toFixed(1)}%
                </span>
                <span style={{ flexShrink: 0, width: 150, fontSize: 10, color: 'var(--muted)' }}>
                  {lbl || '—'}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Detail table */}
      <div className="table-wrap">
        <table aria-label="Pocket data for this system">
          <thead>
            <tr>
              <th>ID</th>
              <th>Location</th>
              <th>Mean freq</th>
              <th>Max freq</th>
              <th>Orthosteric</th>
              <th>Voxels</th>
              <th>GPCRdb numbers</th>
            </tr>
          </thead>
          <tbody>
            {ps.map(p => (
              <tr key={p.pocket_id}
                onClick={() => onHighlight(highlightPocket === p.pocket_id ? null : p.pocket_id)}
                style={{ cursor: 'pointer',
                         background: highlightPocket === p.pocket_id ? 'var(--panel)' : 'inherit' }}>
                <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{p.pocket_id}</td>
                <td><span className="pocket-zone">{pocketLabel(p) || '—'}</span></td>
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
    </div>
  )
}

function zoneBarColor(zone) {
  if (!zone) return 'var(--accent)'
  const z = zone.toLowerCase()
  if (z.includes('orthosteric')) return 'var(--gio)'
  if (z.includes('extracellular')) return 'var(--gs)'
  if (z.includes('intracellular')) return 'var(--gq)'
  if (z.includes('lipid')) return 'var(--g1213)'
  return 'var(--accent)'
}

/**
 * Human-readable label for a pocket, based on WHERE its lining residues are
 * (role_counts → location) rather than the vague catch-all `zone`, which labels
 * any non-receptor pocket "coupling_interface" — misleading for a pocket sitting
 * entirely on Gβ. Returns null when there is no meaningful location to show.
 */
// Subunit display names (match the role_counts keys from the backend).
const SUBUNIT_NAME = { galpha: 'Gα', gbeta: 'Gβ', g_gamma: 'Gγ', receptor: 'Receptor', peptide: 'Peptide', other: 'other' }

function pocketLabel(p) {
  if (!p) return null
  if (p.is_orthosteric) return 'Orthosteric'
  const rc = p.role_counts || {}
  const total = Object.values(rc).reduce((a, b) => a + b, 0) || 1
  const fRec = (rc.receptor || 0) / total
  const fGprot = ((rc.galpha || 0) + (rc.gbeta || 0) + (rc.g_gamma || 0)) / total
  // Receptor + G-protein mixed → interface, naming the dominant G subunit.
  if (fRec >= 0.5 && fGprot >= 0.2) {
    const g = dominantG(rc)
    return g ? `Receptor–${SUBUNIT_NAME[g]} interface` : 'Receptor–G-protein interface'
  }
  // Mostly a single G-protein subunit → name it specifically.
  if (fGprot >= 0.8) {
    const g = dominantG(rc)
    return g ? SUBUNIT_NAME[g] : 'G-protein'
  }
  if (fRec >= 0.8) {
    const z = p.zone || ''
    if (z.includes('extracellular')) return 'Extracellular vestibule'
    if (z.includes('intracellular')) return 'Intracellular/transducer interface'
    if (z.includes('tm_core')) return 'Membrane-facing'
    return 'Receptor (other)'
  }
  return null
}

// Which G-protein subunit (galpha/gbeta/g_gamma) has the most lining residues.
function dominantG(rc) {
  const cands = [['galpha', rc.galpha || 0], ['gbeta', rc.gbeta || 0], ['g_gamma', rc.g_gamma || 0]]
  cands.sort((a, b) => b[1] - a[1])
  return cands[0][1] > 0 ? cands[0][0] : null
}

// Map a pocketLabel back to a zone keyword for the legend swatch color.
function pocketLabelToZone(lbl) {
  if (!lbl) return null
  if (lbl === 'Orthosteric') return 'orthosteric'
  if (lbl.startsWith('Extracellular')) return 'extracellular'
  if (lbl.startsWith('Intracellular')) return 'intracellular'
  if (lbl === 'Membrane-facing') return 'tm_core'
  if (lbl === 'Gα' || lbl === 'Gβ' || lbl === 'Gγ') return 'gprotein'
  if (lbl.includes('interface')) return 'interface'
  return 'other'
}

const CGN_SEGMENTS = ['G.HN', 'G.S1', 'G.S2', 'G.S3', 'G.H1', 'G.S4', 'G.S5', 'G.H2', 'G.H3', 'G.S6', 'G.H4', 'G.H4S6', 'G.H5']

function lerpColor(t, r0, g0, b0, r1, g1, b1) {
  const r = Math.round(r0 + (r1 - r0) * t)
  const gc = Math.round(g0 + (g1 - g0) * t)
  const b = Math.round(b0 + (b1 - b0) * t)
  return `rgb(${r},${gc},${b})`
}

function GproteinSection({ data, highlightGprotein, onHighlight }) {
  const positions = data.positions || []
  if (!positions.length) return <div className="empty">No G-protein position data.</div>

  const bySegment = {}
  CGN_SEGMENTS.forEach(s => { bySegment[s] = [] })
  positions.forEach(p => {
    if (bySegment[p.cgn_segment]) bySegment[p.cgn_segment].push(p)
    else {
      if (!bySegment[p.cgn_segment]) bySegment[p.cgn_segment] = []
      bySegment[p.cgn_segment].push(p)
    }
  })
  CGN_SEGMENTS.forEach(s => {
    bySegment[s] = (bySegment[s] || []).sort((a, b) => a.sim_resid - b.sim_resid)
  })

  const top10 = [...positions]
    .sort((a, b) => b.contact_persistence_mean - a.contact_persistence_mean)
    .slice(0, 10)

  const RMSF_CAP = 8

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 16 }}>
        {data.n_positions} CGN positions
        {highlightGprotein != null && (
          <span style={{ marginLeft: 12 }}>
            Residue {highlightGprotein} highlighted —{' '}
            <a href="#/systems" onClick={e => { e.preventDefault(); onHighlight(null) }}
              style={{ color: 'var(--accent)', cursor: 'pointer' }}>clear</a>
          </span>
        )}
      </p>

      <div style={{ marginBottom: 8 }}>
        <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase',
                     letterSpacing: '0.08em', marginBottom: 6 }}>
          Contact persistence barcode
          <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: 'normal',
                         marginLeft: 8, fontSize: 11, color: 'var(--faint)' }}>
            fraction of frames contacting receptor
          </span>
        </h3>
        <BarcodeStrip
          bySegment={bySegment}
          getValue={p => p.contact_persistence_mean}
          getColor={v => lerpColor(Math.max(0, Math.min(1, v)), 255, 255, 255, 26, 122, 110)}
          legendLow="0"
          legendHigh="1"
          swatchFrom="#ffffff"
          swatchTo="#1a7a6e"
          formatTip={p => `${p.cgn_position} (${p.sim_resname}) persistence = ${(p.contact_persistence_mean ?? 0).toFixed(3)}`}
        />
      </div>

      <div style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase',
                     letterSpacing: '0.08em', marginBottom: 6 }}>
          RMSF barcode
          <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: 'normal',
                         marginLeft: 8, fontSize: 11, color: 'var(--faint)' }}>
            capped at {RMSF_CAP} Å; darker = more flexible
          </span>
        </h3>
        <BarcodeStrip
          bySegment={bySegment}
          getValue={p => Math.min(p.rmsf_mean ?? 0, RMSF_CAP) / RMSF_CAP}
          getColor={v => lerpColor(Math.max(0, Math.min(1, v)), 255, 255, 255, 192, 82, 42)}
          legendLow="0 Å"
          legendHigh={`${RMSF_CAP} Å+`}
          swatchFrom="#ffffff"
          swatchTo="#c0522a"
          formatTip={p => {
            const r = p.rmsf_mean ?? 0
            return `${p.cgn_position} (${p.sim_resname}) RMSF = ${r.toFixed(2)} Å${r > RMSF_CAP ? ' (off-scale)' : ''}`
          }}
        />
      </div>

      <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase',
                   letterSpacing: '0.08em', marginBottom: 8 }}>
        Top 10 positions by contact persistence
        <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: 'normal',
                       marginLeft: 8, fontSize: 11 }}>
          Click a row to highlight on 3D structure
        </span>
      </h3>
      <div className="table-wrap">
        <table aria-label="Top G-protein positions by contact persistence">
          <thead>
            <tr>
              <th>CGN position</th>
              <th>Segment</th>
              <th>Flock class</th>
              <th>Residue</th>
              <th>Contact persistence</th>
              <th>95% CI</th>
              <th>RMSF (Å)</th>
              <th>95% CI</th>
            </tr>
          </thead>
          <tbody>
            {top10.map(p => {
              const isActive = highlightGprotein === p.sim_resid
              return (
                <tr key={p.cgn_position}
                  onClick={() => onHighlight(isActive ? null : p.sim_resid)}
                  style={{ cursor: 'pointer',
                           background: isActive ? 'var(--panel)' : 'inherit' }}>
                  <td style={{ fontFamily: 'monospace', fontSize: 12,
                               color: isActive ? 'var(--accent)' : 'var(--ink)',
                               fontWeight: isActive ? 700 : 400 }}>{p.cgn_position}</td>
                  <td style={{ fontSize: 12 }}>{p.cgn_segment}</td>
                  <td style={{ fontSize: 11, color: 'var(--muted)' }}>{p.flock_class}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{p.sim_resname}</td>
                  <td>{p.contact_persistence_mean?.toFixed(3)}</td>
                  <td style={{ fontSize: 11, color: 'var(--muted)' }}>
                    [{p.contact_persistence_ci_low?.toFixed(2)}, {p.contact_persistence_ci_high?.toFixed(2)}]
                  </td>
                  <td>{p.rmsf_mean?.toFixed(2)}</td>
                  <td style={{ fontSize: 11, color: 'var(--muted)' }}>
                    [{p.rmsf_ci_low?.toFixed(1)}, {p.rmsf_ci_high?.toFixed(1)}]
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        <p style={{ fontSize: 10, color: 'var(--faint)', marginTop: 6 }}>
          Contact persistence = fraction of frames this Gα residue contacts the receptor. CI from {data.n_replicas ?? '?'} replica{data.n_replicas === 1 ? '' : 's'}.
        </p>
      </div>
    </div>
  )
}

function BarcodeStrip({ bySegment, getValue, getColor, legendLow, legendHigh, swatchFrom, swatchTo, formatTip }) {
  const [tooltip, setTooltip] = useState(null)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-start', overflowX: 'auto' }}>
        {CGN_SEGMENTS.map(seg => {
          const positions = bySegment[seg] || []
          if (!positions.length) return null
          return (
            <div key={seg} style={{ flexShrink: 0 }}>
              <div style={{ fontSize: 9, color: 'var(--faint)', fontFamily: 'monospace',
                            textAlign: 'center', marginBottom: 2, whiteSpace: 'nowrap',
                            width: positions.length * 4 }}>
                {seg}
              </div>
              <div style={{ display: 'flex', height: 40 }}>
                {positions.map(p => {
                  const v = getValue(p)
                  return (
                    <div
                      key={p.cgn_position}
                      style={{ width: 4, height: 40, background: getColor(v), flexShrink: 0 }}
                      onMouseEnter={e => setTooltip({
                        x: e.clientX, y: e.clientY,
                        text: formatTip
                          ? formatTip(p)
                          : `${p.cgn_position} (${p.sim_resname}) = ${v.toFixed ? v.toFixed(3) : v}`,
                      })}
                      onMouseLeave={() => setTooltip(null)}
                    />
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
        <span style={{ fontSize: 10, color: 'var(--muted)' }}>{legendLow}</span>
        <div style={{ width: 80, height: 8, borderRadius: 2,
                      background: `linear-gradient(to right, ${swatchFrom}, ${swatchTo})`,
                      border: '1px solid var(--rule)' }} />
        <span style={{ fontSize: 10, color: 'var(--muted)' }}>{legendHigh}</span>
      </div>
      {tooltip && (
        <div style={{
          position: 'fixed', left: tooltip.x + 10, top: tooltip.y - 28,
          background: 'var(--ink)', color: '#fff', fontSize: 11, padding: '3px 8px',
          borderRadius: 4, pointerEvents: 'none', zIndex: 9999, whiteSpace: 'nowrap',
        }}>
          {tooltip.text}
        </div>
      )}
    </div>
  )
}

/* ---- 2D TM helix cross-section diagram ---- */
function TmHelixDiagram({ highlightPair }) {
  // Standard GPCR TM helix positions viewed from extracellular side
  // Positions approximate the classic 7TM bundle cross-section
  const helices = [
    { id: 'TM1', cx: 50,  cy: 28,  r: 11 },
    { id: 'TM2', cx: 80,  cy: 50,  r: 11 },
    { id: 'TM3', cx: 80,  cy: 85,  r: 11 },
    { id: 'TM4', cx: 50,  cy: 108, r: 11 },
    { id: 'TM5', cx: 20,  cy: 85,  r: 11 },
    { id: 'TM6', cx: 20,  cy: 50,  r: 11 },
    { id: 'TM7', cx: 50,  cy: 65,  r: 11 },
  ]

  // Parse highlighted pair (e.g., "TM5-TM6" -> ["TM5", "TM6"])
  const highlighted = highlightPair
    ? highlightPair.split('-').filter(s => s.startsWith('TM'))
    : []

  // Colors for the two highlighted helices
  const colors = ['#e74c3c', '#3498db']

  return (
    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'center' }}>
      <svg viewBox="0 0 100 130" width="200" height="260"
        style={{ display: 'block' }}>
        {/* Membrane outline */}
        <ellipse cx="50" cy="65" rx="48" ry="58"
          fill="none" stroke="var(--rule)" strokeWidth="0.5" strokeDasharray="2,2" />

        {/* TM helices */}
        {helices.map((h, i) => {
          const hlIdx = highlighted.indexOf(h.id)
          const isHighlighted = hlIdx >= 0
          const fill = isHighlighted ? colors[hlIdx] : 'var(--panel)'
          const stroke = isHighlighted ? colors[hlIdx] : 'var(--rule)'
          const textFill = isHighlighted ? '#fff' : 'var(--muted)'
          return (
            <g key={h.id}>
              <circle cx={h.cx} cy={h.cy} r={h.r}
                fill={fill} stroke={stroke} strokeWidth={isHighlighted ? 1.5 : 0.8}
                opacity={isHighlighted ? 0.9 : 0.5}
                style={{ transition: 'all 0.2s ease' }} />
              <text x={h.cx} y={h.cy + 1} textAnchor="middle" dominantBaseline="middle"
                fill={textFill} fontSize="6" fontWeight={isHighlighted ? 700 : 500}
                fontFamily="monospace" style={{ transition: 'all 0.2s ease' }}>
                {h.id.replace('TM', '')}
              </text>
            </g>
          )
        })}

        {/* Label */}
        <text x="50" y="128" textAnchor="middle" fill="var(--faint)" fontSize="4.5"
          fontFamily="sans-serif">
          Extracellular view
        </text>
      </svg>
    </div>
  )
}

/* ---- Gateway section with bar chart + table ---- */
const METRIC_LABELS = {
  occupancy: 'Occupancy',
  open_fraction: 'Open frac.',
  penetration: 'Penetration (Å)',
  penetration_p90: 'Pen. p90 (Å)',
}

function GatewaySection({ records }) {
  if (!records?.length) return <div className="empty">No gateway data.</div>

  // Group by pair for chart
  const byPair = {}
  records.forEach(r => {
    if (!byPair[r.pair]) byPair[r.pair] = {}
    byPair[r.pair][r.metric] = r
  })
  const pairs = Object.keys(byPair).sort()

  // Stable, ordered metric list across all pairs
  const metricOrder = ['occupancy', 'open_fraction', 'penetration', 'penetration_p90']
  const metricKeys = metricOrder.filter(m => records.some(r => r.metric === m))

  // Get occupancy records for the bar chart
  const occRecords = records.filter(r => r.metric === 'occupancy')
  const maxOcc = Math.max(...occRecords.map(r => r.mean), 0.01)

  // Highlight state for TM diagram
  const [highlightPair, setHighlightPair] = useState(null)

  return (
    <div>
      {/* TM helix cross-section diagram */}
      <TmHelixDiagram highlightPair={highlightPair} />

      {/* Occupancy bar chart */}
      {occRecords.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase',
                       letterSpacing: '0.08em', marginBottom: 8 }}>
            Gateway occupancy by TM portal
            <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: 'normal',
                           marginLeft: 8, fontSize: 11 }}>
              Click a portal to highlight helices
            </span>
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {occRecords.map(r => {
              const barW = (r.mean / maxOcc) * 100
              const isActive = highlightPair === r.pair
              return (
                <div key={r.pair}
                  onClick={() => setHighlightPair(isActive ? null : r.pair)}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer',
                           background: isActive ? 'var(--panel)' : 'transparent',
                           borderRadius: 3, padding: '1px 4px' }}>
                  <span style={{ width: 70, flexShrink: 0, fontSize: 11, fontFamily: 'monospace',
                                 color: isActive ? 'var(--accent)' : 'var(--muted)', textAlign: 'right',
                                 fontWeight: isActive ? 700 : 400 }}>
                    {r.pair}
                  </span>
                  <div style={{ flex: 1, height: 18, background: 'var(--panel)', borderRadius: 3,
                                position: 'relative', overflow: 'hidden' }}>
                    <div style={{
                      width: `${barW}%`, height: '100%', borderRadius: 3,
                      background: isActive ? 'var(--accent)' : 'var(--accent)', transition: 'width 0.3s ease',
                      opacity: isActive ? 1 : 0.7,
                    }} />
                    <span style={{
                      position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)',
                      fontSize: 10, fontWeight: 700, color: barW > 30 ? '#fff' : 'var(--ink)',
                    }}>
                      {r.mean?.toFixed(3)}
                    </span>
                  </div>
                  <span style={{ fontSize: 10, color: 'var(--faint)', width: 80 }}>
                    [{r.ci_lo?.toFixed(2)}, {r.ci_hi?.toFixed(2)}]
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Detail table — one row per portal, metrics as columns */}
      <div className="table-wrap">
        <table aria-label="Gateway data for this system">
          <thead>
            <tr>
              <th>Portal</th>
              {metricKeys.map(m => <th key={m} style={{ textAlign: 'right' }}>{METRIC_LABELS[m] || m}</th>)}
              <th style={{ textAlign: 'right' }}>Replicas</th>
            </tr>
          </thead>
          <tbody>
            {pairs.map(pair => {
              const isActive = highlightPair === pair
              const byMetric = byPair[pair] || {}
              return (
                <tr key={pair}
                  onClick={() => setHighlightPair(isActive ? null : pair)}
                  style={{ cursor: 'pointer',
                           background: isActive ? 'var(--panel)' : 'inherit' }}>
                  <td style={{ fontWeight: isActive ? 700 : 600, fontFamily: 'monospace', fontSize: 12,
                               color: isActive ? 'var(--accent)' : 'var(--ink)' }}>{pair}</td>
                  {metricKeys.map(m => {
                    const r = byMetric[m]
                    return (
                      <td key={m} style={{ textAlign: 'right', fontSize: 12,
                                           color: 'var(--muted)',
                                           title: r ? `95% CI [${r.ci_lo?.toFixed(2)}, ${r.ci_hi?.toFixed(2)}]` : '' }}>
                        {r ? r.mean?.toFixed(3) : '—'}
                      </td>
                    )
                  })}
                  <td style={{ textAlign: 'right', fontSize: 12, color: 'var(--muted)' }}>
                    {byMetric[metricKeys[0]]?.n_replicas ?? '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        <p style={{ fontSize: 10, color: 'var(--faint)', marginTop: 6 }}>
          Hover a cell for its 95% confidence interval. Occupancy/open_fraction are unitless fractions; penetration is in Å.
        </p>
      </div>
    </div>
  )
}
