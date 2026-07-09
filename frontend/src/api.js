// All API calls go through this module.
// BASE is empty in dev (Vite proxy handles /api); set VITE_API_BASE in .env for production.
const BASE = import.meta.env.VITE_API_BASE || ''

const MAX_RETRIES = 2
const RETRY_DELAY_MS = 1000
const TIMEOUT_MS = 30_000

async function get(path, params = {}, options = {}) {
  const url = new URL(`${BASE}${path}`, window.location.origin)
  Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v))

  const maxRetries = options.retries ?? MAX_RETRIES
  let lastError

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

    try {
      const res = await fetch(url, { signal: controller.signal })
      clearTimeout(timer)

      if (res.status === 429 && attempt < maxRetries) {
        // Rate-limited — wait and retry
        await new Promise(r => setTimeout(r, RETRY_DELAY_MS * (attempt + 1)))
        continue
      }

      if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${path}`)
      return res.json()
    } catch (e) {
      clearTimeout(timer)
      if (e.name === 'AbortError') {
        lastError = new Error(`Request timed out — ${path}`)
      } else {
        lastError = e
      }
      // Retry on network errors and 5xx (via the throw above for !ok)
      if (attempt < maxRetries && (e.name === 'AbortError' || e.message?.startsWith('5') || e.message?.includes('Failed to fetch'))) {
        await new Promise(r => setTimeout(r, RETRY_DELAY_MS * (attempt + 1)))
        continue
      }
    }
  }

  throw lastError || new Error(`Request failed after ${maxRetries + 1} attempts — ${path}`)
}

// POST with a JSON body. Used for account/key endpoints so credentials and
// API keys never appear in URLs (query strings are logged by nginx and saved
// in browser history).
async function post(path, body = {}) {
  const url = new URL(`${BASE}${path}`, window.location.origin)
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    })
    clearTimeout(timer)
    if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${path}`)
    return res.json()
  } finally {
    clearTimeout(timer)
  }
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

  vizMeta: (sid) => get(`/api/v1/systems/${sid}/viz/meta`),

  couplingGeometry: () => get('/api/v1/consensus/coupling'),
  gproteinBarcode: () => get('/api/v1/consensus/gprotein/barcode'),
  systemGprotein: (sid) => get(`/api/v1/systems/${sid}/gprotein`),
  systemContacts: (sid, params) => get(`/api/v1/systems/${sid}/contacts`, params),
  systemSubunitRanges: (sid) => get(`/api/v1/systems/${sid}/subunit-ranges`),

  // Optional accounts (convenience only — no data is account-gated).
  // Sent as POST so credentials/keys stay out of URLs.
  accountRegister: (params) => post('/api/v1/accounts/register', params),
  accountLogin: (params) => post('/api/v1/accounts/login', params),
  accountDelete: (params) => post('/api/v1/accounts/delete', params),
  accountExport: (params) => post('/api/v1/accounts/export', params),
  requestApiKey: (params) => post('/api/v1/keys/request', params),
  citation: () => get('/api/v1/citation'),
}
