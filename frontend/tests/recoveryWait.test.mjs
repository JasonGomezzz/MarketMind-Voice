import test from 'node:test'
import assert from 'node:assert/strict'
import { createRecoveryWait } from '../src/lib/recoveryWait.js'

test('wait deadline follows server seconds and normalizes email', () => {
  assert.deepEqual(createRecoveryWait(' USER@Example.com ', '30', 1000), { email: 'user@example.com', startedAt: 1000, until: 31000 })
})
test('invalid wait values fall back safely to sixty seconds', () => {
  for (const seconds of [undefined, 'bad', -1, 0, Infinity]) {
    assert.equal(createRecoveryWait('user@example.com', seconds, 1000).until, 61000)
  }
})
