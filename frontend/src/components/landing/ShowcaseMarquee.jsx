import g1 from '@/assets/landing/gallery-1.png'
import g2 from '@/assets/landing/gallery-2.png'
import g3 from '@/assets/landing/gallery-3.png'
import g4 from '@/assets/landing/gallery-4.png'
import g5 from '@/assets/landing/gallery-5.png'
import g6 from '@/assets/landing/gallery-6.png'

const IMAGES = [g1, g2, g3, g4, g5, g6]

export default function ShowcaseMarquee() {
  return (
    <section className="bg-surface-container-low py-16" aria-label="Ejemplos de imágenes para campañas">
      <div className="mx-auto max-w-[1440px] px-6 md:px-10">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <h2 className="text-2xl font-semibold text-on-surface">Cada negocio tiene una historia.</h2>
          <p className="text-sm text-on-surface-variant">Ejemplos visuales de campañas</p>
        </div>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          {IMAGES.map((src, index) => (
            <img key={src} src={src} alt={`Ejemplo visual de campaña ${index + 1}`}
              loading="lazy" className="aspect-square w-full rounded-sm object-cover" />
          ))}
        </div>
      </div>
    </section>
  )
}
