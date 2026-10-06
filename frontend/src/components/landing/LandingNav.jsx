import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

/**
 * Barra de navegación fija de la landing pública.
 * Glass + blur al hacer scroll. Navega a /login (no hay /register aún).
 */
export default function LandingNav() {
  return (
    <header className="fixed top-0 left-0 z-50 w-full bg-surface/80 backdrop-blur-md shadow-sm">
      <nav className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-6 md:px-10">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-2xl font-bold text-primary tracking-tight">
            NexoMark IA
          </Link>
          <div className="hidden items-center gap-6 md:flex">
            <a
              href="#como-funciona"
              className="text-base text-on-surface-variant transition-colors hover:text-primary"
            >
              Cómo funciona
            </a>
            <a
              href="#funciones"
              className="text-base text-on-surface-variant transition-colors hover:text-primary"
            >
              Funciones
            </a>
            <a
              href="#precios"
              className="text-base text-on-surface-variant transition-colors hover:text-primary"
            >
              Precios
            </a>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login">
            <Button variant="ghost" size="sm">
              Iniciar sesión
            </Button>
          </Link>
          <Link to="/login">
            <Button size="sm">Empezar gratis</Button>
          </Link>
        </div>
      </nav>
    </header>
  )
}
