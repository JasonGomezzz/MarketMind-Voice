/**
 * Lógica pura del dictado de campañas (sin React ni DOM, para poder probarla).
 *
 * El navegador transcribe la voz; aquí solo se arma el texto y se decide qué
 * campos interpretados por el backend pueden volcarse al formulario.
 */

export const CAMPOS_INTENT = [
  'titulo',
  'cliente_nombre',
  'cliente_email',
  'industria',
  'tono',
  'plataforma',
  'prompt',
]

export const MIN_BRIEF = 10
export const MAX_BRIEF = 2000

/** Constructor de reconocimiento de voz del navegador, o null si no existe. */
export function getSpeechRecognition(scope = globalThis) {
  return scope?.SpeechRecognition || scope?.webkitSpeechRecognition || null
}

/**
 * ¿Se puede dictar en este navegador?
 *
 * Brave expone webkitSpeechRecognition pero bloquea el servicio que la
 * respalda: siempre falla con error 'network'. Se detecta antes para no
 * ofrecer un botón que nunca funciona.
 */
export function dictationSupport(scope = globalThis) {
  if (scope?.navigator?.brave) return { supported: false, reason: 'brave' }
  if (!getSpeechRecognition(scope)) return { supported: false, reason: 'unsupported' }
  return { supported: true, reason: '' }
}

export function unsupportedMessage(reason) {
  if (reason === 'brave') {
    return 'Brave bloquea el dictado por voz. Usa Chrome o Edge, o escribe el brief.'
  }
  return 'Este navegador no permite dictar. Usa Chrome, Edge o Safari, o escribe el brief.'
}

/**
 * Separa lo ya confirmado por el navegador de lo que aún está reconociendo.
 * `results` es un SpeechRecognitionResultList (o un arreglo con la misma forma).
 */
export function buildTranscript(results) {
  let finalText = ''
  let interimText = ''
  for (let i = 0; i < results.length; i += 1) {
    const texto = results[i][0]?.transcript ?? ''
    if (results[i].isFinal) finalText += texto
    else interimText += texto
  }
  return { finalText: limpiar(finalText), interimText: limpiar(interimText) }
}

/** Une el texto previo con lo nuevo dictado, sin duplicar espacios. */
export function appendDictation(previo, nuevo) {
  return limpiar(`${previo ?? ''} ${nuevo ?? ''}`).slice(0, MAX_BRIEF)
}

function limpiar(texto) {
  return texto.replace(/\s+/g, ' ').trim()
}

/** Mensaje para el usuario según el código de error del reconocimiento. */
export function speechErrorMessage(code) {
  switch (code) {
    case 'not-allowed':
    case 'service-not-allowed':
      return 'No hay permiso para usar el micrófono. Actívalo en el navegador o escribe el brief.'
    case 'no-speech':
      return 'No se escuchó nada. Intenta de nuevo, más cerca del micrófono.'
    case 'audio-capture':
      return 'No se encontró un micrófono. Puedes escribir el brief.'
    case 'network':
      return 'El servicio de dictado del navegador no respondió. Revisa la conexión o usa Chrome o Edge; también puedes escribir el brief.'
    case 'aborted':
      return ''
    default:
      return 'El dictado se interrumpió. Intenta de nuevo o escribe el brief.'
  }
}

/**
 * Decide qué campos interpretados se vuelcan al formulario.
 *
 * Un valor de lista (industria, tono, plataforma) solo se acepta si existe
 * como opción en el formulario; lo demás queda para que el usuario lo complete.
 *
 * @param {object} campos   campos_finales del intent
 * @param {object} opciones { industria: [...], tono: [...], plataforma: [...] } con los `value` válidos
 * @returns {{ valores: object, completados: string[], pendientes: string[] }}
 */
export function camposParaFormulario(campos, opciones = {}) {
  const valores = {}
  const completados = []
  const pendientes = []

  for (const campo of CAMPOS_INTENT) {
    const valor = typeof campos?.[campo] === 'string' ? campos[campo].trim() : ''
    const permitidos = opciones[campo]
    if (valor && (!permitidos || permitidos.includes(valor))) {
      valores[campo] = valor
      completados.push(campo)
    } else {
      pendientes.push(campo)
    }
  }
  return { valores, completados, pendientes }
}

/** Valida el brief antes de enviarlo a interpretar. Devuelve '' si es válido. */
export function briefError(texto) {
  const largo = (texto ?? '').trim().length
  if (largo < MIN_BRIEF) return `Cuéntame un poco más (mínimo ${MIN_BRIEF} caracteres).`
  if (largo > MAX_BRIEF) return `El brief no puede superar ${MAX_BRIEF} caracteres.`
  return ''
}
