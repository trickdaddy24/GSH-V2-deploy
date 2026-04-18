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
