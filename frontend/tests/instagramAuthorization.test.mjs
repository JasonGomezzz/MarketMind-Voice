import assert from 'node:assert/strict'
import test from 'node:test'
import { rememberInstagramAuthorization, takeInstagramAuthorization } from '../src/services/instagramAuthorization.js'

function storage() {
  const values = new Map()
  return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) }
}
const url = 'https://www.instagram.com/oauth/authorize?state=unique-state'

test('local callback accepts the saved state from a fragment exactly once', () => {
  const local = storage()
  assert.equal(rememberInstagramAuthorization(url, local), url)
  assert.deepEqual(takeInstagramAuthorization('', '#code=short-code&state=unique-state', local), {
    code: 'short-code', state: 'unique-state', denied: false,
  })
  assert.throws(() => takeInstagramAuthorization('', '#code=short-code&state=unique-state', local))
})

test('mismatched, missing and expired browser states are rejected', () => {
  const local = storage()
  rememberInstagramAuthorization(url, local)
  assert.throws(() => takeInstagramAuthorization('', '#code=code&state=other-state', local))
  assert.throws(() => takeInstagramAuthorization('?code=code&state=unique-state', '', local))
  rememberInstagramAuthorization(url, local)
  assert.throws(() => takeInstagramAuthorization('?code=code&state=unique-state', '', local, Date.now() + 601000))
})

test('denial returns to the initiating page without exchanging a code', () => {
  const local = storage()
  rememberInstagramAuthorization(url, local)
  assert.deepEqual(takeInstagramAuthorization('', '#error=access_denied&state=unique-state', local), {
    code: null, state: 'unique-state', denied: true,
  })
  assert.equal(takeInstagramAuthorization('', '', local), null)
})

test('untrusted authorization destinations cannot receive the session', () => {
  const local = storage()
  assert.throws(() => rememberInstagramAuthorization('https://evil.example/oauth/authorize?state=secret', local))
  assert.throws(() => rememberInstagramAuthorization('https://www.instagram.com/fake?state=secret', local))
  assert.throws(() => rememberInstagramAuthorization('https://www.instagram.com/oauth/authorize', local))
})
