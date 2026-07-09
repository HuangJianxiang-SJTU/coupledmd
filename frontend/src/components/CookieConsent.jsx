import { useState, useEffect } from 'react'

/**
 * Consent banner — shown once on first visit.
 * CoupledMD uses localStorage (not cookies) for optional account sessions and
 * for this banner's dismissal flag. No third-party or tracking cookies are set.
 */
export default function CookieConsent() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Show banner if user hasn't dismissed it
    const dismissed = localStorage.getItem('coupledmd_cookie_consent')
    if (!dismissed) {
      setVisible(true)
    }
  }, [])

  const handleAccept = () => {
    localStorage.setItem('coupledmd_cookie_consent', 'accepted')
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 9999,
      background: 'var(--ink)', color: '#fff', padding: '12px 24px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      gap: 16, fontSize: 12, boxShadow: '0 -2px 12px rgba(0,0,0,0.2)',
    }}>
      <span style={{ flex: 1 }}>
        This site uses localStorage (not cookies) for optional account sessions.
        No third-party or cross-site tracking cookies are used.{' '}
        <a href="#/privacy" style={{ color: '#8cb4ff', textDecoration: 'underline' }}>
          Privacy policy
        </a>
      </span>
      <button onClick={handleAccept} style={{
        background: '#fff', color: 'var(--ink)', border: 'none',
        borderRadius: 4, padding: '6px 16px', fontWeight: 700,
        fontSize: 12, cursor: 'pointer', whiteSpace: 'nowrap',
      }}>
        OK
      </button>
    </div>
  )
}
