import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import api from '../services/api'
import { Button } from '@/components/ui/button'
import { createRecoveryWait } from '@/lib/recoveryWait'

export default function PasswordRecoveryPage() {
  const location = useLocation()
  const confirming = location.pathname === '/reset-password'
  const params = new URLSearchParams(location.hash.slice(1))
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [message, setMessage] = useState('')
  const [retry, setRetry] = useState(null)
  const [now, setNow] = useState(() => Date.now())
  const normalizedEmail = email.trim().toLowerCase()
  const remaining = retry && (confirming || retry.email === normalizedEmail)
    ? Math.max(0, Math.ceil((retry.until - now) / 1000)) : 0
  useEffect(() => {
    if (!retry) return
    const timer = setInterval(() => {
      const current = Date.now()
      setNow(current)
      if (current >= retry.until) clearInterval(timer)
    }, 1000)
    return () => clearInterval(timer)
  }, [retry])
  async function submit(event) {
    event.preventDefault()
    if (remaining > 0) return
    if (confirming && password !== confirmation) {
      setMessage('Las contraseñas no coinciden.')
      return
    }
    setBusy(true)
    setMessage('')
    try {
      const { data } = await api.post(confirming ? '/api/auth/password-reset/confirm/' : '/api/auth/password-reset/',
        confirming ? { uid: params.get('uid'), token: params.get('token'), new_password: password } : { email })
      setMessage(data.message)
      if (!confirming && data.data?.resend_after) {
        const wait = createRecoveryWait(normalizedEmail, data.data.resend_after)
        setNow(wait.startedAt)
        setRetry(wait)
      }
      setDone(true)
      setPassword('')
      setConfirmation('')
    } catch (error) {
      if (error.response?.status === 429) {
        const seconds = Number(error.response.data?.data?.retry_after || error.response.headers?.['retry-after'])
        const wait = createRecoveryWait(normalizedEmail, seconds)
        setNow(wait.startedAt)
        setRetry(wait)
      }
      setMessage(error.response?.data?.message || error.response?.data?.detail || 'No se pudo procesar la solicitud. Intenta nuevamente.')
    } finally { setBusy(false) }
  }
  const invalidLink = confirming && (!params.get('uid') || !params.get('token'))
  return <main className="auth-shell flex min-h-screen items-center justify-center p-6">
    <section className="glass-liquid w-full max-w-md rounded-3xl p-8">
      <h1 className="mb-4 text-2xl font-bold">{confirming ? 'Nueva contraseña' : 'Recuperar contraseña'}</h1>
      {invalidLink ? <p role="alert">El enlace no es válido. Solicita uno nuevo.</p> : !done && <form onSubmit={submit} className="space-y-4">
        {confirming ? <>
          <label className="block">Nueva contraseña<input className="mt-2 w-full rounded-lg border p-3" type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={password} onChange={e => setPassword(e.target.value)} /></label>
          <label className="block">Confirmar contraseña<input className="mt-2 w-full rounded-lg border p-3" type="password" autoComplete="new-password" required value={confirmation} onChange={e => setConfirmation(e.target.value)} /></label>
        </> : <label className="block">Correo electrónico<input className="mt-2 w-full rounded-lg border p-3" type="email" autoComplete="email" required value={email} onChange={e => setEmail(e.target.value)} /></label>}
        <Button type="submit" disabled={busy || remaining > 0}>{busy ? 'Procesando…' : remaining > 0 ? `Espera ${remaining} s` : confirming ? 'Guardar contraseña' : 'Enviar enlace'}</Button>
      </form>}
      {message && <p role="status" className="mt-4">{message}</p>}
      {done && !confirming && <Button type="button" variant="outline" className="mt-4" onClick={() => { setDone(false); setMessage('') }}>Solicitar otro enlace</Button>}
      <div className="mt-6 flex gap-4"><Link to="/login" className="text-primary underline">Volver al login</Link>{invalidLink && <Link to="/forgot-password" className="text-primary underline">Solicitar enlace</Link>}</div>
    </section>
  </main>
}
