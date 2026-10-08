import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import { rememberXAuthorization, takeXAuthorization } from '../services/xAuthorization'
import { Button } from './ui/button'

export default function XAccounts() {
  const [accounts, setAccounts] = useState([])
  const [configured, setConfigured] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const values = new URLSearchParams(window.location.hash.slice(1))
        if (values.get('provider') === 'x' && values.has('result')) {
          const hash = window.location.hash
          window.history.replaceState(null, '', window.location.pathname)
          const connected = takeXAuthorization(hash)
          if (connected) toast.success('Cuenta de X conectada')
          else setError('X no completó la conexión. Vuelve a intentarlo.')
        }
        const { data } = await api.get('/api/auth/x/accounts/')
        if (!cancelled) {
          setAccounts(data.data.accounts)
          setConfigured(data.data.configured)
        }
      } catch (err) {
        if (!cancelled) setError(err.response?.data?.message || err.message || 'No se pudo cargar X.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => { cancelled = true }
  }, [])

  async function connect() {
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post('/api/auth/x/connect/')
      window.location.assign(rememberXAuthorization(data.data.authorization_url))
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'No se pudo iniciar la conexión con X.')
      setBusy(false)
    }
  }

  async function disconnect(account) {
    if (!window.confirm(`¿Desconectar @${account.username} de NexoMark?`)) return
    setBusy(true)
    try {
      await api.delete(`/api/auth/x/accounts/${account.id}/`)
      setAccounts(current => current.filter(item => item.id !== account.id))
      toast.success('Conexión de X eliminada')
    } catch { toast.error('No se pudo desconectar la cuenta.') }
    finally { setBusy(false) }
  }

  return <section className="rounded-xl border border-outline-variant bg-white p-6 shadow-sm">
    <h2 className="text-xl font-semibold text-on-surface">Redes sociales · X</h2>
    <p className="mt-2 text-sm text-on-surface-variant">Conecta tu cuenta de X para preparar la publicación de campañas aprobadas.</p>
    {error && <p role="alert" className="mt-3 text-sm text-error">{error}</p>}
    {loading ? <p className="mt-3 text-sm">Cargando conexiones…</p> : <>
      {!configured && <p className="mt-3 text-sm text-on-surface-variant">Falta configurar X en el servidor.</p>}
      <ul className="my-4 space-y-3">{accounts.map(account => <li key={account.id} className="flex items-center justify-between gap-3">
        <span>@{account.username}{account.expired ? ' · Vuelve a conectar' : ' · Conectada'}</span>
        <Button variant="outline" size="sm" disabled={busy} onClick={() => disconnect(account)}>Desconectar</Button>
      </li>)}</ul>
      {accounts.length === 0 && <p className="mb-3 text-sm text-on-surface-variant">Todavía no tienes cuentas de X conectadas.</p>}
      <Button disabled={busy || !configured} onClick={connect}>{busy ? 'Procesando…' : 'Conectar X'}</Button>
    </>}
    <p className="mt-3 text-xs text-on-surface-variant">Conectar no publica campañas. Puedes revocar el acceso desde X.</p>
  </section>
}
