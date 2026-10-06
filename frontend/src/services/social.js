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

// ── Estadísticas (Fase 4) ────────────────────────────────────────────────

/** Métricas que muestra cada red, en orden. Facebook llama "reacciones" a sus me gusta. */
const METRICAS = {
  instagram: {
    principales: [
      ['me_gusta', 'Me gusta'],
      ['comentarios', 'Comentarios'],
      ['compartidos', 'Compartidos'],
    ],
    secundarias: [
      ['alcance', 'Alcance'],
      ['vistas', 'Vistas'],
      ['guardados', 'Guardados'],
      ['interacciones', 'Interacciones'],
    ],
  },
  facebook: {
    principales: [
      ['me_gusta', 'Reacciones'],
      ['comentarios', 'Comentarios'],
      ['compartidos', 'Compartidos'],
    ],
    secundarias: [
      ['alcance', 'Alcance'],
      ['vistas', 'Vistas'],
      ['interacciones', 'Clics'],
    ],
  },
}

export function metricasDeRed(red) {
  return METRICAS[red] ?? METRICAS.instagram
}

const NUMERO = new Intl.NumberFormat('es-PE')

/** Un dato que Meta no informa (null/undefined) es "sin dato", nunca 0. */
export function formatoMetrica(valor) {
  if (valor === null || valor === undefined) return 'sin dato'
  return NUMERO.format(valor)
}

const ALCANCE = {
  cliente: 'Solo tus publicaciones aprobadas.',
  marketero: 'Las publicaciones de todos tus clientes.',
  superadmin: 'Todas las publicaciones de la plataforma.',
}

export function alcanceDelRol(rol) {
  return ALCANCE[rol] ?? ALCANCE.cliente
}

/** Filtros de la tabla. `estado` acepta 'todas' o un estado de publicación. */
export function filtrarPublicaciones(lista, { red = 'todas', estado = 'todas' } = {}) {
  return lista.filter(
    (p) => (red === 'todas' || p.red === red) && (estado === 'todas' || p.estado === estado),
  )
}

const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'set', 'oct', 'nov', 'dic']

/**
 * Publicaciones por mes de una red para los últimos `meses` meses, rellenando con 0
 * los meses sin publicaciones (aquí 0 es real: es un conteo propio, no un dato de Meta).
 * @param {{mes: string}[]} porMes filas "YYYY-MM" del resumen
 */
export function serieMensual(porMes, red, hoy = new Date(), meses = 6) {
  const conteo = Object.fromEntries((porMes ?? []).map((fila) => [fila.mes, fila[red] ?? 0]))
  const serie = []
  for (let i = meses - 1; i >= 0; i -= 1) {
    const fecha = new Date(hoy.getFullYear(), hoy.getMonth() - i, 1)
    const clave = `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}`
    serie.push({ mes: clave, etiqueta: MESES_CORTOS[fecha.getMonth()], total: conteo[clave] ?? 0 })
  }
  return serie
}

/** "hace 5 min", "hace 3 h", "hace 2 días" o la fecha corta. */
export function haceCuanto(fechaIso, ahora = new Date()) {
  if (!fechaIso) return null
  const fecha = new Date(fechaIso)
  const minutos = Math.floor((ahora - fecha) / 60000)
  if (minutos < 1) return 'hace un momento'
  if (minutos < 60) return `hace ${minutos} min`
  const horas = Math.floor(minutos / 60)
  if (horas < 24) return `hace ${horas} h`
  const dias = Math.floor(horas / 24)
  if (dias < 7) return dias === 1 ? 'hace 1 día' : `hace ${dias} días`
  return fecha.toLocaleDateString('es-PE', { day: 'numeric', month: 'short', year: 'numeric' })
}
