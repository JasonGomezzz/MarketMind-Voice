import assert from 'node:assert/strict'
import test from 'node:test'
import { canConfirmXPublication } from '../src/services/xPublication.js'

test('a summary requires explicit marketer review and the validated draft identity', () => {
  const campaign = { estado: 'aprobado', plataforma: 'twitter', texto_generado: 'Copy largo', imagen_b64: 'png' }
  const state = { summaryId: 'draft-1', summaryConfirmed: false,
    outcome: { status: 'not_published', accountId: '1', summaryId: 'draft-1', text_validation: { valid: true } } }
  assert.equal(canConfirmXPublication(campaign, '1', state), false)
  assert.equal(canConfirmXPublication(campaign, '1', { ...state, summaryConfirmed: true }), true)
  assert.equal(canConfirmXPublication(campaign, '1', { ...state, summaryConfirmed: true, summaryId: 'different' }), false)
  assert.equal(canConfirmXPublication(campaign, '1', { ...state, summaryConfirmed: true, busy: true }), false)
})

const campaign = { estado: 'aprobado', texto_generado: 'Texto aprobado', imagen_b64: 'image', plataformas: ['twitter'] }
const outcome = { status: 'not_published', accountId: '7', text_validation: { valid: true } }

test('X requires approval, image, selected destination and completed validation', () => {
  assert.equal(canConfirmXPublication(campaign, '7', { outcome }), true)
  for (const key of ['loading', 'checking', 'busy', 'error']) {
    assert.equal(canConfirmXPublication(campaign, '7', { outcome, [key]: true }), false)
  }
  assert.equal(canConfirmXPublication({ ...campaign, estado: 'generado' }, '7', { outcome }), false)
  assert.equal(canConfirmXPublication({ ...campaign, imagen_b64: null }, '7', { outcome }), false)
  assert.equal(canConfirmXPublication({ ...campaign, plataformas: ['facebook'] }, '7', { outcome }), false)
  assert.equal(canConfirmXPublication(campaign, '', { outcome }), false)
  assert.equal(canConfirmXPublication(campaign, '7', {}), false)
  assert.equal(canConfirmXPublication(campaign, '8', { outcome }), false)
  assert.equal(canConfirmXPublication(campaign, '7', { outcome: { ...outcome, text_validation: { valid: false } } }), false)
})

test('X cannot resend a successful or uncertain post; confirmed rejections allow explicit retry', () => {
  for (const status of ['published', 'preparing', 'publishing', 'uncertain']) {
    assert.equal(canConfirmXPublication(campaign, '7', { outcome: { ...outcome, status } }), false)
  }
  assert.equal(canConfirmXPublication(campaign, '7', { outcome: { ...outcome, status: 'failed' } }), true)
})
