import { Toaster } from 'react-hot-toast'

/**
 * Toaster único de la app. Los toasts flotan sobre el contenido: superficie
 * sólida del tema, borde fino y sombra de elemento flotante (claro y oscuro).
 * Reemplaza a los <Toaster/> sueltos por página para garantizar consistencia.
 */
export default function AppToaster() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: 'var(--color-surface-container-lowest)',
          color: 'var(--color-on-surface)',
          border: '1px solid var(--color-outline-variant)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-lg)',
          fontWeight: 500,
        },
        success: { iconTheme: { primary: 'var(--color-success)', secondary: 'var(--color-surface-container-lowest)' } },
        error: { iconTheme: { primary: 'var(--color-error)', secondary: 'var(--color-surface-container-lowest)' } },
      }}
    />
  )
}
