import { useForm } from 'react-hook-form'
import { useNavigate, Link } from 'react-router-dom'
import toast, { Toaster } from 'react-hot-toast'
import { Zap, ShieldCheck, Sparkles } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { Button } from '@/components/ui/button'
import AuthBrandPanel from '@/components/auth/AuthBrandPanel'

/**
 * Login rediseñado (sistema Lumina Creative). Split: formulario + panel de marca.
 * LÓGICA INTACTA: useForm + useAuth().login → shape plano JWT → /dashboard.
 * Sin OAuth social (el backend solo emite JWT).
 */
export default function LoginPage() {
  const { login, loading } = useAuth()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm()

  async function onSubmit({ email, password }) {
    const result = await login(email, password)

    if (!result.ok) {
      const msg =
        result.status === 401 || result.status === 400
          ? 'Credenciales inválidas'
          : 'Error del servidor. Intenta de nuevo.'
      toast.error(msg)
      return
    }

    // Todos los roles van a /dashboard por ahora (HU8 diferenciará)
    navigate('/dashboard', { replace: true })
  }

  return (
    <main className="flex min-h-screen flex-col md:flex-row">
      <Toaster position="top-right" />

      {/* Izquierda: formulario */}
      <section className="z-10 flex w-full items-center justify-center bg-surface p-8 md:w-1/2 md:p-16 lg:p-24">
        <div className="w-full max-w-md">
          <div className="mb-12">
            <Link to="/" className="text-3xl font-bold tracking-tight text-primary">
              MarketMind IA
            </Link>
            <p className="mt-2 text-base text-on-surface-variant">
              Impulsa tu marketing con inteligencia artificial de alto rendimiento.
            </p>
          </div>

          <div className="space-y-6">
            <div className="flex flex-col gap-2">
              <h2 className="text-2xl font-semibold text-on-surface">Bienvenido de nuevo</h2>
              <p className="text-base text-on-surface-variant">
                Ingresa tus credenciales para acceder a tu panel.
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
              <div className="space-y-1.5">
                <label
                  htmlFor="email"
                  className="px-1 text-sm font-medium text-on-surface-variant"
                >
                  Correo electrónico
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="nombre@empresa.com"
                  className={`w-full rounded-xl border px-4 py-3 text-base outline-none transition-all focus:border-transparent focus:ring-2 focus:ring-primary ${
                    errors.email ? 'border-error' : 'border-outline-variant'
                  }`}
                  {...register('email', {
                    required: 'El email es requerido',
                    pattern: {
                      value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                      message: 'Ingresa un email válido',
                    },
                  })}
                />
                {errors.email && (
                  <p className="px-1 text-xs text-error">{errors.email.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between px-1">
                  <label htmlFor="password" className="text-sm font-medium text-on-surface-variant">
                    Contraseña
                  </label>
                  <a href="#" className="text-sm font-medium text-primary hover:underline">
                    ¿Olvidaste tu contraseña?
                  </a>
                </div>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className={`w-full rounded-xl border px-4 py-3 text-base outline-none transition-all focus:border-transparent focus:ring-2 focus:ring-primary ${
                    errors.password ? 'border-error' : 'border-outline-variant'
                  }`}
                  {...register('password', {
                    required: 'La contraseña es requerida',
                    minLength: { value: 8, message: 'Mínimo 8 caracteres' },
                  })}
                />
                {errors.password && (
                  <p className="px-1 text-xs text-error">{errors.password.message}</p>
                )}
              </div>

              <div className="flex items-center gap-2 px-1">
                <input
                  id="remember"
                  type="checkbox"
                  className="h-4 w-4 rounded border-outline-variant text-primary focus:ring-primary"
                />
                <label htmlFor="remember" className="text-sm text-on-surface-variant">
                  Mantener sesión iniciada
                </label>
              </div>

              <Button type="submit" size="lg" disabled={loading} className="w-full text-lg">
                {loading ? 'Ingresando…' : 'Iniciar sesión'}
              </Button>
            </form>

            <p className="text-center text-base text-on-surface-variant">
              ¿No tienes una cuenta?{' '}
              <Link to="/register" className="font-semibold text-primary hover:underline">
                Regístrate ahora
              </Link>
            </p>
          </div>
        </div>
      </section>

      {/* Derecha: panel de marca */}
      <AuthBrandPanel
        highlights={[
          { icon: Zap, titulo: 'Generación 10× más rápida', desc: 'Crea activos publicitarios en segundos, no horas.' },
          { icon: ShieldCheck, titulo: 'Aprobaciones simplificadas', desc: 'Flujos colaborativos entre marketero y cliente.' },
        ]}
        badgeIcon={Sparkles}
      />
    </main>
  )
}
