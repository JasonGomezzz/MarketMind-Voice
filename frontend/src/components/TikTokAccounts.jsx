import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import { rememberTikTokAuthorization, takeTikTokAuthorization } from '../services/tiktokAuthorization'
import { Button } from './ui/button'
import PlatformIcon from './campaign/PlatformIcon'

export default function TikTokAccounts() {
  const [accounts, setAccounts] = useState([])
  const [configured, setConfigured] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const completion = useRef(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const values = new URLSearchParams(window.location.hash.slice(1))
        if (values.get('provider') === 'tiktok' && (values.has('code') || values.has('error')) && !completion.current) {
          const hash = window.location.hash
          window.history.replaceState(null, '', window.location.pathname)
          const { code, state, denied } = takeTikTokAuthorization(hash)
          completion.current = denied
            ? Promise.resolve().then(() => toast.error('No autorizaste la conexión con TikTok.'))
            : api.post('/api/auth/tiktok/complete/', { code, state }).then(() => toast.success('TikTok conectado'))
        }
        if (completion.current) await completion.current
      } catch (err) {
        if (!cancelled) setError(err.response?.data?.message || err.message || 'No se pudo completar TikTok.')
      }
      try {
        const { data } = await api.get('/api/auth/tiktok/accounts/')
        if (!cancelled) {
          setAccounts(data.data.accounts)
          setConfigured(data.data.configured)
        }
      } catch {
        if (!cancelled) setError('No se pudieron cargar las conexiones de TikTok. Recarga la página.')
      } finally { if (!cancelled) setLoading(false) }
    }
    void load()
    return () => { cancelled = true }
  }, [])

  async function connect() {
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post('/api/auth/tiktok/connect/')
      window.location.assign(rememberTikTokAuthorization(data.data.authorization_url))
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'No se pudo iniciar TikTok.')
      setBusy(false)
    }
  }

  async function disconnect(account) {
    if (!window.confirm(`¿Desconectar ${account.display_name} de NexoMark? No elimina publicaciones en TikTok.`)) return
    setBusy(true)
    try {
      await api.delete(`/api/auth/tiktok/accounts/${account.id}/`)
      setAccounts(current => current.filter(item => item.id !== account.id))
      toast.success('Conexión local eliminada')
    } catch { toast.error('No se pudo desconectar TikTok.') }
    finally { setBusy(false) }
  }

  return <section className="rounded-xl border border-outline-variant bg-white p-6 shadow-sm">
    <h2 className="flex items-center gap-2 text-xl font-semibold text-on-surface"><PlatformIcon platform="tiktok" className="h-5 w-5" />Redes sociales · TikTok</h2>
    <p className="mt-2 text-sm text-on-surface-variant">Conecta una cuenta que tengas autorización para administrar. Cada conexión pertenece a tu usuario.</p>
    {error && <p role="alert" className="mt-3 text-sm text-error">{error}</p>}
    {loading ? <p className="mt-3 text-sm">Cargando conexiones…</p> : <>
      {!configured && <p className="mt-3 text-sm text-on-surface-variant">Falta configurar las credenciales y el retorno HTTPS de TikTok en el servidor.</p>}
      <ul className="my-4 space-y-3">{accounts.map(account => <li key={account.id} className="flex items-center justify-between gap-3">
        <span>{account.display_name}{account.expired && !account.can_refresh ? ' · Vuelve a conectar' : ' · Conectada'}</span>
        <Button variant="outline" size="sm" disabled={busy} onClick={() => disconnect(account)}>Desconectar</Button>
      </li>)}</ul>
      {accounts.length === 0 && <p className="mb-3 text-sm text-on-surface-variant">Todavía no tienes cuentas de TikTok conectadas.</p>}
      <Button disabled={busy || !configured} onClick={connect}>{busy ? 'Procesando…' : 'Conectar TikTok'}</Button>
    </>}
    <p className="mt-3 text-xs text-on-surface-variant">Conectar no publica ni envía contenido. Las campañas aprobadas permiten confirmar un envío a TikTok cuando la URL pública de imágenes esté verificada. Debes terminar la publicación en la app de TikTok. Desconectar elimina la credencial local; puedes revocar la autorización también desde TikTok.</p>
  </section>
}
