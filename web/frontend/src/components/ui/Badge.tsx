import { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'muted'
}

const variants: Record<string, React.CSSProperties> = {
  default: { color: 'var(--op-accent)' },
  success: { color: 'var(--op-accent)' },
  warning: { color: 'var(--op-chip-warn-fg)' },
  danger:  { color: 'var(--op-accent2)' },
  muted:   { color: 'var(--op-dim)' },
}

export default function Badge({ className, variant = 'default', style, ...props }: BadgeProps) {
  return (
    <span
      className={cn('op-tag', className)}
      style={{ ...variants[variant], ...style }}
      {...props}
    />
  )
}
