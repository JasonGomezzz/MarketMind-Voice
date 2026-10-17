/**
 * Solicitudes de créditos: el marketero pide, el superadmin aprueba o rechaza.
 * Lógica pura (sin React) para poder probarla con node --test.
 */

export const MAX_CREDITOS = 10000
export const CREDITOS_SUGERIDOS = 100

const ETIQUETAS = {
  pendiente: 'Pendiente de revisión',
  aprobada: 'Aprobada',
  rechazada: 'Rechazada',
}

export function etiquetaEstado(estado) {
  return ETIQUETAS[estado] || estado || '—'
}

/** Error de la cantidad a aprobar, o null si es un entero entre 1 y MAX_CREDITOS. */
export function validarCreditos(valor) {
  const texto = String(valor ?? '').trim()
  if (!/^\d+$/.test(texto)) return 'Ingresa un número entero de créditos.'
  const numero = Number(texto)
  if (numero < 1 || numero > MAX_CREDITOS) return `Ingresa entre 1 y ${MAX_CREDITOS.toLocaleString('es-PE')} créditos.`
  return null
}

/** Frase corta con el estado de la última solicitud del marketero. */
export function resumenSolicitud(solicitud) {
  if (!solicitud) return ''
  if (solicitud.estado === 'pendiente') return 'Tu solicitud está pendiente: el superadmin la revisará.'
  if (solicitud.estado === 'aprobada') {
    return `Última solicitud aprobada: +${solicitud.creditos_otorgados} créditos.`
  }
  const nota = solicitud.nota_resolucion ? ` Motivo: ${solicitud.nota_resolucion}` : ''
  return `Última solicitud rechazada.${nota}`
}
