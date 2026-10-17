import { motion } from 'motion/react'
import { ArrowRight, Info } from 'lucide-react'

const FLOW = ['Dictar', 'Generar', 'Aprobar', 'Publicar', 'Medir']

/**
 * Panel de marca compartido por Login y Register: el azul marino del icono,
 * el recorrido real del producto y un testimonio rotulado como ejemplo
 * (los textos vienen de /api/auth/brand-content/ y no son clientes reales).
 * Sin foto: un avatar de iniciales evita poner cara real a una persona de ejemplo.
 * `highlights` los provee cada pantalla; `demo: true` marca un dato de ejemplo.
 */
export default function AuthBrandPanel({
  highlights = [],
  quote = 'NexoMark transformó nuestra estrategia digital. Lo que antes nos tomaba una semana, ahora lo resolvemos en una mañana.',
  personName = 'Elena Rodríguez',
  personRole = 'Directora de Marketing, Global Creative Co.',
}) {
  const iniciales = personName
    .split(' ')
    .filter(Boolean)
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <aside className="relative hidden min-h-screen w-[46%] shrink-0 flex-col justify-between overflow-hidden bg-navy px-12 py-12 text-on-navy md:flex lg:px-16">
      {/* La N del icono, ampliada y recortada por el borde: firma de marca */}
      <img
        src="/nexomark-icon-192.png"
        alt=""
        aria-hidden="true"
        className="pointer-events-none absolute -right-24 -top-20 h-[26rem] w-[26rem] opacity-[0.07]"
      />

      <motion.div
        initial={{ opacity: 0, transform: 'translateY(12px)' }}
        animate={{ opacity: 1, transform: 'translateY(0px)' }}
        transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
        className="relative max-w-md"
      >
        <p className="text-[2.5rem] font-extrabold leading-[1.05] tracking-[-0.03em] text-balance">
          De la idea dictada al post publicado.
        </p>
        <ol className="mt-8 flex flex-wrap items-center gap-x-1.5 gap-y-2 text-sm font-semibold" aria-label="Recorrido de una campaña">
          {FLOW.map((step, index) => (
            <li key={step} className="flex items-center gap-1.5">
              <span className={index === 0 ? 'rounded-md bg-turquoise px-2 py-1 text-navy' : 'rounded-md bg-white/[0.08] px-2 py-1 text-on-navy'}>
                {step}
              </span>
              {index < FLOW.length - 1 && <ArrowRight className="h-3.5 w-3.5 text-turquoise" aria-hidden="true" />}
            </li>
          ))}
        </ol>

        {highlights.length > 0 && (
          <ul className="mt-10 space-y-5">
            {highlights.map(({ icon: Icon, titulo, desc, demo }) => (
              <li key={titulo} className="flex gap-4">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-navy-raised">
                  {Icon && <Icon className="h-[18px] w-[18px] text-turquoise" aria-hidden="true" />}
                </span>
                <div>
                  <p className="flex flex-wrap items-center gap-2 font-semibold">
                    {titulo}
                    {demo && (
                      <span className="demo-tag demo-tag-on-navy">
                        <Info className="h-3 w-3" aria-hidden="true" />
                        Dato de ejemplo
                      </span>
                    )}
                  </p>
                  <p className="mt-0.5 text-[15px] leading-relaxed text-on-navy-muted">{desc}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </motion.div>

      <figure className="relative mt-12 max-w-md rounded-2xl bg-navy-raised p-6">
        <span className="demo-tag demo-tag-on-navy">
          <Info className="h-3 w-3" aria-hidden="true" />
          Testimonio de ejemplo, no es un cliente real
        </span>
        <blockquote className="mt-4 text-[17px] font-medium leading-relaxed">«{quote}»</blockquote>
        <figcaption className="mt-5 flex items-center gap-3">
          <span
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/10 text-sm font-bold text-on-navy"
            aria-hidden="true"
          >
            {iniciales}
          </span>
          <span>
            <span className="block text-sm font-semibold">{personName}</span>
            <span className="block text-[13px] text-on-navy-muted">{personRole}</span>
          </span>
        </figcaption>
      </figure>

      <p className="relative mt-10 text-[13px] text-on-navy-muted">© {new Date().getFullYear()} NexoMark IA</p>
    </aside>
  )
}
