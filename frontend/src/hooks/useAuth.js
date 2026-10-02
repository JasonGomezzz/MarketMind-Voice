import { useState, useCallback } from 'react'
import api from '../services/api'
import { clearSession, storeTokens } from '../services/session'

export function useAuth() {
  const [loading, setLoading] = useState(false)

  const login = useCallback(async (email, password) => {
    setLoading(true)
    try {
      const { data } = await api.post('/api/auth/token/', { email, password })
      storeTokens(data)
      localStorage.setItem('user_role', data.role)
      localStorage.setItem('user_nombre', data.nombre)
      const me = await api.get('/api/auth/me/')
      const user = me.data?.data?.user
      if (user?.email) localStorage.setItem('user_email', user.email)
      return { ok: true, role: data.role }
    } catch (err) {
      const status = err.response?.status
      const message = err.response?.data?.message
      return { ok: false, status, message }
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem('refresh_token')
    try {
      if (refresh) await api.post('/api/auth/logout/', { refresh })
    } catch {
      // ignore — clear session regardless
    } finally {
      clearSession({ redirect: false })
    }
  }, [])

  const isAuthenticated = () => Boolean(localStorage.getItem('access_token'))

  const getRole = () => localStorage.getItem('user_role')

  const getNombre = () => localStorage.getItem('user_nombre')

  const getEmail = () => localStorage.getItem('user_email')

  return { login, logout, isAuthenticated, getRole, getNombre, getEmail, loading }
}
