import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import api from '../services/api'

const PERIODS = [
  { value: 'week', label: 'Semana' },
  { value: 'month', label: 'Mes' },
  { value: 'quarter', label: 'Trimestre' },
]

const ESTADO_COLORS = {
  borrador: '#94a3b8',
  pendiente_ia: '#fbbf24',
  generado: '#60a5fa',
  pendiente_aprobacion: '#a78bfa',
  aprobado: '#34d399',
  rechazado: '#f87171',
}

const ESTADO_LABELS = {
  borrador: 'Borrador',
  pendiente_ia: 'Pendiente IA',
  generado: 'Generado',
  pendiente_aprobacion: 'Pend. Aprobación',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
}

function KpiCard({ label, value, sub }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-1">
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</span>
      <span className="text-3xl font-bold text-gray-900">{value ?? '—'}</span>
      {sub && <span className="text-xs text-gray-400">{sub}</span>}
    </div>
  )
}

export default function AnalyticsPage() {
  const [period, setPeriod] = useState('month')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api
      .get('/api/admin/analytics/', { params: { period } })
      .then((res) => setData(res.data.data))
      .catch(() => setError('No se pudo cargar el analytics. Verificá tu sesión.'))
      .finally(() => setLoading(false))
  }, [period])

  const pieData = data
    ? data.estados_globales
        .filter((e) => e.total > 0)
        .map((e) => ({
          name: ESTADO_LABELS[e.estado] ?? e.estado,
          value: e.total,
          color: ESTADO_COLORS[e.estado] ?? '#cbd5e1',
        }))
    : []

  return (
    <div className="space-y-6">
      {/* Header + selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Analytics de Campañas</h2>
        <div className="flex gap-2">
          {PERIODS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setPeriod(value)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                period === value
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="text-center py-20 text-gray-400 text-sm">Cargando analytics…</div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && data && (
        <>
          {/* KPI cards */}
          <div className="grid grid-cols-3 gap-4">
            <KpiCard
              label="Total campañas"
              value={data.kpi.total_campanas}
              sub={`Últimos ${period === 'week' ? '7 días' : period === 'month' ? '30 días' : '90 días'}`}
            />
            <KpiCard
              label="Tasa de aprobación"
              value={`${data.kpi.tasa_aprobacion}%`}
              sub="Campañas aprobadas / total"
            />
            <KpiCard
              label="Tiempo prom. aprobación"
              value={data.kpi.tiempo_promedio_aprobacion_dias != null ? `${data.kpi.tiempo_promedio_aprobacion_dias}d` : '—'}
              sub="Días desde creación a aprobado"
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-2 gap-6">
            {/* BarChart — campañas por marketero */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">Campañas por Marketero</h3>
              {data.campanas_por_marketero.length === 0 ? (
                <p className="text-sm text-gray-400 py-8 text-center">Sin datos en este periodo</p>
              ) : (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={data.campanas_por_marketero} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="marketero" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="total" name="Campañas" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* PieChart — distribución de estados */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">Distribución de Estados</h3>
              {pieData.length === 0 ? (
                <p className="text-sm text-gray-400 py-8 text-center">Sin datos en este periodo</p>
              ) : (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      dataKey="value"
                      nameKey="name"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {pieData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend iconType="circle" iconSize={10} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
