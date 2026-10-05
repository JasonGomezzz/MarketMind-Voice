import { getAuthItem, setAuthItem, clearAuthSession } from '@/lib/authStorage'
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = getAuthItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let isRefreshing = false
let failedQueue = []

function processQueue(error, token = null) {
  failedQueue.forEach((prom) => (error ? prom.reject(error) : prom.resolve(token)))
  failedQueue = []
}

// Auto-refresh on 401, redirect to /login if refresh fails
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    const isAuthEntryPoint =
      original?.url?.includes('/api/auth/token/') || original?.url?.includes('/api/auth/register/')

    if (error.response?.status === 401 && !original._retry && !isAuthEntryPoint) {
      original._retry = true

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            original.headers.Authorization = `Bearer ${token}`
            return api(original)
          })
          .catch((err) => Promise.reject(err))
      }

      isRefreshing = true
      const refresh = getAuthItem('refresh_token')

      if (!refresh) {
        isRefreshing = false
        processQueue(error)
        clearSession()
        return Promise.reject(error)
      }

      try {
        const { data } = await axios.post(
          `${import.meta.env.VITE_API_URL}/api/auth/token/refresh/`,
          { refresh }
        )
        setAuthItem('access_token', data.access)
        if (data.refresh) setAuthItem('refresh_token', data.refresh)
        processQueue(null, data.access)
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearSession()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

function clearSession() {
  clearAuthSession()
  window.location.href = '/login'
}

export default api
