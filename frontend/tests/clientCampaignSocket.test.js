import test from 'node:test'
import assert from 'node:assert/strict'
import { connectClientCampaignSocket } from '../src/services/clientCampaignSocket.js'

function fixture(overrides = {}) {
  const sockets = []
  const timers = []
  const notices = []
  let access = 'access-1'
  let refreshes = 0
  let ended = false
  let connected = 0
  const stop = connectClientCampaignSocket({
    url: 'ws://localhost/ws/client-campaigns',
    getToken: () => access,
    refreshToken: async () => { refreshes++; access = 'access-2'; return access },
    endSession: () => { ended = true },
    onConnected: () => { connected++ },
    onNotification: (message) => notices.push(message),
    createSocket: (url) => {
      const socket = { url, sent: [], readyState: 1, send(data) { this.sent.push(JSON.parse(data)) }, close() { this.readyState = 3 } }
      sockets.push(socket)
      return socket
    },
    schedule: (callback) => { timers.push(callback); return callback },
    cancel: () => {},
    ...overrides,
  })
  return { sockets, timers, notices, stop, refreshes: () => refreshes, ended: () => ended, connected: () => connected }
}

test('token only appears in first frame; reconnection authenticates refreshed token and resynchronizes API', async () => {
  const f = fixture()
  const first = f.sockets[0]
  assert.equal(first.url, 'ws://localhost/ws/client-campaigns')
  first.onopen()
  assert.deepEqual(first.sent, [{ type: 'authenticate', accessToken: 'access-1' }])
  first.onmessage({ data: '{"type":"authenticated"}' })
  await first.onclose({ code: 4408 })
  assert.equal(f.refreshes(), 1)
  await f.timers.at(-1)()
  const second = f.sockets[1]
  second.onopen()
  assert.equal(second.sent[0].accessToken, 'access-2')
  second.onmessage({ data: '{"type":"authenticated"}' })
  assert.equal(f.connected(), 2)
  first.onmessage({ data: '{"type":"campaign_submitted","campaignId":5}' })
  assert.equal(f.notices.length, 0, 'stale socket callbacks are discarded')
  second.onmessage({ data: '{"type":"campaign_submitted","campaignId":5}' })
  assert.equal(f.notices.length, 1)
  f.stop()
})

test('revoked user stops reconnecting and clears session', async () => {
  const f = fixture()
  await f.sockets[0].onclose({ code: 4403 })
  assert.equal(f.ended(), true)
  assert.equal(f.timers.length, 0)
})

test('a transient refresh failure preserves session through repeated reconnects', async () => {
  const f = fixture({ refreshToken: async () => { throw new Error('offline') } })
  await f.sockets[0].onclose({ code: 4401 })
  await f.timers.at(-1)()
  await f.sockets[1].onclose({ code: 4401 })
  assert.equal(f.ended(), false)
  assert.equal(f.timers.length, 2)
  f.stop()
})

test('logout during refresh cannot reopen the socket', async () => {
  let resolve
  const f = fixture({ refreshToken: () => new Promise((done) => { resolve = done }) })
  const closed = f.sockets[0].onclose({ code: 4408 })
  f.stop()
  resolve('access-2')
  await closed
  assert.equal(f.timers.length, 0)
})

test('late revoked-session close never clears a replacement account', async () => {
  let access = 'alice-access'
  const f = fixture({ getToken: () => access })
  access = 'bob-access'
  await f.sockets[0].onclose({ code: 4403 })
  assert.equal(f.ended(), false)
  await f.timers.at(-1)()
  f.sockets[1].onopen()
  assert.equal(f.sockets[1].sent[0].accessToken, 'bob-access')
  f.stop()
})
