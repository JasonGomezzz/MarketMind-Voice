import { useEffect, useState } from 'react'
import { motion } from 'motion/react'
import { Check, Loader2, Lock } from 'lucide-react'

/**
 * Estado "Generando con IA" (portado de Stitch: ai_generation_loading_state).
 * Pipeline vertical de 3 pasos que reflejan el flujo real de n8n:
 * análisis → copy → imagen. n8n tarda 8–15s.
 * El backend descuenta 1 crédito ANTES de disparar (estado = pendiente_ia).
 */
const STEPS = [
  { titulo: 'Análisis de contexto', sub: 'Estructura y tono definidos' },
  { titulo: 'Generación de copy creativo', sub: 'Redactando variantes persuasivas…' },
  { titulo: 'Síntesis de imagen editorial', sub: 'Próximo paso' },
]

export default function GeneratingState({ onCancel }) {
  const [seconds, setSeconds] = useState(0)
  // Paso activo simulado por tiempo (0: análisis, 1: copy, 2: imagen)
  const activeStep = seconds < 3 ? 1 : seconds < 9 ? 1 : 2

  useEffect(() => {
    const t = setInterval(() => setSeconds((s) => s + 1), 1000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="flex min-h-[420px] flex-col items-center justify-center rounded-xl border border-outline-variant bg-white p-8 text-center shadow-sm">
      <span className="mb-6 inline-flex items-center gap-2 rounded-full bg-primary-fixed px-3 py-1 text-xs font-semibold text-primary">
        <span className="h-1.5 w-1.5 rounded-full bg-primary" />
        Pendiente IA
      </span>

      <h2 className="mb-3 text-3xl font-bold tracking-tight text-on-surface text-balance">
        Esculpiendo tu campaña
      </h2>
      <p className="mb-8 max-w-sm text-base text-on-surface-variant">
        Nuestros modelos están procesando tu solicitud para crear contenido único y
        optimizado.
      </p>

      {/* Pipeline vertical */}
      <div className="mb-8 w-full max-w-sm space-y-5 text-left">
        {STEPS.map((step, i) => {
          const done = i < activeStep
          const active = i === activeStep
          return (
            <div key={step.titulo} className="flex items-start gap-3">
              <div
                className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                  done
                    ? 'bg-success-container text-success'
                    : active
                      ? 'bg-primary/10 text-primary'
                      : 'bg-surface-container-high text-outline'
                }`}
              >
                {done ? (
                  <Check className="h-4 w-4" />
                ) : active ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  i + 1
                )}
              </div>
              <div>
                <p className={`text-sm font-bold ${active ? 'text-primary' : 'text-on-surface'}`}>
                  {step.titulo}
                </p>
                <p className="text-xs text-on-surface-variant">{step.sub}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Barra de progreso indeterminada */}
      <div className="mb-6 h-1 w-full max-w-sm overflow-hidden rounded-full bg-surface-container-high">
        <motion.div
          className="h-full w-1/3 rounded-full bg-primary"
          animate={{ x: ['-100%', '300%'] }}
          transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      <p className="mb-4 flex items-center gap-1.5 text-xs text-on-surface-variant">
        <Lock className="h-3.5 w-3.5" />
        No cierres esta ventana mientras la IA trabaja · {seconds}s
      </p>

      {onCancel && (
        <button
          onClick={onCancel}
          className="text-sm text-on-surface-variant transition-colors hover:text-error"
        >
          Cancelar generación
        </button>
      )}
    </div>
  )
}
