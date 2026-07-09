import { useState, useEffect, useRef } from 'react'
import './index.css'
import Home from './pages/Home'
import Systems from './pages/Systems'
import SystemDetail from './pages/SystemDetail'
import AtlasBrowser from './pages/AtlasBrowser'
import PartnerSwitch from './pages/PartnerSwitch'
import About from './pages/About'
import Help from './pages/Help'
import Privacy from './pages/Privacy'
import Terms from './pages/Terms'
import CookieConsent from './components/CookieConsent'
import { api } from './api'

function parseRoute() {
  const hash = window.location.hash.replace('#', '') || '/'
  if (hash.startsWith('/systems/')) return { page: 'system', id: hash.split('/')[2] }
  if (hash === '/systems') return { page: 'systems' }
  if (hash === '/atlas') return { page: 'atlas' }
  if (hash === '/compare') return { page: 'compare' }
  if (hash === '/about') return { page: 'about' }
  if (hash === '/help') return { page: 'help' }
  if (hash === '/privacy') return { page: 'privacy' }
  if (hash === '/terms') return { page: 'terms' }
  return { page: 'home' }
}

export default function App() {
  const [route, setRoute] = useState(parseRoute)
  const [account, setAccount] = useState(null)  // logged-in account or null
  const [showLogin, setShowLogin] = useState(false)
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPass, setLoginPass] = useState('')
  const [loginError, setLoginError] = useState('')
  const [showRegister, setShowRegister] = useState(false)
  const [regName, setRegName] = useState('')
  const [regInst, setRegInst] = useState('')
  const [regError, setRegError] = useState('')
  const loginRef = useRef(null)

  // Restore session from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('coupledmd_account')
    if (saved) {
      try { setAccount(JSON.parse(saved)) } catch {}
    }
  }, [])

  // Keep the view in sync with the URL hash so the browser Back/Forward
  // buttons (and manual hash edits) navigate. navigate() only sets the hash;
  // this listener does the actual route update.
  useEffect(() => {
    const onHashChange = () => setRoute(parseRoute())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e) {
      if (loginRef.current && !loginRef.current.contains(e.target)) {
        setShowLogin(false)
        setShowRegister(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  function navigate(path) {
    // Setting the hash fires the hashchange listener (see useEffect above),
    // which updates the route. If the hash is already `path` (e.g. clicking
    // the same nav link), hashchange won't fire, so update explicitly.
    if (window.location.hash === path) setRoute(parseRoute())
    else window.location.hash = path
  }

  async function handleLogin(e) {
    e.preventDefault()
    setLoginError('')
    try {
      const data = await api.accountLogin({ email: loginEmail, password: loginPass })
      setAccount(data.account)
      localStorage.setItem('coupledmd_account', JSON.stringify(data.account))
      setShowLogin(false)
      setLoginEmail('')
      setLoginPass('')
    } catch (err) {
      setLoginError('Invalid email or password')
    }
  }

  async function handleRegister(e) {
    e.preventDefault()
    setRegError('')
    if (loginPass.length < 8) { setRegError('Password must be at least 8 characters'); return }
    try {
      const data = await api.accountRegister({
        email: loginEmail, password: loginPass,
        name: regName, institution: regInst,
      })
      setAccount(data.account)
      localStorage.setItem('coupledmd_account', JSON.stringify(data.account))
      setShowRegister(false)
      setLoginEmail('')
      setLoginPass('')
      setRegName('')
      setRegInst('')
    } catch (err) {
      setRegError(err.message.includes('409') ? 'Email already registered' : 'Registration failed')
    }
  }

  function handleLogout() {
    setAccount(null)
    localStorage.removeItem('coupledmd_account')
  }

  async function handleDeleteAccount() {
    if (!account) return
    if (!confirm('Delete your account and all associated data? This cannot be undone.')) return
    try {
      await api.accountDelete({ email: account.email, password: prompt('Enter your password to confirm:') })
      setAccount(null)
      localStorage.removeItem('coupledmd_account')
    } catch {}
  }

  return (
    <>
      <div className="topbar">
        <div className="topbar-inner">
          <span className="brand" style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>
            Coupled<span>MD</span>
          </span>
          <nav>
            <a href="#/systems" onClick={e => { e.preventDefault(); navigate('/systems') }}>Systems</a>
            <a href="#/atlas" onClick={e => { e.preventDefault(); navigate('/atlas') }}>Atlas</a>
            <a href="#/compare" onClick={e => { e.preventDefault(); navigate('/compare') }}>Compare</a>
            <a href="#/about" onClick={e => { e.preventDefault(); navigate('/about') }}>About</a>
            <a href="#/help" onClick={e => { e.preventDefault(); navigate('/help') }}>Help</a>
            <a href="/api/docs" target="_blank" rel="noreferrer">API</a>

            {/* Account link */}
            <div ref={loginRef} style={{ position: 'relative', display: 'inline-block' }}>
              {account ? (
                <span style={{ position: 'relative' }}>
                  <button onClick={() => setShowLogin(!showLogin)}
                    style={{ background: 'none', border: 'none', color: 'var(--accent)',
                             cursor: 'pointer', fontSize: 'inherit', fontWeight: 600,
                             fontFamily: 'inherit', padding: 0 }}>
                    {account.name || account.email.split('@')[0]}
                  </button>
                  {showLogin && (
                    <div style={{
                      position: 'absolute', right: 0, top: '100%', marginTop: 8,
                      background: '#fff', border: '1px solid var(--rule)', borderRadius: 6,
                      boxShadow: '0 4px 16px rgba(0,0,0,0.12)', minWidth: 220, zIndex: 100,
                      padding: 12, fontSize: 12,
                    }}>
                      <div style={{ color: 'var(--muted)', marginBottom: 8 }}>
                        {account.email}
                      </div>
                      {account.api_key && (
                        <div style={{ marginBottom: 8, padding: '6px 8px', background: 'var(--panel)',
                                      borderRadius: 4, fontSize: 10, fontFamily: 'monospace',
                                      wordBreak: 'break-all' }}>
                          API key: {account.api_key}
                        </div>
                      )}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <button onClick={handleLogout}
                          style={{ background: 'var(--panel)', border: '1px solid var(--rule)',
                                   borderRadius: 4, padding: '6px 12px', cursor: 'pointer',
                                   fontSize: 12, color: 'var(--ink)' }}>
                          Log out
                        </button>
                        <button onClick={handleDeleteAccount}
                          style={{ background: 'none', border: 'none', color: '#c0392b',
                                   cursor: 'pointer', fontSize: 11, padding: '4px 0', textAlign: 'left' }}>
                          Delete account
                        </button>
                      </div>
                      <p style={{ fontSize: 9, color: 'var(--faint)', marginTop: 8, marginBottom: 0 }}>
                        Account is optional. All data remains accessible without login.
                      </p>
                    </div>
                  )}
                </span>
              ) : (
                <span style={{ position: 'relative' }}>
                  <button onClick={() => { setShowLogin(!showLogin); setShowRegister(false); setLoginError('') }}
                    style={{ background: 'none', border: 'none', color: 'var(--accent)',
                             cursor: 'pointer', fontSize: 'inherit', fontWeight: 600,
                             fontFamily: 'inherit', padding: 0 }}>
                    Login
                  </button>
                  {showLogin && !showRegister && (
                    <div style={{
                      position: 'absolute', right: 0, top: '100%', marginTop: 8,
                      background: '#fff', border: '1px solid var(--rule)', borderRadius: 6,
                      boxShadow: '0 4px 16px rgba(0,0,0,0.12)', minWidth: 260, zIndex: 100,
                      padding: 16, fontSize: 12,
                    }}>
                      <form onSubmit={handleLogin}>
                        <div style={{ marginBottom: 8 }}>
                          <label style={{ display: 'block', fontSize: 10, color: 'var(--faint)',
                                          marginBottom: 2, textTransform: 'uppercase',
                                          letterSpacing: '0.06em' }}>Email</label>
                          <input type="email" value={loginEmail} onChange={e => setLoginEmail(e.target.value)}
                            required style={{ width: '100%', padding: '6px 8px', border: '1px solid var(--rule)',
                            borderRadius: 4, fontSize: 12, boxSizing: 'border-box' }} />
                        </div>
                        <div style={{ marginBottom: 8 }}>
                          <label style={{ display: 'block', fontSize: 10, color: 'var(--faint)',
                                          marginBottom: 2, textTransform: 'uppercase',
                                          letterSpacing: '0.06em' }}>Password</label>
                          <input type="password" value={loginPass} onChange={e => setLoginPass(e.target.value)}
                            required style={{ width: '100%', padding: '6px 8px', border: '1px solid var(--rule)',
                            borderRadius: 4, fontSize: 12, boxSizing: 'border-box' }} />
                        </div>
                        {loginError && <div style={{ color: '#c0392b', fontSize: 11, marginBottom: 6 }}>{loginError}</div>}
                        <button type="submit"
                          style={{ width: '100%', background: 'var(--accent)', color: '#fff', border: 'none',
                                   borderRadius: 4, padding: '8px', fontWeight: 700, cursor: 'pointer',
                                   fontSize: 12 }}>
                          Log in
                        </button>
                      </form>
                      <div style={{ borderTop: '1px solid var(--rule)', marginTop: 10, paddingTop: 10 }}>
                        <button onClick={() => { setShowRegister(true); setRegError('') }}
                          style={{ background: 'none', border: 'none', color: 'var(--accent)',
                                   cursor: 'pointer', fontSize: 11, padding: 0 }}>
                          Create account
                        </button>
                        <span style={{ color: 'var(--faint)', marginLeft: 6, fontSize: 10 }}>optional</span>
                      </div>
                    </div>
                  )}
                  {showLogin && showRegister && (
                    <div style={{
                      position: 'absolute', right: 0, top: '100%', marginTop: 8,
                      background: '#fff', border: '1px solid var(--rule)', borderRadius: 6,
                      boxShadow: '0 4px 16px rgba(0,0,0,0.12)', minWidth: 280, zIndex: 100,
                      padding: 16, fontSize: 12,
                    }}>
                      <form onSubmit={handleRegister}>
                        <div style={{ marginBottom: 8 }}>
                          <label style={{ display: 'block', fontSize: 10, color: 'var(--faint)',
                                          marginBottom: 2, textTransform: 'uppercase',
                                          letterSpacing: '0.06em' }}>Email *</label>
                          <input type="email" value={loginEmail} onChange={e => setLoginEmail(e.target.value)}
                            required style={{ width: '100%', padding: '6px 8px', border: '1px solid var(--rule)',
                            borderRadius: 4, fontSize: 12, boxSizing: 'border-box' }} />
                        </div>
                        <div style={{ marginBottom: 8 }}>
                          <label style={{ display: 'block', fontSize: 10, color: 'var(--faint)',
                                          marginBottom: 2, textTransform: 'uppercase',
                                          letterSpacing: '0.06em' }}>Password * (min 8 chars)</label>
                          <input type="password" value={loginPass} onChange={e => setLoginPass(e.target.value)}
                            required minLength={8} style={{ width: '100%', padding: '6px 8px',
                            border: '1px solid var(--rule)', borderRadius: 4, fontSize: 12,
                            boxSizing: 'border-box' }} />
                        </div>
                        <div style={{ marginBottom: 8 }}>
                          <label style={{ display: 'block', fontSize: 10, color: 'var(--faint)',
                                          marginBottom: 2, textTransform: 'uppercase',
                                          letterSpacing: '0.06em' }}>Name (optional)</label>
                          <input type="text" value={regName} onChange={e => setRegName(e.target.value)}
                            style={{ width: '100%', padding: '6px 8px', border: '1px solid var(--rule)',
                            borderRadius: 4, fontSize: 12, boxSizing: 'border-box' }} />
                        </div>
                        <div style={{ marginBottom: 8 }}>
                          <label style={{ display: 'block', fontSize: 10, color: 'var(--faint)',
                                          marginBottom: 2, textTransform: 'uppercase',
                                          letterSpacing: '0.06em' }}>Institution (optional)</label>
                          <input type="text" value={regInst} onChange={e => setRegInst(e.target.value)}
                            style={{ width: '100%', padding: '6px 8px', border: '1px solid var(--rule)',
                            borderRadius: 4, fontSize: 12, boxSizing: 'border-box' }} />
                        </div>
                        {regError && <div style={{ color: '#c0392b', fontSize: 11, marginBottom: 6 }}>{regError}</div>}
                        <button type="submit"
                          style={{ width: '100%', background: 'var(--accent)', color: '#fff', border: 'none',
                                   borderRadius: 4, padding: '8px', fontWeight: 700, cursor: 'pointer',
                                   fontSize: 12 }}>
                          Create account
                        </button>
                      </form>
                      <div style={{ borderTop: '1px solid var(--rule)', marginTop: 10, paddingTop: 10 }}>
                        <button onClick={() => setShowRegister(false)}
                          style={{ background: 'none', border: 'none', color: 'var(--accent)',
                                   cursor: 'pointer', fontSize: 11, padding: 0 }}>
                          Back to login
                        </button>
                      </div>
                      <p style={{ fontSize: 9, color: 'var(--faint)', marginTop: 8, marginBottom: 0 }}>
                        Account is optional. All data remains accessible without login.
                      </p>
                    </div>
                  )}
                </span>
              )}
            </div>
          </nav>
        </div>
      </div>

      {route.page === 'home'    && <Home navigate={navigate} />}
      {route.page === 'systems' && <Systems navigate={navigate} />}
      {route.page === 'system'  && <SystemDetail id={route.id} navigate={navigate} />}
      {route.page === 'atlas'   && <AtlasBrowser navigate={navigate} />}
      {route.page === 'compare' && <PartnerSwitch navigate={navigate} />}
      {route.page === 'about'   && <About />}
      {route.page === 'help'   && <Help />}
      {route.page === 'privacy' && <Privacy />}
      {route.page === 'terms'   && <Terms />}

      <CookieConsent />

      {/* Footer with legal links */}
      <footer style={{
        borderTop: '1px solid var(--rule)', padding: '16px 24px',
        display: 'flex', gap: 16, justifyContent: 'center',
        fontSize: 11, color: 'var(--faint)', background: 'var(--panel)',
      }}>
        <a href="#/privacy" style={{ color: 'var(--faint)' }}>Privacy</a>
        <a href="#/terms" style={{ color: 'var(--faint)' }}>Terms of Use</a>
        <span>Data: CC-BY-4.0</span>
        <span>Code: MIT</span>
      </footer>
    </>
  )
}
