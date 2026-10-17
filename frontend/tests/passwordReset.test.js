import test from 'node:test'
import assert from 'node:assert/strict'
import {
  formatoEspera,
  mensajeDeError,
  segundosDeEspera,
  tokenDesdeHash,
  validarNuevaPassword,
} from '../src/services/passwordReset.js'

test('tokenDesdeHash reads the token from the link fragment only', () => {
  assert.equal(tokenDesdeHash('#token=abc-_123'), 'abc-_123')
  assert.equal(tokenDesdeHash('token=xyz'), 'xyz')
  assert.equal(tokenDesdeHash(''), '')
  assert.equal(tokenDesdeHash('#otro=1'), '')
  assert.equal(tokenDesdeHash(undefined), '')
})

test('validarNuevaPassword checks length and confirmation before calling the API', () => {
  assert.match(validarNuevaPassword('corta', 'corta'), /al menos 8/)
  assert.equal(validarNuevaPassword('NuevaClave2026!', 'otra'), 'Las contraseñas no coinciden.')
  assert.equal(validarNuevaPassword('NuevaClave2026!', 'NuevaClave2026!'), null)
})

test('segundosDeEspera uses the body, then Retry-After, and ignores other errors', () => {
  assert.equal(segundosDeEspera({ response: { status: 429, data: { data: { retry_after: 42 } } } }), 42)
  assert.equal(segundosDeEspera({ response: { status: 429, data: {}, headers: { 'retry-after': '7' } } }), 7)
  assert.equal(segundosDeEspera({ response: { status: 429, data: {}, headers: {} } }), 60)
  assert.equal(segundosDeEspera({ response: { status: 400, data: {} } }), 0)
  assert.equal(segundosDeEspera(new Error('red')), 0)
})

test('mensajeDeError prefers the API message and explains network failures', () => {
  assert.equal(mensajeDeError({ response: { data: { message: 'Ingresa un correo válido.' } } }), 'Ingresa un correo válido.')
  assert.match(mensajeDeError({ response: { data: {} } }), /No se pudo procesar/)
  assert.match(mensajeDeError(new Error('Network Error')), /conectar/)
})

test('formatoEspera shows seconds under a minute and rounds minutes up', () => {
  assert.equal(formatoEspera(45), '45 s')
  assert.equal(formatoEspera(61), '2 min')
})
