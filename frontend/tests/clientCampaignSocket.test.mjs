import test from 'node:test'
import assert from 'node:assert/strict'
import { createClientCampaignSocket } from '../src/services/clientCampaignSocket.js'

async function setup(overrides = {}) {
  const sockets = []
  const events = []
  const timers = []
  class FakeSocket {
    constructor(url) { this.url = url; this.readyState = 0; this.sent = []; sockets.push(this) }
    send(message) { this.sent.push(JSON.parse(message)) }
    close() { this.readyState = 3; this.closed = true }
  }
  const stop = createClientCampaignSocket({
    url: 'ws://localhost:8081/ws/client-campaigns',
    ensureSession: async () => {}, getToken: () => 'access-token',
    onEvent: event => events.push(event), WebSocketImpl: FakeSocket,
    setTimer: (callback, delay) => { const timer = { callback, delay }; timers.push(timer); return timer },
    clearTimer: timer => { if (timer) timer.cancelled = true }, ...overrides,
  })
  await Promise.resolve()
  return { sockets, events, timers, stop }
}

test('authenticates in the first frame with the freshly renewed token, not the URL', async () => {
  let token = 'old-token'
  const state = await setup({ ensureSession: async () => { token = 'fresh-token' }, getToken: () => token })
  const socket = state.sockets[0]
  socket.onopen()
  assert.equal(socket.url, 'ws://localhost:8081/ws/client-campaigns')
  assert.deepEqual(socket.sent, [{ type: 'authenticate', token: 'fresh-token' }])
  state.stop()
})

test('ignores campaign events until authenticated and ignores malformed or unknown frames', async () => {
  const state = await setup()
  const socket = state.sockets[0]
  const event = { type: 'campaign_submitted', campaign: { id: 1 } }
  socket.onmessage({ data: JSON.stringify(event) })
  assert.equal(state.events.length, 0)
  socket.onmessage({ data: '{"type":"authenticated"}' })
  socket.onmessage({ data: 'invalid-json' })
  socket.onmessage({ data: '{"type":"unknown","campaign":{"id":2}}' })
  socket.onmessage({ data: JSON.stringify(event) })
  assert.deepEqual(state.events, [event])
  state.stop()
})

test('does not endlessly reconnect after an authentication rejection', async () => {
  const state = await setup()
  state.sockets[0].onclose({ code: 1008 })
  assert.equal(state.timers.length, 0)
  state.stop()
})

test('revalidates the HTTP session after an authenticated socket expires', async () => {
  let checks = 0
  const state = await setup({ ensureSession: async () => { checks++ } })
  state.sockets[0].onmessage({ data: '{"type":"authenticated"}' })
  state.sockets[0].onclose({ code: 1008 })
  await state.timers[0].callback()
  assert.equal(checks, 2)
  assert.equal(state.sockets.length, 2)
  state.stop()
})

test('cleanup closes the socket and cancels reconnection', async () => {
  const state = await setup()
  state.sockets[0].onclose({ code: 1006 })
  state.stop()
  assert.equal(state.sockets[0].closed, true)
  assert.equal(state.timers[0].cancelled, true)
  await state.timers[0].callback()
  assert.equal(state.sockets.length, 1)
})

test('missing token does not establish a socket', async () => {
  const state = await setup({ getToken: () => null })
  assert.equal(state.sockets.length, 0)
  state.stop()
})

test('unmounting during session validation does not open a late socket', async () => {
  let resolve
  const pending = new Promise(done => { resolve = done })
  const state = await setup({ ensureSession: () => pending })
  state.stop()
  resolve()
  await Promise.resolve()
  assert.equal(state.sockets.length, 0)
})
