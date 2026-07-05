import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { AlertTriangle, ShieldCheck, X, Coins } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { MSG_RESET, PLANS } from '@/lib/credits'

/**
 * Modal de planes de créditos — réplica fiel de Stitch
 * planes_de_cr_ditos_consistencia_lumina (overlay liquid glass a pantalla
 * completa con 3 cards de precio). Sin pasarela de pago en esta versión:
 * los botones informan el flujo real (reset del SuperAdmin, HU24) y
 * "Ver mis créditos" navega a /settings — sin botones fantasma.
 * Trigger ÚNICO: los botones "Elegir plan" de CreditsExhausted.
 */
export default function PlanesModal({ open, onClose }) {
  const navigate = useNavigate()

  useEffect(() => {
    if (!open) return
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="planes-title"
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-on-surface/40 p-4 backdrop-blur-sm"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="glass-liquid relative max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-3xl px-6 py-10 text-center sm:px-12"
      >
        <button
          onClick={onClose}
          aria-label="Cerrar planes"
          className="absolute right-4 top-4 rounded-full p-2 text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <X className="h-5 w-5" />
        </button>

        <span className="mb-6 inline-flex items-center gap-2 rounded-full bg-error-container px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-error">
          <AlertTriangle className="h-3.5 w-3.5" />
          Créditos agotados
        </span>

        <h2
          id="planes-title"
          className="mx-auto mb-4 max-w-2xl text-3xl font-bold leading-tight tracking-tight text-on-surface sm:text-4xl text-balance"
        >
          Tu potencial no tiene límites, pero tus <span className="text-primary">créditos</span> sí.
        </h2>
        <p className="mx-auto mb-10 max-w-xl text-base text-on-surface-variant">
          Has alcanzado el límite de tu plan actual. Recarga{' '}
          <strong className="text-on-surface">Créditos de IA</strong> para continuar
          transformando tus ideas en campañas de alto impacto.
        </p>

        {/* Cards de precio */}
        <div className="mb-10 grid grid-cols-1 gap-6 sm:grid-cols-3 sm:items-stretch">
          {PLANS.map((plan) => (
            <div
              key={plan.nombre}
              className={`relative flex flex-col items-center rounded-2xl p-8 ${
                plan.popular
                  ? 'border-2 border-primary bg-white shadow-xl'
                  : 'border border-outline-variant/60 bg-white/80 shadow-sm'
              }`}
            >
              {plan.popular && (
                <span className="absolute -top-4 rounded-full bg-primary px-4 py-1.5 text-[11px] font-bold uppercase tracking-wide text-on-primary shadow-lg">
                  Más popular
                </span>
              )}
              <p className="mb-4 text-sm font-bold uppercase tracking-[0.2em] text-on-surface">
                {plan.nombre}
              </p>
              <p className="mb-1 text-4xl font-extrabold tabular-nums text-on-surface">
                <span className="mr-1 align-top text-base font-semibold">S/</span>
                {plan.precio}
              </p>
              <p className="mb-6 text-sm font-medium text-primary">
                {plan.creditos} Créditos de IA
              </p>
              <Button
                variant={plan.popular ? 'default' : 'secondary'}
                className="mt-auto w-full"
                onClick={() =>
                  toast(`Plan ${plan.nombre}: disponible próximamente. ${MSG_RESET}`, {
                    icon: 'ℹ️',
                  })
                }
              >
                {plan.popular ? 'Seleccionar Plan' : 'Seleccionar'}
              </Button>
            </div>
          ))}
        </div>

        {/* Acciones secundarias */}
        <div className="mb-6 flex flex-col items-center justify-center gap-3 border-t border-outline-variant/50 pt-6 sm:flex-row sm:gap-8">
          <button
            onClick={() => toast.success(MSG_RESET)}
            className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline"
          >
            <ShieldCheck className="h-4 w-4" />
            Solicitar reset al administrador
          </button>
          <button
            onClick={() => {
              onClose()
              navigate('/settings')
            }}
            className="inline-flex items-center gap-2 text-sm font-medium text-on-surface-variant transition-colors hover:text-on-surface"
          >
            <Coins className="h-4 w-4" />
            Ver mis créditos
          </button>
        </div>

        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-on-surface-variant/70">
          Seguridad garantizada mediante pasarelas de pago locales
        </p>
      </div>
    </div>
  )
}
