import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * Stepper del FSM de campaña — hace visible la máquina de estados.
 * Flujo principal: borrador → pendiente_ia → generado → pendiente_aprobacion → aprobado.
 * Los estados "rechazado" y "fracaso" se muestran como bifurcación desde revisión.
 * Deriva de los tokens de DESIGN.md (sin colores nuevos).
 */
const FLOW = [
  { key: 'borrador', label: 'Borrador' },
  { key: 'pendiente_ia', label: 'Generando IA' },
  { key: 'generado', label: 'Generado' },
  { key: 'pendiente_aprobacion', label: 'En revisión' },
  { key: 'aprobado', label: 'Aprobado' },
]

export default function CampaignStepper({ estado }) {
  const rejected = estado === 'rechazado'
  const failed = estado === 'fracaso'
  // índice del estado actual dentro del flujo principal
  const currentIndex = rejected || failed
    ? FLOW.findIndex((s) => s.key === 'pendiente_aprobacion')
    : FLOW.findIndex((s) => s.key === estado)

  return (
    <div className="flex items-start">
      {FLOW.map((step, i) => {
        const done = i < currentIndex
        const active = i === currentIndex
        const isLast = i === FLOW.length - 1

        return (
          <div key={step.key} className="flex flex-1 items-start last:flex-none">
            {/* Nodo */}
            <div className="flex flex-col items-center gap-2">
              <div
                className={cn(
                  'flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold transition-colors',
                  done && 'bg-primary text-on-primary',
                  active && !rejected && !failed && 'bg-primary text-on-primary ring-4 ring-primary/25',
                  active && (rejected || failed) && 'bg-error text-white ring-4 ring-error/20',
                  !done && !active && 'bg-surface-container-high text-outline',
                )}
              >
                {done ? <Check className="h-4 w-4" /> : i + 1}
              </div>
              <span
                className={cn(
                  'whitespace-nowrap text-xs font-medium',
                  // En pantallas angostas solo se rotula el paso actual.
                  active ? 'text-on-surface' : 'hidden text-on-surface-variant sm:block',
                )}
              >
                {active && rejected ? 'Rechazado' : active && failed ? 'Fracaso' : step.label}
              </span>
            </div>

            {/* Conector */}
            {!isLast && (
              <div
                className={cn(
                  'mx-1 mt-[17px] h-0.5 flex-1 rounded-full transition-colors sm:mx-2',
                  i < currentIndex ? 'bg-primary' : 'bg-outline-variant',
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
