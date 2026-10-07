import assert from 'node:assert/strict'
import test from 'node:test'
import { rememberFacebookAuthorization, takeFacebookAuthorization } from '../src/services/facebookAuthorization.js'
import { rememberInstagramAuthorization, takeInstagramAuthorization } from '../src/services/instagramAuthorization.js'

function storage() {
  const values = new Map()
  return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) }
}
const url = 'https://www.facebook.com/v23.0/dialog/oauth?state=fb-state'
const callback = '#provider=facebook&state=fb-state&code=code'

test('Facebook callback is single-use and isolated from Instagram', () => {
  const local = storage()
  rememberFacebookAuthorization(url, local)
  rememberInstagramAuthorization('https://www.instagram.com/oauth/authorize?state=ig-state', local)
  assert.equal(takeInstagramAuthorization('', callback, local), null)
  assert.deepEqual(takeFacebookAuthorization('', callback, local), { state: 'fb-state', code: 'code', denied: false })
  assert.throws(() => takeFacebookAuthorization('', callback, local))
  assert.deepEqual(takeInstagramAuthorization('', '#state=ig-state&code=ig-code', local), { state: 'ig-state', code: 'ig-code', denied: false })
})

test('Facebook rejects mismatched, expired and unsafe destinations', () => {
  const local = storage()
  assert.throws(() => rememberFacebookAuthorization('https://evil.example/v23.0/dialog/oauth?state=s', local))
  assert.throws(() => rememberFacebookAuthorization('https://www.facebook.com/fake?state=s', local))
  assert.throws(() => rememberFacebookAuthorization('https://www.facebook.com/v23.0/dialog/oauth', local))
  rememberFacebookAuthorization(url, local)
  assert.throws(() => takeFacebookAuthorization('', '#provider=facebook&state=wrong&code=code', local))
  rememberFacebookAuthorization(url, local)
  assert.throws(() => takeFacebookAuthorization('', callback, local, Date.now() + 601000))
})

test('denial is sanitized and foreign callbacks leave Facebook state untouched', () => {
  const local = storage()
  rememberFacebookAuthorization(url, local)
  assert.equal(takeFacebookAuthorization('', '#code=ig-code&state=ig-state', local), null)
  assert.deepEqual(takeFacebookAuthorization('', '#provider=facebook&state=fb-state&error=access_denied', local), {
    state: 'fb-state', code: null, denied: true,
  })
})
