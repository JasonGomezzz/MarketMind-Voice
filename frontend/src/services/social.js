/**
 * Redes sociales: etiquetas y mensajes. Lógica pura, probada en tests/social.test.js.
 * Las llamadas a la API están en socialApi.js.
 */

const REDES = { instagram: 'Instagram', facebook: 'Facebook' }

export function etiquetaRed(red) {
  return REDES[red] ?? red
}

const ESTADOS = {
  esperando_aprobacion: { texto: 'Se publicará al aprobar', tono: 'neutral' },
  publicando: { texto: 'Publicando…', tono: 'neutral' },
  publicado: { texto: 'Publicado', tono: 'ok' },
  fallido: { texto: 'No se pudo publicar', tono: 'error' },
  cancelado: { texto: 'Cancelado', tono: 'neutral' },
}

export function estadoPublicacion(estado) {
  return ESTADOS[estado] ?? { texto: estado, tono: 'neutral' }
}

/** ¿Puede el marketero pulsar "Publicar ahora / Reintentar"? */
export function puedeReintentar(publicacion, estadoCampana) {
  return (
    estadoCampana === 'aprobado' &&
    ['fallido', 'esperando_aprobacion'].includes(publicacion.estado) &&
    (publicacion.intentos ?? 0) < 3
  )
}

/**
 * Mensaje tras volver de Meta a /settings?redes=...
 * @returns {{ tipo: 'ok'|'error'|'info', texto: string } | null}
 */
export function mensajeRetornoMeta(params) {
  const redes = params.get('redes')
  if (!redes) return null
  if (redes === 'conectadas') {
    const n = Number(params.get('cuentas')) || 0
    return { tipo: 'ok', texto: n === 1 ? 'Se conectó 1 cuenta.' : `Se conectaron ${n} cuentas.` }
  }
  if (redes === 'cancelado') return { tipo: 'info', texto: 'Cancelaste la conexión con Meta.' }
  const motivos = {
    sesion: 'El enlace de conexión caducó. Vuelve a intentarlo.',
    sin_paginas:
      'Meta no devolvió páginas. Marca tu página de Facebook (y su Instagram) en el diálogo de permisos.',
    meta: 'Meta rechazó la conexión. Intenta de nuevo en unos minutos.',
  }
  return { tipo: 'error', texto: motivos[params.get('motivo')] ?? 'No se pudo conectar la cuenta.' }
}
