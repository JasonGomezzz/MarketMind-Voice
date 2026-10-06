import test from 'node:test'
import assert from 'node:assert/strict'
import { estadoPublicacion, etiquetaRed, mensajeRetornoMeta, puedeReintentar } from '../src/services/social.js'

test('mensajeRetornoMeta explains every way back from Meta and ignores normal visits', () => {
  assert.equal(mensajeRetornoMeta(new URLSearchParams('')), null)
  assert.deepEqual(mensajeRetornoMeta(new URLSearchParams('redes=conectadas&cuentas=2')), {
    tipo: 'ok',
    texto: 'Se conectaron 2 cuentas.',
  })
  assert.equal(mensajeRetornoMeta(new URLSearchParams('redes=conectadas&cuentas=1')).texto, 'Se conectó 1 cuenta.')
  assert.equal(mensajeRetornoMeta(new URLSearchParams('redes=cancelado')).tipo, 'info')
  assert.match(mensajeRetornoMeta(new URLSearchParams('redes=error&motivo=sin_paginas')).texto, /página/)
  assert.equal(mensajeRetornoMeta(new URLSearchParams('redes=error&motivo=raro')).tipo, 'error')
})

test('puedeReintentar only offers publishing for approved campaigns with attempts left', () => {
  assert.equal(puedeReintentar({ estado: 'fallido', intentos: 1 }, 'aprobado'), true)
  assert.equal(puedeReintentar({ estado: 'esperando_aprobacion', intentos: 0 }, 'aprobado'), true)
  assert.equal(puedeReintentar({ estado: 'fallido', intentos: 3 }, 'aprobado'), false)
  assert.equal(puedeReintentar({ estado: 'publicado', intentos: 1 }, 'aprobado'), false)
  assert.equal(puedeReintentar({ estado: 'esperando_aprobacion', intentos: 0 }, 'pendiente_aprobacion'), false)
})

test('labels fall back to the raw value for unknown networks and states', () => {
  assert.equal(etiquetaRed('instagram'), 'Instagram')
  assert.equal(etiquetaRed('tiktok'), 'tiktok')
  assert.equal(estadoPublicacion('publicado').tono, 'ok')
  assert.equal(estadoPublicacion('fallido').tono, 'error')
  assert.equal(estadoPublicacion('nuevo').texto, 'nuevo')
})
