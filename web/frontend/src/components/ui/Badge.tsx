import { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'muted'
}

const variants = {
  default: 'bg-[rgba(138,77,255,0.08)] text-gsh-accent dark:bg-[rgba(138,77,255,0.15)] dark:text-[#BFA4FF] border border-[rgba(138,77,255,0.2)] dark:border-[rgba(138,77,255,0.3)]',
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
