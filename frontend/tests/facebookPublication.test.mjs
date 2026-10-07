import assert from 'node:assert/strict'
import test from 'node:test'
import { canConfirmFacebookPublication } from '../src/services/facebookPublication.js'

const approved = { estado: 'aprobado', texto_generado: 'Copy aprobado', imagen_b64: 'image', plataformas: ['facebook'] }

test('Facebook requires approved saved text, image, destination and platform', () => {
  assert.equal(canConfirmFacebookPublication(approved, '1'), true)
  for (const campaign of [
    { ...approved, estado: 'generado' }, { ...approved, estado: 'rechazado' },
    { ...approved, texto_generado: '' }, { ...approved, imagen_b64: '' },
    { ...approved, plataformas: ['instagram'] }, { ...approved, texto_generado: 'x'.repeat(60001) },
  ]) assert.equal(canConfirmFacebookPublication(campaign, '1'), false)
  assert.equal(canConfirmFacebookPublication(approved, ''), false)
  assert.equal(canConfirmFacebookPublication({ ...approved, plataformas: [], plataforma: 'facebook' }, '1'), true)
})

test('loading, checking, busy, errors and recorded attempts cannot post', () => {
  for (const state of [{ loading: true }, { checking: true }, { busy: true }, { error: 'network' },
    ...['published', 'publishing', 'uncertain', 'failed'].map(status => ({ outcome: { status } })),
  ]) assert.equal(canConfirmFacebookPublication(approved, '1', state), false)
  assert.equal(canConfirmFacebookPublication(approved, '1', { outcome: { status: 'not_published' } }), true)
})
