import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../lib/auth'

const APP_VERSION = 'v2.7.0'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="op"
      style={{ width: '100%', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
    >
      {/* Top status bar */}
      <div
        style={{
          position: 'fixed', top: 0, left: 0, right: 0, padding: '10px 24px',
          borderBottom: '1px solid var(--op-line)', display: 'flex',
          justifyContent: 'space-between', alignItems: 'center',
          fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, zIndex: 2,
        }}
      >
        <div style={{ display: 'flex', gap: 18, alignItems: 'center' }}>
          <span style={{ fontWeight: 600, letterSpacing: '.06em' }}>
            GSH ▍ GUARDIANSTREAMS BILLING SYSTEM
          </span>
          <span className="op-dim">{APP_VERSION}</span>
          <span className="op-dim">·</span>
          <span className="op-mono op-accent">AURORA</span>
        </div>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <span className="op-blink" style={{ width: 6, height: 6, background: 'var(--op-accent)' }} />
          <span className="op-accent">SYSTEMS NOMINAL</span>
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '420px 280px', gap: 1, background: 'var(--op-line)' }}>
        {/* Form panel */}
        <form className="op-panel" style={{ padding: '36px 36px 28px' }} onSubmit={handleSubmit}>
          <div className="op-eyebrow" style={{ marginBottom: 8 }}>SESSION ▸ AUTHENTICATE</div>
          <div style={{ fontSize: 28, fontWeight: 600, letterSpacing: '-.01em', lineHeight: 1.1 }}>
            Operator Console
          </div>
          <div className="op-dim op-mono" style={{ fontSize: 11, marginTop: 6 }}>
            GuardianStreams billing &amp; subscriber management.
          </div>

          <hr className="op-divider" style={{ margin: '24px 0 20px' }} />

          {error && (
            <div
              className="op-mono"
              style={{
                marginBottom: 14, padding: '9px 12px', fontSize: 11,
                color: 'var(--op-accent2)', border: '1px solid var(--op-accent2)',
                background: 'var(--op-chip-alert)',
              }}
            >
              ▸ {error}
            </div>
          )}

          <div style={{ display: 'grid', gap: 14 }}>
            <div>
              <div className="op-eyebrow" style={{ marginBottom: 6 }}>OPERATOR USERNAME</div>
              <input
                className="op-input" autoComplete="username" required
                placeholder="admin" value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div>
              <div className="op-eyebrow" style={{ marginBottom: 6 }}>PASSWORD</div>
              <input
                className="op-input" type="password" autoComplete="current-password" required
                placeholder="••••••••••" value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit" disabled={loading}
            className="op-btn op-btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '10px 14px', marginTop: 24 }}
          >
            {loading ? '▸ AUTHENTICATING…' : '▸ AUTHENTICATE'}
          </button>

          <div className="op-dim op-mono" style={{ fontSize: 10, marginTop: 18, display: 'flex', justifyContent: 'space-between' }}>
            <span>LAN OPERATOR SESSION</span>
            <span className="op-accent">● TLS 1.3</span>
          </div>
        </form>

        {/* Side panel — static system info (pre-auth: no live data) */}
        <div className="op-panel" style={{ padding: '28px 22px', display: 'flex', flexDirection: 'column' }}>
          <div className="op-eyebrow" style={{ marginBottom: 14 }}>SYSTEM</div>
          {[
            ['SERVICE', 'BILLING API'],
            ['TRANSPORT', 'HTTPS / TLS 1.3'],
            ['AUTH', 'JWT SESSION'],
            ['BUILD', APP_VERSION],
          ].map(([k, v], i) => (
            <div
              key={i}
              style={{
                padding: '12px 0', borderBottom: i < 3 ? '1px solid var(--op-line)' : 'none',
                display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
              }}
            >
              <div className="op-eyebrow" style={{ fontSize: 9 }}>{k}</div>
              <div className="op-mono" style={{ fontSize: 12 }}>{v}</div>
            </div>
          ))}
          <div style={{ marginTop: 'auto', paddingTop: 18 }}>
            <span className="op-dim op-mono" style={{ fontSize: 10 }}>
              Authenticate to load live console metrics.
            </span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          position: 'fixed', bottom: 0, left: 0, right: 0, padding: '8px 24px',
          borderTop: '1px solid var(--op-line)', display: 'flex',
          justifyContent: 'space-between', fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 10, color: 'var(--op-dim)', letterSpacing: '.04em',
        }}
      >
        <span>GSH WEB {APP_VERSION} · NODE-1</span>
        <span>GUARDIANSTREAMS</span>
        <span>F1 HELP · F12 CLI</span>
      </div>
    </div>
  )
}
