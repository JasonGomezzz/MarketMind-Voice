import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Coins, Megaphone, TrendingUp, ShieldQuestion, AlertCircle } from 'lucide-react'
import api from '../services/api'
import StatusBadge from '@/components/StatusBadge'
import PlanesModal from '@/components/campaign/PlanesModal'

/**
 * Detalle de créditos de IA (solo marketero/superadmin — ruta /credits).
 * Consume GET /api/campaigns/credits-detail/: saldo real, métricas del mes
 * en curso y el historial de consumo POR CAMPAÑA (no hay tabla de
 * "transacciones" ni facturación en el backend — no se inventan datos que
 * el producto no tiene, ver CLAUDE.md).
 * Estética: tarjetas/tabla sólidas de alto contraste (glass solo en el
 * modal de planes, que ya trae su propia receta liquid-glass).
 */
const QUOTA_DEFAULT = 100 // tokens_disponibles default del modelo User

export default function CreditsDetailPage() {
  const location = useLocation()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const [showPlanes, setShowPlanes] = useState(false)

  useEffect(() => {
    let cancelled = false
    api
      .get('/api/campaigns/credits-detail/')
      .then(({ data: res }) => {
        if (!cancelled) setData(res.data)
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
  }, [retryCount, location.key])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-64 animate-pulse rounded bg-surface-container-high" />
        <div className="h-40 animate-pulse rounded-xl border border-outline-variant bg-white" />
        <div className="h-64 animate-pulse rounded-xl border border-outline-variant bg-white" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-error/20 bg-error-container px-4 py-3 text-sm text-on-error-container">
        <AlertCircle className="h-4 w-4" />
        No se pudo cargar el detalle de créditos.
        <button
          className="font-semibold underline"
          onClick={() => {
            setLoading(true)
            setError(false)
            setRetryCount((c) => c + 1)
          }}
        >
          Reintentar
        </button>
      </div>
    )
  }

  const pct = Math.min(100, Math.round((data.tokens_disponibles / QUOTA_DEFAULT) * 100))

  return (
    <div className="space-y-6">
      <PlanesModal open={showPlanes} onClose={() => setShowPlanes(false)} />

      <header>
        <h1 className="text-4xl font-bold tracking-tight text-on-surface">Créditos de IA</h1>
        <p className="mt-2 text-base text-on-surface-variant">
          Consulta tu saldo y el historial de consumo de tu cuenta.
        </p>
      </header>

      {/* Tarjeta hero de saldo — sólida, alto contraste */}
      <section className="rounded-xl border border-outline-variant bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary">
              <Coins className="h-4 w-4" />
              Saldo disponible
            </p>
            <p className="text-5xl font-extrabold tabular-nums text-on-surface">
              {data.tokens_disponibles}{' '}
              <span className="text-lg font-medium text-on-surface-variant">créditos</span>
            </p>
          </div>
          <button
            onClick={() => setShowPlanes(true)}
            className="inline-flex h-11 shrink-0 items-center justify-center rounded-lg bg-primary px-6 text-base font-semibold text-on-primary shadow-lg transition-all hover:bg-primary-container active:scale-95"
          >
            Solicitar más créditos
          </button>
        </div>

        <div className="mt-6">
          <div
            role="progressbar"
            aria-valuenow={data.tokens_disponibles}
            aria-valuemin={0}
            aria-valuemax={QUOTA_DEFAULT}
            aria-label="Créditos disponibles sobre el total del plan"
            className="h-2.5 w-full overflow-hidden rounded-full bg-surface-container-high"
          >
            <div
              className={`h-full rounded-full transition-all ${data.tokens_disponibles === 0 ? 'bg-error' : 'bg-primary'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-on-surface-variant">
            Cada crédito equivale a 1 generación o regeneración de IA exitosa.
          </p>
        </div>
      </section>

      {/* Métricas derivadas del mes en curso — todas calculadas del historial real */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <MetricCard
          icon={Coins}
          tint="bg-primary/10 text-primary"
          label="Créditos consumidos este mes"
          value={data.consumidos_mes}
        />
        <MetricCard
          icon={Megaphone}
          tint="bg-secondary-container text-primary"
          label="Campañas generadas este mes"
          value={data.campanas_mes}
        />
        <MetricCard
          icon={TrendingUp}
          tint="bg-tertiary-container text-tertiary"
          label="Promedio de créditos por campaña"
          value={data.promedio_por_campana_mes}
        />
      </section>

      {/* Historial de consumo — por campaña, el evento de consumo real del producto */}
      <section className="overflow-hidden rounded-xl border border-outline-variant bg-white shadow-sm">
        <div className="border-b border-outline-variant px-6 py-4">
          <h2 className="text-lg font-semibold text-on-surface">Historial de consumo</h2>
        </div>

        {data.historial.length === 0 ? (
          <p className="px-6 py-10 text-center text-sm text-on-surface-variant">
            Aún no has generado campañas. Tu historial de consumo aparecerá aquí.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-outline-variant text-xs uppercase tracking-wide text-on-surface-variant">
                  <th className="px-6 py-3 font-semibold">Campaña</th>
                  <th className="px-6 py-3 font-semibold">Fecha</th>
                  <th className="px-6 py-3 font-semibold">Créditos</th>
                  <th className="px-6 py-3 font-semibold">Estado</th>
                </tr>
              </thead>
              <tbody>
                {data.historial.map((c) => (
                  <tr key={c.id} className="border-b border-outline-variant/60 last:border-0">
                    <td className="max-w-xs truncate px-6 py-3 font-medium text-on-surface">
                      {c.titulo}
                    </td>
                    <td className="px-6 py-3 text-on-surface-variant">
                      {new Date(c.fecha_creacion).toLocaleDateString('es-PE', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="px-6 py-3 tabular-nums text-on-surface">
                      {c.tokens_consumidos}
                    </td>
                    <td className="px-6 py-3">
                      <StatusBadge estado={c.estado} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="flex items-center gap-2 text-sm text-on-surface-variant">
        <ShieldQuestion className="h-4 w-4 text-primary" />
        ¿Necesitas más créditos? Un SuperAdmin puede resetear tu cuota o cambiar tu plan desde el
        panel de Usuarios.
      </p>
    </div>
  )
}

function MetricCard({ icon: Icon, tint, label, value }) {
  return (
    <div className="rounded-xl border border-outline-variant bg-white p-6 shadow-sm">
      <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-lg ${tint}`}>
        <Icon className="h-6 w-6" />
      </div>
      <p className="text-sm text-on-surface-variant">{label}</p>
      <h3 className="mt-1 text-3xl font-bold tabular-nums text-on-surface">{value ?? '—'}</h3>
    </div>
  )
}
