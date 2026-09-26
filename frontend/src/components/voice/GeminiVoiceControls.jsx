import { useEffect, useRef, useState } from 'react'
import { LoaderCircle, Mic, Square, Volume2 } from 'lucide-react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'

const AUDIO_TYPES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg']

function supportedAudioType() {
  return AUDIO_TYPES.find((type) => window.MediaRecorder?.isTypeSupported(type)) || ''
}

export function VoiceDictationButton({ onTranscript, onError, disabled = false }) {
  const [state, setState] = useState('idle')
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const timeoutRef = useRef(null)

  function releaseMicrophone() {
    window.clearTimeout(timeoutRef.current)
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
  }

  useEffect(() => () => releaseMicrophone(), [])

  async function sendAudio(blob) {
    setState('transcribing')
    const form = new FormData()
    const extension = blob.type.includes('mp4') ? 'm4a' : blob.type.includes('ogg') ? 'ogg' : 'webm'
    form.append('audio', blob, `dictado.${extension}`)
    try {
      const { data } = await api.post('/api/campaigns/voice/transcribe/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      onTranscript(data.transcript)
    } catch (error) {
      onError?.(error.response?.data?.detail || 'No se pudo transcribir el audio.')
    } finally {
      setState('idle')
    }
  }

  async function toggleRecording() {
    if (state === 'recording') {
      recorderRef.current?.stop()
      return
    }
    if (state !== 'idle') return
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      onError?.('Este navegador no admite grabación de audio.')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      })
      streamRef.current = stream
      chunksRef.current = []
      const mimeType = supportedAudioType()
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      recorderRef.current = recorder
      recorder.ondataavailable = (event) => {
        if (event.data.size) chunksRef.current.push(event.data)
      }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        releaseMicrophone()
        if (blob.size) sendAudio(blob)
        else setState('idle')
      }
      recorder.start()
      setState('recording')
      timeoutRef.current = window.setTimeout(() => recorder.stop(), 60000)
    } catch {
      releaseMicrophone()
      setState('idle')
      onError?.('Permite el acceso al micrófono para usar el dictado.')
    }
  }

  const recording = state === 'recording'
  const transcribing = state === 'transcribing'
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={toggleRecording}
      disabled={disabled || transcribing}
      aria-label={recording ? 'Detener dictado' : 'Dictar con Gemini'}
      className={recording ? 'border-error text-error' : ''}
    >
      {transcribing ? (
        <LoaderCircle className="h-4 w-4 animate-spin" />
      ) : recording ? (
        <Square className="h-4 w-4 fill-current" />
      ) : (
        <Mic className="h-4 w-4" />
      )}
      {transcribing ? 'Transcribiendo…' : recording ? 'Detener' : 'Dictar'}
    </Button>
  )
}

export function VoicePlaybackButton({ text, disabled = false }) {
  const [state, setState] = useState('idle')
  const audioRef = useRef(null)
  const objectUrlRef = useRef(null)

  function stop() {
    audioRef.current?.pause()
    if (audioRef.current) audioRef.current.currentTime = 0
    setState('idle')
  }

  useEffect(
    () => () => {
      audioRef.current?.pause()
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current)
    },
    [],
  )

  async function togglePlayback() {
    if (state === 'playing') {
      stop()
      return
    }
    if (!text?.trim() || state === 'loading') return
    setState('loading')
    try {
      const response = await api.post(
        '/api/campaigns/voice/synthesize/',
        { text: text.trim() },
        { responseType: 'blob' },
      )
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current)
      objectUrlRef.current = URL.createObjectURL(response.data)
      const audio = new Audio(objectUrlRef.current)
      audioRef.current = audio
      audio.onended = () => setState('idle')
      audio.onerror = () => setState('idle')
      await audio.play()
      setState('playing')
    } catch {
      setState('idle')
    }
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={togglePlayback}
      disabled={disabled || !text?.trim() || state === 'loading'}
      aria-label={state === 'playing' ? 'Detener lectura' : 'Escuchar con Gemini'}
    >
      {state === 'loading' ? (
        <LoaderCircle className="h-4 w-4 animate-spin" />
      ) : state === 'playing' ? (
        <Square className="h-4 w-4 fill-current" />
      ) : (
        <Volume2 className="h-4 w-4" />
      )}
      {state === 'loading' ? 'Preparando…' : state === 'playing' ? 'Detener' : 'Escuchar'}
    </Button>
  )
}
