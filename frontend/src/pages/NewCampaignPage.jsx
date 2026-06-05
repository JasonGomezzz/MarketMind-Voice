import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const INDUSTRIAS = [
  { value: 'tecnologia',     label: 'Tecnología' },
  { value: 'salud',          label: 'Salud' },
  { value: 'educacion',      label: 'Educación' },
  { value: 'retail',         label: 'Retail' },
  { value: 'gastronomia',    label: 'Gastronomía' },
  { value: 'moda',           label: 'Moda' },
  { value: 'finanzas',       label: 'Finanzas' },
  { value: 'entretenimiento',label: 'Entretenimiento' },
  { value: 'otro',           label: 'Otro' },
]

const TONOS = [
  { value: 'profesional',  label: 'Profesional' },
  { value: 'casual',       label: 'Casual' },
  { value: 'urgente',      label: 'Urgente' },
  { value: 'inspiracional',label: 'Inspiracional' },
  { value: 'humoristico',  label: 'Humorístico' },
  { value: 'persuasivo',   label: 'Persuasivo' },
]

const PLATAFORMAS = [
  { value: 'instagram',  label: 'Instagram' },
  { value: 'facebook',   label: 'Facebook' },
  { value: 'twitter',    label: 'Twitter / X' },
  { value: 'linkedin',   label: 'LinkedIn' },
  { value: 'google_ads', label: 'Google Ads' },
  { value: 'tiktok',     label: 'TikTok' },
]

const ESTADO_BADGE = {
  generado: 'bg-green-100 text-green-700',
  borrador: 'bg-gray-100 text-gray-600',
}

function FieldError({ message }) {
  if (!message) return null
  return <p className="text-xs text-red-500 mt-1">{message}</p>
}

function inputCls(hasError) {
  return `w-full border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 transition ${
    hasError ? 'border-red-400' : 'border-gray-300'
  }`
}

