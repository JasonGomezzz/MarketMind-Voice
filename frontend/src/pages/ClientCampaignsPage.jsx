import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, AlertCircle, Inbox } from 'lucide-react'
import { getPendingCampaigns } from '../services/clientCampaigns'
import { Button } from '@/components/ui/button'
import { campaignSentAt, relativeTimeFrom } from '../utils/date'

export default function ClientCampaignsPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(0)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)
    getPendingCampaigns({ page, size: 10 })
      .then((response) => {
        if (!cancelled) setData(response)
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
  }, [page])

  const campaigns = data?.content ?? []
  const totalPages = data?.totalPages ?? 1

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-on-surface">Campañas pendientes</h1>
          <p className="mt-2 text-base text-on-surface-variant">
            Todas las solicitudes que esperan tu revisión.
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate('/dashboard')}>
          <ArrowLeft className="h-4 w-4" />
          Dashboard
        </Button>
      </header>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-error/20 bg-error-container px-4 py-3 text-sm text-on-error-container">
          <AlertCircle className="h-4 w-4" />
          No se pudieron cargar las campañas pendientes.
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[0, 1, 2, 3].map((item) => (
            <div key={item} className="h-24 animate-pulse rounded-xl border border-outline-variant bg-white/70" />
          ))}
        </div>
      ) : campaigns.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-outline-variant bg-white/50 p-12 text-center">
          <Inbox className="h-10 w-10 text-outline" />
          <h2 className="text-lg font-semibold text-on-surface">Todo al día</h2>
          <p className="max-w-sm text-sm text-on-surface-variant">
            No hay campañas pendientes por revisar.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {campaigns.map((campaign) => (
            <article
              key={campaign.id}
              className="glass-soft flex flex-col gap-4 rounded-xl p-4 shadow-sm md:flex-row md:items-center"
            >
              <div className="h-20 w-full shrink-0 overflow-hidden rounded-lg bg-surface-container-high md:w-24">
                {campaign.imagenB64 ? (
                  <img
                    src={`data:image/png;base64,${campaign.imagenB64}`}
                    alt=""
                    className="h-full w-full object-cover"
                  />
                ) : null}
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="truncate font-semibold text-on-surface">{campaign.titulo}</h2>
                <p className="truncate text-sm text-on-surface-variant">
                  {campaign.clienteNombre || 'Cliente'} · {campaign.plataforma || '—'} · {campaign.industria || '—'}
                </p>
                <p className="mt-1 text-xs font-medium text-primary">
                  Enviada {relativeTimeFrom(campaignSentAt(campaign))}
                </p>
              </div>
              <Button onClick={() => navigate(`/review/${campaign.id}`)}>
                Revisar
                <ArrowRight className="h-4 w-4" />
              </Button>
            </article>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2">
          <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
            Anterior
          </Button>
          <span className="text-sm text-on-surface-variant">
            Página {page + 1} de {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page + 1 >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Siguiente
          </Button>
        </div>
      )}
    </div>
  )
}
