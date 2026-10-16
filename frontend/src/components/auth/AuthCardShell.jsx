import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

/**
 * Marco de las pantallas públicas pequeñas de autenticación (recuperar y
 * restablecer contraseña): misma superficie que el login, sin panel de marca.
 */
export default function AuthCardShell({ title, subtitle, children }) {
  return (
    <main className="auth-shell flex min-h-screen items-center justify-center px-4 py-16">
      <Link
        to="/login"
        className="glass-soft fixed left-4 top-4 z-30 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold text-on-surface shadow-sm transition hover:-translate-y-0.5 hover:bg-surface-container-low"
      >
        <ArrowLeft className="h-4 w-4" />
        Volver al login
      </Link>
      <section className="glass-liquid w-full max-w-md rounded-[2rem] p-7 md:p-9">
        <Link to="/" className="text-2xl font-bold tracking-tight text-primary">
          NexoMark IA
        </Link>
        <h1 className="mt-8 text-2xl font-semibold text-on-surface">{title}</h1>
        {subtitle && <p className="mt-2 text-base text-on-surface-variant">{subtitle}</p>}
        <div className="mt-6">{children}</div>
      </section>
    </main>
  )
}
