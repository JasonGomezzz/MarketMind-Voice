import assert from 'node:assert/strict'
import test from 'node:test'
import { rememberXAuthorization, takeXAuthorization } from '../src/services/xAuthorization.js'

function storage() {
  const values = new Map()
  return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) }
}

const url = 'https://x.com/i/oauth2/authorize?state=x-state'

test('X callback verifies local state and is single-use', () => {
  const local = storage()
  rememberXAuthorization(url, local)
  assert.equal(takeXAuthorization('#provider=facebook&state=x-state&result=connected', local), null)
  assert.equal(takeXAuthorization('#provider=x&state=x-state&result=connected', local), true)
  assert.throws(() => takeXAuthorization('#provider=x&state=x-state&result=connected', local))
})

test('X rejects another destination or stale callback', () => {
  const local = storage()
  assert.throws(() => rememberXAuthorization('https://evil.example/i/oauth2/authorize?state=x-state', local))
  rememberXAuthorization(url, local)
  assert.throws(() => takeXAuthorization('#provider=x&state=wrong&result=connected', local))
  rememberXAuthorization(url, local)
  assert.throws(() => takeXAuthorization('#provider=x&state=x-state&result=connected', local, Date.now() + 601000))
})
