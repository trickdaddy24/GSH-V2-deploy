import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Users, CreditCard, ShieldAlert, Shield, Sun, Moon, CalendarClock, Settings, LogOut } from 'lucide-react'
import { cn } from '../lib/utils'
import { useTheme } from '../lib/ThemeContext'
import { clearToken } from '../lib/auth'

const NAV = [
  { to: '/dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
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
    <div className="flex h-screen overflow-hidden bg-gsh-bg dark:bg-[#1a1f2e]">
      {/* Sidebar */}
      <aside className="flex w-56 flex-col border-r border-gsh-border dark:border-[#2e3650] bg-white dark:bg-[#242938]">
        <div className="flex items-center gap-2 px-4 py-5">
          <Shield size={22} className="text-gsh-accent" />
          <span className="font-bold text-gsh-text dark:text-[#e0e6f0] tracking-tight">GuardianStreams</span>
        </div>

        <nav className="flex-1 space-y-0.5 px-2 py-2">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors',
                  isActive
                    ? 'bg-[rgba(138,77,255,0.08)] dark:bg-[rgba(138,77,255,0.12)] text-gsh-accent dark:text-[#e0e6f0] border-l-2 border-gsh-accent dark:border-[#00E0FF] pl-[10px]'
                    : 'text-gsh-muted dark:text-[#8899aa] hover:bg-gray-100 dark:hover:bg-[rgba(255,255,255,0.04)] hover:text-gsh-text dark:hover:text-[#e0e6f0]',
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-gsh-border dark:border-[#2e3650] px-4 py-3 flex items-center justify-between">
          <span className="text-xs text-gsh-muted dark:text-[#2e3650] font-mono">GSH Web v2.4.0</span>
          <div className="flex items-center gap-1">
            <button
              onClick={toggle}
              className="rounded-md p-1.5 text-gsh-muted hover:text-gsh-text hover:bg-gray-100 dark:text-[#8899aa] dark:hover:text-[#e0e6f0] dark:hover:bg-[rgba(255,255,255,0.06)] transition-colors"
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
            </button>
            <button
              onClick={handleLogout}
              className="rounded-md p-1.5 text-gsh-muted hover:text-red-600 hover:bg-red-50 dark:text-[#8899aa] dark:hover:text-red-400 dark:hover:bg-red-900/20 transition-colors"
              title="Sign out"
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
