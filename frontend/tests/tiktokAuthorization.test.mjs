import assert from 'node:assert/strict'
import test from 'node:test'
import { rememberTikTokAuthorization, takeTikTokAuthorization } from '../src/services/tiktokAuthorization.js'

function storage() {
  const data = new Map()
  return { getItem: key => data.get(key) ?? null, setItem: (key, value) => data.set(key, value), removeItem: key => data.delete(key) }
}
const url = 'https://www.tiktok.com/v2/auth/authorize/?state=tiktok-state'
test('TikTok completion is local-state-bound and single-use', () => {
  const local = storage()
  rememberTikTokAuthorization(url, local, 1000)
  assert.equal(takeTikTokAuthorization('#provider=x&code=foreign&state=tiktok-state', local, 1000), null)
  assert.deepEqual(takeTikTokAuthorization('#provider=tiktok&state=tiktok-state&code=approved', local, 1001), { state: 'tiktok-state', code: 'approved', denied: false })
  assert.throws(() => takeTikTokAuthorization('#provider=tiktok&state=tiktok-state&code=again', local, 1001))
})
test('TikTok rejects forged, expired, malformed or future browser state', () => {
  for (const [hash, now] of [['#provider=tiktok&state=wrong&code=c', 1001], ['#provider=tiktok&state=tiktok-state&code=c', 602000], ['#provider=tiktok&state=tiktok-state&code=c', 999], ['#provider=tiktok&state=tiktok-state&code=', 1001]]) {
    const local = storage()
    rememberTikTokAuthorization(url, local, 1000)
    assert.throws(() => takeTikTokAuthorization(hash, local, now))
  }
})
test('TikTok refuses unsafe authorization URLs', () => {
  for (const destination of ['https://evil.example/v2/auth/authorize/?state=s', 'http://www.tiktok.com/v2/auth/authorize/?state=s', 'https://www.tiktok.com/wrong?state=s', 'https://user:password@www.tiktok.com/v2/auth/authorize/?state=s', 'https://www.tiktok.com/v2/auth/authorize/']) {
    assert.throws(() => rememberTikTokAuthorization(destination, storage()))
  }
})
test('denial returns a sanitized outcome without a code', () => {
  const local = storage()
  rememberTikTokAuthorization(url, local, 1000)
  assert.deepEqual(takeTikTokAuthorization('#provider=tiktok&state=tiktok-state&error=private-message&code=ignore', local, 1000), { state: 'tiktok-state', code: null, denied: true })
})
