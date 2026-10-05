import { Navigate, Outlet } from 'react-router-dom'

export default function RoleRoute({ roles }) {
  const role = localStorage.getItem('user_role')
  return roles.includes(role) ? <Outlet /> : <Navigate to="/dashboard" replace />
}
