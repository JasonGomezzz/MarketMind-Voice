import { AlertTriangle, ShieldQuestion } from 'lucide-react'
import { Button } from '@/components/ui/button'

/**
 * Estado "Créditos agotados" (portado de Stitch: ai_generation_credits_notice).
 * Se muestra cuando el backend devuelve HTTP 402 (tokens_disponibles == 0).
 * El reset lo hace el SuperAdmin (PATCH /api/admin/users/{id}/reset-quota/);
 * el marketero solo puede SOLICITARLO, no auto-resetearse.
 */
const PLANS = [
  { nombre: 'Básico', precio: 49, tokens: '500 créditos', popular: false },
  { nombre: 'Pro', precio: 129, tokens: '1,500 créditos', popular: true },
  { nombre: 'Elite', precio: 299, tokens: '5,000 créditos', popular: false },
]

export default function CreditsExhausted({ onClose }) {
  return (
    <div className="rounded-xl border border-outline-variant bg-white p-6 shadow-sm">
      <span className="mb-4 inline-flex items-center gap-2 rounded-full bg-error-container px-3 py-1 text-xs font-bold uppercase tracking-wide text-error">
        <AlertTriangle className="h-3.5 w-3.5" />
        Créditos agotados
      </span>

      <h2 className="mb-2 text-2xl font-bold leading-tight tracking-tight text-on-surface text-balance">
        Tu potencial no tiene límites, <span className="text-primary">pero tus créditos sí.</span>
      </h2>
      <p className="mb-6 text-sm text-on-surface-variant">
        Alcanzaste el límite de tu plan. Recarga créditos para seguir generando campañas
        sin interrupciones.
      </p>

      <div className="mb-6 space-y-3">
        {PLANS.map((plan) => (
          <div
            key={plan.nombre}
            className={`flex items-center justify-between rounded-xl border p-4 ${
              plan.popular
                ? 'border-primary bg-primary/5 ring-1 ring-primary'
                : 'border-outline-variant'
            }`}
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold uppercase tracking-wide text-on-surface">
                  {plan.nombre}
                </span>
                {plan.popular && (
                  <span className="rounded-full bg-primary px-2 py-0.5 text-[10px] font-bold uppercase text-on-primary">
                    Más popular
                  </span>
                )}
              </div>
              <p className="text-xs text-on-surface-variant">{plan.tokens}</p>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold tabular-nums text-on-surface">
                S/ {plan.precio}
              </p>
              <Button size="sm" variant={plan.popular ? 'default' : 'outline'} className="mt-1">
                Elegir plan
              </Button>
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-center gap-2 border-t border-outline-variant pt-4">
        <ShieldQuestion className="h-4 w-4 text-primary" />
        <button className="text-sm font-semibold text-primary hover:underline">
          Pedir reset al administrador
        </button>
      </div>

      {onClose && (
        <button
          onClick={onClose}
          className="mt-4 w-full text-center text-sm text-on-surface-variant transition-colors hover:text-on-surface"
        >
          Volver al formulario
        </button>
      )}
    </div>
  )
}
