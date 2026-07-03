import { AlertCircle, Info, RefreshCw, Pencil } from 'lucide-react'
import { Button } from '@/components/ui/button'

/**
 * Estado de error de generación IA (portado de Stitch: error_total_generacion_fallida).
 * El backend devolvió el crédito (atomic), guardó ia_error_message y la campaña
 * volvió a borrador. Reintentos hasta 3 (intentos_generacion).
 */
export default function ErrorState({ message, attempt = 1, maxAttempts = 3, onRetry, onEditBrief }) {
  return (
    <div className="flex min-h-[420px] flex-col items-center justify-center rounded-xl border border-outline-variant bg-white p-8 text-center shadow-sm">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-error-container">
        <AlertCircle className="h-8 w-8 text-error" />
      </div>

      <h2 className="mb-3 text-2xl font-bold tracking-tight text-on-surface text-balance">
        No pudimos generar tu campaña
      </h2>
      <p className="mb-6 max-w-sm text-base text-on-surface-variant">
        {message || 'El servicio de IA está saturado. Se te devolvió tu crédito automáticamente.'}
      </p>

      <div className="mb-6 flex items-center gap-2 rounded-full bg-surface-container-low px-4 py-2 text-sm text-on-surface-variant">
        <Info className="h-4 w-4" />
        No se te descontaron créditos por este intento.
      </div>

      {/* Contador de intentos */}
      <div className="mb-6">
        <p className="mb-2 text-sm font-semibold text-on-surface">
          Intento {attempt} de {maxAttempts}
        </p>
        <div className="flex justify-center gap-2">
          {Array.from({ length: maxAttempts }).map((_, i) => (
            <span
              key={i}
              className={`h-1.5 w-10 rounded-full ${
                i < attempt ? 'bg-error' : 'bg-surface-container-high'
              }`}
            />
          ))}
        </div>
      </div>

      <div className="flex w-full max-w-xs flex-col gap-3">
        <Button onClick={onRetry} disabled={attempt >= maxAttempts}>
          <RefreshCw className="h-4 w-4" />
          Reintentar generación
        </Button>
        <Button variant="outline" onClick={onEditBrief}>
          <Pencil className="h-4 w-4" />
          Editar brief
        </Button>
      </div>
    </div>
  )
}
