import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { Button } from '@/components/ui/button'

/**
 * CTA final + footer. El HTML de Stitch no traía footer;
 * se construye coherente con el sistema Lumina Creative.
 */
export default function LandingFooter() {
  return (
    <footer>
      {/* CTA final */}
      <section className="mx-auto max-w-[1440px] px-6 pb-16 md:px-10">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.6 }}
          className="step-gradient overflow-hidden rounded-3xl px-8 py-16 text-center text-white md:px-16"
        >
          <h2 className="mx-auto mb-4 max-w-2xl text-4xl font-bold tracking-tight text-balance">
            Empieza a crear campañas con IA hoy mismo
          </h2>
          <p className="mx-auto mb-8 max-w-xl text-lg text-white/85">
            Regístrate gratis y genera tu primera campaña en minutos.
          </p>
          <Link to="/login">
            <Button variant="light" size="lg">
              Empezar gratis
            </Button>
          </Link>
        </motion.div>
      </section>

      {/* Pie */}
      <div className="border-t border-outline-variant bg-surface-container-low">
        <div className="mx-auto flex max-w-[1440px] flex-col items-center gap-4 px-6 py-10 text-center md:px-10">
          <span className="text-xl font-bold text-primary">MarketMind IA</span>
          <p className="max-w-md text-sm text-on-surface-variant">
            Automatización de campañas publicitarias con IA para agencias digitales.
          </p>
          <div className="flex gap-6 text-sm text-on-surface-variant">
            <a href="#precios" className="transition-colors hover:text-primary">
              Precios
            </a>
            <a href="#funciones" className="transition-colors hover:text-primary">
              Funciones
            </a>
            <Link to="/login" className="transition-colors hover:text-primary">
              Iniciar sesión
            </Link>
          </div>
          <p className="mt-2 text-xs text-outline">
            © {new Date().getFullYear()} MarketMind IA. Todos los derechos reservados.
          </p>
        </div>
      </div>
    </footer>
  )
}
