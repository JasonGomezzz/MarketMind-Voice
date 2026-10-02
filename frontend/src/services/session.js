import axios from 'axios'

export const SESSION_CHANGED = 'marketmind:session-changed'
let pendingRefresh = null

export function storeTokens({ access, refresh }) {
  localStorage.setItem('access_token', access)
  if (refresh) localStorage.setItem('refresh_token', refresh)
  window.dispatchEvent(new Event(SESSION_CHANGED))
}

export function clearSession({ redirect = true } = {}) {
  for (const key of ['access_token', 'refresh_token', 'user_role', 'user_nombre', 'user_email']) {
    localStorage.removeItem(key)
  }
  window.dispatchEvent(new Event(SESSION_CHANGED))
  if (redirect) window.location.href = '/login'
}

// One rotation for Django, Spring and WebSocket in this tab. A late 401 that used
// an old token reuses the newer access token instead of rotating refresh again.
export function refreshAccessToken(rejectedToken) {
  const current = localStorage.getItem('access_token')
  if (rejectedToken && current && rejectedToken !== current) return Promise.resolve(current)
  if (pendingRefresh) return pendingRefresh
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) {
    clearSession()
    return Promise.reject(new Error('Sesión expirada.'))
  }
  pendingRefresh = axios.post(`${import.meta.env?.VITE_API_URL || ''}/api/auth/token/refresh/`, { refresh })
    .then(({ data }) => {
      // A response belonging to a logged-out or replaced session cannot resurrect it.
      if (localStorage.getItem('refresh_token') !== refresh) throw new Error('La sesión cambió.')
      if (!data.access) throw new Error('Respuesta de renovación inválida.')
      storeTokens(data)
      return data.access
    })
    .catch((error) => {
      if ([401, 403].includes(error.response?.status)
          && localStorage.getItem('refresh_token') === refresh) clearSession()
      // Network and server failures are retryable; preserve the signed-in session.
      throw error
    })
    .finally(() => { pendingRefresh = null })
  return pendingRefresh
}

export function attachSessionInterceptors(client) {
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })
  client.interceptors.response.use((response) => response, async (error) => {
    const original = error.config
    const authEntry = /\/api\/auth\/(token|register)\//.test(original?.url || '')
    if (error.response?.status !== 401 || !original || original._retry || authEntry) throw error
    original._retry = true
    const rejectedToken = original.headers?.Authorization?.replace(/^Bearer /, '')
    const token = await refreshAccessToken(rejectedToken)
    original.headers.Authorization = `Bearer ${token}`
    return client(original)
  })
}
