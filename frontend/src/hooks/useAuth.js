import { getAuthItem, setAuthItem, clearAuthSession, startAuthSession } from '@/lib/authStorage'
import { useState, useCallback } from 'react'
import api from '../services/api'

export function useAuth() {
  const [loading, setLoading] = useState(false)

  const login = useCallback(async (email, password, remember = false) => {
    setLoading(true)
    try {
      const { data } = await api.post('/api/auth/token/', { email, password })
      startAuthSession(data, remember)
      const me = await api.get('/api/auth/me/')
      const user = me.data?.data?.user
      if (user?.email) setAuthItem('user_email', user.email)
      return { ok: true, role: data.role }
    } catch (err) {
      clearAuthSession()
      const status = err.response?.status
      const message = err.response?.data?.message
      return { ok: false, status, message }
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    const refresh = getAuthItem('refresh_token')
    try {
      if (refresh) await api.post('/api/auth/logout/', { refresh })
    } catch {
      // ignore — clear session regardless
    } finally {
      clearAuthSession()
    }
  }, [])

  const isAuthenticated = () => Boolean(getAuthItem('access_token'))

  const getRole = () => getAuthItem('user_role')

  const getNombre = () => getAuthItem('user_nombre')

  const getEmail = () => getAuthItem('user_email')

  return { login, logout, isAuthenticated, getRole, getNombre, getEmail, loading }
}
