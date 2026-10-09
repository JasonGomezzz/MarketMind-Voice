import test from 'node:test'
import assert from 'node:assert/strict'
import { getPlatformCopy, getApprovedPublicationCopy } from '../src/services/campaignPublication.js'
import { canConfirmFacebookPublication } from '../src/services/facebookPublication.js'

test('each platform publishes its saved approved copy, preserving legacy campaigns', () => {
  const campaign = { estado: 'aprobado', texto_generado: 'Base', plataformas: ['twitter', 'facebook'],
    textos_por_plataforma: { twitter: 'Breve', facebook: 'Amplio' }, imagen_b64: 'png' }
  assert.equal(getApprovedPublicationCopy(campaign, 'twitter'), 'Breve')
  assert.equal(getApprovedPublicationCopy(campaign, 'facebook'), 'Amplio')
  assert.equal(getPlatformCopy(campaign, 'instagram'), 'Base')
  assert.equal(getApprovedPublicationCopy({ ...campaign, estado: 'generado' }, 'twitter'), null)
  assert.equal(getApprovedPublicationCopy({ ...campaign, textos_por_plataforma: { twitter: '' } }, 'twitter'), null)
  assert.equal(canConfirmFacebookPublication({ ...campaign, texto_generado: 'a'.repeat(60001) }, '1'), true)
  assert.equal(canConfirmFacebookPublication({ ...campaign, textos_por_plataforma: { facebook: 'a'.repeat(60001) } }, '1'), false)
})
