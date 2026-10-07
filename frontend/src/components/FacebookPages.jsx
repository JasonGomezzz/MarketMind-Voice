import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import { rememberFacebookAuthorization, takeFacebookAuthorization } from '../services/facebookAuthorization'
import { Button } from './ui/button'

export default function FacebookPages() {
  const [pages, setPages] = useState([])
  const [configured, setConfigured] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const completion = useRef(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const fragment = new URLSearchParams(window.location.hash.slice(1))
        const query = new URLSearchParams(window.location.search)
        const values = fragment.has('code') || fragment.has('error') ? fragment : query
        if (values.get('provider') === 'facebook' && (values.has('code') || values.has('error')) && !completion.current) {
          const search = window.location.search, hash = window.location.hash
          window.history.replaceState(null, '', window.location.pathname)
          const { state, code, denied } = takeFacebookAuthorization(search, hash)
          completion.current = denied
            ? Promise.resolve().then(() => toast.error('No autorizaste la conexión con Facebook.'))
            : api.post('/api/auth/facebook/complete/', { state, code }).then(() => toast.success('Páginas de Facebook conectadas'))
        }
        if (completion.current) await completion.current
      } catch (err) {
        if (!cancelled) setError(err.response?.data?.message || err.message || 'No se pudo completar la autorización de Facebook.')
      }
      try {
        const { data } = await api.get('/api/auth/facebook/pages/')
        if (!cancelled) {
          setPages(data.data.pages)
          setConfigured(data.data.configured)
        }
      } catch {
        if (!cancelled) setError('No se pudieron cargar tus Páginas. Reintenta recargando la página.')
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
      const { data } = await api.post('/api/auth/facebook/connect/')
      window.location.assign(rememberFacebookAuthorization(data.data.authorization_url))
    } catch (err) {
      toast.error(err.response?.data?.message || 'No se pudo iniciar la conexión con Facebook.')
      setBusy(false)
    }
  }

  async function disconnect(page) {
    if (!window.confirm(`¿Desconectar la Página ${page.name} de NexoMark?`)) return
    setBusy(true)
    try {
      await api.delete(`/api/auth/facebook/pages/${page.id}/`)
      setPages(current => current.filter(item => item.id !== page.id))
      toast.success('Conexión eliminada de NexoMark')
    } catch { toast.error('No se pudo desconectar la Página.') }
    finally { setBusy(false) }
  }

  return (
    <section className="rounded-xl border border-outline-variant bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-on-surface">Redes sociales · Facebook</h2>
      <p className="mt-2 text-sm text-on-surface-variant">Autoriza las Páginas que administras con tu cuenta de Facebook. Cada conexión pertenece a tu usuario; no se publica en tu perfil personal.</p>
      {error && <p role="alert" className="mt-3 text-sm text-error">{error}</p>}
      {loading ? <p className="mt-3 text-sm">Cargando conexiones…</p> : <>
        {!configured && <p className="mt-3 text-sm text-on-surface-variant">Falta configurar Facebook en el servidor. No se pueden conectar Páginas todavía.</p>}
        <ul className="my-4 space-y-3">
          {pages.map(page => <li key={page.id} className="flex items-center justify-between gap-3">
            <span>{page.name}{page.expired ? ' · Autorización vencida: vuelve a conectar' : ' · Conectada'}</span>
            <Button variant="outline" size="sm" disabled={busy} onClick={() => disconnect(page)}>Desconectar</Button>
          </li>)}
        </ul>
        {pages.length === 0 && <p className="mb-3 text-sm text-on-surface-variant">Todavía no tienes Páginas conectadas.</p>}
        <Button disabled={busy || !configured} onClick={connect}>{busy ? 'Procesando…' : 'Conectar Facebook'}</Button>
      </>}
      <p className="mt-3 text-xs text-on-surface-variant">Conectar no publica automáticamente. Puedes publicar en tu Página desde una campaña aprobada, revisando su imagen y texto. Desconectar elimina la credencial local; también puedes revocar el acceso desde Facebook.</p>
    </section>
  )
}
