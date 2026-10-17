import test from 'node:test'
import assert from 'node:assert/strict'
import {
  alcanceDelRol,
  estadoPublicacion,
  etiquetaRed,
  filtrarPublicaciones,
  formatoMetrica,
  haceCuanto,
  leerRetornoMeta,
  mensajeMotivoRetornoMeta,
  metricasDeRed,
  publicacionAtascada,
  puedeReintentar,
  serieMensual,
  textoCuentasConectadas,
} from '../src/services/social.js'

test('leerRetornoMeta reads code and state from the fragment and reports every error', () => {
  assert.deepEqual(leerRetornoMeta('#code=AQB%2Fx&state=abc'), { tipo: 'codigo', code: 'AQB/x', state: 'abc' })
  assert.deepEqual(leerRetornoMeta('#error=cancelado'), { tipo: 'error', motivo: 'cancelado' })
  assert.deepEqual(leerRetornoMeta('#code=solo-codigo'), { tipo: 'error', motivo: 'sin_datos' })
  assert.deepEqual(leerRetornoMeta(''), { tipo: 'error', motivo: 'sin_datos' })
  assert.deepEqual(leerRetornoMeta(undefined), { tipo: 'error', motivo: 'sin_datos' })
})

test('mensajeMotivoRetornoMeta explains each way back from Meta in Spanish', () => {
  assert.match(mensajeMotivoRetornoMeta('cancelado'), /Cancelaste/)
  assert.match(mensajeMotivoRetornoMeta('sesion'), /caducó o ya se usó/)
  assert.equal(mensajeMotivoRetornoMeta('raro'), 'No se pudo conectar la cuenta.')
  assert.equal(textoCuentasConectadas(1), 'Se conectó 1 cuenta.')
  assert.equal(textoCuentasConectadas(2), 'Se conectaron 2 cuentas.')
})

test('puedeReintentar only offers publishing for approved campaigns with attempts left', () => {
  assert.equal(puedeReintentar({ estado: 'fallido', intentos: 1 }, 'aprobado'), true)
  assert.equal(puedeReintentar({ estado: 'esperando_aprobacion', intentos: 0 }, 'aprobado'), true)
  assert.equal(puedeReintentar({ estado: 'fallido', intentos: 3 }, 'aprobado'), false)
  assert.equal(puedeReintentar({ estado: 'publicado', intentos: 1 }, 'aprobado'), false)
  assert.equal(puedeReintentar({ estado: 'esperando_aprobacion', intentos: 0 }, 'pendiente_aprobacion'), false)
})

test('a publication stuck in publicando for more than 5 minutes can be retried', () => {
  const ahora = new Date('2026-10-16T12:00:00Z')
  const atascada = { estado: 'publicando', intentos: 3, publicando_desde: '2026-10-16T11:54:00Z' }
  const reciente = { estado: 'publicando', intentos: 1, publicando_desde: '2026-10-16T11:58:00Z' }
  assert.equal(publicacionAtascada(atascada, ahora), true)
  assert.equal(publicacionAtascada(reciente, ahora), false)
  assert.equal(publicacionAtascada({ estado: 'publicando' }, ahora), false)
  assert.equal(puedeReintentar(atascada, 'aprobado', ahora), true)
  assert.equal(puedeReintentar(reciente, 'aprobado', ahora), false)
  assert.equal(puedeReintentar(atascada, 'pendiente_aprobacion', ahora), false)
})

test('labels fall back to the raw value for unknown networks and states', () => {
  assert.equal(etiquetaRed('instagram'), 'Instagram')
  assert.equal(etiquetaRed('tiktok'), 'tiktok')
  assert.equal(estadoPublicacion('publicado').tono, 'ok')
  assert.equal(estadoPublicacion('fallido').tono, 'error')
  assert.equal(estadoPublicacion('nuevo').texto, 'nuevo')
})

test('formatoMetrica never turns a missing Meta value into zero', () => {
  assert.equal(formatoMetrica(null), 'sin dato')
  assert.equal(formatoMetrica(undefined), 'sin dato')
  assert.equal(formatoMetrica(0), '0')
  assert.equal(formatoMetrica(12500), (12500).toLocaleString('es-PE'))
})

test('metricasDeRed names Facebook likes as reactions and hides saves', () => {
  assert.equal(metricasDeRed('facebook').principales[0][1], 'Reacciones')
  assert.ok(!metricasDeRed('facebook').secundarias.some(([campo]) => campo === 'guardados'))
  assert.ok(metricasDeRed('instagram').secundarias.some(([campo]) => campo === 'guardados'))
})

test('serieMensual fills the last six months and keeps the counts of the summary', () => {
  const serie = serieMensual([{ mes: '2026-10', instagram: 2, facebook: 1 }, { mes: '2026-08', instagram: 1, facebook: 0 }],
    'instagram', new Date(2026, 9, 6))
  assert.deepEqual(serie.map((m) => m.mes), ['2026-05', '2026-06', '2026-07', '2026-08', '2026-09', '2026-10'])
  assert.deepEqual(serie.map((m) => m.total), [0, 0, 0, 1, 0, 2])
  assert.equal(serie.at(-1).etiqueta, 'oct')
  assert.equal(serieMensual([], 'facebook', new Date(2026, 0, 15))[0].mes, '2025-08')
})

test('filtrarPublicaciones combines network and state filters', () => {
  const lista = [
    { id: 1, red: 'instagram', estado: 'publicado' },
    { id: 2, red: 'facebook', estado: 'publicado' },
    { id: 3, red: 'instagram', estado: 'fallido' },
  ]
  assert.deepEqual(filtrarPublicaciones(lista).map((p) => p.id), [1, 2, 3])
  assert.deepEqual(filtrarPublicaciones(lista, { red: 'instagram' }).map((p) => p.id), [1, 3])
  assert.deepEqual(filtrarPublicaciones(lista, { red: 'instagram', estado: 'publicado' }).map((p) => p.id), [1])
})

test('haceCuanto and alcanceDelRol speak plain Spanish', () => {
  const ahora = new Date('2026-10-06T19:00:00Z')
  assert.equal(haceCuanto(null, ahora), null)
  assert.equal(haceCuanto('2026-10-06T18:58:30Z', ahora), 'hace 1 min')
  assert.equal(haceCuanto('2026-10-06T16:00:00Z', ahora), 'hace 3 h')
  assert.equal(haceCuanto('2026-10-05T18:00:00Z', ahora), 'hace 1 día')
  assert.match(alcanceDelRol('marketero'), /tus clientes/)
  assert.match(alcanceDelRol('desconocido'), /tus publicaciones/)
})
