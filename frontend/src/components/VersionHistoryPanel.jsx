import { useEffect, useState } from 'react'
import api from '../services/api'

export default function VersionHistoryPanel({ campaignId }) {
  const [versions, setVersions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    async function fetchVersions() {
      try {
        const { data } = await api.get(`/api/campaigns/${campaignId}/versions/`)
        setVersions(data.data)
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    fetchVersions()
  }, [campaignId])

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
        Historial de versiones
      </p>

      {loading && (
        <p className="text-xs text-gray-400">Cargando versiones…</p>
      )}

      {error && (
        <p className="text-xs text-red-400">No se pudieron cargar las versiones.</p>
      )}

      {!loading && !error && versions.length === 0 && (
        <p className="text-xs text-gray-400">No hay versiones anteriores aún.</p>
      )}

      {!loading && !error && versions.length > 0 && (
        <ul className="space-y-3 max-h-96 overflow-y-auto pr-1">
          {versions.map(v => (
            <li
              key={v.id}
              className="flex gap-3 items-start border-b border-gray-100 pb-3 last:border-0 last:pb-0"
            >
              <div className="flex-shrink-0 w-20">
                {v.tiene_imagen ? (
                  <img
                    src={`data:image/png;base64,${v.imagen_b64}`}
                    alt={`Versión ${v.version_number}`}
                    className="w-20 h-20 object-cover rounded-lg"
                  />
                ) : (
                  <div className="w-20 h-20 rounded-lg bg-gray-100 flex items-center justify-center">
                    <span className="text-xs text-gray-400 text-center leading-tight">
                      Sin imagen
                    </span>
                  </div>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                    V{v.version_number}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(v.created_at).toLocaleString('es-PE')}
                  </span>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed line-clamp-3">
                  {v.texto_preview}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
