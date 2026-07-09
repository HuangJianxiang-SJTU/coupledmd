export default function Privacy() {
  return (
    <div className="page" style={{ maxWidth: 720 }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: 20 }}>Privacy Policy</h1>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>Data We Collect</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          CoupledMD is a fully open-access resource. No personal data is required to browse,
          search, download, or use the API. If you optionally register an account, we store:
        </p>
        <ul style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.8, paddingLeft: 20 }}>
          <li>Email address (required to register an optional account)</li>
          <li>Name, institution, research area (all optional)</li>
          <li>A hashed password (argon2id — never stored in plaintext)</li>
          <li>API key for higher rate limits</li>
        </ul>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>Cookies &amp; Local Storage</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          CoupledMD does not use cookies. Optional account sessions are stored in your
          browser's localStorage (not cookies). No third-party or cross-site tracking
          cookies are used, and no analytics cookies are set. A one-time consent banner
          is shown on first visit and its dismissal is also recorded in localStorage.
        </p>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>Server Logs</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          Standard server-side access logs (IP address, requested URL, timestamp, user agent)
          are retained for operational and security purposes. These logs are not shared with
          third parties and are rotated regularly.
        </p>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>Data Minimisation</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          We collect the minimum data necessary. Account fields beyond email and password
          are optional. You can delete your account and all associated data at any time via
          the account settings or the API (<code>/api/v1/accounts/delete</code>).
        </p>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>GDPR / PIPL Compliance</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          As an international resource, we respect both the EU General Data Protection
          Regulation (GDPR) and China's Personal Information Protection Law (PIPL).
          You may request export of all your stored data (<code>/api/v1/accounts/export</code>)
          and deletion of your account at any time.
        </p>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>Third-Party Services</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          CoupledMD does not integrate any third-party analytics, advertising, or tracking
          services. The NGL molecular viewer loads structure and trajectory data only from
          our own servers.
        </p>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>Contact</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          For privacy-related inquiries, contact the CoupledMD team.
        </p>
      </section>
    </div>
  )
}
