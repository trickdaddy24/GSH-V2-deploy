import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'green' | 'slate' | 'violet' | 'teal'
  size?: 'sm' | 'md' | 'lg'
}

const variants = {
  primary:   'bg-gsh-accent hover:bg-gsh-accent-hover text-white',
  secondary: 'bg-gsh-card hover:bg-gray-200 dark:bg-[rgba(255,255,255,0.05)] dark:hover:bg-[rgba(255,255,255,0.08)] text-gsh-muted dark:text-[#8899aa] border border-gsh-border dark:border-[#2e3650]',
  danger:    'bg-red-600 hover:bg-red-700 text-white dark:bg-red-700 dark:hover:bg-red-600',
  ghost:     'bg-transparent hover:bg-gray-100 dark:hover:bg-[rgba(255,255,255,0.05)] text-gsh-muted dark:text-[#8899aa]',
  green:     'bg-green-600 hover:bg-green-700 text-white dark:bg-green-700 dark:hover:bg-green-600',
  slate:     'bg-slate-700 hover:bg-slate-800 text-white dark:bg-slate-600 dark:hover:bg-slate-500',
  violet:    'bg-violet-600 hover:bg-violet-700 text-white dark:bg-violet-700 dark:hover:bg-violet-600',
  teal:      'bg-teal-600 hover:bg-teal-700 text-white dark:bg-teal-700 dark:hover:bg-teal-600',
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
