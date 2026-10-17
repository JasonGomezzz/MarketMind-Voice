import LandingNav from '@/components/landing/LandingNav'
import HeroSection from '@/components/landing/HeroSection'
import HowItWorks from '@/components/landing/HowItWorks'
import FeaturesBento from '@/components/landing/FeaturesBento'
import ShowcaseGallery from '@/components/landing/ShowcaseGallery'
import PricingSection from '@/components/landing/PricingSection'
import LandingFooter from '@/components/landing/LandingFooter'

/**
 * Portada pública (ruta /), antes del login. Tablero de piezas con la marca
 * NexoMark: propuesta, flujo de ejemplo, pasos, funciones, ejemplos y planes.
 */
export default function LandingPage() {
  return (
    <div className="bg-background text-on-background">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[60] focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-on-primary"
      >
        Saltar al contenido
      </a>
      <LandingNav />
      <main id="contenido">
        <HeroSection />
        <HowItWorks />
        <FeaturesBento />
        <ShowcaseGallery />
        <PricingSection />
      </main>
      <LandingFooter />
    </div>
  )
}
