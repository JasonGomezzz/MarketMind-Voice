import { useState } from 'react'
import { motion, useAnimationFrame, useMotionValue } from 'motion/react'
import g1 from '@/assets/landing/gallery-1.png'
import g2 from '@/assets/landing/gallery-2.png'
import g3 from '@/assets/landing/gallery-3.png'
import g4 from '@/assets/landing/gallery-4.png'
import g5 from '@/assets/landing/gallery-5.png'
import g6 from '@/assets/landing/gallery-6.png'

/**
 * Galería showcase de anuncios generados.
 * - Auto-scroll infinito hacia la izquierda.
 * - Se PAUSA al pasar el mouse por encima.
 * - Se puede ARRASTRAR con el mouse/touch (drag horizontal).
 * - Cada imagen hace un ligero ZOOM al hover.
 */
const IMAGES = [g1, g2, g3, g4, g5, g6]
const CARD = 256 // ancho (w-64) + gap gestionado por CSS
const GAP = 32 // gap-8
const SPEED = 40 // px por segundo
// Ancho de UNA tanda (la mitad del track duplicado). Las tarjetas son de
// tamaño fijo, así que es una constante — no hay nada que medir en resize.
const HALF = (CARD + GAP) * IMAGES.length

export default function ShowcaseMarquee() {
  // duplicamos las imágenes para el bucle infinito
  const loop = [...IMAGES, ...IMAGES]
  const x = useMotionValue(0)
  const [paused, setPaused] = useState(false)
  const [dragging, setDragging] = useState(false)

  // auto-scroll: avanza x cada frame salvo si está en pausa o arrastrando
  useAnimationFrame((_, delta) => {
    if (paused || dragging) return
    let next = x.get() - (SPEED * delta) / 1000
    // reciclar sin salto: al pasar una tanda, sumamos su ancho
    if (next <= -HALF) next += HALF
    x.set(next)
  })

  // al soltar el drag, normalizamos x dentro del rango del bucle
  function handleDragEnd() {
    setDragging(false)
    let v = x.get() % HALF
    if (v > 0) v -= HALF
    x.set(v)
  }

  return (
    <section
      className="overflow-hidden bg-surface-container-highest py-16"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      aria-label="Galería de anuncios generados con IA"
    >
      <motion.div
        className="flex w-max cursor-grab gap-8 px-8 active:cursor-grabbing"
        style={{ x }}
        drag="x"
        dragConstraints={{ left: -HALF * 2, right: HALF }}
        dragElastic={0.05}
        onDragStart={() => setDragging(true)}
        onDragEnd={handleDragEnd}
      >
        {loop.map((src, i) => (
          <motion.img
            key={i}
            src={src}
            alt=""
            aria-hidden={i >= IMAGES.length}
            draggable={false}
            whileHover={{ scale: 1.05 }}
            transition={{ type: 'spring', stiffness: 300, damping: 22 }}
            className="h-64 w-64 flex-shrink-0 select-none rounded-2xl object-cover shadow-sm"
          />
        ))}
      </motion.div>
    </section>
  )
}
