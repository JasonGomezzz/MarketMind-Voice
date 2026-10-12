const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

export function monthLabel(value) {
  if (typeof value !== 'string' || !/^\d{4}-(0[1-9]|1[0-2])$/.test(value)) return '—'
  return months[Number(value.slice(5)) - 1]
}

export function monthlyChartData(rows = []) {
  return rows.map(row => ({ ...row, name: monthLabel(row.month) }))
}
