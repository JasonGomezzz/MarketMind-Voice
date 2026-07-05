import axios from 'axios'

/**
 * Cliente HTTP para el BLOQUE USUARIO — Spring Boot :8080 (el "mostrador").
 *
 * Arquitectura políglota: Django (:8000) y Spring Boot (:8080) hablan con la
 * MISMA PostgreSQL, NO entre sí. El cliente final (rol "cliente") consume ESTE
 * cliente para ver y aprobar/rechazar campañas.
 *
 * JWT COMPARTIDO: Spring Boot valida el mismo access_token que emite Django
 * (mismo SECRET_KEY). Aquí solo lo adjuntamos; el refresh vive en api.js (Django),
 * porque Spring Boot NO emite ni refresca tokens.
 *
 * Endpoints (CampaignController):
 *   GET   /api/v1/campaigns/pending        → feed de campañas por revisar
 *   GET   /api/v1/campaigns/{id}           → detalle
 *   PATCH /api/v1/campaigns/{id}/status    → aprobar / rechazar (+ feedback)
 */
const userApi = axios.create({
  baseURL: import.meta.env.VITE_USER_API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Adjunta el access_token (el mismo de Django) a cada request.
userApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let isRefreshing = false
let failedQueue = []

function processQueue(error, token = null) {
  failedQueue.forEach((prom) => (error ? prom.reject(error) : prom.resolve(token)))
  failedQueue = []
}

// En 401, refresca contra DJANGO (único emisor de JWT) y reintenta el request a Spring.
userApi.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            original.headers.Authorization = `Bearer ${token}`
            return userApi(original)
          })
          .catch((err) => Promise.reject(err))
      }

      isRefreshing = true
      const refresh = localStorage.getItem('refresh_token')

      if (!refresh) {
        clearSession()
        return Promise.reject(error)
      }

      try {
        // El refresh SIEMPRE va a Django, no a Spring Boot.
        const { data } = await axios.post(
          `${import.meta.env.VITE_API_URL}/api/auth/token/refresh/`,
          { refresh },
        )
        localStorage.setItem('access_token', data.access)
        if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
        processQueue(null, data.access)
        original.headers.Authorization = `Bearer ${data.access}`
        return userApi(original)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearSession()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

function clearSession() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_role')
  localStorage.removeItem('user_nombre')
  window.location.href = '/login'
}

export default userApi
