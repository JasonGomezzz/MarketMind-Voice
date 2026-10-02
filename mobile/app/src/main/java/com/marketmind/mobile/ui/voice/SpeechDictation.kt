package com.marketmind.mobile.ui.voice

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer

/**
 * Dictado con el reconocedor de voz del sistema (Google en la mayoría de
 * teléfonos). La voz se transcribe en el dispositivo o en el servicio del
 * sistema; a nuestro backend solo llega texto.
 *
 * Debe crearse y usarse en el hilo principal. Cada [start] escucha una
 * frase y termina tras un silencio; se puede volver a pulsar para seguir.
 */
class SpeechDictation(
    context: Context,
    private val onPartial: (String) -> Unit,
    private val onFinal: (String) -> Unit,
    private val onError: (String) -> Unit,
    private val onEnd: () -> Unit,
) {
    private val recognizer: SpeechRecognizer? =
        if (SpeechRecognizer.isRecognitionAvailable(context)) {
            SpeechRecognizer.createSpeechRecognizer(context)
        } else {
            null
        }

    val available: Boolean get() = recognizer != null

    init {
        recognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onPartialResults(partialResults: Bundle?) {
                onPartial(primerResultado(partialResults))
            }

            override fun onResults(results: Bundle?) {
                val texto = primerResultado(results)
                if (texto.isNotBlank()) onFinal(texto)
                onEnd()
            }

            override fun onError(error: Int) {
                speechErrorMessage(error)?.let(onError)
                onEnd()
            }

            override fun onReadyForSpeech(params: Bundle?) = Unit
            override fun onBeginningOfSpeech() = Unit
            override fun onRmsChanged(rmsdB: Float) = Unit
            override fun onBufferReceived(buffer: ByteArray?) = Unit
            override fun onEndOfSpeech() = Unit
            override fun onEvent(eventType: Int, params: Bundle?) = Unit
        })
    }

    fun start(languageTag: String = "es-PE") {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, languageTag)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }
        recognizer?.startListening(intent)
    }

    fun stop() {
        recognizer?.stopListening()
    }

    fun destroy() {
        recognizer?.destroy()
    }

    private fun primerResultado(bundle: Bundle?): String =
        bundle?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull().orEmpty()
}

/** Mensaje para el usuario según el error del reconocedor; null si no hay que mostrar nada. */
fun speechErrorMessage(error: Int): String? = when (error) {
    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS ->
        "Sin permiso de micrófono. Actívalo en Ajustes o escribe el brief."
    SpeechRecognizer.ERROR_NO_MATCH, SpeechRecognizer.ERROR_SPEECH_TIMEOUT ->
        "No se entendió nada. Intenta de nuevo, más cerca del micrófono."
    SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT ->
        "El dictado necesita conexión. Revisa la red o escribe el brief."
    SpeechRecognizer.ERROR_AUDIO ->
        "No se pudo usar el micrófono. Puedes escribir el brief."
    SpeechRecognizer.ERROR_RECOGNIZER_BUSY ->
        "El micrófono está ocupado. Intenta de nuevo en un momento."
    SpeechRecognizer.ERROR_CLIENT -> null
    else -> "El dictado se interrumpió. Intenta de nuevo o escribe el brief."
}
