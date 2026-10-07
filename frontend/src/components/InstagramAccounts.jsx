import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import { rememberInstagramAuthorization, takeInstagramAuthorization } from '../services/instagramAuthorization'
import { Button } from './ui/button'

export default function InstagramAccounts() {
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
        const query = new URLSearchParams(window.location.search)
        const fragment = new URLSearchParams(window.location.hash.slice(1))
        if ((query.has('code') || query.has('error') || fragment.has('code') || fragment.has('error')) && !completion.current) {
          const search = window.location.search, hash = window.location.hash
          // Remove authorization values before loading anything else or showing errors.
          window.history.replaceState(null, '', window.location.pathname)
          const { code, state, denied } = takeInstagramAuthorization(search, hash)
          completion.current = denied
            ? Promise.resolve().then(() => toast.error('No autorizaste la conexión con Instagram.'))
            : api.post('/api/auth/instagram/complete/', { code, state }).then(() => toast.success('Instagram conectado'))
        }
        // Reuse the same completion during React StrictMode's effect replay.
        if (completion.current) await completion.current
      } catch (err) {
        if (!cancelled) setError(err.response?.data?.message || err.message || 'No se pudo completar la autorización. Vuelve a conectar Instagram.')
      }
      try {
        const { data } = await api.get('/api/auth/instagram/accounts/')
        if (!cancelled) {
          setAccounts(data.data.accounts)
          setConfigured(data.data.configured)
        }
      } catch {
        if (!cancelled) setError('No se pudieron cargar tus cuentas. Reintenta recargando la página.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => { cancelled = true }
  }, [])

  async function connect() {
    setBusy(true)
    try {
      const { data } = await api.post('/api/auth/instagram/connect/')
      window.location.assign(rememberInstagramAuthorization(data.data.authorization_url))
    } catch (err) {
      toast.error(err.response?.data?.message || 'No se pudo iniciar la conexión con Instagram.')
      setBusy(false)
    }
  }

  async function disconnect(account) {
    if (!window.confirm(`¿Desconectar @${account.username} de NexoMark?`)) return
    setBusy(true)
    try {
      await api.delete(`/api/auth/instagram/accounts/${account.id}/`)
      setAccounts(current => current.filter(item => item.id !== account.id))
      toast.success('Conexión eliminada de NexoMark')
    } catch { toast.error('No se pudo desconectar la cuenta.') }
    finally { setBusy(false) }
  }

  return (
    <section className="rounded-xl border border-outline-variant bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-on-surface">Redes sociales · Instagram</h2>
      <p className="mt-2 text-sm text-on-surface-variant">Conecta una o varias cuentas profesionales que tengas autorización para administrar. Cada conexión pertenece a tu usuario.</p>
      {error && <p role="alert" className="mt-3 text-sm text-error">{error}</p>}
      {loading ? <p className="mt-3 text-sm">Cargando conexiones…</p> : <>
        {!configured && <p className="mt-3 text-sm text-on-surface-variant">Falta configurar la conexión de Meta en el servidor. No se pueden conectar cuentas todavía.</p>}
        <ul className="my-4 space-y-3">
          {accounts.map(account => <li key={account.id} className="flex items-center justify-between gap-3">
            <span>@{account.username}{account.expired ? ' · Autorización vencida: vuelve a conectar' : ' · Conectada'}</span>
            <Button variant="outline" size="sm" disabled={busy} onClick={() => disconnect(account)}>Desconectar</Button>
          </li>)}
        </ul>
        {accounts.length === 0 && <p className="mb-3 text-sm text-on-surface-variant">Todavía no tienes cuentas conectadas.</p>}
        <Button disabled={!configured || busy} onClick={connect}>{busy ? 'Procesando…' : 'Conectar Instagram'}</Button>
        <p className="mt-3 text-xs text-on-surface-variant">Conectar no publica automáticamente. Puedes publicar desde una campaña aprobada, revisando su imagen y texto. Desconectar elimina la credencial local; puedes revocar también el acceso desde Instagram.</p>
      </>}
    </section>
  )
}
