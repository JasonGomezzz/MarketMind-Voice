import { useState, useCallback } from 'react'
import api from '../services/api'

export function useAuth() {
  const [loading, setLoading] = useState(false)

  const login = useCallback(async (email, password) => {
    setLoading(true)
    try {
      const { data } = await api.post('/api/auth/token/', { email, password })
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      localStorage.setItem('user_role', data.role)
      localStorage.setItem('user_nombre', data.nombre)
      return { ok: true, role: data.role }
    } catch (err) {
      const status = err.response?.status
      return { ok: false, status }
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
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_role')
      localStorage.removeItem('user_nombre')
    }
  }, [])

  const isAuthenticated = () => Boolean(localStorage.getItem('access_token'))

  const getRole = () => localStorage.getItem('user_role')

  const getNombre = () => localStorage.getItem('user_nombre')

  return { login, logout, isAuthenticated, getRole, getNombre, loading }
}
