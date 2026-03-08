import { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'muted'
}

const variants = {
  default: 'bg-brand-900 text-brand-100',
  success: 'bg-emerald-900 text-emerald-300',
  warning: 'bg-yellow-900 text-yellow-300',
  danger:  'bg-red-900 text-red-300',
  muted:   'bg-slate-800 text-slate-400',
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
