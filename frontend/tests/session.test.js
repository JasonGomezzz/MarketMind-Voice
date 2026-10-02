import test, { beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import axios from 'axios'
import { refreshAccessToken, clearSession, attachSessionInterceptors } from '../src/services/session.js'

beforeEach(() => {
  const values = new Map([['access_token', 'old-access'], ['refresh_token', 'old-refresh']])
  globalThis.localStorage = { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: (key) => values.delete(key) }
  globalThis.window = { dispatchEvent() {}, location: { href: '' } }
})

test('socket and both APIs share one refresh; a stale 401 reuses its rotated token', async () => {
  let calls = 0
  let complete
  axios.post = () => { calls++; return new Promise((resolve) => { complete = resolve }) }
  const first = refreshAccessToken('old-access')
  const second = refreshAccessToken('old-access')
  assert.equal(first, second)
  complete({ data: { access: 'new-access', refresh: 'new-refresh' } })
  assert.equal(await first, 'new-access')
  assert.equal(await refreshAccessToken('old-access'), 'new-access')
  assert.equal(calls, 1)
  assert.equal(localStorage.getItem('refresh_token'), 'new-refresh')
})

test('transport or 5xx failure preserves tokens; invalid refresh clears them', async () => {
  axios.post = async () => { throw { response: { status: 503 } } }
  await assert.rejects(refreshAccessToken('old-access'))
  assert.equal(localStorage.getItem('access_token'), 'old-access')
  axios.post = async () => { throw { response: { status: 401 } } }
  await assert.rejects(refreshAccessToken('old-access'))
  assert.equal(localStorage.getItem('access_token'), null)
  assert.equal(window.location.href, '/login')
})

test('refresh completing after logout never restores the session', async () => {
  let complete
  axios.post = () => new Promise((resolve) => { complete = resolve })
  const pending = refreshAccessToken('old-access')
  clearSession({ redirect: false })
  complete({ data: { access: 'late-access', refresh: 'late-refresh' } })
  await assert.rejects(pending)
  assert.equal(localStorage.getItem('access_token'), null)
})

test('Django and Spring interceptors retry simultaneous 401s with one rotation', async () => {
  let refreshes = 0
  axios.post = async () => { refreshes++; return { data: { access: 'new-access', refresh: 'new-refresh' } } }
  const client = () => {
    const api = axios.create({ adapter: async (config) => {
      if (config.headers.Authorization === 'Bearer old-access') {
        throw { config, response: { status: 401 } }
      }
      return { config, status: 200, data: 'authorized' }
    } })
    attachSessionInterceptors(api)
    return api
  }
  const responses = await Promise.all([client().get('/api/campaigns/'), client().get('/api/v1/campaigns/mine')])
  assert.deepEqual(responses.map((response) => response.data), ['authorized', 'authorized'])
  assert.equal(refreshes, 1)
})
