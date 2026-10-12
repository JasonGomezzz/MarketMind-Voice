import { useCallback, useEffect, useRef, useState } from 'react'
import api from '../services/api'
import { getPlatformCopy } from '../services/campaignPublication'
import { canSendTikTok, shouldPollTikTok } from '../services/tiktokPublication'
import { Button } from './ui/button'

export default function TikTokUploadDialog({ campaign, onClose }) {
  const [accounts, setAccounts] = useState([])
  const [accountId, setAccountId] = useState('')
  const [configured, setConfigured] = useState(false)
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [outcome, setOutcome] = useState(null)
  const inFlight = useRef(false)
  const dialog = useRef(null)
  const mounted = useRef(true)

  useEffect(() => {
    mounted.current = true
    let active = true
    const previousFocus = document.activeElement
    dialog.current?.focus()
    api.get('/api/auth/tiktok/accounts/').then(({ data }) => {
      if (!active) return
      setConfigured(data.data.configured)
      setAccounts(data.data.accounts.filter(a => !a.expired || a.can_refresh))
    }).catch(() => { if (active) setError('No se pudieron cargar tus cuentas de TikTok.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false; mounted.current = false; previousFocus?.focus() }
  }, [])

  useEffect(() => {
    if (!accountId) return
    let active = true
    api.get(`/api/campaigns/${campaign.id}/send-tiktok/`, { params: { account_id: accountId } })
      .then(({ data }) => { if (active) setOutcome({ ...data.data, message: data.message }) })
      .catch(() => { if (active) setError('No se pudo comprobar un envío anterior. No reenvíes sin verificar.') })
      .finally(() => { if (active) setChecking(false) })
    return () => { active = false }
  }, [accountId, campaign.id])

  const state = { loading, busy, checking, error, outcome, configured }
  const allowed = canSendTikTok(campaign, accountId, state)
  const act = useCallback(async (refresh = false) => {
    if (inFlight.current || (!refresh && !allowed)) return
    inFlight.current = true
    setBusy(true)
    setError('')
    try {
      const endpoint = refresh ? 'tiktok-status' : 'send-tiktok'
      const { data } = await api.post(`/api/campaigns/${campaign.id}/${endpoint}/`, {
        account_id: Number(accountId), version: campaign.version, confirm: !refresh,
      })
      if (mounted.current) setOutcome({ ...data.data, message: data.message })
    } catch (failure) {
      if (mounted.current) setError(failure.response?.data?.message || 'Resultado no confirmado. Revisa TikTok; no reenvíes.')
    } finally { inFlight.current = false; if (mounted.current) setBusy(false) }
  }, [accountId, campaign.id, campaign.version, allowed])

  useEffect(() => {
    if (!accountId || !shouldPollTikTok(outcome?.status)) return undefined
    // Read status only; this effect never invokes the upload endpoint.
    const timer = setInterval(() => act(true), 30000)
    return () => clearInterval(timer)
  }, [accountId, outcome?.status, act])

  function onKeyDown(event) {
    if (event.key === 'Escape' && !busy) onClose()
    if (event.key !== 'Tab') return
    const controls = [...dialog.current.querySelectorAll('button:not(:disabled),select:not(:disabled),a[href]')]
    const first = controls[0], last = controls.at(-1)
    if (!first) { event.preventDefault(); return }
    if (event.shiftKey && [first, dialog.current].includes(document.activeElement)) { event.preventDefault(); last.focus() }
    else if (!event.shiftKey && [last, dialog.current].includes(document.activeElement)) { event.preventDefault(); first.focus() }
  }

  const copy = getPlatformCopy(campaign, 'tiktok')
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
    <div ref={dialog} tabIndex={-1} onKeyDown={onKeyDown} role="dialog" aria-modal="true" aria-labelledby="tiktok-upload-title"
      className="glass-liquid max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-3xl p-6">
      <h2 id="tiktok-upload-title" className="text-xl font-semibold">Enviar a TikTok</h2>
      <p className="my-3 text-sm">Enviarás la imagen y el texto aprobado. Luego debes abrir la notificación en la bandeja de TikTok, revisar las etiquetas comerciales y de IA y terminar la publicación. Enviar no significa publicar.</p>
      {campaign.imagen_b64 && <img src={`data:image/png;base64,${campaign.imagen_b64}`} alt="Imagen aprobada para TikTok" className="mx-auto max-h-72 rounded-xl object-contain" />}
      <div className="my-4 whitespace-pre-wrap rounded-xl border border-outline-variant p-4 text-sm">{copy}</div>
      <p className="text-xs">{copy.length}/4000 unidades UTF-16. Se etiqueta el contenido como generado con IA; no se recorta ni reescribe el texto automáticamente.</p>
      <label htmlFor="tiktok-upload-account" className="mt-3 block text-sm font-semibold">Cuenta de destino</label>
      <select id="tiktok-upload-account" value={accountId} disabled={busy || loading || checking}
        className="my-2 w-full rounded-xl border border-outline-variant bg-surface-container-low p-3"
        onChange={e => { setAccountId(e.target.value); setChecking(!!e.target.value); setOutcome(null); setError('') }}>
        <option value="">Selecciona una cuenta</option>
        {accounts.map(a => <option key={a.id} value={a.id}>{a.display_name}</option>)}
      </select>
      {!loading && (!configured || !accounts.length) && <p className="text-sm">Completa la conexión de TikTok en Configuración.</p>}
      {outcome && !outcome.media_ready && <p className="my-2 text-sm">Falta configurar y verificar la URL pública de imágenes en el portal de TikTok.</p>}
      {!campaign.imagen_b64 && <p role="alert">La campaña necesita una imagen.</p>}
      {copy.length > 4000 && <p role="alert">El texto supera el límite. Revisa la campaña; no se enviará recortado.</p>}
      {outcome?.status !== 'not_sent' && outcome?.message && <p role="status" className="my-3">{outcome.message}</p>}
      {shouldPollTikTok(outcome?.status) && <p className="my-2 text-xs">El estado se actualiza automáticamente cada 30 segundos mientras esta ventana está abierta. Si ya publicaste, esperamos la confirmación de TikTok; no vuelvas a enviar.</p>}
      {error && <p role="alert" className="my-3 text-error">{error}</p>}
      <div className="mt-4 flex flex-wrap justify-end gap-3">
        <Button variant="outline" disabled={busy} onClick={onClose}>Cerrar</Button>
        {outcome && ['processing', 'inbox', 'uncertain'].includes(outcome.status) && <Button variant="outline" disabled={busy} onClick={() => act(true)}>Consultar estado</Button>}
        <Button disabled={!allowed} onClick={() => act()}>{busy ? 'Procesando…' : checking ? 'Verificando…' : 'Confirmar envío a TikTok'}</Button>
      </div>
    </div>
  </div>
}
