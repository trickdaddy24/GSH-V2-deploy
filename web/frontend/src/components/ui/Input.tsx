import { InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/utils'

const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn('op-input', 'disabled:opacity-50 disabled:cursor-not-allowed', className)}
      {...props}
    />
  ),
)

Input.displayName = 'Input'
export default Input
