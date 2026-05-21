import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import api from '../services/api'

export default function DashboardPage() {
  const nombre = localStorage.getItem('user_nombre') || 'usuario'
  const role = localStorage.getItem('user_role') || ''

  const [stats, setStats] = useState(null)
  const [tokens, setTokens] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const location = useLocation()

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)

    async function fetchData() {
      try {
        const [statsRes, meRes] = await Promise.all([
          api.get('/api/campaigns/stats/'),
          api.get('/api/auth/me/'),
        ])
        if (!cancelled) {
          setStats(statsRes.data.data)
          setTokens(meRes.data.data.user.tokens_disponibles)
        }
      } catch {
        if (!cancelled) setError(true)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchData()
    return () => { cancelled = true }
  }, [retryCount, location.key])

  const activeCampaigns = stats
    ? (stats.generado ?? 0) + (stats.pendiente_aprobacion ?? 0) + (stats.aprobado ?? 0)
    : null

  const iaGenerations = stats
    ? (stats.pendiente_ia ?? 0) + (stats.generado ?? 0) +
      (stats.pendiente_aprobacion ?? 0) + (stats.aprobado ?? 0) +
      (stats.rechazado ?? 0)
    : null

  const cards = [
    { label: 'Campañas activas', value: activeCampaigns },
    { label: 'Tokens disponibles', value: tokens },
    { label: 'Generaciones IA', value: iaGenerations },
  ]

  function displayValue(val) {
    if (loading) return '…'
    if (error) return '—'
    return val ?? 0
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-1">
        Bienvenido, {nombre}
      </h2>
      <p className="text-sm text-gray-500 capitalize">Rol: {role}</p>

      {error && (
        <p className="mt-3 text-sm text-red-500">
          No se pudieron cargar los datos.{' '}
          <button className="underline" onClick={() => setRetryCount(c => c + 1)}>
            Reintentar
          </button>
        </p>
      )}

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {cards.map(({ label, value }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500">{label}</p>
            <p className={`text-2xl font-bold mt-1 ${loading ? 'text-gray-300 animate-pulse' : 'text-gray-900'}`}>
              {displayValue(value)}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
