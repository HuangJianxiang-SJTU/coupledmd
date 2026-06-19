// All API calls go through this module.
// BASE is empty in dev (Vite proxy handles /api); set VITE_API_BASE in .env for production.
const BASE = import.meta.env.VITE_API_BASE || ''

async function get(path, params = {}) {
  const url = new URL(`${BASE}${path}`, window.location.origin)
  Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v))
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${path}`)
  return res.json()
}

export const api = {
  health: () => get('/api/v1/health'),
  families: () => get('/api/v1/families'),

  systems: (params) => get('/api/v1/systems', params),
  system: (sid) => get(`/api/v1/systems/${sid}`),
  systemPockets: (sid, gpcrdb = true) => get(`/api/v1/systems/${sid}/pockets`, { gpcrdb }),
  systemGateways: (sid) => get(`/api/v1/systems/${sid}/gateways`),

  consensusDruggable: () => get('/api/v1/consensus/pockets/druggable'),
  consensusOrthosteric: () => get('/api/v1/consensus/pockets/orthosteric'),
  consensusGateways: (params) => get('/api/v1/consensus/gateways', params),
  nominations: () => get('/api/v1/consensus/nominations'),
  reorg: () => get('/api/v1/consensus/reorg'),
}
