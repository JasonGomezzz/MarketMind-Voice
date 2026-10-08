import { useEffect, useRef, useState } from 'react'
import api from '../services/api'
import { canConfirmXPublication } from '../services/xPublication'
import { Button } from '@/components/ui/button'

export default function XPublicationDialog({ campaign, onClose }) {
  const [accounts, setAccounts] = useState([])
  const [accountId, setAccountId] = useState('')
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(true)
  const [busy, setBusy] = useState(false)
  const [outcome, setOutcome] = useState(null)
  const [error, setError] = useState('')
  const inFlight = useRef(false)
  const mounted = useRef(true)
  const dialog = useRef(null)

  useEffect(() => {
    mounted.current = true
    let active = true
    api.get('/api/auth/x/accounts/').then(({ data }) => {
      if (!active) return
      const available = data.data.accounts.filter(account => !account.expired || account.can_refresh)
      setAccounts(available)
      if (available.length === 1) {
        setChecking(true)
        setAccountId(String(available[0].id))
      }
      if (!data.data.configured) setError('Falta configurar X en el servidor.')
    }).catch(() => { if (active) setError('No se pudieron cargar tus cuentas de X.') })
      .finally(() => { if (active) setLoading(false) })
    const previousFocus = document.activeElement
    dialog.current?.focus()
    return () => { active = false; mounted.current = false; previousFocus?.focus() }
  }, [])

  useEffect(() => {
    let active = true
    api.get(`/api/campaigns/${campaign.id}/publish-x/`, { params: accountId ? { account_id: accountId } : {} })
      .then(({ data }) => { if (active) setOutcome({ ...data.data, accountId, message: data.message }) })
      .catch(() => { if (active) setError('No se pudo comprobar el estado de publicación en X.') })
      .finally(() => { if (active) setChecking(false) })
    return () => { active = false }
  }, [accountId, campaign.id])

  function handleKeyDown(event) {
    if (event.key === 'Escape' && !busy) onClose()
    if (event.key !== 'Tab') return
    const controls = [...dialog.current.querySelectorAll('button:not(:disabled), select:not(:disabled), a[href]')]
    if (!controls.length) { event.preventDefault(); return }
    const first = controls[0], last = controls.at(-1)
    if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.current)) {
      event.preventDefault(); last.focus()
    } else if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialog.current)) {
      event.preventDefault(); first.focus()
    }
  }

  async function publish() {
    if (inFlight.current || !canConfirmXPublication(campaign, accountId, { loading, checking, busy, error, outcome })) return
    inFlight.current = true
    setBusy(true)
    try {
      const { data } = await api.post(`/api/campaigns/${campaign.id}/publish-x/`, {
        account_id: Number(accountId), version: campaign.version, confirm: true,
      })
      if (mounted.current) setOutcome({ ...data.data, accountId, message: data.message })
    } catch (failure) {
      if (mounted.current) setError(failure.response?.data?.message || 'No se confirmó el resultado. Revisa X antes de volver a intentarlo.')
    } finally {
      inFlight.current = false
      if (mounted.current) setBusy(false)
    }
  }

  const selected = accounts.find(account => String(account.id) === accountId)
  const validation = outcome?.text_validation
  const allowed = canConfirmXPublication(campaign, accountId, { loading, checking, busy, error, outcome })
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
    <div ref={dialog} tabIndex={-1} onKeyDown={handleKeyDown} role="dialog" aria-modal="true"
      aria-labelledby="x-publication-title" className="glass-liquid max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-3xl p-6">
      <h2 id="x-publication-title" className="text-xl font-semibold">Publicar en Twitter / X</h2>
      <p className="my-3 text-sm">Revisa la imagen y el texto aprobado. Al confirmar, se publicarán en la cuenta que elijas.</p>
      {campaign.imagen_b64 ? <img src={`data:image/png;base64,${campaign.imagen_b64}`} alt="Imagen aprobada para X"
        className="mx-auto max-h-72 rounded-xl object-contain" /> : <p role="alert">Esta campaña no tiene imagen para publicar.</p>}
      <div className="my-4 whitespace-pre-wrap break-words rounded-xl border border-outline-variant p-4 text-sm">{campaign.texto_generado}</div>
      {validation && <p className={`mb-3 text-sm ${validation.valid ? 'text-on-surface-variant' : 'text-error'}`}>
        {validation.weighted_length} / {validation.limit} caracteres según las reglas de X.
      </p>}
      {validation && !validation.valid && <p role="alert" className="mb-3 text-sm text-error">
        El texto aprobado no cumple el límite de X. Necesitas una campaña con texto válido aprobado; no se recortará automáticamente.
      </p>}
      <label htmlFor="x-destination" className="text-sm font-semibold">Cuenta de destino</label>
      <select id="x-destination" value={accountId} disabled={loading || busy || checking}
        onChange={event => {
          setChecking(true)
          setOutcome(null)
          setError('')
          setAccountId(event.target.value)
        }} className="my-2 w-full rounded-xl border border-outline-variant bg-surface-container-low p-3">
        <option value="">{loading ? 'Cargando…' : 'Selecciona una cuenta'}</option>
        {accounts.map(account => <option key={account.id} value={account.id}>@{account.username}</option>)}
      </select>
      {!loading && !accounts.length && <p className="my-2 text-sm">Conecta tu cuenta de X en <a href="/settings" className="text-primary underline">Configuración</a> antes de publicar.</p>}
      <p className="my-2 text-xs text-on-surface-variant">X requiere créditos disponibles en la cuenta de desarrollador para usar su API.</p>
      {error && <p role="alert" className="my-3 text-error">{error}</p>}
      {outcome && outcome.status !== 'not_published' && <p role="status" className={`my-3 text-sm ${outcome.status === 'failed' ? 'text-error' : ''}`}>{outcome.message}</p>}
      {outcome?.status === 'published' && outcome.publication_url && <a href={outcome.publication_url}
        target="_blank" rel="noopener noreferrer" className="text-sm text-primary underline">Ver publicación en X</a>}
      <div className="mt-4 flex flex-wrap justify-end gap-3">
        <Button variant="outline" disabled={busy} onClick={onClose}>Cerrar</Button>
        <Button disabled={!allowed} onClick={publish}>{checking ? 'Verificando…' : busy ? 'Publicando…'
          : outcome?.status === 'published' ? 'Ya publicada' : `${outcome?.status === 'failed' ? 'Volver a confirmar' : 'Publicar'}${selected ? ` en @${selected.username}` : ''}`}</Button>
      </div>
    </div>
  </div>
}
