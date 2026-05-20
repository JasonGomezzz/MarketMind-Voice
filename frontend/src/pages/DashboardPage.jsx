export default function DashboardPage() {
  const nombre = localStorage.getItem('user_nombre') || 'usuario'
  const role = localStorage.getItem('user_role') || ''

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-1">
        Bienvenido, {nombre}
      </h2>
      <p className="text-sm text-gray-500 capitalize">Rol: {role}</p>

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: 'Campañas activas', value: '—' },
          { label: 'Tokens disponibles', value: '—' },
          { label: 'Generaciones IA', value: '—' },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500">{label}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          </div>
        ))}
      </div>

      <p className="mt-8 text-sm text-gray-400">
        HU8 completará este dashboard con datos reales de campañas.
      </p>
    </div>
  )
}
