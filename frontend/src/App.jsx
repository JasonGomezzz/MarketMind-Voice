import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PrivateRoute from './components/PrivateRoute'
import AppLayout from './components/AppLayout'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<PrivateRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            {/* Placeholder routes para HU8, HU9, HU10 */}
            <Route path="/campaigns" element={<div className="text-gray-500">Campañas — HU8</div>} />
            <Route path="/admin" element={<div className="text-gray-500">Admin — HU18</div>} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
