import { motion } from 'motion/react'
import { FileText, PenLine, Image as ImageIcon, CheckCheck, Rocket } from 'lucide-react'

/**
 * "Cómo funciona": el pipeline real de NexoMark como 5 pasos animados
 * al hacer scroll. Refleja el flujo Brief → Copy IA → Imagen IA → Aprobación → Publicar.
 */
const STEPS = [
  { icon: FileText, titulo: 'Brief', desc: 'Describe tu producto, tono y plataforma objetivo.' },
  { icon: PenLine, titulo: 'Copy con IA', desc: 'Gemini redacta el mensaje persuasivo del anuncio.' },
  { icon: ImageIcon, titulo: 'Imagen con IA', desc: 'Se genera la imagen del anuncio a partir del brief.' },
  { icon: CheckCheck, titulo: 'Aprobación', desc: 'Tu cliente revisa y aprueba desde web o móvil.' },
  { icon: Rocket, titulo: 'Publicar', desc: 'La campaña queda lista para lanzarse.' },
]

export default function HowItWorks() {
  return (
    <section id="como-funciona" className="bg-surface-container-low py-24">
      <div className="mx-auto max-w-[1440px] px-6 md:px-10">
        <div className="mb-16 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.5 }}
            className="mb-4 text-4xl font-bold tracking-tight text-on-surface text-balance"
          >
            De la idea a la campaña, guiado por IA
          </motion.h2>
          <p className="mx-auto max-w-xl text-base text-on-surface-variant">
            El motor de IA te acompaña en cada paso, desde el brief inicial hasta
            la aprobación del cliente.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-8 md:grid-cols-5">
          {STEPS.map((step, i) => {
            const Icon = step.icon
            return (
              <motion.div
                key={step.titulo}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-60px' }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="group text-center"
              >
                <div className="step-gradient mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full text-white shadow-lg transition-transform group-hover:scale-110">
                  <Icon className="h-7 w-7" />
                </div>
                <h3 className="mb-2 text-2xl font-semibold text-on-surface">
                  {step.titulo}
                </h3>
                <p className="px-4 text-sm text-on-surface-variant">{step.desc}</p>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
