# GSH Design Token System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `brand.*` sky-blue token system with a `gsh.*` token namespace (Saltbox dark navy + LoginX purple/cyan accents) and re-theme all components and pages to use the new tokens.

**Architecture:** Define 10 tokens in `tailwind.config.js` under `gsh.*`. Light-mode values are Tailwind config defaults; dark-mode overrides use `dark:` prefix classes in components. No runtime theming changes — existing `ThemeContext` and `darkMode: 'class'` config remain untouched.

**Tech Stack:** React 18, Vite, Tailwind CSS 3.4, TypeScript. No test framework — verification is visual via `npm run dev`.

**Important workaround:** `gsh-muted` resolves to its light value (`#6B7280`) even with `dark:` prefix — Tailwind does not support per-mode custom values. Always use `dark:text-[#8899aa]` directly for dark muted text (never `dark:text-gsh-muted`). Same applies to all background/border dark values — always write raw hex in `dark:` classes.

---

## File Map

| File | Change |
|---|---|
| `web/frontend/tailwind.config.js` | Replace `brand.*` with `gsh.*` tokens |
| `web/frontend/src/index.css` | Body bg/text + `<pre>` code block styles |
| `web/frontend/src/components/Layout.tsx` | Sidebar bg, nav active/hover, borders, footer |
| `web/frontend/src/components/ui/Card.tsx` | Card bg, border, CardTitle muted text |
| `web/frontend/src/components/ui/Button.tsx` | All 4 variants |
| `web/frontend/src/components/ui/Badge.tsx` | `default` and `muted` variants |
| `web/frontend/src/components/ui/Input.tsx` | Border, focus ring, dark bg |
| `web/frontend/src/components/StatCard.tsx` | Value color, icon bg, label/sub colors, default iconColor |
| `web/frontend/src/pages/Login.tsx` | Logo icon bg, form card, inputs, submit button |
| `web/frontend/src/pages/Dashboard.tsx` | iconColor on brand-500 StatCards, heading |
| `web/frontend/src/pages/Subscribers.tsx` | Select dark classes, table dark classes, headings |
| `web/frontend/src/pages/Settings.tsx` | Toggle `bg-brand-600`, selects, code element |
| `web/frontend/src/pages/SubscriberDetail.tsx` | Back button, headings, dark text classes |
| `web/frontend/src/pages/Risk.tsx` | Headings, mode-toggle button classes |
| `web/frontend/src/pages/BulkUpdate.tsx` | Headings, any hardcoded dark classes |
| `web/frontend/src/pages/Payments.tsx` | Headings, any hardcoded dark classes |

---

## Task 1: Tailwind Config — Define gsh.* tokens

**Files:**
- Modify: `web/frontend/tailwind.config.js`

- [ ] **Step 1: Start the dev server** (keep running for all tasks)

```bash
cd "web/frontend" && npm run dev
```

Open `http://localhost:5173` in browser. Leave it running throughout.

- [ ] **Step 2: Replace the entire tailwind.config.js**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gsh: {
          bg:             '#FFFFFF',
          card:           '#F9F9FB',
          border:         '#E5E7EB',
          accent:         '#8A4DFF',
          'accent-hover': '#7A3DEF',
          muted:          '#6B7280',
          text:           '#0B0F2A',
          cyan:           '#2EC7FF',
          lavender:       '#BFA4FF',
          'code-bg':      '#f6f8fa',
        },
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 3: Verify no build errors**

Check the terminal running `npm run dev`. Expected: no errors. The app may look broken (brand-* classes now resolve to nothing) — that's expected until components are updated.

- [ ] **Step 4: Commit**

```bash
git add web/frontend/tailwind.config.js
git commit -m "feat: add gsh.* design tokens, remove brand.* from tailwind config"
```

---

## Task 2: Global CSS — Body styles + code block

**Files:**
- Modify: `web/frontend/src/index.css`

