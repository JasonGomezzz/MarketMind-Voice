import { forwardRef } from 'react'
import { cva } from 'class-variance-authority'
import { cn } from '@/lib/utils'

/**
 * Variantes del botón — sistema Lumina Creative (ver DESIGN.md).
 * Patrón shadcn/ui en modo JavaScript.
 */
const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap font-semibold ' +
    'transition-all active:scale-95 focus-visible:outline-none focus-visible:ring-2 ' +
    'focus-visible:ring-primary focus-visible:ring-offset-2 disabled:pointer-events-none ' +
    'disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-on-primary shadow-lg hover:bg-primary-container',
        outline:
          'border border-outline-variant bg-surface-container-lowest text-on-surface hover:bg-surface-container-low',
        secondary:
          'bg-secondary-container text-on-secondary-container hover:bg-surface-container-high',
        ghost: 'text-on-surface-variant hover:text-primary hover:bg-primary/5',
        light: 'bg-surface-container-lowest text-primary hover:bg-surface-container-low',
      },
      size: {
        default: 'h-11 px-6 text-base rounded-lg',
        sm: 'h-9 px-4 text-sm rounded-lg',
        lg: 'h-14 px-8 text-xl rounded-xl',
        icon: 'h-10 w-10 rounded-lg',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

const Button = forwardRef(function Button({ className, variant, size, ...props }, ref) {
  return (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  )
})

export { Button }
