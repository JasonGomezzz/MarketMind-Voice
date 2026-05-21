import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const ESTADO_BADGE = {
  borrador: 'bg-gray-100 text-gray-600',
  pendiente_ia: 'bg-yellow-100 text-yellow-700',
  generado: 'bg-green-100 text-green-700',
  pendiente_aprobacion: 'bg-blue-100 text-blue-700',
  aprobado: 'bg-emerald-100 text-emerald-700',
  rechazado: 'bg-red-100 text-red-700',
}

const ESTADO_LABEL = {
  borrador: 'Borrador',
  pendiente_ia: 'Pendiente IA',
  generado: 'Generado',
  pendiente_aprobacion: 'Pendiente Aprobación',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
}

export default function CampaignListPage() {
  const role = localStorage.getItem('user_role') || ''
  const navigate = useNavigate()

  const [campaigns, setCampaigns] = useState([])
  const [count, setCount] = useState(0)
  const [nextUrl, setNextUrl] = useState(null)
  const [prevUrl, setPrevUrl] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  async function fetchCampaigns(url = '/api/campaigns/') {
    setLoading(true)
    setError(false)
    try {
      const { data } = await api.get(url)
      setCampaigns(data.results)
      setCount(data.count)
      setNextUrl(data.next)
      setPrevUrl(data.previous)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchCampaigns() }, [])

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-10 bg-gray-100 rounded animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <p className="text-sm text-red-500">
        Error al cargar campañas.{' '}
        <button className="underline" onClick={() => fetchCampaigns()}>Reintentar</button>
      </p>
    )
  }

  if (campaigns.length === 0) {
    return (
      <div>
        <PageHeader role={role} count={0} onNew={() => navigate('/campaigns/new')} />
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg font-medium">
            {role === 'cliente' ? 'No tienes campañas asignadas.' : 'Aún no hay campañas.'}
          </p>
          {role === 'marketero' && (
            <button
              onClick={() => navigate('/campaigns/new')}
              className="mt-4 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Crear primera campaña
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader role={role} count={count} onNew={() => navigate('/campaigns/new')} />

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
            <tr>
              {['Título', 'Cliente', 'Industria', 'Tono', 'Plataforma', 'Estado', 'Fecha'].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {campaigns.map(c => (
              <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-900 max-w-[180px] truncate">{c.titulo}</td>
                <td className="px-4 py-3 text-gray-600">{c.cliente_nombre}</td>
                <td className="px-4 py-3 text-gray-600 capitalize">{c.industria}</td>
                <td className="px-4 py-3 text-gray-600 capitalize">{c.tono}</td>
                <td className="px-4 py-3 text-gray-600 capitalize">{c.plataforma}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${ESTADO_BADGE[c.estado] ?? 'bg-gray-100 text-gray-600'}`}>
                    {ESTADO_LABEL[c.estado] ?? c.estado}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(c.fecha_creacion).toLocaleDateString('es-PE')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(prevUrl || nextUrl) && (
        <div className="flex justify-between mt-4">
          <button
            disabled={!prevUrl}
            onClick={() => fetchCampaigns(prevUrl)}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Anterior
          </button>
          <button
            disabled={!nextUrl}
            onClick={() => fetchCampaigns(nextUrl)}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  )
}

function PageHeader({ role, count, onNew }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-baseline gap-3">
        <h2 className="text-xl font-semibold text-gray-900">Campañas</h2>
        {count > 0 && <p className="text-sm text-gray-500">{count} total</p>}
      </div>
      {role === 'marketero' && (
        <button
          onClick={onNew}
          className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
        >
          + Nueva Campaña
        </button>
      )}
    </div>
  )
}