- [ ] **Step 1: Replace index.css entirely**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gsh-bg text-gsh-text antialiased;
  }
  .dark body {
    @apply bg-[#1a1f2e] text-[#e0e6f0];
  }
  pre, code {
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', ui-monospace, monospace;
  }
  pre {
    @apply bg-gsh-code-bg dark:bg-[#0d1117] border border-gsh-border dark:border-[#2e3650] rounded-md p-3 text-sm overflow-x-auto;
  }
}
```

- [ ] **Step 2: Verify in browser**

With dark mode active: body background should be `#1a1f2e` (deep navy). With light mode: body should be white `#FFFFFF`.

- [ ] **Step 3: Commit**

```bash
git add web/frontend/src/index.css
git commit -m "feat: update body bg/text to gsh tokens, add code block base styles"
```

---

## Task 3: Layout.tsx — Sidebar re-theme

**Files:**
- Modify: `web/frontend/src/components/Layout.tsx`

Current file is 81 lines. Replace the full file content:

- [ ] **Step 1: Replace Layout.tsx**

```tsx
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
                    ? 'bg-[rgba(138,77,255,0.08)] dark:bg-[rgba(138,77,255,0.12)] text-gsh-accent dark:text-[#e0e6f0] border-l-2 border-gsh-accent dark:border-gsh-cyan pl-[10px]'
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
          <span className="text-xs text-gsh-border dark:text-[#2e3650] font-mono">GSH Web v2.3.0</span>
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
```

- [ ] **Step 2: Verify in browser**

Dark mode: sidebar is `#242938`, active nav item has purple bg tint + cyan left border, inactive items are `#8899aa`, version text is barely visible `#2e3650`. Light mode: sidebar is white, active nav is purple-tinted with purple left border.

- [ ] **Step 3: Commit**

```bash
git add web/frontend/src/components/Layout.tsx
git commit -m "feat: re-theme Layout sidebar with gsh tokens"
```

---

## Task 4: Card.tsx — Card surface re-theme

**Files:**
- Modify: `web/frontend/src/components/ui/Card.tsx`

- [ ] **Step 1: Replace Card.tsx**

```tsx
import { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('rounded-xl bg-white dark:bg-[#242938] border border-gsh-border dark:border-[#2e3650] p-4', className)}
      {...props}
    />
  )
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mb-3 flex items-center justify-between', className)} {...props} />
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn('text-sm font-semibold text-gsh-muted dark:text-[#8899aa] uppercase tracking-wide', className)} {...props} />
}
```

- [ ] **Step 2: Verify in browser**

Dark mode: cards should be `#242938` with `#2e3650` borders. Light mode: white cards with light gray borders.

- [ ] **Step 3: Commit**

```bash
git add web/frontend/src/components/ui/Card.tsx
git commit -m "feat: re-theme Card with gsh tokens"
```

---

## Task 5: Button.tsx — All variants

**Files:**
- Modify: `web/frontend/src/components/ui/Button.tsx`

- [ ] **Step 1: Replace Button.tsx**

```tsx
import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

const variants = {
  primary:   'bg-gsh-accent hover:bg-gsh-accent-hover text-white',
  secondary: 'bg-gsh-card hover:bg-gray-200 dark:bg-[rgba(255,255,255,0.05)] dark:hover:bg-[rgba(255,255,255,0.08)] text-gsh-muted dark:text-[#8899aa] border border-gsh-border dark:border-[#2e3650]',
  danger:    'bg-red-600 hover:bg-red-700 text-white dark:bg-red-700 dark:hover:bg-red-600',
  ghost:     'bg-transparent hover:bg-gray-100 dark:hover:bg-[rgba(255,255,255,0.05)] text-gsh-muted dark:text-[#8899aa]',
}

const sizes = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-4 py-1.5 text-sm',
  lg: 'px-5 py-2 text-base',
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md font-medium transition-colors',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  ),
)

Button.displayName = 'Button'
export default Button
```

- [ ] **Step 2: Verify in browser**

Primary buttons should be purple `#8A4DFF`. Secondary: light gray bg with border. Ghost: transparent. Danger: red. Check both modes.

- [ ] **Step 3: Commit**

```bash
git add web/frontend/src/components/ui/Button.tsx
git commit -m "feat: re-theme Button variants with gsh tokens"
```

---

## Task 6: Badge.tsx — Default and muted variants

**Files:**
- Modify: `web/frontend/src/components/ui/Badge.tsx`

- [ ] **Step 1: Replace Badge.tsx**

```tsx
import { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'muted'
}

const variants = {
  default: 'bg-[rgba(138,77,255,0.08)] text-gsh-accent dark:bg-[rgba(138,77,255,0.15)] dark:text-gsh-lavender border border-[rgba(138,77,255,0.2)] dark:border-[rgba(138,77,255,0.3)]',
  success: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
  danger:  'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  muted:   'bg-gsh-card text-gsh-muted dark:bg-[rgba(255,255,255,0.05)] dark:text-[#8899aa] border border-gsh-border dark:border-[#2e3650]',
}

export default function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        variants[variant],
        className,
      )}
      {...props}
    />
  )
}
```

- [ ] **Step 2: Verify in browser**

Navigate to Risk page (uses all badge variants). Default badge: purple/lavender. Success: emerald. Warning: yellow. Danger: red. Muted: gray.

- [ ] **Step 3: Commit**

```bash
git add web/frontend/src/components/ui/Badge.tsx
git commit -m "feat: re-theme Badge default and muted variants with gsh tokens"
```

---

## Task 7: Input.tsx — Border, focus ring, dark bg

**Files:**
- Modify: `web/frontend/src/components/ui/Input.tsx`

- [ ] **Step 1: Replace Input.tsx**

```tsx
import { InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/utils'

const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'w-full rounded-md border px-3 py-1.5 text-sm transition-colors',
        'bg-white border-gsh-border text-gsh-text placeholder:text-gsh-muted',
        'dark:bg-[#1a1f2e] dark:border-[#2e3650] dark:text-[#e0e6f0] dark:placeholder:text-[#8899aa]',
        'focus:outline-none focus:ring-2 focus:ring-gsh-accent focus:border-transparent',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className,
      )}
      {...props}
    />
  ),
)

Input.displayName = 'Input'
export default Input
```

- [ ] **Step 2: Verify in browser**

Navigate to Subscribers page. Search input: dark bg `#1a1f2e`, border `#2e3650`, focus ring purple `#8A4DFF`. Light mode: white bg, gray border.

- [ ] **Step 3: Commit**

```bash
git add web/frontend/src/components/ui/Input.tsx
git commit -m "feat: re-theme Input with gsh tokens"
```

---

## Task 8: StatCard.tsx — Value color, icon bg, labels

**Files:**
- Modify: `web/frontend/src/components/StatCard.tsx`

- [ ] **Step 1: Replace StatCard.tsx**

```tsx
import { LucideIcon } from 'lucide-react'
import { Card } from './ui/Card'
import { cn } from '../lib/utils'

interface Props {
  label: string
  value: string | number
  icon: LucideIcon
  iconColor?: string
  sub?: string
}

export default function StatCard({ label, value, icon: Icon, iconColor = 'text-gsh-accent', sub }: Props) {
  return (
    <Card className="flex items-start gap-4">
      <div className={cn('mt-0.5 rounded-lg bg-[#F3F0FF] dark:bg-[rgba(138,77,255,0.12)] p-2', iconColor)}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-xs text-gsh-muted dark:text-[#8899aa] uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-gsh-accent">{value}</p>
        {sub && <p className="text-xs text-gsh-muted dark:text-[#8899aa] mt-0.5">{sub}</p>}
      </div>
    </Card>
  )
}
```

- [ ] **Step 2: Verify in browser**

Dashboard stat values should be purple `#8A4DFF`. Icon containers: `#F3F0FF` light / purple-tinted dark. Labels: muted gray.

- [ ] **Step 3: Commit**

```bash
git add web/frontend/src/components/StatCard.tsx
git commit -m "feat: re-theme StatCard with gsh tokens — purple values, lavender icon bg"
```

---

## Task 9: Login.tsx — Standalone page re-theme

`Login.tsx` renders outside the `Layout` wrapper, so it has its own hardcoded bg, card, and brand-* colors.

**Files:**
- Modify: `web/frontend/src/pages/Login.tsx`

- [ ] **Step 1: Replace Login.tsx**

```tsx
import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { login } from '../lib/auth'

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
    <div className="flex min-h-screen items-center justify-center bg-gsh-bg dark:bg-[#1a1f2e] px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8 gap-3">
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gsh-accent text-white">
            <Shield size={24} />
          </div>
          <div className="text-center">
            <h1 className="text-xl font-bold text-gsh-text dark:text-[#e0e6f0]">GuardianStreams</h1>
            <p className="text-sm text-gsh-muted dark:text-[#8899aa]">Sign in to your account</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white dark:bg-[#242938] rounded-xl border border-gsh-border dark:border-[#2e3650] p-6 space-y-4 shadow-sm">
          {error && (
            <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-3 py-2 text-sm text-red-700 dark:text-red-400">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label htmlFor="username" className="block text-sm font-medium text-gsh-text dark:text-[#e0e6f0]">
              Username
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              required
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full rounded-lg border border-gsh-border dark:border-[#2e3650] bg-white dark:bg-[#1a1f2e] px-3 py-2 text-sm text-gsh-text dark:text-[#e0e6f0] placeholder-gsh-muted dark:placeholder-[#8899aa] focus:outline-none focus:ring-2 focus:ring-gsh-accent focus:border-transparent"
              placeholder="admin"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="password" className="block text-sm font-medium text-gsh-text dark:text-[#e0e6f0]">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gsh-border dark:border-[#2e3650] bg-white dark:bg-[#1a1f2e] px-3 py-2 text-sm text-gsh-text dark:text-[#e0e6f0] placeholder-gsh-muted dark:placeholder-[#8899aa] focus:outline-none focus:ring-2 focus:ring-gsh-accent focus:border-transparent"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-gsh-accent hover:bg-gsh-accent-hover disabled:opacity-60 disabled:cursor-not-allowed px-4 py-2 text-sm font-semibold text-white transition-colors focus:outline-none focus:ring-2 focus:ring-gsh-accent focus:ring-offset-2"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify in browser**

Navigate to `/login` (log out first). Dark mode: navy bg, dark card `#242938`, purple submit button. Light mode: white bg, white card, purple submit button.

- [ ] **Step 3: Commit**

```bash
git add web/frontend/src/pages/Login.tsx
git commit -m "feat: re-theme Login page with gsh tokens"
```

---

## Task 10: Dashboard.tsx + Settings.tsx — Page color cleanup

**Files:**
- Modify: `web/frontend/src/pages/Dashboard.tsx`
- Modify: `web/frontend/src/pages/Settings.tsx`

- [ ] **Step 1: Update Dashboard.tsx**

Apply these targeted changes (not a full replace — only the lines that change):

Line 28 — loading state:
```tsx
if (isLoading) return <p className="text-gsh-muted dark:text-[#8899aa]">Loading dashboard…</p>
```

Line 37 — heading:
```tsx
<h1 className="text-xl font-bold text-gsh-text dark:text-[#e0e6f0]">Dashboard</h1>
```

Lines 42, 43 — StatCard iconColor:
```tsx
iconColor="text-gsh-muted dark:text-[#8899aa]"   // was: "text-gray-400 dark:text-slate-500"
```

Lines 48–54 — revenue StatCards, change `text-brand-500` to `text-gsh-accent`:
```tsx
<StatCard label="Revenue This Month" value={formatCurrency(data.revenue_this_month)} icon={DollarSign} iconColor="text-gsh-accent" />
<StatCard
  label="Revenue Last Month"
  value={formatCurrency(data.revenue_last_month)}
  icon={TrendingUp}
  iconColor="text-gsh-accent"
  sub={revenueChange !== null ? `${revenueChange}% vs last month` : undefined}
/>
```

Line 66 — notification service text:
```tsx
<span className="capitalize text-gsh-text dark:text-[#e0e6f0]">{svc}</span>
<span className={cfg.enabled ? 'text-emerald-500' : 'text-gsh-muted dark:text-[#8899aa]'}>
```

Line 89 — card description:
```tsx
<p className="text-sm text-gsh-muted dark:text-[#8899aa] mb-4">
```

- [ ] **Step 2: Update Settings.tsx — Toggle component**

The `Toggle` component at line 71 uses `bg-brand-600`. Change to `bg-gsh-accent`:
```tsx
className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
  checked ? 'bg-gsh-accent' : 'bg-gray-300 dark:bg-[rgba(255,255,255,0.1)]'
}`}
```

Line 44 — loading state:
```tsx
if (isLoading) return <p className="text-gsh-muted dark:text-[#8899aa]">Loading settings…</p>
```

Line 49 — heading:
```tsx
<h1 className="text-xl font-bold text-gsh-text dark:text-[#e0e6f0]">Notification Settings</h1>
```

Line 51 — description `<code>` element (inline code tag):
```tsx
<p className="text-sm text-gsh-muted dark:text-[#8899aa]">
  Changes save to <code className="text-xs bg-gsh-code-bg dark:bg-[#0d1117] border border-gsh-border dark:border-[#2e3650] px-1 py-0.5 rounded">.env</code> and take effect immediately without restart.
