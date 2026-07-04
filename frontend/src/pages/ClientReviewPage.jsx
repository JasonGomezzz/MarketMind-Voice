import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import AppToaster from '@/components/ui/AppToaster'
import { ArrowLeft, CircleCheck, CircleX, Download, ImageOff, AlertCircle } from 'lucide-react'
import { getCampaignById, approveCampaign, rejectCampaign } from '../services/clientCampaigns'
import { Button } from '@/components/ui/button'
import StatusBadge from '@/components/StatusBadge'
import RejectModal from '@/components/campaign/RejectModal'

/**
 * Review de campaña del rol CLIENTE (HU14/HU15). Consume Spring Boot :8080
 * (camelCase: textoGenerado, imagenB64, clienteNombre, feedbackRechazo, version).
 * El cliente revisa el copy + imagen y APRUEBA o RECHAZA (feedback obligatorio).
 * El PATCH incluye `version` (optimistic locking @Version de JPA — Spring lo exige).
 */
export default function ClientReviewPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [campaign, setCampaign] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [busy, setBusy] = useState(false)
  const [showReject, setShowReject] = useState(false)

  // Sin setState síncrono en el efecto: el estado inicial cubre el primer load.
  useEffect(() => {
    let cancelled = false
    getCampaignById(id)
      .then((c) => {
        if (!cancelled) setCampaign(c)
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
  }, [id])

  async function handleApprove() {
    setBusy(true)
    try {
      await approveCampaign(id, campaign.version)
      toast.success('Campaña aprobada')
      setTimeout(() => navigate('/dashboard'), 1000)
    } catch (err) {
      toast.error(err.response?.data?.message || 'No se pudo aprobar la campaña.')
      setBusy(false)
    }
  }

  async function handleReject(feedback) {
    setBusy(true)
    try {
      await rejectCampaign(id, feedback, campaign.version)
      setShowReject(false)
      toast.success('Campaña rechazada. El marketero recibirá tu feedback.')
      setTimeout(() => navigate('/dashboard'), 1200)
    } catch (err) {
      toast.error(err.response?.data?.message || 'No se pudo rechazar la campaña.')
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <div className="flex animate-pulse gap-6">
        <div className="h-96 flex-1 rounded-xl bg-surface-container-high" />
        <div className="hidden h-96 w-80 rounded-xl bg-surface-container-high lg:block" />
      </div>
    )
  }

  if (error || !campaign) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-error/20 bg-error-container px-4 py-3 text-sm text-on-error-container">
        <AlertCircle className="h-4 w-4" />
        No se pudo cargar la campaña. Verifica tu conexión o vuelve al inicio.
      </div>
    )
  }

  const puedeRevisar = campaign.estado === 'pendiente_aprobacion'

  return (
    <>
      <AppToaster />

      {/* Encabezado */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="min-w-0">
          <button
            onClick={() => navigate('/dashboard')}
            className="mb-2 inline-flex items-center gap-1.5 text-sm text-on-surface-variant transition-colors hover:text-primary"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver al inicio
          </button>
          <h1 className="truncate text-2xl font-bold tracking-tight text-on-surface md:text-3xl">
            {campaign.titulo}
          </h1>
        </div>
        <StatusBadge estado={campaign.estado} className="px-4 py-1.5 text-sm" />
      </div>

      {/* Aviso si ya fue revisada */}
      {!puedeRevisar && (
        <div
          className={`mb-6 rounded-xl border px-4 py-3 text-sm font-medium ${
            campaign.estado === 'aprobado'
              ? 'border-success/20 bg-success-container text-success'
              : campaign.estado === 'rechazado'
                ? 'border-error/20 bg-error-container text-on-error-container'
                : 'border-outline-variant bg-surface-container-low text-on-surface-variant'
          }`}
        >
          {campaign.estado === 'aprobado'
            ? 'Ya aprobaste esta campaña.'
            : campaign.estado === 'rechazado'
              ? 'Ya rechazaste esta campaña. El marketero está trabajando en una nueva versión.'
              : 'Esta campaña aún no está lista para revisión.'}
        </div>
      )}

      <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
        {/* ── Contenido: copy + imagen ── */}
        <div className="min-w-0 flex-1 space-y-4">
          <div className="rounded-xl border border-outline-variant bg-white p-6 shadow-sm">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-on-surface-variant">
              Copy propuesto
            </p>
            <p className="whitespace-pre-wrap text-base leading-relaxed text-on-surface">
              {campaign.textoGenerado || 'Sin copy generado.'}
            </p>
          </div>

          <div className="rounded-xl border border-outline-variant bg-white p-6 shadow-sm">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-on-surface-variant">
              Imagen del anuncio
            </p>
            {campaign.imagenB64 ? (
              <div className="space-y-3">
                <img
                  src={`data:image/png;base64,${campaign.imagenB64}`}
                  alt={`Imagen propuesta para ${campaign.titulo}`}
                  className="w-full rounded-lg"
                />
                <a
                  href={`data:image/png;base64,${campaign.imagenB64}`}
                  download={`campaign_${id}_imagen.png`}
                  className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline"
                >
                  <Download className="h-4 w-4" />
                  Descargar PNG
                </a>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 py-8 text-center text-on-surface-variant">
                <ImageOff className="h-8 w-8 text-outline" />
                <p className="text-sm">Imagen no disponible</p>
              </div>
            )}
          </div>

          {/* Feedback previo si la rechazó antes */}
          {campaign.estado === 'rechazado' && campaign.feedbackRechazo && (
            <div className="rounded-xl border border-outline-variant bg-white p-6 shadow-sm">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-error">
                Tu feedback
              </p>
              <p className="text-sm leading-relaxed text-on-surface">{campaign.feedbackRechazo}</p>
            </div>
          )}
        </div>

        {/* ── Panel lateral: metadatos + acciones ── */}
        <div className="w-full shrink-0 space-y-4 lg:sticky lg:top-6 lg:w-80">
          <div className="space-y-3 rounded-xl border border-outline-variant bg-white p-5 shadow-sm">
            <MetaRow
              label="Marketero"
              value={campaign.marketeroNombre || (campaign.marketeroId ? `#${campaign.marketeroId}` : '—')}
            />
            <MetaRow label="Industria" value={campaign.industria} capitalize />
            <MetaRow label="Tono" value={campaign.tono} capitalize />
            <MetaRow label="Plataforma" value={campaign.plataforma} capitalize />
            {campaign.fechaCreacion && (
              <MetaRow
                label="Creada"
                value={new Date(campaign.fechaCreacion).toLocaleDateString('es-PE')}
              />
            )}
          </div>

          {puedeRevisar && (
            <div className="glass-soft space-y-3 rounded-xl p-5 shadow-sm">
              <p className="text-sm font-semibold text-on-surface">¿Qué decides?</p>
              <Button
                size="lg"
                className="w-full bg-success hover:bg-success/90"
                disabled={busy}
                onClick={handleApprove}
              >
                <CircleCheck className="h-5 w-5" />
                {busy ? 'Procesando…' : 'Aprobar campaña'}
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="w-full border-error/30 text-error hover:bg-error-container/50"
                disabled={busy}
                onClick={() => setShowReject(true)}
              >
                <CircleX className="h-5 w-5" />
                Rechazar
              </Button>
              <p className="text-xs text-on-surface-variant">
                Si rechazas, deberás indicar el motivo para que el marketero pueda mejorarla.
              </p>
            </div>
          )}
        </div>
      </div>

      <RejectModal
        open={showReject}
        busy={busy}
        onCancel={() => setShowReject(false)}
        onConfirm={handleReject}
      />
    </>
  )
}

function MetaRow({ label, value, capitalize }) {
  return (
    <div className="flex items-start justify-between gap-2 text-sm">
      <span className="shrink-0 text-on-surface-variant">{label}</span>
      <span className={`text-right text-on-surface ${capitalize ? 'capitalize' : ''}`}>
        {value || '—'}
      </span>
    </div>
  )
}
