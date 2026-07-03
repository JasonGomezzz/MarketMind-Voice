import { useForm } from 'react-hook-form'
import { useNavigate, Link } from 'react-router-dom'
import { useState } from 'react'
import toast, { Toaster } from 'react-hot-toast'
import { Rocket, Users, Sparkles } from 'lucide-react'
import api from '../services/api'
import { Button } from '@/components/ui/button'
import AuthBrandPanel from '@/components/auth/AuthBrandPanel'

/**
 * Registro rediseñado (sistema Lumina Creative). Mismo split que Login.
 * Consume el endpoint real POST /api/auth/register/ con {email, nombre, password, rol}.
 * Sin OAuth. Roles ofrecidos: marketero (crea campañas) y cliente (revisa/aprueba).
 */
export default function RegisterPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm({ defaultValues: { rol: 'marketero' } })

  const rolSel = watch('rol')

  async function onSubmit({ nombre, email, password, rol }) {
    setLoading(true)
    try {
      await api.post('/api/auth/register/', { nombre, email, password, rol })
      toast.success('Cuenta creada. Ya puedes iniciar sesión.')
      navigate('/login', { replace: true })
    } catch (err) {
      // El backend envuelve los errores por campo en {success, message, data: {campo: [...]}}
      const fieldErrors = err.response?.data?.data
      const msg =
        fieldErrors?.email?.[0] ||
        fieldErrors?.password?.[0] ||
        fieldErrors?.nombre?.[0] ||
        fieldErrors?.rol?.[0] ||
        err.response?.data?.message ||
        'No se pudo crear la cuenta. Revisa los datos e intenta de nuevo.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const roles = [
    { val: 'marketero', label: 'Marketero', desc: 'Creo campañas con IA' },
    { val: 'cliente', label: 'Cliente', desc: 'Reviso y apruebo campañas' },
  ]

  return (
    <main className="flex min-h-screen flex-col md:flex-row">
      <Toaster position="top-right" />

      {/* Izquierda: formulario */}
      <section className="z-10 flex w-full items-center justify-center bg-surface p-8 md:w-1/2 md:p-16 lg:p-20">
        <div className="w-full max-w-md">
          <div className="mb-10">
            <Link to="/" className="text-3xl font-bold tracking-tight text-primary">
              MarketMind IA
            </Link>
            <p className="mt-2 text-base text-on-surface-variant">
              Impulsa tu marketing con inteligencia artificial de alto rendimiento.
            </p>
          </div>

          <div className="space-y-6">
            <div className="flex flex-col gap-2">
              <h2 className="text-2xl font-semibold text-on-surface">Crea tu cuenta</h2>
              <p className="text-base text-on-surface-variant">
                Empieza a generar campañas con IA en minutos.
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
              <div className="space-y-1.5">
                <label htmlFor="nombre" className="px-1 text-sm font-medium text-on-surface-variant">
                  Nombre completo
                </label>
                <input
                  id="nombre"
                  type="text"
                  autoComplete="name"
                  placeholder="Tu nombre"
                  className={`w-full rounded-xl border px-4 py-3 text-base outline-none transition-all focus:border-transparent focus:ring-2 focus:ring-primary ${
                    errors.nombre ? 'border-error' : 'border-outline-variant'
                  }`}
                  {...register('nombre', { required: 'El nombre es requerido' })}
                />
                {errors.nombre && <p className="px-1 text-xs text-error">{errors.nombre.message}</p>}
              </div>

              <div className="space-y-1.5">
                <label htmlFor="email" className="px-1 text-sm font-medium text-on-surface-variant">
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
                {errors.email && <p className="px-1 text-xs text-error">{errors.email.message}</p>}
              </div>

              <div className="space-y-1.5">
                <label htmlFor="password" className="px-1 text-sm font-medium text-on-surface-variant">
                  Contraseña
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Mínimo 8 caracteres"
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

              {/* Selector de rol */}
              <div className="space-y-2">
                <span className="px-1 text-sm font-medium text-on-surface-variant">
                  ¿Cómo usarás MarketMind?
                </span>
                <div className="grid grid-cols-2 gap-3">
                  {roles.map((r) => (
                    <button
                      key={r.val}
                      type="button"
                      onClick={() => setValue('rol', r.val)}
                      className={`rounded-xl border p-4 text-left transition-all ${
                        rolSel === r.val
                          ? 'border-primary bg-primary/5 ring-1 ring-primary'
                          : 'border-outline-variant hover:bg-surface-container-low'
                      }`}
                    >
                      <span className="block text-sm font-semibold text-on-surface">{r.label}</span>
                      <span className="mt-0.5 block text-xs text-on-surface-variant">{r.desc}</span>
                    </button>
                  ))}
                </div>
                <input type="hidden" {...register('rol', { required: true })} />
              </div>

              <Button type="submit" size="lg" disabled={loading} className="w-full text-lg">
                {loading ? 'Creando cuenta…' : 'Crear cuenta'}
              </Button>
            </form>

            <p className="text-center text-base text-on-surface-variant">
              ¿Ya tienes una cuenta?{' '}
              <Link to="/login" className="font-semibold text-primary hover:underline">
                Inicia sesión
              </Link>
            </p>
          </div>
        </div>
      </section>

      {/* Derecha: panel de marca */}
      <AuthBrandPanel
        highlights={[
          { icon: Rocket, titulo: 'Tu primera campaña en minutos', desc: 'Del brief al anuncio, guiado por IA.' },
          { icon: Users, titulo: 'Colabora con tus clientes', desc: 'Aprobaciones desde web y móvil.' },
        ]}
        badgeIcon={Sparkles}
      />
    </main>
  )
}
