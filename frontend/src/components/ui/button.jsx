import { forwardRef } from 'react'
import { Link } from 'react-router-dom'
import { cva } from 'class-variance-authority'
import { cn } from '@/lib/utils'

/**
 * Variantes del botón — sistema visual de NexoMark (ver DESIGN.md).
 * Patrón shadcn/ui en modo JavaScript.
 */
const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap font-semibold ' +
    'transition-[background-color,color,border-color,transform] duration-150 ease-out active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2 ' +
    'focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none ' +
    'disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-on-primary hover:bg-primary-container',
        outline:
          'border border-outline-variant bg-surface-container-lowest text-on-surface hover:bg-surface-container-low',
        secondary:
          'bg-secondary-container text-on-secondary-container hover:bg-surface-container-high',
        ghost: 'text-on-surface-variant hover:text-primary hover:bg-primary/5',
        light: 'bg-surface-container-lowest text-primary hover:bg-surface-container-low',
        // Sobre superficies de marca (marino o turquesa) en ambos temas.
        onBrand: 'bg-paper text-navy hover:bg-turquoise-soft',
      },
      size: {
        default: 'h-11 px-6 text-base rounded-lg',
        sm: 'h-9 px-4 text-sm rounded-lg',
        lg: 'h-12 px-7 text-base rounded-lg',
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

/** Enlace con aspecto de botón (evita anidar <button> dentro de <a>). */
const ButtonLink = forwardRef(function ButtonLink({ className, variant, size, to, href, ...props }, ref) {
  const classes = cn(buttonVariants({ variant, size }), className)
  if (to) return <Link ref={ref} to={to} className={classes} {...props} />
  return <a ref={ref} href={href} className={classes} {...props} />
})

export { Button, ButtonLink }
