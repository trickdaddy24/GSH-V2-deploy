import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, Users, CreditCard, ShieldAlert, Shield, Sun, Moon, CalendarClock, Settings } from 'lucide-react'
import { cn } from '../lib/utils'
import { useTheme } from '../lib/ThemeContext'

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

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-slate-950">
      {/* Sidebar */}
      <aside className="flex w-56 flex-col border-r border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="flex items-center gap-2 px-4 py-5">
          <Shield size={22} className="text-brand-500" />
          <span className="font-bold text-gray-900 dark:text-slate-100 tracking-tight">GuardianStreams</span>
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
                    ? 'bg-brand-600 text-white'
                    : 'text-gray-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800 hover:text-gray-900 dark:hover:text-slate-100',
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-gray-200 dark:border-slate-800 px-4 py-3 flex items-center justify-between">
          <span className="text-xs text-gray-400 dark:text-slate-600">GSH Web v2.2.4</span>
          <button
            onClick={toggle}
            className="rounded-md p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:text-slate-500 dark:hover:text-slate-200 dark:hover:bg-slate-800 transition-colors"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
