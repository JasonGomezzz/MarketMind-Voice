import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'

const labels = { pending: 'Pendiente', approved: 'Aprobada', rejected: 'Rechazada' }

export default function CreditRequestsAdminPanel({ onResolved }) {
  const [items, setItems] = useState([])
  const [page, setPage] = useState(1)
  const [next, setNext] = useState(false)
  const [revision, setRevision] = useState(0)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(null)
  const [message, setMessage] = useState('')
  const [amounts, setAmounts] = useState({})

  useEffect(() => {
    let active = true
    api.get('/api/admin/credit-requests/', { params: { page } }).then(({ data }) => {
      if (active) { setItems(data.results ?? []); setNext(Boolean(data.next)) }
    }).catch(() => { if (active) setMessage('No se pudieron cargar las solicitudes.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [page, revision])

  async function resolve(item, status) {
    const credits = Number(amounts[item.id] ?? 100)
    if (status === 'approved' && (!Number.isInteger(credits) || credits < 1 || credits > 10000)) {
      setMessage('Ingresa entre 1 y 10000 créditos enteros.'); return
    }
    if (!window.confirm(status === 'approved' ? `¿Añadir ${credits} créditos a ${item.email}?` : `¿Rechazar la solicitud de ${item.email}?`)) return
    setBusy(item.id)
    setMessage('')
    try {
      const { data } = await api.patch(`/api/admin/credit-requests/${item.id}/`, { status, ...(status === 'approved' ? { credits } : {}) })
      setMessage(data.message)
      setRevision(value => value + 1)
      onResolved()
    } catch (error) {
      setMessage(error.response?.data?.message ?? 'No se pudo resolver la solicitud.')
    } finally { setBusy(null) }
  }

  function go(delta) { setLoading(true); setMessage(''); setPage(value => value + delta) }
  return (
    <section aria-label="Solicitudes de créditos" className="space-y-3 rounded-xl border border-outline-variant bg-white p-6">
      <h2 className="text-xl font-semibold">Solicitudes de créditos</h2>
      <p className="text-sm text-on-surface-variant">Aprobar añade créditos al saldo existente; rechazar no lo modifica. No es un pago.</p>
      <p role="status">{message}</p>
      {loading ? <p>Cargando solicitudes…</p> : items.length === 0 ? <p>No hay solicitudes.</p> : items.map(item => (
        <div key={item.id} className="flex flex-wrap items-center gap-3 border-t border-outline-variant py-3">
          <div className="flex-1"><p>{item.nombre} — {item.email}</p><p className="text-sm">{new Date(item.created_at).toLocaleString('es-PE')} · {labels[item.status]}{item.credits_granted ? ` · +${item.credits_granted} créditos` : ''}</p></div>
          {item.status === 'pending' && <>
            <label className="text-sm">Créditos <input type="number" min="1" max="10000" step="1" value={amounts[item.id] ?? 100} onChange={e => setAmounts({ ...amounts, [item.id]: e.target.value })} className="w-24 rounded border p-2" /></label>
            <Button disabled={busy !== null} onClick={() => resolve(item, 'approved')}>Aprobar</Button>
            <Button variant="outline" disabled={busy !== null} onClick={() => resolve(item, 'rejected')}>Rechazar</Button>
          </>}
        </div>
      ))}
      <div className="flex items-center gap-3"><Button variant="outline" disabled={page === 1 || loading} onClick={() => go(-1)}>Anterior</Button><span>Página {page}</span><Button variant="outline" disabled={!next || loading} onClick={() => go(1)}>Siguiente</Button></div>
    </section>
  )
}
