import test from 'node:test'
import assert from 'node:assert/strict'
import { canSendTikTok, shouldPollTikTok } from '../src/services/tiktokPublication.js'

const campaign = { estado: 'aprobado', plataformas: ['tiktok'], texto_generado: 'Café', imagen_b64: 'image' }
const ready = { configured: true, outcome: { status: 'not_sent', media_ready: true } }
test('status polling stops on confirmed or terminal outcomes and never starts before an upload', () => {
  for (const value of ['sending', 'processing', 'inbox', 'uncertain']) assert.equal(shouldPollTikTok(value), true)
  for (const value of [undefined, 'not_sent', 'published', 'failed']) assert.equal(shouldPollTikTok(value), false)
})
test('TikTok requires approval, verified media and a destination', () => {
  assert.equal(canSendTikTok(campaign, '1', ready), true)
  assert.equal(canSendTikTok(campaign, '', ready), false)
  assert.equal(canSendTikTok({ ...campaign, estado: 'generado' }, '1', ready), false)
  assert.equal(canSendTikTok(campaign, '1', { ...ready, outcome: { status: 'not_sent', media_ready: false } }), false)
})
test('never resends processing, inbox, published or ambiguous outcomes', () => {
  for (const status of ['processing', 'inbox', 'published', 'uncertain', 'failed']) {
    assert.equal(canSendTikTok(campaign, '1', { ...ready, outcome: { media_ready: true, status } }), false)
  }
})
test('UTF-16 overflow and dirty/error state prevent send', () => {
  assert.equal(canSendTikTok({ ...campaign, texto_generado: '😀'.repeat(2001) }, '1', ready), false)
  assert.equal(canSendTikTok(campaign, '1', { ...ready, error: 'Failed' }), false)
})
