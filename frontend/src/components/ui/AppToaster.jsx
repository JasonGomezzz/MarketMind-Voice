import { Toaster } from 'react-hot-toast'

/**
 * Toaster único de la app con la receta liquid glass de Lumina (los toasts
 * FLOTAN sobre el contenido — es exactamente donde el glass corresponde).
 * Reemplaza a los <Toaster/> sueltos por página para garantizar consistencia.
 */
export default function AppToaster() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: 'rgba(255, 255, 255, 0.72)',
          backdropFilter: 'blur(18px) saturate(1.4)',
          WebkitBackdropFilter: 'blur(18px) saturate(1.4)',
          border: '1px solid rgba(255, 255, 255, 0.55)',
          boxShadow:
            '0 8px 32px rgba(45, 40, 90, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.6)',
          color: '#1b1b21',
          fontWeight: 500,
        },
      }}
    />
  )
}
