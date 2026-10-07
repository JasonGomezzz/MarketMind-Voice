const PENDING_KEY = 'facebook_pending_authorization'

export function rememberFacebookAuthorization(url, storage = sessionStorage) {
  const destination = new URL(url)
  const state = destination.searchParams.get('state')
  if (destination.origin !== 'https://www.facebook.com' || !/^\/v\d+\.\d+\/dialog\/oauth$/.test(destination.pathname) || !state) {
    throw new Error('Destino de Facebook inválido')
  }
  storage.setItem(PENDING_KEY, JSON.stringify({ state, createdAt: Date.now() }))
  return destination.href
}

export function takeFacebookAuthorization(search, hash, storage = sessionStorage, now = Date.now()) {
  const fragment = new URLSearchParams(hash.startsWith('#') ? hash.slice(1) : '')
  const values = fragment.has('code') || fragment.has('error') ? fragment : new URLSearchParams(search)
  if (values.get('provider') !== 'facebook' || !values.has('code') && !values.has('error')) return null
  const pending = storage.getItem(PENDING_KEY)
  storage.removeItem(PENDING_KEY)
  let remembered
  try { remembered = JSON.parse(pending) } catch { /* Reject invalid browser state. */ }
  const state = values.get('state')
  if (!remembered || !Number.isFinite(remembered.createdAt) || !state || remembered.state !== state
      || now - remembered.createdAt > 600000 || now < remembered.createdAt) {
    throw new Error('La conexión venció o se inició en otra pestaña. Vuelve a conectar Facebook.')
  }
  return { state, code: values.get('code'), denied: values.has('error') }
}
