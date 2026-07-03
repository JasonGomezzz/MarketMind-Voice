import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Megaphone,
  BarChart3,
  Users,
  LogOut,
  LifeBuoy,
  Coins,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

/**
 * Navegación por rol. Etiquetas en español, sin nav pública dentro del panel.
 * (Se conserva la separación de roles que ya existía en la lógica.)
 */
const NAV_ITEMS = {
  marketero: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/campaigns', label: 'Campañas', icon: Megaphone },
  ],
  superadmin: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/campaigns', label: 'Campañas', icon: Megaphone },
    { to: '/admin', label: 'Usuarios', icon: Users },
    { to: '/admin/analytics', label: 'Analytics', icon: BarChart3 },
  ],
  cliente: [{ to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }],
}

const ROLE_LABEL = {
  superadmin: 'SuperAdmin',
  marketero: 'Marketero',
  cliente: 'Cliente',
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

  const iniciales =
    nombre
      .split(' ')
      .map((p) => p[0])
      .slice(0, 2)
      .join('')
      .toUpperCase() || 'U'

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar claro Lumina Creative */}
      <aside className="flex w-64 flex-col border-r border-outline-variant bg-surface-container-low">
        <div className="px-6 py-6">
          <span className="text-xl font-bold tracking-tight text-primary">MarketMind IA</span>
        </div>

        <nav className="flex-1 space-y-1 px-3">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/dashboard'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-secondary-container text-on-secondary-container'
                    : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                }`
              }
            >
              <Icon className="h-5 w-5" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Token Balance */}
        <div className="px-4 py-4">
          <div className="rounded-xl border border-primary/10 bg-primary/5 p-4">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-primary/70">
              Créditos de IA
            </p>
            <div className="flex items-center gap-2">
              <Coins className="h-5 w-5 text-primary" />
              <span className="text-2xl font-bold text-primary tabular-nums">—</span>
            </div>
          </div>
        </div>

        {/* Usuario + rol + acciones */}
        <div className="mx-4 mb-4 space-y-3 border-t border-outline-variant pt-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-sm font-bold text-on-primary">
              {iniciales}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-on-surface">{nombre || 'Usuario'}</p>
              <span className="inline-block rounded-full bg-primary-fixed px-2 py-0.5 text-xs font-semibold text-on-primary-fixed">
                {ROLE_LABEL[role] ?? role}
              </span>
            </div>
          </div>
          <div className="space-y-1">
            <a
              href="#"
              className="flex items-center gap-3 px-1 py-1.5 text-sm text-on-surface-variant transition-colors hover:text-primary"
            >
              <LifeBuoy className="h-4 w-4" />
              Soporte
            </a>
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-3 px-1 py-1.5 text-sm text-on-surface-variant transition-colors hover:text-error"
            >
              <LogOut className="h-4 w-4" />
              Cerrar sesión
            </button>
          </div>
        </div>
      </aside>

      {/* Contenido */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <main className="flex-1 overflow-auto bg-background p-8">
          <div className="mx-auto max-w-[1440px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
