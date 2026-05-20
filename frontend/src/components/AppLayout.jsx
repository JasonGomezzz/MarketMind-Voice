import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const NAV_ITEMS = {
  marketero: [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/campaigns', label: 'Campañas' },
  ],
  superadmin: [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/campaigns', label: 'Campañas' },
    { to: '/admin', label: 'Administración' },
  ],
  cliente: [
    { to: '/dashboard', label: 'Dashboard' },
  ],
}

export default function AppLayout() {
  const { logout, getRole, getNombre } = useAuth()
  const navigate = useNavigate()
  const role = getRole() || 'cliente'
  const nombre = getNombre() || ''
  const navItems = NAV_ITEMS[role] ?? NAV_ITEMS.cliente

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-56 bg-indigo-900 text-white flex flex-col">
        <div className="px-5 py-6 border-b border-indigo-700">
          <span className="text-lg font-bold tracking-tight">MarketMind IA</span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-700 text-white'
                    : 'text-indigo-200 hover:bg-indigo-800 hover:text-white'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-4 border-t border-indigo-700 text-xs text-indigo-300">
          <p className="truncate font-medium text-white">{nombre}</p>
          <p className="capitalize mt-0.5">{role}</p>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Navbar */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <h1 className="text-base font-semibold text-gray-800">MarketMind IA</h1>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-red-600 transition-colors"
          >
            Cerrar sesión
          </button>
        </header>

        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
