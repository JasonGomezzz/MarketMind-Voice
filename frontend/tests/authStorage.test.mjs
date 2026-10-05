import { beforeEach, test } from 'node:test'
import assert from 'node:assert/strict'
import { startAuthSession, getAuthItem, setAuthItem, clearAuthSession } from '../src/lib/authStorage.js'

function memoryStorage() {
  const items = new Map()
  return { getItem: key => items.get(key) ?? null, setItem: (key, value) => items.set(key, String(value)), removeItem: key => items.delete(key) }
}
beforeEach(() => {
  globalThis.localStorage = memoryStorage()
  globalThis.sessionStorage = memoryStorage()
})
const credentials = { access: 'access', refresh: 'refresh', role: 'marketero', nombre: 'Test' }
test('unmarked login and refresh stay in session storage', () => {
  startAuthSession(credentials)
  setAuthItem('access_token', 'renewed')
  assert.equal(sessionStorage.getItem('access_token'), 'renewed')
  assert.equal(localStorage.getItem('access_token'), null)
  assert.equal(getAuthItem('user_role'), 'marketero')
})
test('remembered login and refresh stay persistent', () => {
  startAuthSession(credentials, true)
  setAuthItem('refresh_token', 'renewed')
  assert.equal(localStorage.getItem('refresh_token'), 'renewed')
  assert.equal(sessionStorage.getItem('access_token'), null)
})
test('switching persistence and logout remove stale credentials but preserve preferences', () => {
  localStorage.setItem('theme', 'dark')
  startAuthSession(credentials, true)
  startAuthSession({ ...credentials, role: 'cliente' })
  assert.equal(localStorage.getItem('user_role'), null)
  assert.equal(getAuthItem('user_role'), 'cliente')
  clearAuthSession()
  assert.equal(getAuthItem('access_token'), null)
  assert.equal(sessionStorage.getItem('user_role'), null)
  assert.equal(localStorage.getItem('theme'), 'dark')
})
