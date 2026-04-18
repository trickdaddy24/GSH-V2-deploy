# GSH Design Token System — Implementation Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current `brand.*` sky-blue token system with a `gsh.*` token namespace combining Saltbox-inspired dark navy backgrounds with LoginX-derived purple/cyan accents. Re-theme all components to use the new tokens. Dark-first, both modes supported.

---

## Design Sources

| Element | Source | Description |
|---|---|---|
| Backgrounds (bg, card) | Saltbox docs | Deep navy `#1a1f2e`, dark card `#242938` |
| Borders | Saltbox docs | Dark blue-slate `#2e3650` |
| Sidebar nav style | Saltbox docs | Cyan left-border active indicator |
| Code block style | Saltbox docs | Near-black `#0d1117` bg |
| Accent (primary) | LoginX | Electric Purple `#8A4DFF` |
| Hover accent | LoginX | Neon Cyan `#00E0FF` (dark), `#7A3DEF` (light) |
| Cyan | LoginX | `#00E0FF` dark / `#2EC7FF` light |
| Lavender | LoginX | `#BFA4FF` — badge tints |

---

## Token Table

Defined in `web/frontend/tailwind.config.js` under `theme.extend.colors.gsh`. Light values are the config defaults. Dark overrides are applied via `dark:` prefix classes in components.

| Token | Light | Dark | Role |
|---|---|---|---|
| `gsh-bg` | `#FFFFFF` | `#1a1f2e` | Page/body background |
| `gsh-card` | `#F9F9FB` | `#242938` | Cards, sidebar |
| `gsh-border` | `#E5E7EB` | `#2e3650` | Card, input, nav borders |
| `gsh-accent` | `#8A4DFF` | `#8A4DFF` | Primary buttons, active nav, stat values |
| `gsh-accent-hover` | `#7A3DEF` | `#00E0FF` | Button/link hover — light uses darker purple; dark uses neon cyan |
| `gsh-muted` | `#6B7280` | `#8899aa` | Secondary text, labels, inactive nav |
| `gsh-text` | `#0B0F2A` | `#e0e6f0` | Primary body text |
| `gsh-cyan` | `#2EC7FF` | `#00E0FF` | Active nav indicator (dark mode), glow effects |
| `gsh-lavender` | `#BFA4FF` | `#BFA4FF` | Badge tints (same both modes) |
| `gsh-code-bg` | `#f6f8fa` | `#0d1117` | Code block / `<pre>` background |

> **Known workaround:** `gsh-muted` resolves to its light value (`#6B7280`) even with `dark:` prefix — Tailwind doesn't support per-mode custom values. Use `dark:text-[#8899aa]` directly wherever dark muted text is needed (same pattern as MovieNexus `nexus-muted`).

---

## Files to Modify

| File | Change |
|---|---|
| `web/frontend/tailwind.config.js` | Replace `brand.*` block with `gsh.*` tokens |
| `web/frontend/src/index.css` | Update body light/dark bg and text colors |
| `web/frontend/src/components/Layout.tsx` | New sidebar styles: bg, nav active state, borders |
| `web/frontend/src/components/ui/Card.tsx` | `gsh-card`, `gsh-border` tokens |
| `web/frontend/src/components/ui/Button.tsx` | primary=`gsh-accent`, secondary/ghost dark overrides |
| `web/frontend/src/components/ui/Badge.tsx` | default variant → lavender/purple; keep semantic variants |
| `web/frontend/src/components/ui/Input.tsx` | `gsh-border`, `gsh-accent` focus ring, dark bg |
| `web/frontend/src/components/StatCard.tsx` | value color → `gsh-accent`, icon bg, muted labels |
| Pages (`Dashboard`, `Subscribers`, `Payments`, `Risk`, `BulkUpdate`, `Settings`, `Login`, `SubscriberDetail`) | Replace all `brand-*` with `gsh-accent`, hardcoded `slate-*`/`gray-*` dark values with `gsh-*` equivalents |

---

## Component Specs

### `tailwind.config.js`

Remove the existing `brand` block. Add:

```js
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
```

### `index.css`

```css
@layer base {
  body {
    @apply bg-gsh-bg text-gsh-text antialiased;
  }
  .dark body {
    @apply bg-[#1a1f2e] text-[#e0e6f0];
  }
}
```

### `Layout.tsx`

Outer wrapper:
```tsx
<div className="flex h-screen overflow-hidden bg-gsh-bg dark:bg-[#1a1f2e]">
```

Sidebar:
```tsx
<aside className="flex w-56 flex-col border-r border-gsh-border dark:border-[#2e3650] bg-white dark:bg-[#242938]">
```

Logo text:
```tsx
<span className="font-bold text-gsh-text dark:text-[#e0e6f0] tracking-tight">GuardianStreams</span>
```

NavLink active class:
```tsx
// active
'bg-[rgba(138,77,255,0.08)] dark:bg-[rgba(138,77,255,0.12)] text-gsh-accent dark:text-[#e0e6f0] border-l-2 border-gsh-accent dark:border-gsh-cyan pl-[8px]'
// inactive
'text-gsh-muted dark:text-[#8899aa] hover:bg-gray-100 dark:hover:bg-[rgba(255,255,255,0.04)] hover:text-gsh-text dark:hover:text-[#e0e6f0]'
```

