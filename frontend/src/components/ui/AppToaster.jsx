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
          background: 'var(--color-surface-container-lowest)',
          border: 'none',
          borderRadius: 4,
          boxShadow: 'var(--shadow-sm)',
          color: 'var(--color-on-surface)',
          fontWeight: 500,
        },
      }}
    />
  )
}
