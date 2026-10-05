import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'

const labels = { pending: 'Pendiente de revisión', approved: 'Aprobada', rejected: 'Rechazada' }

export default function CreditRequestButton() {
  const [busy, setBusy] = useState(false)
  const [latest, setLatest] = useState(null)
  const [message, setMessage] = useState('')
  useEffect(() => {
    let active = true
    api.get('/api/auth/credit-requests/').then(({ data }) => {
      if (active) setLatest(data.results?.[0] ?? null)
    }).catch(() => { if (active) setMessage('No se pudo consultar el estado de la solicitud.') })
    return () => { active = false }
  }, [])

  async function submit() {
    setBusy(true)
    setMessage('')
    try {
      const { data } = await api.post('/api/auth/credit-requests/')
      setLatest(data.data)
      setMessage(data.message)
    } catch {
      setMessage('No se pudo enviar la solicitud. Intenta nuevamente.')
    } finally { setBusy(false) }
  }

  return (
    <div className="space-y-2">
      <Button type="button" variant="outline" disabled={busy || latest?.status === 'pending'} onClick={submit}>
        {busy ? 'Enviando…' : latest?.status === 'pending' ? 'Solicitud pendiente' : 'Solicitar créditos al administrador'}
      </Button>
      <p role="status" className="text-sm text-on-surface-variant">
        {message || (latest ? `Última solicitud: ${labels[latest.status]}${latest.credits_granted ? ` (+${latest.credits_granted} créditos)` : ''}` : '')}
      </p>
    </div>
  )
}
