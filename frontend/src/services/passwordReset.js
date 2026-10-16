/**
 * Lógica pura de la recuperación de contraseña (sin React ni DOM, para probarla).
 *
 * El correo trae el enlace /reset-password#token=...: el token va en el
 * fragmento para que no llegue a logs de servidores ni al Referer.
 */

export const MIN_PASSWORD = 8

/** Token del fragmento de la URL ('#token=abc'), o '' si no hay. */
export function tokenDesdeHash(hash = '') {
  const params = new URLSearchParams(String(hash).replace(/^#/, ''))
  return (params.get('token') || '').trim()
}

/** Mensaje de error del formulario de nueva contraseña, o null si está bien. */
export function validarNuevaPassword(password, confirmacion) {
  if (!password || password.length < MIN_PASSWORD) {
    return `La contraseña debe tener al menos ${MIN_PASSWORD} caracteres.`
  }
  if (password !== confirmacion) return 'Las contraseñas no coinciden.'
  return null
}

/** Segundos que pide esperar el backend en un 429 (cuerpo o cabecera Retry-After). */
export function segundosDeEspera(error) {
  const response = error?.response
  if (response?.status !== 429) return 0
  const segundos = Number(response.data?.data?.retry_after ?? response.headers?.['retry-after'])
  return Number.isFinite(segundos) && segundos > 0 ? Math.ceil(segundos) : 60
}

/** Mensaje legible de un error de la API de recuperación. */
export function mensajeDeError(error, porDefecto = 'No se pudo procesar la solicitud. Intenta nuevamente.') {
  if (!error?.response) return 'No se pudo conectar con el servidor. Revisa tu conexión.'
  return error.response.data?.message || porDefecto
}

/** Texto del contador de espera: '45 s' o '2 min'. */
export function formatoEspera(segundos) {
  if (segundos < 60) return `${segundos} s`
  return `${Math.ceil(segundos / 60)} min`
}
