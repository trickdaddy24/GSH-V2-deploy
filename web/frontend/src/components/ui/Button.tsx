import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'green' | 'slate' | 'violet' | 'teal'
  size?: 'sm' | 'md' | 'lg'
}

// Operator look: every variant is an .op-btn; accent/danger get the
// distinct treatments, the rest fall back to the default outline button.
const variants = {
  primary:   'op-btn-primary',
  secondary: '',
  danger:    'op-btn-danger',
  ghost:     '',
  green:     'op-btn-primary',
  slate:     '',
  violet:    'op-btn-primary',
  teal:      'op-btn-primary',
}

const sizes = {
  sm: 'text-[11px]',
  md: '',
  lg: 'px-4 py-2.5 text-sm',
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => (
    <button
      ref={ref}
      className={cn('op-btn', variants[variant], sizes[size], className)}
      {...props}
    />
  ),
)

Button.displayName = 'Button'
export default Button
