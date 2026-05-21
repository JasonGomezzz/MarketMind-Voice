import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import toast, { Toaster } from 'react-hot-toast'
import api from '../services/api'

const ESTADO_BADGE = {
  borrador: 'bg-gray-100 text-gray-600',
  pendiente_ia: 'bg-yellow-100 text-yellow-700',
  generado: 'bg-green-100 text-green-700',
  pendiente_aprobacion: 'bg-blue-100 text-blue-700',
  aprobado: 'bg-emerald-100 text-emerald-700',
  rechazado: 'bg-red-100 text-red-700',
}

const ESTADO_LABEL = {
  borrador: 'Borrador',
  pendiente_ia: 'Pendiente IA',
  generado: 'Generado',
  pendiente_aprobacion: 'Pendiente Aprobación',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
}

const READONLY_STATES = ['aprobado', 'rechazado']

function wordCount(text) {
  return text.trim() ? text.trim().split(/\s+/).length : 0
}

function first100Words(text) {
  return text.trim().split(/\s+/).slice(0, 100).join(' ')
}

export default function CampaignDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [campaign, setCampaign] = useState(null)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [saving, setSaving] = useState(false)
  const [submitting, setSubmitting] = useState(false)
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
        setText(draft !== null ? draft : (c.texto_generado || ''))
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    fetchCampaign()
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [id])

  // Autosave con debounce de 30s
  useEffect(() => {
    if (!campaign || READONLY_STATES.includes(campaign.estado)) return
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      localStorage.setItem(draftKey, text)
      setAutoSavedAt(new Date().toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' }))
    }, 30000)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [text])

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
      toast.success('Campaña enviada al cliente')
      setTimeout(() => navigate('/dashboard'), 1200)
    } catch (err) {
      toast.error(err.response?.data?.message || 'Error al enviar')
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingSkeleton />
  if (error) return <p className="text-sm text-red-500 p-4">Error al cargar la campaña.</p>

  const isReadonly = READONLY_STATES.includes(campaign.estado)
  const canSubmit = campaign.estado === 'generado'

  return (
    <>
      <Toaster position="top-right" />

      <div className="flex items-center justify-between mb-5">
        <h2 className="text-xl font-semibold text-gray-900 truncate max-w-[60%]">
          {campaign.titulo}
        </h2>
        <button
          onClick={() => navigate('/campaigns')}
          className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          ← Volver
        </button>
      </div>

      <div className="flex gap-6 items-start">

        {/* ── Columna izquierda: Metadatos ─────────────────── */}
        <div className="w-72 shrink-0 space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
            <MetaRow label="Estado">
              <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${ESTADO_BADGE[campaign.estado] ?? 'bg-gray-100 text-gray-600'}`}>
                {ESTADO_LABEL[campaign.estado] ?? campaign.estado}
              </span>
            </MetaRow>
            <MetaRow label="Cliente">{campaign.cliente_nombre}</MetaRow>
            <MetaRow label="Industria" capitalize>{campaign.industria}</MetaRow>
            <MetaRow label="Tono" capitalize>{campaign.tono}</MetaRow>
            <MetaRow label="Plataforma" capitalize>{campaign.plataforma}</MetaRow>
            <MetaRow label="Creada">
              {new Date(campaign.fecha_creacion).toLocaleDateString('es-PE')}
            </MetaRow>
            <MetaRow label="Marketero">{campaign.marketero}</MetaRow>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
              Prompt original
            </p>
            <p className="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap">
              {campaign.prompt}
            </p>
          </div>
        </div>

        {/* ── Columna derecha: Editor ──────────────────────── */}
        <div className="flex-1 min-w-0">

          {isReadonly && (
            <div className={`mb-4 px-4 py-3 rounded-lg text-sm font-medium border ${
              campaign.estado === 'aprobado'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                : 'bg-red-50 border-red-200 text-red-700'
            }`}>
              {campaign.estado === 'aprobado'
                ? 'Esta campaña fue aprobada. El texto está bloqueado.'
                : 'Esta campaña fue rechazada. El texto está bloqueado.'}
            </div>
          )}

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-gray-700">Copy publicitario</p>
              {autoSavedAt && (
                <p className="text-xs text-gray-400">
                  Guardado automáticamente a las {autoSavedAt}
                </p>
              )}
            </div>

            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              disabled={isReadonly}
              rows={18}
              className={`w-full border rounded-lg px-4 py-3 text-sm leading-relaxed resize-y outline-none focus:ring-2 focus:ring-indigo-500 transition ${
                isReadonly
                  ? 'bg-gray-50 text-gray-500 cursor-not-allowed border-gray-200'
                  : 'border-gray-300'
              }`}
            />

            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-400">{wordCount(text)} palabras</p>
              {!isReadonly && (
                <div className="flex gap-2">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-60 transition-colors"
                  >
                    {saving ? 'Guardando…' : 'Guardar cambios'}
                  </button>
                  {canSubmit && (
                    <button
                      onClick={() => setShowModal(true)}
                      disabled={submitting}
                      className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-60 transition-colors"
                    >
                      {submitting ? 'Enviando…' : 'Enviar al cliente'}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showModal && (
        <SubmitModal
          preview={first100Words(text)}
          wordTotal={wordCount(text)}
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
      <span className="text-gray-400 shrink-0">{label}</span>
      <span className={`text-gray-800 text-right ${capitalize ? 'capitalize' : ''}`}>
        {children}
      </span>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="flex gap-6 animate-pulse">
      <div className="w-72 space-y-3">
        {[...Array(7)].map((_, i) => (
          <div key={i} className="h-6 bg-gray-100 rounded" />
        ))}
      </div>
      <div className="flex-1 h-72 bg-gray-100 rounded" />
    </div>
  )
}

function SubmitModal({ preview, wordTotal, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">Enviar al cliente</h3>
        <p className="text-sm text-gray-500 mb-4">
          El cliente verá el siguiente copy para aprobación:
        </p>
        <div className="bg-gray-50 rounded-lg border border-gray-200 px-4 py-3 text-sm text-gray-700 leading-relaxed mb-5 max-h-48 overflow-y-auto whitespace-pre-wrap">
          {preview}
          {wordTotal > 100 && <span className="text-gray-400"> …</span>}
        </div>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 py-2.5 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-2.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
          >
            Confirmar envío
          </button>
        </div>
      </div>
    </div>
  )
}
