import test from 'node:test'
import assert from 'node:assert/strict'
import { etiquetaEstado, resumenSolicitud, validarCreditos } from '../src/services/creditRequests.js'

test('validarCreditos accepts whole numbers between 1 and 10000 only', () => {
  assert.equal(validarCreditos('100'), null)
  assert.equal(validarCreditos(1), null)
  assert.equal(validarCreditos('10000'), null)
  assert.match(validarCreditos('0'), /entre 1/)
  assert.match(validarCreditos('10001'), /entre 1/)
  assert.match(validarCreditos('1.5'), /entero/)
  assert.match(validarCreditos(''), /entero/)
  assert.match(validarCreditos('-5'), /entero/)
})

test('etiquetaEstado names every request state in Spanish', () => {
  assert.equal(etiquetaEstado('pendiente'), 'Pendiente de revisión')
  assert.equal(etiquetaEstado('aprobada'), 'Aprobada')
  assert.equal(etiquetaEstado('rechazada'), 'Rechazada')
  assert.equal(etiquetaEstado(undefined), '—')
})

test('resumenSolicitud explains the latest request to the marketer', () => {
  assert.equal(resumenSolicitud(null), '')
  assert.match(resumenSolicitud({ estado: 'pendiente' }), /pendiente/)
  assert.equal(
    resumenSolicitud({ estado: 'aprobada', creditos_otorgados: 50 }),
    'Última solicitud aprobada: +50 créditos.',
  )
  assert.equal(
    resumenSolicitud({ estado: 'rechazada', nota_resolucion: 'Sin presupuesto' }),
    'Última solicitud rechazada. Motivo: Sin presupuesto',
  )
})
