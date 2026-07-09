import { useEffect, useRef, useState, useCallback } from 'react'
import { api } from '../api'

const FAM_COLOR = { Gi: '#2166ac', Gq: '#d6604d', Gs: '#4dac26', 'G12-13': '#762a83' }

// Interaction type colors (matching GPCRmd / manuscript style)
const ITYPE_COLOR = {
  sb: '#f39c12',   // salt bridges — orange
  vdw: '#95a5a6',  // van der Waals — gray
  hb: '#e74c3c',   // hydrogen bonds — red
  hp: '#2c3e50',   // hydrophobic — dark blue-gray
  pc: '#9b59b6',   // pi-cation — purple
  ps: '#8e44ad',   // pi-stacking — dark purple
  wb: '#3498db',   // water bridges — blue
}

const ITYPE_LABELS = {
  all: 'All contacts',
  sb: 'Salt bridges',
  vdw: 'Van der Waals',
  inter: 'Receptor–Gα only',
  hb: 'Hydrogen bonds',
  hp: 'Hydrophobic',
  pc: 'Pi-cation',
  ps: 'Pi-stacking',
  wb: 'Water bridges',
}

/**
 * Interactive flareplot (circular interaction network) component.
 * Renders a Circos-style plot on canvas with hover/click interactivity.
 */
