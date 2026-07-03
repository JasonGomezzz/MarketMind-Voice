import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { ClipboardCheck, CircleCheck, CircleX, AlertCircle, ArrowRight, Inbox } from 'lucide-react'
import { getPendingCampaigns } from '../services/clientCampaigns'
import { Button } from '@/components/ui/button'

/**
 * Dashboard del rol CLIENTE. Consume Spring Boot :8080 (arquitectura políglota).
 * Muestra: Por revisar / Aprobadas / Rechazadas + lista de campañas pendientes.
 * El cliente revisa/aprueba, NO crea campañas.
 */
export default function ClientDashboardPage() {
  const nombre = localStorage.getItem('user_nombre') || 'usuario'
  const navigate = useNavigate()
  const location = useLocation()

  const [pending, setPending] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)

    getPendingCampaigns()
      .then((data) => {
        if (!cancelled) setPending(data?.content ?? [])
      })
      .catch(() => {
        if (!cancelled) setError(true)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [retry, location.key])

  const porRevisar = pending.length

  const stats = [
    {
      key: 'revisar',
      label: 'Por revisar',
      value: porRevisar,
      icon: ClipboardCheck,
      highlight: true,
    },
    { key: 'aprobadas', label: 'Aprobadas', value: null, icon: CircleCheck, tint: 'bg-success-container text-success' },
    { key: 'rechazadas', label: 'Rechazadas', value: null, icon: CircleX, tint: 'bg-error-container text-error' },
  ]

  return (
    <div className="space-y-8">
      {/* Encabezado */}
      <header>
        <h1 className="text-4xl font-bold tracking-tight text-on-surface">
          Hola, {nombre.split(' ')[0]}
        </h1>
        <p className="mt-2 text-base text-on-surface-variant">
          {loading
            ? 'Cargando tus campañas…'
            : porRevisar > 0
              ? `Tienes ${porRevisar} ${porRevisar === 1 ? 'campaña' : 'campañas'} esperando tu revisión.`
              : 'No tienes campañas pendientes por ahora.'}
        </p>
      </header>

      {/* Stat cards */}
      <section className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {stats.map(({ key, label, value, icon: Icon, highlight, tint }) =>
          highlight ? (
            <div
              key={key}
              className="flex h-40 flex-col justify-between rounded-xl border border-primary/20 bg-primary-container p-6 text-on-primary-container shadow-lg transition-transform hover:-translate-y-1"
            >
              <div className="flex items-start justify-between">
                <span className="text-xs font-bold uppercase tracking-widest opacity-80">{label}</span>
                <span className="rounded-lg bg-white/20 p-2">
                  <Icon className="h-5 w-5" />
                </span>
              </div>
              <div className="text-5xl font-extrabold tabular-nums">
                {loading ? (
                  <span className="inline-block h-10 w-16 animate-pulse rounded bg-white/20" />
                ) : (
                  String(value).padStart(2, '0')
                )}
              </div>
            </div>
          ) : (
            <div
              key={key}
              className="flex h-40 flex-col justify-between rounded-xl border border-outline-variant bg-white p-6 shadow-sm transition-shadow hover:shadow-lg"
            >
              <div className="flex items-start justify-between">
                <span className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                  {label}
                </span>
                <span className={`rounded-lg p-2 ${tint}`}>
                  <Icon className="h-5 w-5" />
                </span>
              </div>
              <div className="text-5xl font-extrabold tabular-nums text-on-surface">
                {value ?? '—'}
              </div>
            </div>
          ),
        )}
      </section>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-error/20 bg-error-container px-4 py-3 text-sm text-on-error-container">
          <AlertCircle className="h-4 w-4" />
          No se pudieron cargar las campañas.
          <button className="font-semibold underline" onClick={() => setRetry((c) => c + 1)}>
            Reintentar
          </button>
        </div>
      )}

      {/* Lista de campañas pendientes */}
      <section>
        <h2 className="mb-4 text-xl font-semibold text-on-surface">Campañas pendientes</h2>

        {loading ? (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-24 animate-pulse rounded-xl border border-outline-variant bg-white" />
            ))}
          </div>
        ) : !error && pending.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-outline-variant bg-white/50 p-12 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-surface-container-high text-outline">
              <Inbox className="h-7 w-7" />
            </div>
            <h3 className="text-lg font-semibold text-on-surface">Todo al día</h3>
            <p className="max-w-sm text-sm text-on-surface-variant">
              No tienes campañas esperando revisión. Cuando un marketero envíe una, aparecerá aquí.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {pending.map((c) => (
              <article
                key={c.id}
                className="flex items-center gap-4 rounded-xl border border-outline-variant bg-white p-4 shadow-sm transition-shadow hover:shadow-lg"
              >
                <div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg bg-surface-container-high">
                  {c.imagenB64 ? (
                    <img
                      src={`data:image/png;base64,${c.imagenB64}`}
                      alt=""
                      className="h-full w-full object-cover"
                    />
                  ) : null}
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="truncate font-semibold text-on-surface">{c.titulo}</h3>
                  <p className="truncate text-sm text-on-surface-variant">
                    {c.clienteNombre || 'Cliente'} · {c.plataforma || '—'}
                  </p>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Button variant="outline" size="sm" onClick={() => navigate(`/review/${c.id}`)}>
                    Detalles
                  </Button>
                  <Button size="sm" onClick={() => navigate(`/review/${c.id}`)}>
                    Revisar ahora
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
