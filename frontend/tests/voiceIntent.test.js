import test from 'node:test'
import assert from 'node:assert/strict'
import {
  appendDictation,
  briefError,
  buildTranscript,
  camposParaFormulario,
  dictationSupport,
  getSpeechRecognition,
  speechErrorMessage,
  MAX_BRIEF,
  unsupportedMessage,
} from '../src/services/voiceIntent.js'

const resultado = (transcript, isFinal) => Object.assign([{ transcript }], { isFinal })

test('buildTranscript separates confirmed speech from speech still being recognised', () => {
  const { finalText, interimText } = buildTranscript([
    resultado('quiero una campaña ', true),
    resultado('para una  cafetería', true),
    resultado(' en insta', false),
  ])
  assert.equal(finalText, 'quiero una campaña para una cafetería')
  assert.equal(interimText, 'en insta')
})

test('appendDictation joins phrases with single spaces and respects the brief limit', () => {
  assert.equal(appendDictation('', ' hola '), 'hola')
  assert.equal(appendDictation('quiero una campaña', 'para   Instagram'), 'quiero una campaña para Instagram')
  assert.equal(appendDictation('a'.repeat(MAX_BRIEF), 'extra').length, MAX_BRIEF)
})

test('camposParaFormulario only fills list fields with options the form really has', () => {
  const { valores, completados, pendientes } = camposParaFormulario(
    {
      titulo: ' 2x1 en capuchinos ',
      cliente_nombre: null,
      cliente_email: '',
      industria: 'gastronomia',
      tono: 'juvenil',
      plataforma: 'instagram',
      prompt: 'Campaña 2x1 para universitarios',
      estado: 'aprobado',
    },
    { industria: ['gastronomia'], tono: ['casual'], plataforma: ['instagram'] },
  )
  assert.deepEqual(valores, {
    titulo: '2x1 en capuchinos',
    industria: 'gastronomia',
    plataforma: 'instagram',
    prompt: 'Campaña 2x1 para universitarios',
  })
  assert.deepEqual(completados, ['titulo', 'industria', 'plataforma', 'prompt'])
  assert.deepEqual(pendientes, ['cliente_nombre', 'cliente_email', 'tono'])
  assert.equal('estado' in valores, false)
})

test('camposParaFormulario tolerates a missing or malformed intent', () => {
  assert.equal(camposParaFormulario(null).pendientes.length, 7)
  assert.deepEqual(camposParaFormulario({ titulo: 123 }).valores, {})
})

test('briefError enforces the same length limits as the backend', () => {
  assert.notEqual(briefError('corto'), '')
  assert.notEqual(briefError('x'.repeat(MAX_BRIEF + 1)), '')
  assert.equal(briefError('Campaña para una cafetería'), '')
})

test('speech errors become actionable messages and a user abort stays silent', () => {
  assert.match(speechErrorMessage('not-allowed'), /permiso/)
  assert.match(speechErrorMessage('audio-capture'), /micrófono/)
  assert.equal(speechErrorMessage('aborted'), '')
  assert.notEqual(speechErrorMessage('algo-nuevo'), '')
})

test('getSpeechRecognition finds the prefixed constructor and reports absence', () => {
  class Prefixed {}
  assert.equal(getSpeechRecognition({ webkitSpeechRecognition: Prefixed }), Prefixed)
  assert.equal(getSpeechRecognition({}), null)
})

test('dictationSupport rules out Brave even though it exposes the constructor', () => {
  class Recognizer {}
  assert.deepEqual(dictationSupport({ webkitSpeechRecognition: Recognizer, navigator: {} }), {
    supported: true,
    reason: '',
  })
  assert.equal(dictationSupport({ webkitSpeechRecognition: Recognizer, navigator: { brave: {} } }).reason, 'brave')
  assert.equal(dictationSupport({ navigator: {} }).reason, 'unsupported')
  assert.match(unsupportedMessage('brave'), /Brave/)
  assert.match(unsupportedMessage('unsupported'), /Chrome/)
})