</p>
```

Line 84 — Field label:
```tsx
<label className="text-xs text-gsh-muted dark:text-[#8899aa] mb-1 block">{label}</label>
```

Line 104 — SecretInput eye button:
```tsx
className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gsh-muted hover:text-gsh-text dark:text-[#8899aa] dark:hover:text-[#e0e6f0]"
```

- [ ] **Step 3: Verify in browser**

Dashboard: revenue icon colors should be purple. Settings: toggle should be purple when enabled. `.env` code element should use gsh-code-bg.

- [ ] **Step 4: Commit**

```bash
git add web/frontend/src/pages/Dashboard.tsx web/frontend/src/pages/Settings.tsx
git commit -m "feat: re-theme Dashboard and Settings pages with gsh tokens"
```

---

## Task 11: Subscribers.tsx — Table, select, dark classes

**Files:**
- Modify: `web/frontend/src/pages/Subscribers.tsx`

- [ ] **Step 1: Update headings and text**

Line 120 — heading:
```tsx
<h1 className="text-xl font-bold text-gsh-text dark:text-[#e0e6f0]">
  Subscribers
  {data && <span className="ml-2 text-sm font-normal text-gsh-muted dark:text-[#8899aa]">({data.total})</span>}
</h1>
```

- [ ] **Step 2: Update status filter `<select>`** (line 151–154)

```tsx
<select
  className="rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-gsh-accent
             bg-white border-gsh-border text-gsh-muted
             dark:bg-[#1a1f2e] dark:border-[#2e3650] dark:text-[#8899aa]"
  value={statusFilter}
  onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
>
```

- [ ] **Step 3: Update filter label and search icon** (lines 143, 161)

```tsx
// Search icon (line 143)
<Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gsh-muted dark:text-[#8899aa]" />

// Show Inactive label (line 161)
<label className="flex items-center gap-2 text-sm text-gsh-muted dark:text-[#8899aa] cursor-pointer">
```

- [ ] **Step 4: Update table** (lines 173–214)

Table wrapper:
```tsx
<div className="rounded-xl border border-gsh-border dark:border-[#2e3650] overflow-hidden">
```

Table head:
```tsx
<thead className="bg-gsh-card dark:bg-[#242938]">
```

Table header cells:
```tsx
className={`px-3 py-2 text-left text-xs font-medium text-gsh-muted dark:text-[#8899aa] uppercase tracking-wide select-none
  ${col.key ? 'cursor-pointer hover:text-gsh-text dark:hover:text-[#e0e6f0]' : ''}`}
```

Table body:
```tsx
<tbody className="divide-y divide-gsh-border dark:divide-[#2e3650] bg-white dark:bg-[#1a1f2e]">
```

Empty/loading rows:
```tsx
<td ... className="px-3 py-6 text-center text-gsh-muted dark:text-[#8899aa]">
```

Table rows:
```tsx
className="hover:bg-gsh-card dark:hover:bg-[rgba(255,255,255,0.03)] cursor-pointer transition-colors"
```

Table cells:
```tsx
<td key={col.label} className="px-3 py-2.5 text-gsh-text dark:text-[#e0e6f0]">
```

- [ ] **Step 5: Update pagination** (lines 220–231)

```tsx
<div className="flex items-center justify-between text-sm text-gsh-muted dark:text-[#8899aa]">
```

- [ ] **Step 6: Update AddForm** (line 255)

```tsx
<form ... className="rounded-xl border border-gsh-border dark:border-[#2e3650] bg-white dark:bg-[#242938] p-4 grid grid-cols-2 gap-3 md:grid-cols-3">
```

AddForm label elements (lines 257, 261, 265, etc.):
```tsx
<label className="text-xs text-gsh-muted dark:text-[#8899aa] mb-1 block">
```

AddForm package `<select>` (line 270–275):
```tsx
className="w-full rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-gsh-accent
           bg-white border-gsh-border text-gsh-text dark:bg-[#1a1f2e] dark:border-[#2e3650] dark:text-[#e0e6f0]"
```

- [ ] **Step 7: Verify in browser**

Subscribers page: table has navy dark bg, purple-border focused select, dark rows on hover are subtle. Add form card matches sidebar bg.

- [ ] **Step 8: Commit**

```bash
git add web/frontend/src/pages/Subscribers.tsx
git commit -m "feat: re-theme Subscribers page with gsh tokens"
```

---

## Task 12: SubscriberDetail.tsx + Risk.tsx + BulkUpdate.tsx + Payments.tsx

**Files:**
- Modify: `web/frontend/src/pages/SubscriberDetail.tsx`
- Modify: `web/frontend/src/pages/Risk.tsx`
- Modify: `web/frontend/src/pages/BulkUpdate.tsx`
- Modify: `web/frontend/src/pages/Payments.tsx`

These pages mostly use `Card`, `Button`, `Badge`, `Input` (already re-themed). Only headings, back buttons, and any inline dark class overrides need updating. Apply this pattern to all four files:

- [ ] **Step 1: Apply to SubscriberDetail.tsx**

Find and replace these patterns:
- `text-gray-900 dark:text-slate-100` → `text-gsh-text dark:text-[#e0e6f0]`
- `text-gray-400 dark:text-slate-400` → `text-gsh-muted dark:text-[#8899aa]`
- `text-gray-400 dark:text-slate-500` → `text-gsh-muted dark:text-[#8899aa]`
- `text-gray-500 dark:text-slate-400` → `text-gsh-muted dark:text-[#8899aa]`
- `dark:text-slate-100` → `dark:text-[#e0e6f0]`
- `dark:text-slate-300` → `dark:text-[#e0e6f0]`
- `dark:text-slate-400` → `dark:text-[#8899aa]`
- `dark:text-slate-500` → `dark:text-[#8899aa]`
- `dark:bg-slate-800` → `dark:bg-[rgba(255,255,255,0.05)]`
- `dark:bg-slate-900` → `dark:bg-[#242938]`
- `dark:border-slate-700` → `dark:border-[#2e3650]`
- `dark:border-slate-800` → `dark:border-[#2e3650]`
- `divide-gray-100 dark:divide-slate-800` → `divide-gsh-border dark:divide-[#2e3650]`

- [ ] **Step 2: Apply same pattern to Risk.tsx, BulkUpdate.tsx, Payments.tsx**

Use the same find/replace list from Step 1 on each file. Also replace any `brand-*` occurrences:
- `text-brand-500`, `text-brand-600` → `text-gsh-accent`
- `bg-brand-600`, `bg-brand-700` → `bg-gsh-accent`
- `ring-brand-500` → `ring-gsh-accent`
- `border-brand-500` → `border-gsh-accent`

- [ ] **Step 3: Verify in browser**

Navigate through Subscriber Detail, Risk Analysis, Bulk Update, Payments. Check that no sky-blue (`#0ea5e9`) elements remain and all text/borders use the gsh token values.

- [ ] **Step 4: Commit**

```bash
git add web/frontend/src/pages/SubscriberDetail.tsx web/frontend/src/pages/Risk.tsx web/frontend/src/pages/BulkUpdate.tsx web/frontend/src/pages/Payments.tsx
git commit -m "feat: re-theme SubscriberDetail, Risk, BulkUpdate, Payments pages with gsh tokens"
```

---

## Task 13: Version bump + CHANGELOG

**Files:**
- Modify: `web/frontend/src/components/Layout.tsx` (already set to `v2.3.0` in Task 3)
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update CHANGELOG.md**

Add at the top of the file (before any existing entries):

```markdown
## [2.3.0] — 2026-04-18

### Changed
- Replaced `brand.*` sky-blue Tailwind tokens with `gsh.*` design token namespace
- Dark mode: Saltbox-inspired deep navy palette (`#1a1f2e` bg, `#242938` cards, `#2e3650` borders)
- Light mode: clean white/off-white Stripe-like palette
- Accent color: LoginX Electric Purple `#8A4DFF` (buttons, active nav, stat values)
- Active nav indicator: neon cyan left border `#00E0FF` in dark mode
- Badges: lavender `#BFA4FF` default tint (dark), purple `#8A4DFF` tint (light)
- Code blocks: Saltbox-style near-black `#0d1117` background (dark), `#f6f8fa` (light)
- Re-themed: Layout, Card, Button, Badge, Input, StatCard, Login, all pages
```

- [ ] **Step 2: Verify version string**

Open the app and check sidebar footer shows `GSH Web v2.3.0`.

- [ ] **Step 3: Final smoke check**

- [ ] Toggle dark/light mode — all pages switch cleanly
- [ ] Navigate to every page (Dashboard, Subscribers, Payments, Risk, Bulk Update, Settings, Subscriber Detail) — no sky-blue `#0ea5e9` visible anywhere
- [ ] Log out and back in — Login page uses new theme
- [ ] Check both sidebar active and inactive nav states

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md
git commit -m "chore: bump version to 2.3.0, document gsh design token system in CHANGELOG"
```
