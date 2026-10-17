import { Info } from 'lucide-react'
import g1 from '@/assets/landing/gallery-1.webp'
import g2 from '@/assets/landing/gallery-2.webp'
import g3 from '@/assets/landing/gallery-3.webp'
import g4 from '@/assets/landing/gallery-4.webp'
import g5 from '@/assets/landing/gallery-5.webp'
import g6 from '@/assets/landing/gallery-6.webp'

/**
 * Galería estática de imágenes de ejemplo generadas con IA. Sin carrusel ni
 * movimiento infinito: se ve completa de un vistazo, también en el teléfono.
 */
const IMAGES = [
  { src: g6, rubro: 'Cafetería', alt: 'Taza de café con arte latte sobre granos' },
  { src: g4, rubro: 'Moda', alt: 'Modelo con conjunto de lino claro sobre fondo verde' },
  { src: g1, rubro: 'Relojería', alt: 'Reloj deportivo oscuro con detalles turquesa' },
  { src: g2, rubro: 'Mercado', alt: 'Teléfono mostrando una caja de verduras frescas' },
  { src: g3, rubro: 'Hospedaje', alt: 'Villa con piscina al atardecer' },
  { src: g5, rubro: 'Eventos', alt: 'Afiche con una forma abstracta turquesa y violeta' },
]

export default function ShowcaseGallery() {
  return (
    <section id="ejemplos" aria-labelledby="ejemplos-title" className="scroll-mt-16 px-2 py-24 sm:px-3 lg:py-36">
      <div className="mx-auto max-w-[1440px]">
        <div className="flex flex-wrap items-end justify-between gap-4 px-2 sm:px-3 lg:px-8">
          <h2
            id="ejemplos-title"
            className="text-[clamp(2rem,4vw,3.5rem)] font-extrabold leading-[1.05] tracking-[-0.03em] text-on-surface"
          >
            Imágenes de ejemplo
          </h2>
          <p className="flex max-w-md items-start gap-2 text-base text-on-surface-variant">
            <Info className="mt-1 h-4 w-4 shrink-0" aria-hidden="true" />
            Generadas con IA para campañas de prueba. No son clientes ni publicaciones reales.
          </p>
        </div>
        <ul className="mt-12 grid grid-cols-2 gap-2 sm:gap-3 lg:mt-16 lg:grid-cols-3">
          {IMAGES.map((image) => (
            <li key={image.rubro} className="relative overflow-hidden rounded-2xl bg-surface-container">
              <img
                src={image.src}
                alt={image.alt}
                width="512"
                height="512"
                loading="lazy"
                className="aspect-square w-full object-cover"
              />
              <span className="absolute bottom-2 left-2 rounded-md bg-navy/85 px-2.5 py-1 text-[13px] font-medium text-on-navy sm:bottom-3 sm:left-3">
                {image.rubro}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
