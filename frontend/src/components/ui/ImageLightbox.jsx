import { useEffect, useState } from 'react'
import { Download, Maximize2, X } from 'lucide-react'

/**
 * Imagen compacta con lightbox a pantalla completa.
 * Vista normal: contenida a max-h-[400px] (la imagen IA de ~1MP ya no obliga
 * a hacer zoom-out) con caption y descarga. Clic/Enter → modal glass oscuro
 * con la imagen a 90vh/90vw, Esc / clic-fuera / X cierran.
 * El texto/alt viene de datos propios (no HTML crudo) — escapado JSX normal.
 */
export default function ImageLightbox({ src, alt, downloadName }) {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    function onKey(e) {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  return (
    <>
      {/* Vista compacta */}
      <div className="space-y-2">
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Ver imagen a pantalla completa"
          className="group relative block w-full cursor-zoom-in overflow-hidden rounded-lg bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <img
            src={src}
            alt={alt}
            className="mx-auto max-h-[400px] w-auto object-contain transition-transform duration-300 group-hover:scale-[1.02]"
          />
          <span className="pointer-events-none absolute bottom-3 right-3 inline-flex items-center gap-1.5 rounded-full bg-on-surface/70 px-3 py-1.5 text-xs font-medium text-white opacity-0 backdrop-blur-sm transition-opacity group-hover:opacity-100">
            <Maximize2 className="h-3.5 w-3.5" />
            Pantalla completa
          </span>
        </button>
        <div className="flex items-center justify-between">
          <p className="text-xs text-on-surface-variant">Clic en la imagen para ampliarla</p>
          <a
            href={src}
            download={downloadName}
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline"
          >
            <Download className="h-4 w-4" />
            Descargar PNG
          </a>
        </div>
      </div>

      {/* Lightbox */}
      {open && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={alt || 'Imagen a pantalla completa'}
          onClick={() => setOpen(false)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-on-surface/80 p-4 backdrop-blur-md"
        >
          <img
            src={src}
            alt={alt}
            onClick={(e) => e.stopPropagation()}
            className="max-h-[90vh] max-w-[90vw] rounded-xl object-contain shadow-2xl"
          />
          <button
            onClick={() => setOpen(false)}
            aria-label="Cerrar imagen"
            className="absolute right-5 top-5 rounded-full bg-white/10 p-2.5 text-white transition-colors hover:bg-white/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
          >
            <X className="h-5 w-5" />
          </button>
          <a
            href={src}
            download={downloadName}
            onClick={(e) => e.stopPropagation()}
            className="glass-liquid-dark absolute bottom-6 inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold text-white"
          >
            <Download className="h-4 w-4" />
            Descargar PNG
          </a>
        </div>
      )}
    </>
  )
}
