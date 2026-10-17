import { useEffect, useState } from 'react'
import { useReducedMotion } from 'motion/react'
import { Check, Info, Mic, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'
import instagramLogo from '@/assets/social/instagram.png'
import facebookLogo from '@/assets/social/facebook.png'
import cafeImg from '@/assets/landing/gallery-6.webp'
import modaImg from '@/assets/landing/gallery-4.webp'
import mercadoImg from '@/assets/landing/gallery-2.webp'

/**
 * Demostración del flujo en la portada. Es solo un ejemplo animado:
 * no llama a la API, no usa IA y no publica nada. Los textos son de ejemplo.
 */
const EXAMPLES = [
  {
    id: 'cafe',
    label: 'Cafetería',
    transcript: 'Súbeme una foto del latte de temporada con 2x1 este sábado, tono cercano.',
    copy: 'Este sábado el latte de temporada va por partida doble: 2x1 toda la mañana. ¿A quién invitas?',
    image: cafeImg,
    imageAlt: 'Taza de latte sobre granos de café',
    redes: ['facebook'],
    destino: 'Página de Facebook · Café Aurora',
    version: 2,
  },
  {
    id: 'moda',
    label: 'Tienda de ropa',
    transcript: 'Anuncia la nueva línea de lino para el verano, tono inspiracional, para Instagram.',
    copy: 'Lino que respira contigo. La línea de verano ya está en tienda: piezas ligeras para días largos.',
    image: modaImg,
    imageAlt: 'Modelo con conjunto de lino claro',
    redes: ['instagram'],
    destino: 'Instagram · @nexomarkia',
    version: 1,
  },
  {
    id: 'mercado',
    label: 'Mercado',
    transcript: 'Promociona las verduras frescas del mercado con delivery gratis el lunes.',
    copy: 'Del campo a tu mesa: verduras frescas con delivery gratis este lunes. Pide antes de las 11 a. m.',
    image: mercadoImg,
    imageAlt: 'Caja de verduras frescas en la pantalla de un teléfono',
    redes: ['instagram', 'facebook'],
    destino: 'Instagram y Facebook',
    version: 1,
  },
]

const STEPS = ['Dictar', 'Generar', 'Aprobar', 'Publicar', 'Medir']
const TYPE_MS = 26
const STEP_MS = [0, 1500, 1100, 1100, 1200]
const LOGOS = { instagram: instagramLogo, facebook: facebookLogo }

function useFlowTimeline(example, runId, reduced) {
  const [state, setState] = useState({ key: '', step: 0, typed: 0 })
  const key = `${example.id}:${runId}`

  useEffect(() => {
    if (reduced) return undefined
    const timers = []
    const at = (ms, fn) => timers.push(setTimeout(fn, ms))
    const length = example.transcript.length
    at(0, () => setState({ key, step: 0, typed: 0 }))
    for (let i = 1; i <= length; i++) at(350 + i * TYPE_MS, () => setState({ key, step: 0, typed: i }))
    let t = 350 + length * TYPE_MS + 450
    for (let step = 1; step <= STEPS.length; step++) {
      const current = step
      at(t, () => setState({ key, step: current, typed: length }))
      t += STEP_MS[step] ?? 1100
    }
    return () => timers.forEach(clearTimeout)
  }, [example, key, reduced])

  // Movimiento reducido (o antes del primer tick): flujo completo, sin animar.
  if (reduced) return { step: STEPS.length, typed: example.transcript.length }
  if (state.key !== key) return { step: 0, typed: 0 }
  return state
}

function StepMarker({ index, status }) {
  return (
    <span
      className={cn(
        'relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[13px] font-bold transition-[background-color,color,box-shadow] duration-300',
        status === 'done' && 'bg-turquoise text-navy',
        status === 'active' && 'bg-navy text-on-navy ring-2 ring-turquoise',
        status === 'pending' && 'bg-white/[0.08] text-on-navy-muted',
      )}
      aria-hidden="true"
    >
      {status === 'done' ? <Check className="h-4 w-4" strokeWidth={3} /> : index + 1}
    </span>
  )
}

export default function FlowDemo() {
  const [exampleId, setExampleId] = useState(EXAMPLES[0].id)
  const [runId, setRunId] = useState(0)
  const reduced = useReducedMotion()
  const example = EXAMPLES.find((e) => e.id === exampleId)
  const { step, typed } = useFlowTimeline(example, runId, reduced)
  const statusOf = (i) => (i < step ? 'done' : i === step ? 'active' : 'pending')
  const transcript = example.transcript.slice(0, typed)

  return (
    <div data-ui className="flex h-full flex-col rounded-2xl bg-navy p-5 text-on-navy ring-white/[0.08] sm:p-7 dark:ring-1">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[15px] font-semibold">Así se ve una campaña en NexoMark</p>
        <span className="demo-tag demo-tag-on-navy">
          <Info className="h-3 w-3" aria-hidden="true" />
          Ejemplo de flujo
        </span>
      </div>

      <div className="mt-4 flex flex-wrap gap-2" role="group" aria-label="Elige un ejemplo">
        {EXAMPLES.map((e) => (
          <button
            key={e.id}
            type="button"
            aria-pressed={e.id === exampleId}
            onClick={() => {
              setExampleId(e.id)
              setRunId((n) => n + 1)
            }}
            className={cn(
              'h-9 rounded-lg px-3.5 text-sm font-semibold transition-[background-color,color,transform] duration-150 active:scale-[0.97]',
              e.id === exampleId
                ? 'bg-turquoise text-navy'
                : 'bg-white/[0.08] text-on-navy-muted hover:bg-white/[0.14] hover:text-on-navy',
            )}
          >
            {e.label}
          </button>
        ))}
      </div>

      <ol className="mt-6 flex-1 space-y-1" aria-label={`Ejemplo del recorrido: ${example.label}`}>
        {STEPS.map((title, i) => {
          const status = statusOf(i)
          return (
            <li key={title} className="flow-step relative flex gap-4 rounded-xl p-2.5" data-state={status}>
              {i < STEPS.length - 1 && (
                <span
                  className={cn(
                    'absolute left-[1.55rem] top-11 bottom-[-0.5rem] w-0.5 rounded-full transition-colors duration-300',
                    i < step ? 'bg-turquoise/60' : 'bg-white/[0.12]',
                  )}
                  aria-hidden="true"
                />
              )}
              <StepMarker index={i} status={status} />
              <div className="min-w-0 flex-1 pt-1">
                <p className="text-[15px] font-semibold leading-6">{title}</p>

                {i === 0 && (
                  <p className="mt-1 flex gap-2 text-[15px] leading-relaxed text-on-navy-muted">
                    <Mic className={cn('mt-1 h-4 w-4 shrink-0', status === 'active' ? 'text-turquoise' : 'text-on-navy-muted')} aria-hidden="true" />
                    {/* El texto completo invisible reserva el alto: no salta mientras se escribe. */}
                    <span className="relative block">
                      <span className="invisible" aria-hidden="true">«{example.transcript}»</span>
                      <span className="sr-only">«{example.transcript}»</span>
                      <span className="absolute inset-0" aria-hidden="true">
                        «{transcript}
                        {status === 'active' && <span className="caret-blink ml-px inline-block h-4 w-[2px] translate-y-0.5 bg-turquoise" />}
                        {status !== 'active' && '»'}
                      </span>
                    </span>
                  </p>
                )}

                {i === 1 && (
                  <div className="mt-1.5 min-h-16">
                    {status === 'done' ? (
                      <div className="flex gap-3">
                        <img
                          src={example.image}
                          alt={example.imageAlt}
                          width="64"
                          height="64"
                          className="h-16 w-16 shrink-0 rounded-lg object-cover"
                        />
                        <p className="text-[15px] leading-relaxed text-on-navy">{example.copy}</p>
                      </div>
                    ) : (
                      <>
                        <p className="text-[13px] text-on-navy-muted">
                          {status === 'active' ? 'Generación IA · 98% completado' : 'Copy e imagen con Gemini'}
                        </p>
                        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/[0.1]">
                          <div
                            className="flow-progress h-full rounded-full bg-turquoise"
                            style={{ '--progress': status === 'active' ? 0.98 : 0 }}
                          />
                        </div>
                      </>
                    )}
                  </div>
                )}

                {i === 2 && (
                  <p className="mt-1 text-[15px] text-on-navy-muted">
                    {status === 'done'
                      ? `El cliente aprobó la versión ${example.version}: esa es la que se publica.`
                      : status === 'active'
                        ? 'El cliente revisa la versión exacta…'
                        : 'El cliente revisa antes de publicar.'}
                  </p>
                )}

                {i === 3 && (
                  <p className="mt-1 flex items-start gap-2 text-[15px] text-on-navy-muted">
                    <span className="mt-0.5 flex shrink-0 -space-x-1">
                      {example.redes.map((red) => (
                        <img key={red} src={LOGOS[red]} alt="" width="20" height="20" className="h-5 w-5 rounded-full ring-2 ring-navy" />
                      ))}
                    </span>
                    {status === 'done' ? `Publicado en ${example.destino}` : `Se publicará en ${example.destino}`}
                  </p>
                )}

                {i === 4 && (
                  <p className="mt-1 text-[15px] text-on-navy-muted">
                    {status === 'done'
                      ? 'Me gusta: sin dato · Alcance: sin dato. Meta puede tardar hasta 48\u00a0h.'
                      : 'Las métricas llegan desde Meta.'}
                  </p>
                )}
              </div>
            </li>
          )
        })}
      </ol>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-white/[0.05] px-3 py-2.5">
        <p className="text-[13px] text-on-navy-muted">Demostración: no usa IA ni publica nada.</p>
        <button
          type="button"
          onClick={() => setRunId((n) => n + 1)}
          className="inline-flex h-9 items-center gap-2 rounded-lg bg-white/[0.08] px-3.5 text-sm font-semibold text-on-navy transition-[background-color,transform] duration-150 hover:bg-white/[0.14] active:scale-[0.97]"
        >
          <RotateCcw className="h-4 w-4" aria-hidden="true" />
          Reproducir de nuevo
        </button>
      </div>
    </div>
  )
}
