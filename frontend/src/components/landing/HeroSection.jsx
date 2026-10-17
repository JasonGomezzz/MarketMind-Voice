import { ArrowRight } from 'lucide-react'
import { ButtonLink } from '@/components/ui/button'
import FlowDemo from '@/components/landing/FlowDemo'
import instagramLogo from '@/assets/social/instagram.png'
import facebookLogo from '@/assets/social/facebook.png'
import deskPhoto from '@/assets/landing/hero-desk.webp'

/**
 * Portada como tablero: la propuesta a la izquierda, el flujo de ejemplo a la
 * derecha (la pieza viva de la página) y una foto de ambiente. Sin llamadas a
 * la API: todo lo que se ve aquí es demostración.
 */
export default function HeroSection() {
  return (
    <section aria-labelledby="hero-title" className="px-2 pt-2 sm:px-3 sm:pt-3">
      <div className="mx-auto grid max-w-[1440px] gap-2 sm:gap-3 lg:grid-cols-12 lg:grid-rows-[auto_minmax(15rem,1fr)]">
        {/* Propuesta */}
        <div className="flex flex-col justify-between rounded-2xl bg-surface-container-low px-6 py-10 sm:px-10 sm:py-14 lg:col-span-7 lg:px-14 lg:py-16">
          <div>
            <h1
              id="hero-title"
              className="text-[clamp(1.85rem,5.3vw,4.6rem)] font-extrabold leading-[1.02] tracking-[-0.035em] text-on-surface"
            >
              De la idea dictada al post publicado.
            </h1>
            <p className="mt-7 max-w-[36rem] text-lg leading-relaxed text-on-surface sm:text-xl">
              Dicta la campaña con tu voz. La IA escribe el copy y crea la imagen, tu cliente aprueba esa versión
              exacta y NexoMark la publica en Instagram y Facebook.
            </p>
            <div className="mt-9 flex flex-wrap items-center gap-3">
              <ButtonLink to="/register" size="lg">
                Crear mi primera campaña
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </ButtonLink>
              <ButtonLink href="#como-funciona" variant="ghost" size="lg">
                Ver cómo funciona
              </ButtonLink>
            </div>
          </div>
          <div className="mt-12 flex items-center gap-3 text-[15px] text-on-surface-variant">
            <span>Publica en</span>
            <img src={instagramLogo} alt="Instagram" width="24" height="24" className="h-6 w-6" />
            <img src={facebookLogo} alt="Facebook" width="24" height="24" className="h-6 w-6" />
          </div>
        </div>

        {/* La pieza viva: el flujo de ejemplo */}
        <div className="lg:col-span-5 lg:row-span-2">
          <FlowDemo />
        </div>

        {/* Foto de ambiente (generada con IA; ver hero-desk.prompt.md) */}
        <figure className="shutter-in relative min-h-60 overflow-hidden rounded-2xl bg-surface-container lg:col-span-7">
          <img
            src={deskPhoto}
            alt="Escritorio de un pequeño negocio preparando una campaña: laptop, prenda doblada y hojas de fotos"
            width="1600"
            height="900"
            className="absolute inset-0 h-full w-full object-cover object-[70%_70%]"
          />
          <figcaption className="absolute bottom-3 left-3 rounded-md bg-navy/85 px-2.5 py-1 text-[13px] font-medium text-on-navy">
            Foto de ambiente generada con IA
          </figcaption>
        </figure>
      </div>
    </section>
  )
}