Footer area:
```tsx
<div className="border-t border-gsh-border dark:border-[#2e3650] px-4 py-3 ...">
```

Theme toggle / logout buttons — replace `slate-*` hover colors:
```tsx
// theme toggle
'dark:text-[#8899aa] dark:hover:text-[#e0e6f0] dark:hover:bg-[rgba(255,255,255,0.06)]'
// logout
'dark:text-[#8899aa] dark:hover:text-red-400 dark:hover:bg-red-900/20'
```

### `Card.tsx`

```tsx
<div className={cn(
  'rounded-xl bg-white dark:bg-[#242938] border border-gsh-border dark:border-[#2e3650] p-4',
  className
)} />
```

`CardTitle`:
```tsx
<h3 className={cn('text-sm font-semibold text-gsh-muted dark:text-[#8899aa] uppercase tracking-wide', className)} />
```

### `Button.tsx`

```tsx
const variants = {
  primary:   'bg-gsh-accent hover:bg-gsh-accent-hover text-white',
  secondary: 'bg-gsh-card hover:bg-gray-200 dark:bg-[rgba(255,255,255,0.05)] dark:hover:bg-[rgba(255,255,255,0.08)] text-gsh-muted dark:text-[#8899aa] border border-gsh-border dark:border-[#2e3650]',
  danger:    'bg-red-600 hover:bg-red-700 text-white dark:bg-red-700 dark:hover:bg-red-600',
  ghost:     'bg-transparent hover:bg-gray-100 dark:hover:bg-[rgba(255,255,255,0.05)] text-gsh-muted dark:text-[#8899aa]',
}
```

### `Badge.tsx`

```tsx
const variants = {
  default: 'bg-[rgba(138,77,255,0.08)] text-gsh-accent dark:bg-[rgba(138,77,255,0.15)] dark:text-gsh-lavender border border-[rgba(138,77,255,0.2)] dark:border-[rgba(138,77,255,0.3)]',
  success: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
  danger:  'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  muted:   'bg-gsh-card text-gsh-muted dark:bg-[rgba(255,255,255,0.05)] dark:text-[#8899aa] border border-gsh-border dark:border-[#2e3650]',
}
```

### `Input.tsx`

```tsx
'bg-white dark:bg-[#1a1f2e] border-gsh-border dark:border-[#2e3650] text-gsh-text dark:text-[#e0e6f0] placeholder:text-gsh-muted dark:placeholder:text-[#8899aa]',
'focus:outline-none focus:ring-2 focus:ring-gsh-accent focus:border-transparent',
```

### `StatCard.tsx`

```tsx
// icon container
<div className={cn('mt-0.5 rounded-lg bg-[#F3F0FF] dark:bg-[rgba(138,77,255,0.12)] p-2', iconColor)}>

// label
<p className="text-xs text-gsh-muted dark:text-[#8899aa] uppercase tracking-wide">{label}</p>

// value — purple in both modes
<p className="text-2xl font-bold text-gsh-accent">{value}</p>

// sub
<p className="text-xs text-gsh-muted dark:text-[#8899aa] mt-0.5">{sub}</p>
```

`iconColor` default prop: change from `text-brand-500` → `text-gsh-accent`

### Pages — Global Find/Replace Rules

After updating components, do a global search across all `.tsx` page files and apply:

| Find | Replace with |
|---|---|
| `text-brand-500`, `text-brand-600`, `text-brand-700` | `text-gsh-accent` |
| `bg-brand-600`, `bg-brand-700` | `bg-gsh-accent` |
| `border-brand-*` | `border-gsh-accent` |
| `ring-brand-500` | `ring-gsh-accent` |
| `dark:bg-slate-950` | `dark:bg-[#1a1f2e]` |
| `dark:bg-slate-900` | `dark:bg-[#242938]` |
| `dark:bg-slate-800` | `dark:bg-[rgba(255,255,255,0.05)]` |
| `dark:border-slate-800` | `dark:border-[#2e3650]` |
| `dark:text-slate-100` | `dark:text-[#e0e6f0]` |
| `dark:text-slate-400`, `dark:text-slate-500` | `dark:text-[#8899aa]` |

---

## Code Block Styling (`index.css`)

Add a global style for `<pre>` / `<code>` blocks (Saltbox element E):

```css
@layer base {
  pre, code {
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  }
  pre {
    @apply bg-gsh-code-bg dark:bg-[#0d1117] border border-gsh-border dark:border-[#2e3650] rounded-md p-3 text-sm overflow-x-auto;
  }
}
```

---

## Dark Mode Architecture

- `darkMode: 'class'` already configured in `tailwind.config.js` — no change needed
- `ThemeContext.tsx` already exists and handles toggle — no change needed
- Light values are the Tailwind config defaults (used without `dark:` prefix)
- Dark values are applied via `dark:` prefix classes in each component
- `gsh-muted` resolves to light value only — always use `dark:text-[#8899aa]` for dark muted text

---

## Out of Scope

- No changes to FastAPI backend
- No changes to Docker/deployment config
- No new pages or routes
- No changes to `StatusBadge.tsx` logic (delegates to `Badge` — covered by Badge spec above)
- No changes to `RatingBadge` or other semantic color components
- No Tailwind v4 upgrade

---

## Version Bump

Bump `VERSION` in `web/frontend/src/components/Layout.tsx` footer from `v2.2.6` → `v2.3.0` and update `CHANGELOG.md`.
