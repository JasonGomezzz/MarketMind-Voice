const PENDING_KEY = 'instagram_pending_authorization'

export function rememberInstagramAuthorization(url, storage = sessionStorage) {
  const destination = new URL(url)
  const state = destination.searchParams.get('state')
  if (destination.origin !== 'https://www.instagram.com' || destination.pathname !== '/oauth/authorize' || !state) {
    throw new Error('Invalid Instagram destination')
  }
  storage.setItem(PENDING_KEY, JSON.stringify({ state, createdAt: Date.now() }))
  return destination.href
}

export function takeInstagramAuthorization(search, hash, storage = sessionStorage, now = Date.now()) {
  const query = new URLSearchParams(hash.startsWith('#') ? hash.slice(1) : '')
  const values = query.has('code') || query.has('error') ? query : new URLSearchParams(search)
  if (!values.has('code') && !values.has('error')) return null
  const pending = storage.getItem(PENDING_KEY)
  storage.removeItem(PENDING_KEY)
  let remembered
  try { remembered = JSON.parse(pending) } catch { /* Invalid local state is rejected. */ }
  const state = values.get('state')
  if (!remembered || !Number.isFinite(remembered.createdAt) || !state || remembered.state !== state || now - remembered.createdAt > 10 * 60 * 1000
      || now < remembered.createdAt) throw new Error('La conexión venció o se inició en otra pestaña. Vuelve a conectar Instagram.')
  return { state, code: values.get('code'), denied: values.has('error') }
}
