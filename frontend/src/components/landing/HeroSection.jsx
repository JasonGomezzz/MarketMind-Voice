import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import heroImg from '@/assets/landing/hero.png'

/**
 * Hero de la landing. Titular potente + 2 CTAs + mockup con zoom-in de entrada.
 * Tarjeta flotante "glass" para dar profundidad.
 */
export default function HeroSection() {
  return (
    <section className="relative overflow-hidden pt-32 pb-24">
      <div className="mx-auto max-w-[1440px] px-6 text-center md:px-10">
        <motion.span
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6 inline-block rounded-full bg-secondary-container px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-on-secondary-container"
        >
          Nueva era del marketing con IA
        </motion.span>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.05 }}
          className="mx-auto mb-6 max-w-4xl text-4xl font-extrabold leading-tight tracking-tight text-on-surface text-balance md:text-6xl"
        >
          Crea campañas publicitarias con IA en{' '}
          <span className="italic text-primary">segundos</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.12 }}
          className="mx-auto mb-10 max-w-2xl text-lg text-on-surface-variant"
        >
          Desde el brief hasta la aprobación. Genera copys persuasivos, imágenes
          deslumbrantes y gestiona las aprobaciones de tus clientes en una sola
          plataforma.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.18 }}
          className="mb-16 flex flex-col justify-center gap-4 sm:flex-row"
        >
          <Link to="/login">
            <Button size="lg" className="w-full sm:w-auto">
              Empezar gratis
            </Button>
          </Link>
          <a href="#como-funciona">
            <Button variant="outline" size="lg" className="w-full sm:w-auto">
              Ver cómo funciona
            </Button>
          </a>
        </motion.div>

        {/* Mockup del producto con zoom-in de entrada */}
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 40 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          className="relative mx-auto max-w-5xl"
        >
          <div className="overflow-hidden rounded-3xl border-4 border-white/50 bg-surface-variant shadow-2xl">
            <img
              src={heroImg}
              alt="Panel de MarketMind IA generando el copy y la imagen de una campaña"
              className="aspect-[16/10] w-full object-cover"
            />
          </div>

          {/* Tarjeta flotante para profundidad */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.9 }}
            className="glass-card absolute -top-6 -right-6 hidden rounded-xl p-4 shadow-xl md:block"
          >
            <div className="flex items-center gap-3">
              <Sparkles className="h-5 w-5 text-primary" />
              <div className="text-left">
                <p className="text-xs uppercase tracking-wider text-on-surface-variant">
                  Generación IA
                </p>
                <p className="text-sm font-bold text-on-surface">98% completado</p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}
