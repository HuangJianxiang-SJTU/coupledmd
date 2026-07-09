import { useEffect, useRef, useState } from 'react'

const BASE = import.meta.env.VITE_API_BASE || ''

// Subunit colors: Gα by family, Receptor gray, Gβ green, Gγ purple
const FAM_COLOR = { Gi: '#2166ac', Gq: '#d6604d', Gs: '#4dac26', 'G12-13': '#762a83' }
const SUBUNIT_COLORS = {
  G_alpha: null,       // resolved from family at render time
  Receptor: '#b0b0b0',
  G_beta: '#7fbf7b',
  G_gamma: '#af8dc3',
}
const SUBUNIT_LABELS = {
  G_alpha: 'Gα',
  Receptor: 'Receptor',
  G_beta: 'Gβ',
  G_gamma: 'Gγ',
}

export default function TrajectoryViewer({ systemId, highlightPocket, highlightGprotein, highlightResidue, family, subunitRanges }) {
  const mountRef = useRef(null)
  const stageRef = useRef(null)
  const compRef = useRef(null)
  const pocketRepRef = useRef(null)
  const gproteinRepRef = useRef(null)
  const residueRepRef = useRef(null)
  const [status, setStatus] = useState('idle')   // idle | loading | ready | error | unavailable
  const [trajStatus, setTrajStatus] = useState('idle') // idle | loading | ready | error
  const [meta, setMeta] = useState(null)
  const [frame, setFrame] = useState(0)
  const [playing, setPlaying] = useState(false)
  const playRef = useRef(null)

  useEffect(() => {
    fetch(`${BASE}/api/v1/systems/${systemId}/viz/meta`)
      .then(r => {
        if (r.status === 404) { setStatus('unavailable'); return null }
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(d => { if (d) setMeta(d) })
      .catch(() => setStatus('unavailable'))
  }, [systemId])

  useEffect(() => {
    if (!meta || !mountRef.current) return
    setStatus('loading')
    setTrajStatus('idle')
    let cancelled = false

    import('ngl').then(NGL => {
      if (cancelled || !mountRef.current) return

      if (stageRef.current) { stageRef.current.dispose(); stageRef.current = null }

      const stage = new NGL.Stage(mountRef.current, {
        backgroundColor: '#f8f8f8',
        quality: 'medium',
      })
      stageRef.current = stage

      const structUrl = `${window.location.origin}${BASE}/api/v1/systems/${systemId}/viz/structure`
      const trajUrl = `${window.location.origin}${BASE}/api/v1/systems/${systemId}/viz/trajectory`

      stage.loadFile(structUrl, { ext: 'pdb', defaultRepresentation: false })
        .then(comp => {
          if (cancelled) return
          compRef.current = comp

          // Color by subunit using subunitRanges from the contacts parquet
          if (subunitRanges && Object.keys(subunitRanges).length > 0) {
            const gaColor = FAM_COLOR[family] || '#95a5a6'
            // Build a list of all subunit residue ranges for NGL selection
            const subunitOrder = ['G_alpha', 'Receptor', 'G_beta', 'G_gamma']
            const coveredResidues = []

            for (const sub of subunitOrder) {
              const ranges = subunitRanges[sub]
              if (!ranges) continue
              const color = sub === 'G_alpha' ? gaColor : SUBUNIT_COLORS[sub]
              // Support both array of ranges [{min,max},...] and single {min,max}
              const rangeList = Array.isArray(ranges) ? ranges : [ranges]
              for (const range of rangeList) {
                const sele = `${range.min}-${range.max}`
                coveredResidues.push(sele)
                comp.addRepresentation('cartoon', {
                  sele: sele,
                  color: color,
                  opacity: 0.92,
                })
              }
            }

            // Any protein residues NOT covered by known subunits → gray
            if (coveredResidues.length > 0) {
              comp.addRepresentation('cartoon', {
                sele: `protein and not (${coveredResidues.join(' or ')})`,
                color: '#d0d0d0',
                opacity: 0.92,
              })
            }
          } else {
            // Fallback: chain-based coloring (all viz PDBs use chain X, so this is uniform)
            comp.addRepresentation('cartoon', {
              colorScheme: 'chainid',
              opacity: 0.92,
            })
          }
          comp.addRepresentation('ball+stick', {
            sele: 'not protein and not water',
            colorScheme: 'element',
          })
          comp.autoView()

          // Structure is ready — show controls immediately
          setStatus('ready')
          setFrame(0)

          // Load trajectory
          setTrajStatus('loading')
          NGL.autoLoad(trajUrl, { ext: 'xtc' })
            .then(frames => {
              if (cancelled) return
              comp.addTrajectory(frames)
              setTrajStatus('ready')
            })
            .catch(e => {
              console.error('NGL trajectory load error:', e)
              if (!cancelled) setTrajStatus('error')
            })
        })
        .catch(e => {
          console.error('NGL structure load error:', e)
          if (!cancelled) setStatus('error')
        })

      const handleResize = () => stage.handleResize()
      window.addEventListener('resize', handleResize)
      return () => window.removeEventListener('resize', handleResize)
    }).catch(e => {
      console.error('NGL import error:', e)
      if (!cancelled) setStatus('error')
    })

    return () => {
      cancelled = true
      if (playRef.current) clearInterval(playRef.current)
    }
  }, [meta, systemId, subunitRanges, family])

  // Highlight pocket on the 3D structure
  useEffect(() => {
    const comp = compRef.current
    if (!comp) return

    // Remove previous pocket representation
    if (pocketRepRef.current) {
      try { comp.removeRepresentation(pocketRepRef.current) } catch {}
      pocketRepRef.current = null
    }

    if (highlightPocket == null) return

    // Fetch pocket data to get lining residues and centroid
    const BASE = import.meta.env.VITE_API_BASE || ''
    fetch(`${BASE}/api/v1/systems/${systemId}/pockets?gpcrdb=false`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return
        const pocket = (data.pockets || []).find(p => p.pocket_id === highlightPocket)
        if (!pocket) return

        // Highlight lining residues by recoloring their cartoon segment red.
        // (NGL cartoon coloring needs a colorScheme that assigns red to these
        // residues; use a residue-index scheme built from the selection.)
        const resids = pocket.lining_resids || []
        if (resids.length > 0) {
          // Build a selection string of the lining residues
          const sele = resids.join(' ')
          const rep = comp.addRepresentation('cartoon', {
            sele: sele,
            color: '#e74c3c',
            opacity: 0.98,
            aspectRatio: 5,
            radiusScale: 1.15,
          })
          pocketRepRef.current = rep
        }
      })
      .catch(() => {})
  }, [highlightPocket, systemId])

  // Highlight G-protein residue on the 3D structure
  useEffect(() => {
    const comp = compRef.current
    if (!comp) return

    // Remove previous G-protein representation
    if (gproteinRepRef.current) {
      try { comp.removeRepresentation(gproteinRepRef.current) } catch {}
      gproteinRepRef.current = null
    }

    if (highlightGprotein == null) return

    // Highlight the residue as ball+stick with a wider radius for visibility
    const rep = comp.addRepresentation('ball+stick', {
      sele: `${highlightGprotein}`,
      color: '#2980b9',
      opacity: 0.95,
      radiusType: 'vdw',
      radiusFactor: 0.6,
    })
    gproteinRepRef.current = rep
  }, [highlightGprotein, systemId])

  // Highlight a generic residue (e.g. from the flareplot click) on the 3D structure
  useEffect(() => {
    const comp = compRef.current
    if (!comp) return

    if (residueRepRef.current) {
      try { comp.removeRepresentation(residueRepRef.current) } catch {}
      residueRepRef.current = null
    }

    if (highlightResidue == null) return

    const rep = comp.addRepresentation('ball+stick', {
      sele: `${highlightResidue}`,
      color: '#e74c3c',
      opacity: 0.95,
      radiusType: 'vdw',
      radiusFactor: 0.6,
    })
    residueRepRef.current = rep
  }, [highlightResidue, systemId])

  function seekFrame(f) {
    const traj = compRef.current?.trajList?.[0]?.trajectory
    if (!traj) return
    const n = traj.frameCount
    const clamped = Math.max(0, Math.min(f, n - 1))
    traj.setFrame(clamped)
    setFrame(clamped)
  }

  function togglePlay() {
    if (playing) {
      clearInterval(playRef.current)
      setPlaying(false)
    } else {
      const traj = compRef.current?.trajList?.[0]?.trajectory
      if (!traj) return
      const n = traj.frameCount
      playRef.current = setInterval(() => {
        setFrame(prev => {
          const next = (prev + 1) % n
          traj.setFrame(next)
          return next
        })
      }, 80)
      setPlaying(true)
    }
  }

  const nFrames = meta?.viz_files?.traj_xtc?.n_frames ?? 0
  const nAtoms = meta?.viz_files?.structure_pdb?.n_atoms ?? 0

  // Build color legend from subunitRanges
  const legendItems = []
  if (subunitRanges) {
    const gaColor = FAM_COLOR[family] || '#95a5a6'
    for (const sub of ['G_alpha', 'Receptor', 'G_beta', 'G_gamma']) {
      if (subunitRanges[sub]) {
        legendItems.push({
          label: SUBUNIT_LABELS[sub],
          color: sub === 'G_alpha' ? gaColor : SUBUNIT_COLORS[sub],
        })
      }
    }
  }

  if (status === 'unavailable') {
    return (
      <div style={{ padding: '24px 0', color: 'var(--muted)', fontSize: 13 }}>
        Trajectory viewer not available for this system (viz files not yet built).
      </div>
    )
  }

  return (
    <div style={{ marginTop: 8 }}>
      <div
        ref={mountRef}
        role="img"
        aria-label="3D trajectory viewer"
        style={{
          width: '100%', height: 700, borderRadius: 8,
          border: '1px solid var(--rule)', background: '#f8f8f8',
          position: 'relative', overflow: 'hidden',
        }}
      >
        {status === 'loading' && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            background: 'rgba(248,248,248,0.85)', fontSize: 13, color: 'var(--muted)',
          }}>
            Loading structure…
          </div>
        )}
        {status === 'error' && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            color: '#b00', fontSize: 13,
          }}>
            Failed to load structure. Check browser console for details.
          </div>
        )}
      </div>

      {status === 'ready' && (
        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 12 }}>
          <button onClick={togglePlay} disabled={trajStatus !== 'ready'}
            aria-label={playing ? 'Pause trajectory' : 'Play trajectory'}
            style={{
              padding: '5px 14px', borderRadius: 6, border: '1px solid var(--rule)',
              background: trajStatus === 'ready' ? 'var(--accent)' : '#ccc',
              color: '#fff', cursor: trajStatus === 'ready' ? 'pointer' : 'default', fontSize: 13,
            }}>
            {playing ? '⏸ Pause' : '▶ Play'}
          </button>

          <input
            type="range" min={0} max={Math.max(0, nFrames - 1)} value={frame}
            onChange={e => seekFrame(Number(e.target.value))}
            disabled={trajStatus !== 'ready'}
            aria-label="Trajectory frame"
            style={{ flex: 1 }}
          />

          <span style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>
            {trajStatus === 'loading' ? 'Loading trajectory…' : `${frame + 1} / ${nFrames}`}
          </span>
        </div>
      )}

      {meta && (
        <div style={{ marginTop: 6, fontSize: 11, color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <span>
            {nAtoms.toLocaleString()} atoms · {nFrames} frames
            {meta.viz_files?.traj_xtc?.size_bytes
              ? ` · ${(meta.viz_files.traj_xtc.size_bytes / 1e6).toFixed(1)} MB XTC`
              : ''}
          </span>
          {legendItems.length > 0 && legendItems.map(item => (
            <span key={item.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: item.color, display: 'inline-block' }} />
              {item.label}
            </span>
          ))}
          {trajStatus === 'error' && (
            <span style={{ color: '#b00' }}>
              Trajectory failed to load — structure only.
            </span>
          )}
        </div>
      )}
    </div>
  )
}
