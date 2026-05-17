import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Users, CreditCard, ShieldAlert, Sun, Moon, CalendarClock, Settings, LogOut } from 'lucide-react'
import { cn } from '../lib/utils'
import { useTheme } from '../lib/ThemeContext'
import { clearToken } from '../lib/auth'

const APP_VERSION = 'v2.7.0'

const NAV = [
  { to: '/dashboard',   label: 'Console',      icon: LayoutDashboard },
  { to: '/subscribers', label: 'Subscribers',  icon: Users },
  { to: '/payments',    label: 'Payments',     icon: CreditCard },
  { to: '/risk',        label: 'Risk',         icon: ShieldAlert },
  { to: '/bulk-update', label: 'Bulk Update',  icon: CalendarClock },
  { to: '/settings',    label: 'Settings',     icon: Settings },
]

export default function Layout() {
  const { theme, toggle } = useTheme()
  const navigate = useNavigate()

  function handleLogout() {
    clearToken()
    navigate('/login', { replace: true })
  }

  return (
    <div className="op" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* TOP BAR */}
      <header
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '10px 16px', borderBottom: '1px solid var(--op-line)',
          background: 'var(--op-card)', position: 'relative', zIndex: 2,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontFamily: 'IBM Plex Mono, monospace', fontSize: 11 }}>
          <span style={{ fontWeight: 600, letterSpacing: '.06em' }}>GSH ▍ BILLING</span>
          <span className="op-dim">·</span>
          <span className="op-accent op-mono">▍AURORA</span>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', fontFamily: 'IBM Plex Mono, monospace', fontSize: 11 }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <span className="op-blink" style={{ width: 6, height: 6, background: 'var(--op-accent)' }} />
            <span className="op-accent">LIVE</span>
          </span>
          <span className="op-dim">·</span>
          <span className="op-dim">{APP_VERSION}</span>
          <button className="op-btn" onClick={toggle} title="Toggle theme" style={{ padding: '5px 8px' }}>
            {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
          </button>
          <button className="op-btn op-btn-danger" onClick={handleLogout} title="Sign out" style={{ padding: '5px 8px' }}>
            <LogOut size={13} /> EXIT
          </button>
        </div>
      </header>

      {/* TAB NAV */}
      <nav style={{ display: 'flex', borderBottom: '1px solid var(--op-line)', background: 'var(--op-sub)' }}>
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => cn('op-tab', isActive && 'is-on')}
          >
            <Icon size={13} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* MAIN */}
      <main style={{ flex: 1, overflow: 'auto', padding: 16, position: 'relative', zIndex: 1 }}>
        <Outlet />
      </main>

      {/* STATUS BAR */}
      <footer
        style={{
          display: 'flex', justifyContent: 'space-between', padding: '6px 16px',
          borderTop: '1px solid var(--op-line)', background: 'var(--op-sub)',
          fontFamily: 'IBM Plex Mono, monospace', fontSize: 10,
          color: 'var(--op-dim)', letterSpacing: '.04em',
        }}
      >
        <span>READY · DB OK</span>
        <span>GSH WEB {APP_VERSION} · NODE-1</span>
        <span>F1 HELP · F12 CLI</span>
      </footer>
    </div>
  )
}