export default function Flareplot({ systemId, family, onResidueClick }) {
  const canvasRef = useRef(null)
  const [contacts, setContacts] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [minFreq, setMinFreq] = useState(0.90)
  const [scope, setScope] = useState('receptor_galpha')
  const [itype, setItype] = useState('all')
  const [hoveredResid, setHoveredResid] = useState(null)
  const [selectedResid, setSelectedResid] = useState(null)
  const [tooltip, setTooltip] = useState(null)

  // Refs for hit-testing (stored outside React state for perf)
  const layoutRef = useRef(null)

  // Fetch contact data
  useEffect(() => {
    setLoading(true)
    setError(null)
    setSelectedResid(null)
    api.systemContacts(systemId, { min_freq: 0.4, scope })
      .then(data => {
        setContacts(data.contacts)
        setLoading(false)
      })
      .catch(e => {
        setError(e.message)
        setLoading(false)
      })
  }, [systemId, scope])

  // Build layout when contacts or minFreq change
  useEffect(() => {
    if (!contacts) return

    // Filter by itype — 'inter' is a special filter for interchain only
    let filtered = contacts.filter(c => c.frequency >= minFreq)
    if (itype === 'inter') {
      filtered = filtered.filter(c =>
        (c.subunit1 === 'Receptor' && c.subunit2 === 'G_alpha') ||
        (c.subunit1 === 'G_alpha' && c.subunit2 === 'Receptor')
      )
    } else if (itype !== 'all') {
      filtered = filtered.filter(c => c.itype === itype)
    }

    // Normalize subunit labels: collapse Receptor_frag* → Receptor,
    // and drop UNRESOLVED/Unknown/peptide_ligand from the circo plot.
    const normalizeSubunit = s => {
      if (!s) return null
      if (s.startsWith('Receptor')) return 'Receptor'
      if (s === 'G_alpha' || s === 'G_beta' || s === 'G_gamma') return s
      return null  // UNRESOLVED, Unknown, peptide_ligand → excluded
    }

    // Map each residue to its primary (normalized) subunit
    const residSub = {}
    filtered.forEach(c => {
      const s1 = normalizeSubunit(c.subunit1)
      const s2 = normalizeSubunit(c.subunit2)
      if (s1 && !residSub[c.res1]) residSub[c.res1] = s1
      if (s2 && !residSub[c.res2]) residSub[c.res2] = s2
    })

    // Collect unique resids per subunit
    const subResids = { Receptor: [], G_alpha: [], G_beta: [], G_gamma: [] }
    const allActive = new Set()
    filtered.forEach(c => { allActive.add(c.res1); allActive.add(c.res2) })
    allActive.forEach(r => {
      const s = residSub[r]
      if (s && subResids[s]) subResids[s].push(r)
    })

    // Build sectors
    const sectorDefs = [
      { key: 'Receptor', label: 'Receptor', color: '#b0b0b0', labelColor: '#444' },
      { key: 'G_alpha', label: 'Gα', color: FAM_COLOR[family] || '#95a5a6', labelColor: '#fff' },
      { key: 'G_beta', label: 'Gβ', color: '#7fbf7b', labelColor: '#fff' },
      { key: 'G_gamma', label: 'Gγ', color: '#af8dc3', labelColor: '#fff' },
    ]

    const sectors = []
    sectorDefs.forEach(def => {
      const resids = subResids[def.key]
      if (!resids || resids.length === 0) return
      const sorted = [...resids].sort((a, b) => a - b)
      sectors.push({ ...def, size: sorted.length, resids: sorted })
    })

    // Build edges — use normalized subunit names for isInterchain detection
    const edgeList = filtered.map(c => {
      const s1 = normalizeSubunit(c.subunit1) || c.subunit1
      const s2 = normalizeSubunit(c.subunit2) || c.subunit2
      return {
        res1: c.res1,
        res2: c.res2,
        sub1: s1,
        sub2: s2,
        itype: c.itype,
        freq: c.frequency,
        isInterchain: (s1 === 'Receptor' && s2 === 'G_alpha') ||
                      (s1 === 'G_alpha' && s2 === 'Receptor'),
      }
    })
    edgeList.sort((a, b) => a.freq - b.freq)

    layoutRef.current = { sectors, edges: edgeList, residSub }
  }, [contacts, minFreq, family, itype])

  // Render on canvas
  useEffect(() => {
    const canvas = canvasRef.current
    const layout = layoutRef.current
    if (!canvas || !layout || layout.sectors.length === 0) return

    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1
    // Size canvas to fill its container width, height = width * 0.75 (shorter than square)
    const containerW = canvas.parentElement?.clientWidth || 600
    const displayW = containerW
    const displayH = Math.round(containerW * 0.75)  // 3:4 aspect ratio — shorter
    canvas.style.width = displayW + 'px'
    canvas.style.height = displayH + 'px'
    canvas.width = displayW * dpr
    canvas.height = displayH * dpr
    ctx.scale(dpr, dpr)

    const W = displayW
    const H = displayH
    const cx = W / 2
    const cy = H / 2
    const R = Math.min(W, H) / 2 - 36  // more margin for larger labels
    const trackW = 18  // wider track for bigger sector labels
    const innerR = R - trackW

    ctx.clearRect(0, 0, W, H)

    const { sectors, edges } = layout
    const totalSize = sectors.reduce((s, sec) => s + sec.size, 0)
    const gapAngle = 0.04
    const totalGap = gapAngle * sectors.length
    const availableAngle = 2 * Math.PI - totalGap

    let currentAngle = -Math.PI / 2
    const sectorAngles = []
    const residAngle = {}
    const residSector = {}

    // Draw sectors
    sectors.forEach((sec) => {
      const arcLen = (sec.size / totalSize) * availableAngle
      const startAngle = currentAngle
      const endAngle = currentAngle + arcLen

      sectorAngles.push({ ...sec, startAngle, endAngle })

      // Sector arc
      ctx.beginPath()
      ctx.arc(cx, cy, R, startAngle, endAngle)
      ctx.arc(cx, cy, innerR, endAngle, startAngle, true)
      ctx.closePath()
      ctx.fillStyle = sec.color
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 1
      ctx.stroke()

      // Gα ring — decorative outer arc for the G_alpha sector (GPCRmd-style)
      if (sec.key === 'G_alpha') {
        const ringR = R + 6
        ctx.beginPath()
        ctx.arc(cx, cy, ringR, startAngle, endAngle)
        ctx.strokeStyle = sec.color
        ctx.lineWidth = 3
        ctx.stroke()
      }

      // Sector label — larger font
      const midA = (startAngle + endAngle) / 2
      const labelR = (R + innerR) / 2
      const lx = cx + labelR * Math.cos(midA)
      const ly = cy + labelR * Math.sin(midA)
      ctx.save()
      ctx.translate(lx, ly)
      let rot = midA + Math.PI / 2
      if (rot > Math.PI / 2 && rot < 3 * Math.PI / 2) rot += Math.PI
      ctx.rotate(rot)
      ctx.fillStyle = sec.labelColor || '#333'
      ctx.font = 'bold 11px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(sec.label, 0, 0)
      ctx.restore()

      // Structural region labels for Receptor sector
      // Mark TM helix boundaries and loop regions
      if (sec.key === 'Receptor' && sec.size > 20) {
        const regionLabels = [
          { name: 'TM1-3', frac: 0.15 },
          { name: 'ICL2', frac: 0.30 },
          { name: 'TM4-5', frac: 0.45 },
          { name: 'ECL2', frac: 0.55 },
          { name: 'TM6-7', frac: 0.75 },
          { name: 'H8', frac: 0.92 },
        ]
        const regionR = innerR - 8
        regionLabels.forEach(rl => {
          const rAngle = startAngle + rl.frac * arcLen
          const rx = cx + regionR * Math.cos(rAngle)
          const ry = cy + regionR * Math.sin(rAngle)
          ctx.save()
          ctx.translate(rx, ry)
          let rRot = rAngle + Math.PI / 2
          if (rRot > Math.PI / 2 && rRot < 3 * Math.PI / 2) rRot += Math.PI
          ctx.rotate(rRot)
          ctx.fillStyle = 'rgba(255,255,255,0.7)'
          ctx.font = '7px sans-serif'
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          ctx.fillText(rl.name, 0, 0)
          ctx.restore()
        })
      }

      // Residue positions and tick marks
      const nTicks = Math.min(sec.size, 14)
      const tickStep = Math.max(1, Math.floor(sec.size / nTicks))
      for (let j = 0; j < sec.size; j++) {
        const frac = (j + 0.5) / sec.size
        const angle = startAngle + frac * arcLen
        residAngle[sec.resids[j]] = angle
        residSector[sec.resids[j]] = sec.key

        if (j % tickStep === 0) {
          // Tick mark — longer
          const x1 = cx + (R + 2) * Math.cos(angle)
          const y1 = cy + (R + 2) * Math.sin(angle)
          const x2 = cx + (R + 7) * Math.cos(angle)
          const y2 = cy + (R + 7) * Math.sin(angle)
          ctx.beginPath()
          ctx.moveTo(x1, y1)
          ctx.lineTo(x2, y2)
          ctx.strokeStyle = '#999'
          ctx.lineWidth = 0.8
          ctx.stroke()

          // Residue number label — larger font
          const tx = cx + (R + 14) * Math.cos(angle)
          const ty = cy + (R + 14) * Math.sin(angle)
          ctx.fillStyle = '#666'
          ctx.font = '8px monospace'  // was 5.5px
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          ctx.fillText(String(sec.resids[j]), tx, ty)
        }
      }

      currentAngle = endAngle + gapAngle
    })

    // Draw chords (edges)
    const chordR = (R + innerR) / 2
    const showItypeColor = itype !== 'all' && itype !== 'inter'

    edges.forEach(edge => {
      const a1 = residAngle[edge.res1]
      const a2 = residAngle[edge.res2]
      if (a1 == null || a2 == null) return

      const x1 = cx + chordR * Math.cos(a1)
      const y1 = cy + chordR * Math.sin(a1)
      const x2 = cx + chordR * Math.cos(a2)
      const y2 = cy + chordR * Math.sin(a2)

      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.quadraticCurveTo(cx, cy, x2, y2)

      const alpha = Math.min(0.75, 0.05 + edge.freq * 0.7)
      const lw = 0.2 + edge.freq * 1.8

      if (showItypeColor) {
        // Color by interaction type
        const c = ITYPE_COLOR[edge.itype] || '#aaaaaa'
        ctx.strokeStyle = c + Math.round(alpha * 255).toString(16).padStart(2, '0')
        ctx.lineWidth = lw + 0.3
      } else if (edge.isInterchain) {
        const c = FAM_COLOR[family] || '#e74c3c'
        ctx.strokeStyle = c + Math.round(alpha * 255).toString(16).padStart(2, '0')
        ctx.lineWidth = lw + 0.3
      } else {
        ctx.strokeStyle = `rgba(180,180,180,${alpha})`
        ctx.lineWidth = lw
      }
      ctx.stroke()
    })

    // Highlight the selected + hovered residue positions on the ring
    const highlightResid = (rid, fill, stroke, ringR) => {
      const a = residAngle[rid]
      if (a == null) return
      const x = cx + ringR * Math.cos(a)
      const y = cy + ringR * Math.sin(a)
      ctx.beginPath()
      ctx.arc(x, y, 5, 0, 2 * Math.PI)
      ctx.fillStyle = fill
      ctx.fill()
      ctx.strokeStyle = stroke
      ctx.lineWidth = 1.5
      ctx.stroke()
    }
    if (selectedResid != null) highlightResid(selectedResid, '#fff', '#e74c3c', chordR)
    if (hoveredResid != null && hoveredResid !== selectedResid) {
      highlightResid(hoveredResid, 'rgba(231,76,60,0.35)', '#e74c3c', chordR)
    }

    // Store layout refs for hit-testing
    layoutRef.current = { sectors, edges, residAngle, residSector, sectorAngles, cx, cy, R, innerR, chordR }
  }, [contacts, minFreq, family, itype, hoveredResid, selectedResid])

  // Hit-test: which residue (if any) is under the mouse pointer?
  const hitTest = useCallback((e) => {
    const layout = layoutRef.current
    if (!layout || !layout.residAngle) return null

    const canvas = canvasRef.current
    if (!canvas) return null
    const rect = canvas.getBoundingClientRect()
    const mx = e.clientX - rect.left
    const my = e.clientY - rect.top
    const { cx, cy, R, innerR, residAngle, edges } = layout

    const dx = mx - cx
    const dy = my - cy
    const dist = Math.sqrt(dx * dx + dy * dy)

    if (dist < innerR - 5 || dist > R + 5) return null

    const mouseAngle = Math.atan2(dy, dx)
    let closestResid = null
    let closestDist = Infinity

    Object.entries(residAngle).forEach(([resid, angle]) => {
      let d = Math.abs(mouseAngle - angle)
      if (d > Math.PI) d = 2 * Math.PI - d
      if (d < closestDist) {
        closestDist = d
        closestResid = parseInt(resid)
      }
    })

    if (closestDist < 0.05 && closestResid != null) {
      const sub = layout.residSector[closestResid]
      const relatedEdges = edges.filter(ed => ed.res1 === closestResid || ed.res2 === closestResid)
      const interEdges = relatedEdges.filter(ed => ed.isInterchain)
      return {
        resid: closestResid,
        subunit: sub,
        nEdges: relatedEdges.length,
        nInter: interEdges.length,
      }
    }
    return null
  }, [])

  // Mouse move handler for hover tooltips
  const handleMouseMove = useCallback((e) => {
    const hit = hitTest(e)
    if (hit) {
      setTooltip({ x: e.clientX, y: e.clientY, ...hit })
      setHoveredResid(hit.resid)
    } else {
      setTooltip(null)
      setHoveredResid(null)
    }
  }, [hitTest])

  // Click → select residue and propagate to parent (3D highlight)
  const handleClick = useCallback((e) => {
    const hit = hitTest(e)
    if (!hit) return
    const next = selectedResid === hit.resid ? null : hit.resid
    setSelectedResid(next)
    if (onResidueClick) onResidueClick(next, hit.subunit)
  }, [hitTest, selectedResid, onResidueClick])

  const handleMouseLeave = useCallback(() => {
    setTooltip(null)
    setHoveredResid(null)
  }, [])

  if (loading) return <div style={{ fontSize: 12, color: 'var(--muted)', padding: 20 }}>Loading contacts…</div>
  if (error) return (
    <div style={{ fontSize: 12, color: 'var(--muted)', padding: 20 }}>
      No contact data available for this system.
    </div>
  )
  if (contacts && contacts.length === 0) return (
    <div style={{ fontSize: 12, color: 'var(--muted)', padding: 20 }}>
      No contacts above the frequency threshold. Try lowering “Min freq”.
    </div>
  )

  const nEdges = layoutRef.current?.edges?.length ?? 0

  // Build itype options from available data + fixed options
  const availableItypes = new Set(contacts?.map(c => c.itype) || [])
  const itypeOptions = [
    { value: 'all', label: 'All contacts' },
    { value: 'inter', label: 'Receptor–Gα only' },
    ...['sb', 'vdw', 'hb', 'hp', 'pc', 'ps', 'wb']
      .filter(t => availableItypes.has(t))
      .map(t => ({ value: t, label: ITYPE_LABELS[t] })),
  ]

  return (
    <div style={{ position: 'relative' }}>
      {/* Controls */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
        <label style={{ fontSize: 11, color: 'var(--muted)' }}>
          Min freq: {minFreq.toFixed(2)}
          <input type="range" min="0.4" max="1.0" step="0.05" value={minFreq}
            onChange={e => setMinFreq(parseFloat(e.target.value))}
            style={{ width: 80, marginLeft: 4, verticalAlign: 'middle' }} />
        </label>
        <select value={scope} onChange={e => setScope(e.target.value)}
          style={{ fontSize: 11, padding: '2px 6px', border: '1px solid var(--rule)', borderRadius: 3 }}>
          <option value="receptor_galpha">Receptor + Gα</option>
          <option value="receptor_only">Receptor only</option>
          <option value="all">All subunits</option>
        </select>
        <select value={itype} onChange={e => setItype(e.target.value)}
          style={{ fontSize: 11, padding: '2px 6px', border: '1px solid var(--rule)', borderRadius: 3 }}>
          {itypeOptions.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <span style={{ fontSize: 10, color: 'var(--faint)' }}>
          {nEdges} edges{nEdges === 0 ? ' (none at this filter)' : ''}
        </span>
        {selectedResid != null && (
          <span style={{ fontSize: 10, color: 'var(--accent)' }}>
            Res {selectedResid} selected —{' '}
            <a href="#/systems" onClick={e => {
              e.preventDefault()
              setSelectedResid(null)
              if (onResidueClick) onResidueClick(null)
            }} style={{ cursor: 'pointer' }}>clear</a>
          </span>
        )}
      </div>
      <p style={{ fontSize: 10, color: 'var(--faint)', margin: '0 0 8px' }}>
        Click a residue to highlight it on the 3D structure. Hover for contact counts.
      </p>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        style={{ display: 'block', margin: '0 auto', cursor: 'pointer' }}
      />

      {/* Legend */}
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        {itype !== 'all' && itype !== 'inter' ? (
          // Show only the selected itype in the legend
          <span style={{ fontSize: 9, color: 'var(--muted)' }}>
            <span style={{ display: 'inline-block', width: 14, height: 3, background: ITYPE_COLOR[itype] || '#aaa', marginRight: 3, verticalAlign: 'middle', borderRadius: 1 }} />
            {ITYPE_LABELS[itype]}
          </span>
        ) : (
          <>
            <span style={{ fontSize: 9, color: 'var(--muted)' }}>
              <span style={{ display: 'inline-block', width: 14, height: 3, background: FAM_COLOR[family] || '#e74c3c', marginRight: 3, verticalAlign: 'middle', borderRadius: 1 }} />
              Receptor–Gα (inter-chain)
            </span>
            <span style={{ fontSize: 9, color: 'var(--muted)' }}>
              <span style={{ display: 'inline-block', width: 14, height: 3, background: '#bbb', marginRight: 3, verticalAlign: 'middle', borderRadius: 1 }} />
              Intra-chain
            </span>
          </>
        )}
        <span style={{ fontSize: 9, color: 'var(--faint)' }}>
          Chord thickness ∝ frequency
        </span>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: 'fixed', left: tooltip.x + 12, top: tooltip.y - 30,
          background: 'var(--ink)', color: '#fff', fontSize: 11, padding: '4px 10px',
          borderRadius: 4, pointerEvents: 'none', zIndex: 9999, whiteSpace: 'nowrap',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        }}>
          <strong>Res {tooltip.resid}</strong> ({tooltip.subunit})
          <br />
          {tooltip.nEdges} contacts ({tooltip.nInter} interchain)
        </div>
      )}
    </div>
  )
}
