import { useCallback, useEffect, useRef, useState } from 'react'
import {
  buildTranscript,
  dictationSupport,
  getSpeechRecognition,
  speechErrorMessage,
} from '../services/voiceIntent'

/**
 * Dictado con la Web Speech API del navegador (Chrome, Edge, Safari).
 * La voz se transcribe en el dispositivo/navegador: a nuestro backend solo
 * llega texto. Si el navegador no lo soporta, `supported` es false y la
 * pantalla ofrece escribir el brief. En Brave también es false (ver dictationSupport).
 *
 * @param {(texto: string) => void} onFinal  recibe cada frase confirmada
 */
export default function useSpeechRecognition(onFinal, lang = 'es-PE') {
  const [listening, setListening] = useState(false)
  const [interim, setInterim] = useState('')
  const [error, setError] = useState('')
  const recognitionRef = useRef(null)
  const onFinalRef = useRef(onFinal)
  const { supported, reason: unsupportedReason } = dictationSupport()

  useEffect(() => {
    onFinalRef.current = onFinal
  }, [onFinal])

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
  }, [])

  const start = useCallback(() => {
    const SpeechRecognition = getSpeechRecognition()
    if (!supported || !SpeechRecognition || recognitionRef.current) return

    const recognition = new SpeechRecognition()
    recognition.lang = lang
    recognition.continuous = true
    recognition.interimResults = true

    // Solo los resultados nuevos de este evento: los anteriores ya se entregaron.
    recognition.onresult = (event) => {
      const nuevos = Array.from(event.results).slice(event.resultIndex)
      const { finalText, interimText } = buildTranscript(nuevos)
      if (finalText) onFinalRef.current?.(finalText)
      setInterim(interimText)
    }
    recognition.onerror = (event) => setError(speechErrorMessage(event.error))
    recognition.onend = () => {
      recognitionRef.current = null
      setListening(false)
      setInterim('')
    }

    recognitionRef.current = recognition
    setError('')
    setListening(true)
    try {
      recognition.start()
    } catch {
      recognitionRef.current = null
      setListening(false)
      setError(speechErrorMessage('unknown'))
    }
  }, [lang, supported])

  // Soltar el micrófono al salir de la pantalla.
  useEffect(() => () => recognitionRef.current?.abort(), [])

  return { supported, unsupportedReason, listening, interim, error, start, stop }
}
