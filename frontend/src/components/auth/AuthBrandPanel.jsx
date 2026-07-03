import { motion } from 'motion/react'
import testimonialImg from '@/assets/landing/testimonial.png'

/**
 * Panel de marca derecho compartido por Login y Register.
 * Degradado indigo + blobs flotantes + glass-card con features + testimonial.
 * `highlights` y `badgeIcon` los provee cada pantalla.
 */
export default function AuthBrandPanel({ highlights = [], badgeIcon: BadgeIcon }) {
  return (
    <section className="relative hidden w-1/2 items-center justify-center overflow-hidden bg-primary-container p-12 md:flex">
      {/* Fondo animado */}
      <div className="absolute inset-0 z-0">
        <div className="step-gradient absolute inset-0 opacity-90" />
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />
        <motion.div
          className="absolute -left-[10%] -top-[10%] h-[60%] w-[60%] rounded-full bg-white/10 blur-[120px]"
          animate={{ y: [0, -20, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute -bottom-[5%] -right-[5%] h-[40%] w-[40%] rounded-full bg-secondary-container/20 blur-[100px]"
          animate={{ y: [0, -20, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut', delay: -2 }}
        />
      </div>

      {/* Contenido */}
      <div className="relative z-10 w-full max-w-lg text-on-primary">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12 rounded-2xl border border-white/20 bg-white/10 p-8 shadow-2xl backdrop-blur-md"
        >
          <div className="mb-6 flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/20">
              {BadgeIcon && <BadgeIcon className="h-6 w-6 text-white" />}
            </div>
            <div>
              <h3 className="text-xl font-semibold">Constructor inteligente de campañas</h3>
              <p className="text-xs uppercase tracking-widest opacity-80">
                Optimización en tiempo real
              </p>
            </div>
          </div>

          <div className="mb-6 h-2 w-full overflow-hidden rounded-full bg-white/10">
            <div className="h-full w-3/4 bg-white" />
          </div>

          <div className="flex flex-col gap-4">
            {highlights.map((h) => {
              const Icon = h.icon
              return (
                <div
                  key={h.titulo}
                  className="flex items-start gap-4 rounded-xl bg-white/5 p-4 transition-colors hover:bg-white/10"
                >
                  {Icon && <Icon className="h-5 w-5 shrink-0 text-tertiary-container" />}
                  <div>
                    <h4 className="text-sm font-bold">{h.titulo}</h4>
                    <p className="text-sm opacity-80">{h.desc}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </motion.div>

        {/* Testimonial */}
        <div className="px-4">
          <p className="mb-6 text-xl font-medium italic leading-relaxed">
            «MarketMind transformó nuestra estrategia digital. Lo que antes nos tomaba
            una semana, ahora lo resolvemos en una mañana.»
          </p>
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 overflow-hidden rounded-full border-2 border-white/20">
              <img
                src={testimonialImg}
                alt="Elena Rodríguez"
                className="h-full w-full object-cover"
              />
            </div>
            <div>
              <p className="text-sm font-bold">Elena Rodríguez</p>
              <p className="text-xs opacity-70">Directora de Marketing, Global Creative Co.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Pie */}
      <div className="absolute bottom-8 left-12 right-12 z-10 flex items-center justify-between text-xs text-on-primary/60">
        <span>© {new Date().getFullYear()} MarketMind IA</span>
        <div className="flex gap-6">
          <a href="#" className="transition-colors hover:text-white">Privacidad</a>
          <a href="#" className="transition-colors hover:text-white">Términos</a>
          <a href="#" className="transition-colors hover:text-white">Soporte</a>
        </div>
      </div>
    </section>
  )
}
