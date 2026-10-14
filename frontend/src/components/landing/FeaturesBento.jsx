import { motion } from 'motion/react'
import { PenLine, BarChart3, Smartphone } from 'lucide-react'
import featureImage from '@/assets/landing/feature-image.png'

/**
 * Bento grid de funciones reales de NexoMark:
 * copy cognitivo, imágenes IA, analytics y app del cliente.
 */
const reveal = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-60px' },
  transition: { duration: 0.5 },
}

export default function FeaturesBento() {
  return (
    <section id="funciones" className="bg-white py-24">
      <div className="mx-auto max-w-[1440px] px-6 md:px-10">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3 md:grid-rows-2">
          {/* Copy IA — tarjeta alta */}
          <motion.div
            {...reveal}
            className="glass-card flex flex-col justify-between rounded-3xl p-8 transition-all hover:shadow-xl md:row-span-2"
          >
            <div>
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                <PenLine className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mb-4 text-3xl font-semibold text-on-surface">
                Texto con intención
              </h3>
              <p className="text-base text-on-surface-variant">
                Prepara el mensaje de tu negocio según su público, tono y canal.
                Revísalo y ajústalo antes de enviarlo al cliente.
              </p>
            </div>
            <blockquote className="mt-8 bg-surface-container p-5 text-sm leading-relaxed text-on-surface">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-primary">Ejemplo de texto</p>
              Un buen café también es una buena pausa. Descubre el sabor que
              acompaña tus mañanas y compártelo con alguien especial.
            </blockquote>
          </motion.div>

          {/* Imágenes IA — tarjeta ancha */}
          <motion.div
            {...reveal}
            transition={{ duration: 0.5, delay: 0.08 }}
            className="glass-card flex items-center gap-8 rounded-3xl p-8 transition-all hover:shadow-xl md:col-span-2"
          >
            <div className="flex-1">
              <h3 className="mb-4 text-3xl font-semibold text-on-surface">
                Imágenes de impacto
              </h3>
              <p className="text-base text-on-surface-variant">
                Motor de generación visual integrado. Crea la imagen del anuncio a
                partir del brief, sin salir de la plataforma.
              </p>
            </div>
            <div className="hidden flex-1 md:block">
              <img
                src={featureImage}
                alt="Imagen de producto generada por IA"
                className="h-48 w-full rounded-2xl object-cover"
              />
            </div>
          </motion.div>

          {/* Analytics */}
          <motion.div
            {...reveal}
            transition={{ duration: 0.5, delay: 0.12 }}
            className="glass-card rounded-3xl p-8 transition-all hover:shadow-xl"
          >
            <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-tertiary/10">
              <BarChart3 className="h-6 w-6 text-tertiary" />
            </div>
            <h3 className="mb-2 text-2xl font-semibold text-on-surface">Analytics</h3>
            <p className="text-sm text-on-surface-variant">
              Mide el estado de tus campañas y el consumo de créditos en tiempo real.
            </p>
          </motion.div>

          {/* App cliente */}
          <motion.div
            {...reveal}
            transition={{ duration: 0.5, delay: 0.16 }}
            className="glass-card flex flex-col justify-between rounded-3xl p-8 transition-all hover:shadow-xl"
          >
            <div>
              <h3 className="mb-2 text-2xl font-semibold text-on-surface">
                App para tu cliente
              </h3>
              <p className="text-sm text-on-surface-variant">
                Tus clientes aprueban o rechazan campañas en segundos desde su móvil.
              </p>
            </div>
            <div className="mt-4 flex justify-end">
              <Smartphone className="h-9 w-9 text-outline-variant" />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
