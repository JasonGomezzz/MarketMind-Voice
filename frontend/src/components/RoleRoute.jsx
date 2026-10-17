import { Navigate, Outlet } from 'react-router-dom'
import { useVerifiedUser } from '@/hooks/useVerifiedUser'

/**
 * Deja pasar solo a los roles indicados. El rol viene del usuario que
 * PrivateRoute verificó en el servidor; el resto vuelve a su dashboard.
 * La API sigue aplicando sus propios permisos: esto evita pantallas rotas,
 * no reemplaza la autorización del backend.
 */
export default function RoleRoute({ roles }) {
  const user = useVerifiedUser()
  return roles.includes(user?.rol) ? <Outlet /> : <Navigate to="/dashboard" replace />
}
