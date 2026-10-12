const PENDING_KEY = 'tiktok_pending_authorization'

export function rememberTikTokAuthorization(url, storage = sessionStorage, now = Date.now()) {
  const destination = new URL(url)
  const state = destination.searchParams.get('state')
  if (destination.origin !== 'https://www.tiktok.com' ||
      destination.pathname !== '/v2/auth/authorize/' || destination.username || destination.password ||
      !state || state.length > 128) throw new Error('Destino de TikTok inválido.')
  storage.setItem(PENDING_KEY, JSON.stringify({ state, createdAt: now }))
  return destination.href
}

export function takeTikTokAuthorization(hash, storage = sessionStorage, now = Date.now()) {
  const values = new URLSearchParams(hash.startsWith('#') ? hash.slice(1) : hash)
  if (values.get('provider') !== 'tiktok' || (!values.has('code') && !values.has('error'))) return null
  const pending = storage.getItem(PENDING_KEY)
  storage.removeItem(PENDING_KEY)
  let remembered
  try { remembered = JSON.parse(pending) } catch { /* Reject malformed state. */ }
  const state = values.get('state')
  if (!remembered || !Number.isFinite(remembered.createdAt) || !state ||
      remembered.state !== state || now - remembered.createdAt > 600000 || now < remembered.createdAt) {
    throw new Error('La conexión venció o se inició en otra pestaña. Vuelve a conectar TikTok.')
  }
  if (values.has('error')) return { state, code: null, denied: true }
  const code = values.get('code')
  if (!code || code.length > 4096) throw new Error('TikTok no devolvió una autorización válida.')
  return { state, code, denied: false }
}
