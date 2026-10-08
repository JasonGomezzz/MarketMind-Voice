const PENDING_KEY = 'x_pending_authorization'

export function rememberXAuthorization(url, storage = sessionStorage) {
  const destination = new URL(url)
  const state = destination.searchParams.get('state')
  if (destination.origin !== 'https://x.com' || destination.pathname !== '/i/oauth2/authorize' || !state) {
    throw new Error('Destino de X inválido')
  }
  storage.setItem(PENDING_KEY, JSON.stringify({ state, createdAt: Date.now() }))
  return destination.href
}

export function takeXAuthorization(hash, storage = sessionStorage, now = Date.now()) {
  const values = new URLSearchParams(hash.startsWith('#') ? hash.slice(1) : hash)
  if (values.get('provider') !== 'x' || !values.has('result')) return null
  const pending = storage.getItem(PENDING_KEY)
  storage.removeItem(PENDING_KEY)
  let remembered
  try { remembered = JSON.parse(pending) } catch { /* Invalid state. */ }
  if (!remembered || !Number.isFinite(remembered.createdAt) ||
      remembered.state !== values.get('state') || now - remembered.createdAt > 600000 || now < remembered.createdAt) {
    throw new Error('La conexión venció o se inició en otra pestaña. Vuelve a conectar X.')
  }
  return values.get('result') === 'connected'
}
