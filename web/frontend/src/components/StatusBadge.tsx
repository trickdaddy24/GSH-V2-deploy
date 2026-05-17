import { CheckCircle, Clock, AlertTriangle, XCircle, Sparkles, MinusCircle } from 'lucide-react'
import type { ElementType } from 'react'

interface Props { status: string; isActive?: 0 | 1 }

const OVERDUE_CONFIG = {
  icon: AlertTriangle,
  label: 'Past Due',
  classes:     'bg-orange-50 text-orange-700 border border-orange-200',
  darkClasses: 'dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-700/40',
}

const STATUS_CONFIG: Record<string, {
  icon: ElementType
  label: string
  classes: string          // pill bg + text (light)
  darkClasses: string      // pill bg + text (dark) — raw hex required
}> = {
  initial: {
    icon: Sparkles,
    label: 'Initial',
    classes:     'bg-blue-50 text-blue-700 border border-blue-200',
    darkClasses: 'dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700/40',
  },
  paid: {
    icon: CheckCircle,
    label: 'Paid',
    classes:     'bg-emerald-50 text-emerald-700 border border-emerald-200',
    darkClasses: 'dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700/40',
  },
  active: {
    icon: CheckCircle,
    label: 'Active',
    classes:     'bg-emerald-50 text-emerald-700 border border-emerald-200',
    darkClasses: 'dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700/40',
  },
  pending: {
    icon: Clock,
    label: 'Pending',
    classes:     'bg-amber-50 text-amber-700 border border-amber-200',
    darkClasses: 'dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-700/40',
  },
  overdue: OVERDUE_CONFIG,
  pastdue: OVERDUE_CONFIG,
  delinquent: {
    icon: XCircle,
    label: 'Delinquent',
    classes:     'bg-red-50 text-red-700 border border-red-200',
    darkClasses: 'dark:bg-red-900/30 dark:text-red-300 dark:border-red-700/40',
  },
}

const INACTIVE_CONFIG = {
  icon: MinusCircle,
  label: 'Inactive',
  classes:     'bg-gray-100 text-gray-500 border border-gray-200',
  darkClasses: 'dark:bg-[rgba(255,255,255,0.05)] dark:text-[#8899aa] dark:border-[#2e3650]',
}

export default function StatusBadge({ status, isActive = 1 }: Props) {
  const cfg = !isActive
    ? INACTIVE_CONFIG
    : (STATUS_CONFIG[status.toLowerCase()] ?? {
        icon: Sparkles,
        label: status,
        classes:     'bg-blue-50 text-blue-700 border border-blue-200',
        darkClasses: 'dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700/40',
      })

  const Icon = cfg.icon

  // Operator look: map semantic status → theme accent vars on an op-tag.
  const key = !isActive ? 'inactive' : status.toLowerCase()
  const tone =
    key === 'inactive'
      ? { color: 'var(--op-dim)', background: 'transparent' }
      : ['active', 'paid'].includes(key)
        ? { color: 'var(--op-accent)', background: 'var(--op-chip-active)' }
        : ['overdue', 'pastdue', 'delinquent'].includes(key)
          ? { color: 'var(--op-accent2)', background: 'var(--op-chip-alert)' }
          : { color: 'var(--op-chip-warn-fg)', background: 'var(--op-chip-warn)' }

  return (
    <span className="op-tag solid" style={tone}>
      <Icon size={11} aria-hidden="true" />
      {cfg.label}
    </span>
  )
}
