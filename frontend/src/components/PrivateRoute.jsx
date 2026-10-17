import { Navigate, Outlet } from 'react-router-dom'
import { getAuthItem } from '../services/session'

export default function PrivateRoute() {
  const token = getAuthItem('access_token')
  return token ? <Outlet /> : <Navigate to="/login" replace />
}
