/**
 * Estados FSM de Campaign — fuente única de verdad para labels y estilos.
 * Deriva de los tokens de DESIGN.md. Lo consumen StatusBadge, DashboardPage
 * y AnalyticsPage (labels); los hex de los charts viven en AnalyticsPage
 * porque Recharts no acepta clases Tailwind.
 */
export const STATES = {
  borrador: { label: 'Borrador', className: 'bg-surface-container-high text-on-surface-variant' },
  pendiente_ia: { label: 'Pendiente IA', className: 'bg-primary-fixed text-primary' },
  generado: { label: 'Generado', className: 'bg-secondary-container text-primary' },
  pendiente_aprobacion: { label: 'Pendiente aprobación', className: 'bg-warning-container text-tertiary' },
  aprobado: { label: 'Aprobado', className: 'bg-success-container text-success' },
  rechazado: { label: 'Rechazado', className: 'bg-error-container text-error' },
}