export default function NewCampaignPage() {
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)   // { campaign, warning }
  const [serverError, setServerError] = useState('')

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm()

  async function onSubmit(formData) {
    setSubmitting(true)
    setServerError('')
    setResult(null)

    try {
      const { data } = await api.post('/api/campaigns/', formData)
      setResult({ campaign: data.data.campaign, warning: null })
    } catch (err) {
      const httpStatus = err.response?.status
      const body = err.response?.data

      if (httpStatus === 400) {
        const errMap = body?.data?.errors ?? {}
        const first = Object.values(errMap)[0]?.[0]
        setServerError(first || 'Error de validación. Revisa los campos.')
      } else if (httpStatus === 402) {
        setServerError('Sin tokens disponibles. Contacta al administrador para renovar tu plan.')
      } else if (httpStatus === 503) {
        // Campaign saved as borrador but IA failed
        setResult({ campaign: body?.data?.campaign, warning: body?.message })
      } else {
        setServerError('Error inesperado. Intenta de nuevo.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  function handleReset() {
    setResult(null)
    setServerError('')
    reset()
  }

  return (
    <div className="flex gap-6 items-start">

      {/* ── Form panel ─────────────────────────────────────── */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-semibold text-gray-900">Nueva Campaña</h2>
          <button
            type="button"
            onClick={() => navigate('/campaigns')}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            ← Volver
          </button>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          className="bg-white rounded-xl border border-gray-200 p-6 space-y-5"
        >
          {/* Título */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Título de la campaña
            </label>
            <input
              type="text"
              placeholder="Ej: Lanzamiento Black Friday 2026"
              className={inputCls(errors.titulo)}
              disabled={submitting}
              {...register('titulo', {
                required: 'El título es obligatorio.',
                minLength: { value: 5, message: 'Mínimo 5 caracteres.' },
                maxLength: { value: 200, message: 'Máximo 200 caracteres.' },
              })}
            />
            <FieldError message={errors.titulo?.message} />
          </div>

          {/* Cliente — nombre + email */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre del cliente
              </label>
              <input
                type="text"
                placeholder="Ej: Empresa S.A.C."
                className={inputCls(errors.cliente_nombre)}
                disabled={submitting}
                {...register('cliente_nombre', {
                  required: 'El nombre del cliente es obligatorio.',
                  maxLength: { value: 150, message: 'Máximo 150 caracteres.' },
                })}
              />
              <FieldError message={errors.cliente_nombre?.message} />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email del cliente
              </label>
              <input
                type="email"
                placeholder="cliente@empresa.com"
                className={inputCls(errors.cliente_email)}
                disabled={submitting}
                {...register('cliente_email', {
                  required: 'El email del cliente es obligatorio.',
                  pattern: {
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: 'Formato de email inválido.',
                  },
                })}
              />
              <FieldError message={errors.cliente_email?.message} />
            </div>
          </div>

          {/* Industria + Tono en 2 columnas */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Industria
              </label>
              <select
                className={inputCls(errors.industria)}
                disabled={submitting}
                {...register('industria', { required: 'Selecciona una industria.' })}
              >
                <option value="">Seleccionar…</option>
                {INDUSTRIAS.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
              <FieldError message={errors.industria?.message} />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tono del mensaje
              </label>
              <select
                className={inputCls(errors.tono)}
                disabled={submitting}
                {...register('tono', { required: 'Selecciona un tono.' })}
              >
                <option value="">Seleccionar…</option>
                {TONOS.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
              <FieldError message={errors.tono?.message} />
            </div>
          </div>

          {/* Plataforma */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Plataforma
            </label>
            <select
              className={inputCls(errors.plataforma)}
              disabled={submitting}
              {...register('plataforma', { required: 'Selecciona una plataforma.' })}
            >
              <option value="">Seleccionar…</option>
              {PLATAFORMAS.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
            <FieldError message={errors.plataforma?.message} />
          </div>

          {/* Prompt */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Instrucciones para la IA
            </label>
            <textarea
              rows={5}
              placeholder="Describe el objetivo de la campaña, el público objetivo, puntos clave a destacar y cualquier restricción creativa…"
              className={`${inputCls(errors.prompt)} resize-y`}
              disabled={submitting}
              {...register('prompt', {
                required: 'Las instrucciones son obligatorias.',
                minLength: { value: 10, message: 'Mínimo 10 caracteres.' },
                maxLength: { value: 2000, message: 'Máximo 2000 caracteres.' },
              })}
            />
            <FieldError message={errors.prompt?.message} />
          </div>

          {/* Server-level error */}
          {serverError && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
              {serverError}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-medium py-2.5 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <Spinner />
                Generando con IA…
              </>
            ) : (
              'Generar campaña con IA'
            )}
          </button>
        </form>
      </div>

      {/* ── Result panel ───────────────────────────────────── */}
      <div className="w-[420px] shrink-0 sticky top-6">
        {result ? (
          <ResultPanel
            result={result}
            onReset={handleReset}
            onNavigate={() => navigate('/campaigns')}
          />
        ) : (
          <EmptyResultPanel submitting={submitting} />
        )}
      </div>

    </div>
  )
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  )
}

function EmptyResultPanel({ submitting }) {
  return (
    <div className="bg-white rounded-xl border border-dashed border-gray-300 p-8 flex flex-col items-center justify-center text-center min-h-[300px]">
      {submitting ? (
        <>
          <div className="mb-4">
            <svg className="animate-spin h-10 w-10 text-indigo-500 mx-auto" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          </div>
          <p className="text-sm font-medium text-gray-700">Generando contenido con IA…</p>
          <p className="text-xs text-gray-400 mt-1">Esto puede tomar unos segundos.</p>
        </>
      ) : (
        <>
          <div className="text-4xl mb-3">✦</div>
          <p className="text-sm font-medium text-gray-500">El resultado de la IA aparecerá aquí</p>
          <p className="text-xs text-gray-400 mt-1">Completa el formulario y haz clic en Generar.</p>
        </>
      )}
    </div>
  )
}

function ResultPanel({ result, onReset, onNavigate }) {
  const { campaign, warning } = result

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-800">Resultado IA</span>
          {campaign?.estado && (
            <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${ESTADO_BADGE[campaign.estado] ?? 'bg-gray-100 text-gray-600'}`}>
              {campaign.estado === 'generado' ? 'Generado' : 'Borrador'}
            </span>
          )}
        </div>
        {warning && (
          <span className="text-xs text-amber-600 font-medium">⚠ Servicio IA no disponible</span>
        )}
      </div>

      <div className="p-5 space-y-4">
        {warning ? (
          <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
            {warning} La campaña fue guardada como borrador.
          </div>
        ) : (
          <>
            {/* Copy generado */}
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                Copy publicitario
              </p>
              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                {campaign?.texto_generado || '—'}
              </div>
            </div>

            {/* Imagen preview */}
            {campaign?.imagen_url && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                  Imagen generada
                </p>
                <img
                  src={campaign.imagen_url}
                  alt="Preview generado por IA"
                  className="w-full rounded-lg border border-gray-200 object-cover"
                  onError={(e) => { e.target.style.display = 'none' }}
                />
              </div>
            )}
          </>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-1">
          <button
            onClick={onNavigate}
            className="flex-1 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
          >
            Ver en lista
          </button>
          <button
            onClick={onReset}
            className="flex-1 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Crear otra
          </button>
        </div>
      </div>
    </div>
  )
}
