import test from 'node:test'
import assert from 'node:assert/strict'
import { getApprovedPublicationCopy } from '../src/services/campaignPublication.js'

test('publication is blocked before approval and after rejection or failure', () => {
  for (const estado of ['borrador', 'pendiente_ia', 'generado', 'enviado', 'pendiente_aprobacion', 'rechazado', 'fracaso', undefined]) {
    assert.equal(getApprovedPublicationCopy({ estado, texto_generado: 'Texto listo' }), null)
  }
  assert.equal(getApprovedPublicationCopy(null), null)
})

test('publication uses only the saved approved copy', () => {
  assert.equal(getApprovedPublicationCopy({ estado: 'aprobado', texto_generado: 'Texto aprobado', draft: 'Texto sin aprobar' }), 'Texto aprobado')
})

test('approved campaigns without usable text cannot prepare a publication', () => {
  for (const texto_generado of ['', '   ', null, undefined, 123]) {
    assert.equal(getApprovedPublicationCopy({ estado: 'aprobado', texto_generado }), null)
  }
})
