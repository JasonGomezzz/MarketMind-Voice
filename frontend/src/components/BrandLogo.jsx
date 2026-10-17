import { cn } from '@/lib/utils'

/**
 * Logo de NexoMark IA: icono aprobado (brand/) + nombre con la cápsula "IA".
 * `tone="navy"` se usa sobre el panel marino (texto blanco, cápsula turquesa).
 * El tamaño sigue al font-size del contenedor (text-lg, text-2xl…).
 */
export default function BrandLogo({ compact = false, tone = 'surface', className = '' }) {
  const onNavy = tone === 'navy'
  return (
    <span className={cn('inline-flex items-center gap-[0.45em] leading-none', className)}>
      <img
        src="/nexomark-icon-192.png"
        alt={compact ? 'NexoMark IA' : ''}
        width="192"
        height="192"
        className="h-[1.6em] w-[1.6em] shrink-0"
      />
      {!compact && (
        <span className="inline-flex items-center gap-[0.3em] font-extrabold tracking-[-0.02em]">
          <span className={onNavy ? 'text-on-navy' : 'text-on-surface'}>NexoMark</span>
          <span
            className={cn(
              'rounded-[0.3em] px-[0.32em] py-[0.14em] text-[0.62em] font-extrabold tracking-normal',
              onNavy ? 'bg-turquoise text-navy' : 'bg-primary text-on-primary',
            )}
          >
            IA
          </span>
        </span>
      )}
    </span>
  )
}
