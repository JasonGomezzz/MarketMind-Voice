import { cn } from '@/lib/utils'

/**
 * Badge de estado FSM — fuente única de verdad para los 6 estados.
 * Deriva de los tokens de DESIGN.md. Úsalo en TODA pantalla que muestre estado
 * para garantizar consistencia (dashboard, listas, detalle, review).
 */
const STATES = {
  borrador: { label: 'Borrador', className: 'bg-surface-container-high text-on-surface-variant' },
  pendiente_ia: { label: 'Pendiente IA', className: 'bg-primary-fixed text-primary' },
  generado: { label: 'Generado', className: 'bg-secondary-container text-primary' },
  pendiente_aprobacion: { label: 'Pendiente aprobación', className: 'bg-warning-container text-tertiary' },
  aprobado: { label: 'Aprobado', className: 'bg-success-container text-success' },
  rechazado: { label: 'Rechazado', className: 'bg-error-container text-error' },
}

export default function StatusBadge({ estado, className }) {
  const s = STATES[estado] ?? {
    label: estado ?? '—',
    className: 'bg-surface-container-high text-on-surface-variant',
  }
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold whitespace-nowrap',
        s.className,
        className,
      )}
    >
      {s.label}
    </span>
  )
}
