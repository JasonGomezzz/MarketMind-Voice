import test from 'node:test'
import assert from 'node:assert/strict'
import { monthLabel, monthlyChartData } from '../src/services/publicationStatistics.js'

test('months use unambiguous Spanish labels in calendar order', () => {
  assert.deepEqual(Array.from({ length: 12 }, (_, i) => monthLabel(`2026-${String(i + 1).padStart(2, '0')}`)),
    ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'])
  for (const value of [null, '', '2026-00', '2026-13', '2026-1']) assert.equal(monthLabel(value), '—')
})

test('chart labels preserve actual zeroes and missing measurements', () => {
  const rows = [{ month: '2026-01', facebook: 0 }, { month: '2026-02', facebook: null }]
  const result = monthlyChartData(rows)
  assert.equal(result[0].facebook, 0)
  assert.equal(result[1].facebook, null)
  assert.equal(result[0].name, 'Ene')
  assert.equal(rows[0].name, undefined)
})
