export default function Terms() {
  return (
    <div className="page" style={{ maxWidth: 720 }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: 20 }}>Terms of Use</h1>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>Open Access</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          CoupledMD is a fully open-access resource. No login, registration, or email is
          required to access any data, download, or API endpoint. All content is freely
          available to all users without restriction.
        </p>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>Licence</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          <strong>Data:</strong> All datasets, analysis results, trajectories, and derived
          products are licensed under <strong>Creative Commons Attribution 4.0 International
          (CC-BY-4.0)</strong>. You are free to share and adapt the data for any purpose,
          including commercial, provided you give appropriate credit.
        </p>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7, marginTop: 8 }}>
          <strong>Code:</strong> The CoupledMD software (source code, build scripts,
          configuration) is licensed under the <strong>MIT License</strong>.
        </p>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>Citation</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          If you use CoupledMD data or software in your research, please cite:
        </p>
        <blockquote style={{
          borderLeft: '3px solid var(--accent)', margin: '12px 0', padding: '8px 16px',
          color: 'var(--muted)', fontSize: 14, background: 'var(--panel)', borderRadius: '0 var(--radius) var(--radius) 0',
        }}>
          Huang J et al., CoupledMD: a web resource for GPCR–G-protein molecular dynamics.
          Citation details to be confirmed (pre-publication).
        </blockquote>
        <p style={{ color: 'var(--faint)', fontSize: 12 }}>
          The Zenodo DOI for the archived dataset is{' '}
          <a href="https://doi.org/10.5281/zenodo.21395292" target="_blank" rel="noreferrer">
            10.5281/zenodo.21395292
          </a>.
        </p>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>Rate Limits</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          Anonymous users are subject to a per-IP rate limit of 60 requests per minute.
          This is generous for normal browsing and API use. If you need higher limits
          for programmatic access, request a free API key at{' '}
          <code>/api/v1/keys/request</code> — no email required.
        </p>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8 }}>No Warranty</h2>
        <p style={{ color: 'var(--muted)', fontSize: 14, lineHeight: 1.7 }}>
          CoupledMD is provided "as is" without warranty of any kind, express or implied.
          The authors and hosting institution make no warranties regarding accuracy,
          completeness, or fitness for any particular purpose.
        </p>
      </section>
    </div>
  )
}
