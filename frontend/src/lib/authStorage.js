const KEYS = ['access_token', 'refresh_token', 'user_role', 'user_nombre', 'user_email']

function storage() {
  return sessionStorage.getItem('access_token') ? sessionStorage : localStorage
}

export function getAuthItem(key) {
  return storage().getItem(key)
}

export function setAuthItem(key, value) {
  storage().setItem(key, value)
}

export function clearAuthSession() {
  for (const key of KEYS) {
    sessionStorage.removeItem(key)
    localStorage.removeItem(key)
  }
}

export function startAuthSession(data, remember = false) {
  clearAuthSession()
  const target = remember ? localStorage : sessionStorage
  target.setItem('access_token', data.access)
  target.setItem('refresh_token', data.refresh)
  target.setItem('user_role', data.role)
  target.setItem('user_nombre', data.nombre)
}
