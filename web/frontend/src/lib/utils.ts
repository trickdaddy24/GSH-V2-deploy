import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

export function formatDate(dateStr: string | null) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export function statusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'current':    return 'text-emerald-400'
    case 'due today':  return 'text-yellow-400'
    case 'overdue':    return 'text-red-400'
    case 'inactive':   return 'text-slate-500'
    default:           return 'text-slate-300'
  }
}

export function riskColor(level: string): string {
  switch (level.toLowerCase()) {
    case 'critical': return 'text-red-400'
    case 'high':     return 'text-orange-400'
    case 'medium':   return 'text-yellow-400'
    case 'low':      return 'text-emerald-400'
    default:         return 'text-slate-400'
  }
}
