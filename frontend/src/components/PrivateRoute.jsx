import { Navigate, Outlet } from 'react-router-dom'
import { useEffect, useState } from 'react'
import api from '../services/api'

export default function PrivateRoute() {
  const token = localStorage.getItem('access_token')
  const [status, setStatus] = useState('loading')
  useEffect(() => {
    if (!token) return
    let cancelled = false
    api.get('/api/auth/me/').then(({ data }) => {
      const user = data?.data?.user
      if (!['cliente', 'marketero', 'superadmin'].includes(user?.rol)) {
        if (!cancelled) setStatus('invalid')
        return
      }
      localStorage.setItem('user_role', user.rol)
      if (!cancelled) setStatus('ready')
    }).catch((error) => {
      if (!cancelled) setStatus(error.response?.status === 401 ? 'invalid' : 'error')
    })
    return () => { cancelled = true }
  }, [token])
  if (!token || status === 'invalid') return <Navigate to="/login" replace />
  if (status === 'error') return <main className="p-8"><p>No se pudo verificar tu sesión.</p><button onClick={() => window.location.reload()}>Reintentar</button></main>
  return status === 'ready' ? <Outlet /> : <p className="p-8" role="status">Verificando sesión…</p>
}
