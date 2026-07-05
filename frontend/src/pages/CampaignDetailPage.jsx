import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import AppToaster from '@/components/ui/AppToaster'
import { ArrowLeft, FileText, ImageOff, RefreshCw, Send } from 'lucide-react'
import ImageLightbox from '@/components/ui/ImageLightbox'
import api from '../services/api'
import VersionHistoryPanel from '../components/VersionHistoryPanel'
import { Button } from '@/components/ui/button'
import StatusBadge from '@/components/StatusBadge'
import CampaignStepper from '@/components/CampaignStepper'

const READONLY_STATES = ['aprobado', 'rechazado']

function wordCount(text) {
  return text.trim() ? text.trim().split(/\s+/).length : 0
}

/**
 * Detalle de campaña (Lumina Creative). Marketero edita copy, envía a aprobación,
 * exporta PDF. LÓGICA INTACTA: fetch, autosave debounce 30s, guardar, submit+modal,
 * export PDF (blob + 402), imagen b64 + descarga, estados readonly, historial.
 * Agrega: stepper FSM del estado.
 */
export default function CampaignDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [campaign, setCampaign] = useState(null)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [saving, setSaving] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [autoSavedAt, setAutoSavedAt] = useState(null)
  const [showModal, setShowModal] = useState(false)

  const debounceRef = useRef(null)
  const draftKey = `campaign_${id}_draft`

  useEffect(() => {
    async function fetchCampaign() {
      try {
        const { data } = await api.get(`/api/campaigns/${id}/`)
        const c = data.data.campaign
        setCampaign(c)
        const draft = localStorage.getItem(draftKey)
        setText(draft !== null ? draft : c.texto_generado || '')
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    fetchCampaign()
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [id, draftKey])

  // Autosave con debounce de 30s
  useEffect(() => {
    if (!campaign || READONLY_STATES.includes(campaign.estado)) return
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      localStorage.setItem(draftKey, text)
      setAutoSavedAt(new Date().toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' }))
    }, 30000)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [text, campaign, draftKey])

  async function handleSave() {
    setSaving(true)
    try {
      const { data } = await api.patch(`/api/campaigns/${id}/`, { texto_generado: text })
      setCampaign(data.data.campaign)
      localStorage.removeItem(draftKey)
      setAutoSavedAt(null)
      toast.success('Cambios guardados')
    } catch (err) {
      toast.error(err.response?.data?.message || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  async function handleSubmitConfirm() {
    setSubmitting(true)
    setShowModal(false)
    try {
      await api.post(`/api/campaigns/${id}/submit/`)
      localStorage.removeItem(draftKey)
      toast.success('Enviada a aprobación del cliente')
      setTimeout(() => navigate('/dashboard'), 1200)
    } catch (err) {
      if (err.response?.status === 402) {
        toast.error('Cuota agotada. Pide un reset al administrador.')
      } else {
        toast.error(err.response?.data?.message || 'Error al enviar')
      }
      setSubmitting(false)
    }
  }

  async function handleRegenerate() {
    setRegenerating(true)
    try {
      const { data } = await api.post(`/api/campaigns/${id}/regenerate/`)
      const c = data.data.campaign
      setCampaign(c)
      setText(c.texto_generado || '')
      localStorage.removeItem(draftKey)
      window.dispatchEvent(new Event('credits-updated'))
      toast.success(data.message || 'Regeneración iniciada')
    } catch (err) {
      if (err.response?.status === 402) {
        toast.error('Cuota agotada. Pide un reset al administrador.')
      } else {
        toast.error(err.response?.data?.message || 'No se pudo regenerar')
      }
    } finally {
      setRegenerating(false)
    }
  }

  async function handleExportPDF() {
    try {
      const response = await api.get(`/api/campaigns/${id}/export-pdf/`, {
        responseType: 'blob',
      })
      const blobUrl = window.URL.createObjectURL(
        new Blob([response.data], { type: 'application/pdf' }),
      )
      const anchor = document.createElement('a')
      anchor.href = blobUrl
      anchor.download = `campana_${campaign.titulo}.pdf`
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      window.URL.revokeObjectURL(blobUrl)
    } catch (err) {
      let msg = 'Error al generar el PDF.'
      if (err.response?.data instanceof Blob) {
        try {
          const parsed = JSON.parse(await err.response.data.text())
          msg = parsed.message || msg
        } catch {
          /* usar mensaje genérico */
        }
      }
      toast.error(msg)
    }
  }

  if (loading) return <LoadingSkeleton />
  if (error)
    return (
      <p className="rounded-xl border border-error/20 bg-error-container p-4 text-sm text-on-error-container">
        Error al cargar la campaña.
      </p>
    )

  const isReadonly = READONLY_STATES.includes(campaign.estado)
  const canSubmit = campaign.estado === 'generado'
  // HU regenerar: borrador (fallo previo) o rechazado (vuelve a borrador en backend)
  const canRegenerate = ['borrador', 'rechazado'].includes(campaign.estado)

  return (
    <>
      <AppToaster />

      {/* Encabezado */}
      <div className="mb-6 flex items-center justify-between gap-4">
        <div className="min-w-0">
          <button
            onClick={() => navigate('/campaigns')}
            className="mb-2 inline-flex items-center gap-1.5 text-sm text-on-surface-variant transition-colors hover:text-primary"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver a campañas
          </button>
          <h1 className="truncate text-3xl font-bold tracking-tight text-on-surface">
            {campaign.titulo}
          </h1>
        </div>
        <StatusBadge estado={campaign.estado} className="px-4 py-1.5 text-sm" />
      </div>

      {/* Stepper FSM del estado */}
      <div className="mb-6 rounded-xl border border-outline-variant bg-white p-6 shadow-sm">
        <CampaignStepper estado={campaign.estado} />
      </div>

      <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
        {/* ── Columna izquierda: Metadatos ── */}
        <div className="w-full shrink-0 space-y-4 lg:w-72">
          <div className="space-y-3 rounded-xl border border-outline-variant bg-white p-5 shadow-sm">
            <MetaRow label="Cliente">{campaign.cliente_nombre}</MetaRow>
            <MetaRow label="Industria" capitalize>{campaign.industria}</MetaRow>
            <MetaRow label="Tono" capitalize>{campaign.tono}</MetaRow>
            <MetaRow label="Plataforma" capitalize>{campaign.plataforma}</MetaRow>
            <MetaRow label="Creada">
              {new Date(campaign.fecha_creacion).toLocaleDateString('es-PE')}
            </MetaRow>
            <MetaRow label="Marketero">
              {campaign?.marketero ? String(campaign.marketero).split(' <')[0] : '—'}
            </MetaRow>
          </div>

          <div className="rounded-xl border border-outline-variant bg-white p-5 shadow-sm">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-on-surface-variant">
              Prompt original
            </p>
            <p className="whitespace-pre-wrap text-xs leading-relaxed text-on-surface-variant">
              {campaign.prompt}
            </p>
          </div>

          <VersionHistoryPanel
            campaignId={id}
            canRestore={['borrador', 'generado'].includes(campaign.estado)}
            onRestored={(c) => {
              setCampaign(c)
              setText(c.texto_generado || '')
              localStorage.removeItem(draftKey)
            }}
          />
        </div>

        {/* ── Columna derecha: Editor + Imagen ── */}
        <div className="min-w-0 flex-1">
          {isReadonly && (
            <div
              className={`mb-4 rounded-xl border px-4 py-3 text-sm font-medium ${
                campaign.estado === 'aprobado'
                  ? 'border-success/20 bg-success-container text-success'
                  : 'border-error/20 bg-error-container text-on-error-container'
              }`}
            >
              {campaign.estado === 'aprobado'
                ? 'Esta campaña fue aprobada. El texto está bloqueado.'
                : 'Esta campaña fue rechazada. Revisa el feedback del cliente y regenérala con IA.'}
            </div>
          )}

          {/* Feedback de rechazo, si existe (HU15) */}
          {campaign.estado === 'rechazado' && campaign.feedback_rechazo && (
            <div className="mb-4 rounded-xl border border-outline-variant bg-white p-5 shadow-sm">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-error">
                Feedback del cliente
              </p>
              <p className="text-sm leading-relaxed text-on-surface">{campaign.feedback_rechazo}</p>
            </div>
          )}

          <div className="rounded-xl border border-outline-variant bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-semibold text-on-surface">Copy publicitario</p>
              {autoSavedAt && (
                <p className="text-xs text-on-surface-variant">
                  Guardado automáticamente a las {autoSavedAt}
                </p>
              )}
            </div>

            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={isReadonly}
              rows={16}
              className={`w-full resize-y rounded-lg border px-4 py-3 text-sm leading-relaxed outline-none transition focus:border-transparent focus:ring-2 focus:ring-primary ${
                isReadonly
                  ? 'cursor-not-allowed border-outline-variant bg-surface-container-low text-on-surface-variant'
                  : 'border-outline-variant'
              }`}
            />

            <div className="mt-3 flex items-center justify-between">
              <p className="text-xs text-on-surface-variant">{wordCount(text)} palabras</p>
              <div className="flex gap-2">
                {!isReadonly && (
                  <>
                    <Button variant="outline" size="sm" onClick={handleSave} disabled={saving}>
                      {saving ? 'Guardando…' : 'Guardar cambios'}
                    </Button>
                    {canSubmit && (
                      <Button size="sm" onClick={() => setShowModal(true)} disabled={submitting}>
                        <Send className="h-4 w-4" />
                        {submitting ? 'Enviando…' : 'Enviar al cliente'}
                      </Button>
                    )}
                  </>
                )}
                {canRegenerate && (
                  <Button size="sm" onClick={handleRegenerate} disabled={regenerating}>
                    <RefreshCw className={`h-4 w-4 ${regenerating ? 'animate-spin' : ''}`} />
                    {regenerating ? 'Regenerando…' : 'Regenerar con IA'}
                  </Button>
                )}
                {campaign.estado === 'aprobado' && (
                  <Button size="sm" onClick={handleExportPDF}>
                    <FileText className="h-4 w-4" />
                    Exportar PDF
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Imagen generada — HU22 */}
          <div className="mt-4 rounded-xl border border-outline-variant bg-white p-5 shadow-sm">
            <p className="mb-3 text-sm font-semibold text-on-surface">Imagen generada</p>
            {campaign.imagen_b64 ? (
              <ImageLightbox
                src={`data:image/png;base64,${campaign.imagen_b64}`}
                alt="Imagen generada por IA"
                downloadName={`campaign_${id}_imagen.png`}
              />
            ) : (
              <div className="flex flex-col items-center gap-2 py-8 text-center text-on-surface-variant">
                <ImageOff className="h-8 w-8 text-outline" />
                <p className="text-sm">Imagen no generada aún</p>
                {campaign.estado === 'generado' && (
                  <p className="glass-soft mt-2 max-w-sm rounded-lg px-3 py-2 text-xs">
                    <span className="font-semibold text-primary">Activo provisional: </span>
                    el copy está listo, pero falta el activo visual. Regenerar (1 crédito)
                    vuelve a intentar copy e imagen.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {showModal && (
        <SubmitModal
          preview={text}
          onConfirm={handleSubmitConfirm}
          onCancel={() => setShowModal(false)}
        />
      )}
    </>
  )
}

function MetaRow({ label, children, capitalize }) {
  return (
    <div className="flex items-start justify-between gap-2 text-sm">
      <span className="shrink-0 text-on-surface-variant">{label}</span>
      <span className={`text-right text-on-surface ${capitalize ? 'capitalize' : ''}`}>
        {children}
      </span>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="flex animate-pulse gap-6">
      <div className="w-72 space-y-3">
        {[...Array(7)].map((_, i) => (
          <div key={i} className="h-6 rounded bg-surface-container-high" />
        ))}
      </div>
      <div className="h-72 flex-1 rounded bg-surface-container-high" />
    </div>
  )
}

function SubmitModal({ preview, onConfirm, onCancel }) {
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onCancel])

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="submit-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-on-surface/40 p-4 backdrop-blur-sm"
    >
      <div className="glass-liquid w-full max-w-lg rounded-3xl p-8">
        <h3 id="submit-title" className="mb-1 text-lg font-semibold text-on-surface">Enviar al cliente</h3>
        <p className="mb-4 text-sm text-on-surface-variant">
          El cliente verá el siguiente copy para aprobación:
        </p>
        <div className="mb-5 max-h-72 overflow-y-auto whitespace-pre-wrap rounded-lg border border-outline-variant bg-surface-container-low px-4 py-3 text-sm leading-relaxed text-on-surface">
          {preview}
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="flex-1" onClick={onCancel}>
            Cancelar
          </Button>
          <Button className="flex-1" onClick={onConfirm}>
            Confirmar envío
          </Button>
        </div>
      </div>
    </div>
  )
}
