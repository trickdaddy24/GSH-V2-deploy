import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, Users, CreditCard, ShieldAlert, Shield } from 'lucide-react'
import { cn } from '../lib/utils'

const NAV = [
  { to: '/dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
  { to: '/subscribers', label: 'Subscribers',  icon: Users },
  { to: '/payments',    label: 'Payments',     icon: CreditCard },
  { to: '/risk',        label: 'Risk',         icon: ShieldAlert },
]

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-56 flex-col border-r border-slate-800 bg-slate-900">
        <div className="flex items-center gap-2 px-4 py-5">
          <Shield size={22} className="text-brand-500" />
          <span className="font-bold text-slate-100 tracking-tight">GuardianStreams</span>
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
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100',
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-3 text-xs text-slate-600">GSH Web v1.0</div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
