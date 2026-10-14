import { Link } from 'react-router-dom'
import { ArrowRight, Check, FileText, Image as ImageIcon, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import PlatformIcon from '@/components/campaign/PlatformIcon'
import heroBackground from '@/assets/landing/hero-business-background-v1.png'

const WORKFLOW = [
  { title: 'Brief del negocio', detail: 'Producto, público y objetivo', icon: FileText },
  { title: 'Contenido de campaña', detail: 'Texto e imagen para cada canal', icon: ImageIcon },
  { title: 'Revisión del cliente', detail: 'Feedback y aprobación antes de publicar', icon: Check },
  { title: 'Publicación', detail: 'Entrega según el flujo de cada plataforma', icon: Send },
]

/** Demonstration only: no API calls, generated assets or publication actions. */
export default function HeroSection() {
  return (
    <section className="landing-hero pt-28 pb-16 md:pt-40 md:pb-24" style={{ '--hero-photo': `url(${heroBackground})` }}>
      <div className="mx-auto grid max-w-[1440px] items-center gap-12 px-6 md:px-10 lg:grid-cols-[1.05fr_1fr] lg:gap-20">
        <div className="hero-introduction">
          <p className="mb-6 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
            Del negocio a sus clientes
          </p>
          <h1 className="mb-6 max-w-2xl text-4xl font-semibold leading-[1.08] tracking-tight text-on-surface md:text-6xl">
            Tus ideas, convertidas en <span className="text-primary">campañas.</span>
          </h1>
          <p className="mb-8 max-w-xl text-lg leading-relaxed text-on-surface-variant">
            Crea contenido con IA, trabaja las propuestas con tu cliente y lleva
            cada campaña a sus redes. Todo en un mismo espacio, con la aprobación
            siempre en manos de las personas.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link to="/login">
              <Button className="shadow-sm">Crear mi campaña <ArrowRight className="h-4 w-4" /></Button>
            </Link>
            <a href="#como-funciona">
              <Button variant="ghost">Conocer el proceso</Button>
            </a>
          </div>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <span className="text-sm text-on-surface-variant">Conecta tus canales</span>
            {['facebook', 'instagram', 'twitter', 'tiktok'].map(platform => (
              <PlatformIcon key={platform} platform={platform} className="h-5 w-5" />
            ))}
          </div>
        </div>
        <div className="workflow-demo" aria-label="Ejemplo ilustrativo del flujo de una campaña">
          <div className="flex items-center justify-between gap-4 pb-6">
            <div className="flex items-center gap-3">
              <img src="/nexomark-icon.png" alt="" className="h-8 w-8" />
              <span className="text-sm font-semibold">Un proceso conectado</span>
            </div>
            <span className="text-xs text-white/70">Ejemplo de flujo</span>
          </div>
          <ol className="workflow-steps">
            {WORKFLOW.map(({ title, detail, icon: Icon }, index) => (
              <li key={title} className="workflow-step" style={{ '--step': index }}>
                <span className="workflow-step-number" aria-hidden="true">0{index + 1}</span>
                <div className="workflow-step-content">
                  <div className="flex items-center gap-3">
                    <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                    <span className="text-sm font-semibold">{title}</span>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-white/75">{detail}</p>
                  <div className="workflow-step-progress" aria-hidden="true"><span /></div>
                </div>
              </li>
            ))}
          </ol>
          <p className="mt-6 text-xs leading-relaxed text-white/70">
            Tú creas. Tu cliente revisa. NexoMark conecta el proceso.
          </p>
        </div>
      </div>
    </section>
  )
}
