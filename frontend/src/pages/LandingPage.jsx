import LandingNav from '@/components/landing/LandingNav'
import HeroSection from '@/components/landing/HeroSection'
import HowItWorks from '@/components/landing/HowItWorks'
import FeaturesBento from '@/components/landing/FeaturesBento'
import ShowcaseMarquee from '@/components/landing/ShowcaseMarquee'
import PricingSection from '@/components/landing/PricingSection'
import LandingFooter from '@/components/landing/LandingFooter'

/**
 * Landing page pública (ruta /). Se ve antes del login.
 * Ensambla las secciones del sistema Lumina Creative.
 */
export default function LandingPage() {
  return (
    <div className="bg-background text-on-background">
      <LandingNav />
      <main>
        <HeroSection />
        <HowItWorks />
        <FeaturesBento />
        <ShowcaseMarquee />
        <PricingSection />
      </main>
      <LandingFooter />
    </div>
  )
}
