import { useEffect, useState } from 'react'
import toast, { Toaster } from 'react-hot-toast'
import api from '../services/api'

const ROL_BADGES = {
  superadmin: 'bg-purple-100 text-purple-700',
  marketero: 'bg-indigo-100 text-indigo-700',
  cliente: 'bg-emerald-100 text-emerald-700',
}

const ROL_LABELS = {
  superadmin: 'SuperAdmin',
  marketero: 'Marketero',
  cliente: 'Cliente',
}

const PAGE_SIZE = 20

function RolBadge({ rol }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ROL_BADGES[rol] ?? 'bg-gray-100 text-gray-700'}`}>
      {ROL_LABELS[rol] ?? rol}
    </span>
  )
}

function EstadoChip({ activo }) {
  return activo ? (
    <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
      Activo
    </span>
  ) : (
    <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-red-50 text-red-700 border border-red-200">
      Suspendido
    </span>
  )
}

function ConfirmModal({ title, message, confirmLabel, onConfirm, onCancel, busy }) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">{title}</h3>
        <p className="text-sm text-gray-600 mb-5">{message}</p>
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            disabled={busy}
            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {busy ? 'Procesando…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function UsersAdminPage() {
  const [users, setUsers] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentUserId, setCurrentUserId] = useState(null)
  const [confirm, setConfirm] = useState(null) // { type: 'reset' | 'suspend' | 'activate', user }
  const [busy, setBusy] = useState(false)

  const fetchUsers = (targetPage = page) => {
    setLoading(true)
    setError(null)
    api
      .get('/api/admin/users/', { params: { page: targetPage } })
      .then((res) => {
        setUsers(res.data.results ?? [])
        setCount(res.data.count ?? 0)
      })
      .catch(() => setError('No se pudo cargar la lista de usuarios. Verificá tu sesión.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    api
      .get('/api/auth/me/')
      .then((res) => setCurrentUserId(res.data?.data?.user?.id ?? null))
      .catch(() => setCurrentUserId(null))
  }, [])

  useEffect(() => {
    fetchUsers(page)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE))

  const handleToggleActive = (user) => {
    setConfirm({
      type: user.is_active ? 'suspend' : 'activate',
      user,
    })
  }

  const handleResetQuota = (user) => {
    setConfirm({ type: 'reset', user })
  }

  const performAction = async () => {
    if (!confirm) return
    setBusy(true)
    try {
      if (confirm.type === 'reset') {
        const { data } = await api.patch(`/api/admin/users/${confirm.user.id}/reset-quota/`)
        toast.success(data?.message ?? 'Cuota reseteada.')
      } else {
        const targetActive = confirm.type === 'activate'
        const { data } = await api.patch(`/api/admin/users/${confirm.user.id}/`, {
          is_active: targetActive,
        })
        toast.success(data?.message ?? (targetActive ? 'Usuario reactivado.' : 'Usuario suspendido.'))
      }
      setConfirm(null)
      fetchUsers(page)
    } catch (err) {
      const apiMessage = err?.response?.data?.message
      toast.error(apiMessage ?? 'No se pudo completar la acción.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <Toaster position="top-right" />

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-800">Gestión de Usuarios</h2>
          <p className="text-sm text-gray-500 mt-1">
            Suspendé cuentas o reseteá la cuota de tokens. Solo SuperAdmin.
          </p>
        </div>
        <span className="text-xs text-gray-500">
          {count} usuario{count === 1 ? '' : 's'} en total
        </span>
      </div>

      {loading && (
        <div className="text-center py-20 text-gray-400 text-sm">Cargando usuarios…</div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 uppercase text-xs tracking-wide">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Nombre</th>
                  <th className="text-left px-4 py-3 font-medium">Email</th>
                  <th className="text-left px-4 py-3 font-medium">Rol</th>
                  <th className="text-left px-4 py-3 font-medium">Estado</th>
                  <th className="text-right px-4 py-3 font-medium">Tokens</th>
                  <th className="text-right px-4 py-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center py-10 text-gray-400">
                      No hay usuarios en esta página.
                    </td>
                  </tr>
                )}
                {users.map((u) => {
                  const isSelf = u.id === currentUserId
                  return (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-800 font-medium">
                        {u.nombre}
                        {isSelf && (
                          <span className="ml-2 text-xs text-gray-400">(tú)</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{u.email}</td>
                      <td className="px-4 py-3">
                        <RolBadge rol={u.rol} />
                      </td>
                      <td className="px-4 py-3">
                        <EstadoChip activo={u.is_active} />
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700 font-mono">
                        {u.tokens_disponibles}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => handleToggleActive(u)}
                            disabled={isSelf}
                            title={isSelf ? 'No puedes modificar tu propia cuenta' : ''}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                              isSelf
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : u.is_active
                                ? 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-200'
                                : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                            }`}
                          >
                            {u.is_active ? 'Suspender' : 'Activar'}
                          </button>
                          <button
                            onClick={() => handleResetQuota(u)}
                            disabled={isSelf}
                            title={isSelf ? 'No puedes modificar tu propia cuenta' : ''}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                              isSelf
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200'
                            }`}
                          >
                            Resetear cuota
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">
              Página {page} de {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 rounded-lg text-sm font-medium bg-white border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Anterior
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-3 py-1.5 rounded-lg text-sm font-medium bg-white border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Siguiente →
              </button>
            </div>
          </div>
        </>
      )}

      {confirm && (
        <ConfirmModal
          title={
            confirm.type === 'reset'
              ? 'Resetear cuota de tokens'
              : confirm.type === 'suspend'
              ? 'Suspender usuario'
              : 'Reactivar usuario'
          }
          message={
            confirm.type === 'reset'
              ? `Vas a resetear los tokens de ${confirm.user.nombre} a 100. ¿Confirmás?`
              : confirm.type === 'suspend'
              ? `${confirm.user.nombre} no podrá iniciar sesión ni usar la app. ¿Confirmás?`
              : `${confirm.user.nombre} podrá volver a usar la app. ¿Confirmás?`
          }
          confirmLabel={
            confirm.type === 'reset'
              ? 'Resetear'
              : confirm.type === 'suspend'
              ? 'Suspender'
              : 'Reactivar'
          }
          onConfirm={performAction}
          onCancel={() => setConfirm(null)}
          busy={busy}
        />
      )}
    </div>
  )
}
