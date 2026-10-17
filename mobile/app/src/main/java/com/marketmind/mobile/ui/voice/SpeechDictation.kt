package com.marketmind.mobile.ui.voice

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.speech.ModelDownloadListener
import android.speech.RecognitionListener
import android.speech.RecognitionSupport
import android.speech.RecognitionSupportCallback
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.annotation.RequiresApi
import androidx.core.content.ContextCompat

/** Lo que la pantalla necesita para contarle al usuario dónde se transcribe su voz. */
data class EstadoDictado(
    val modo: ModoDictado,
    /** El teléfono puede descargar español para dictar sin enviar audio. */
    val idiomaDescargable: Boolean = false,
    /** El sistema está descargando (o programó) ese paquete de español. */
    val descargando: Boolean = false,
)

/**
 * Dictado con el reconocedor de voz del teléfono. A NexoMark solo llega el
 * texto; el audio nunca pasa por nuestro backend ni por Gemini.
 *
 * - Android 12+ con reconocedor en el dispositivo: se usa ese y el audio no
 *   sale del teléfono. En Android 13+ además se comprueba que haya español
 *   instalado y, si falta, se ofrece descargarlo.
 * - En otro caso: reconocedor del sistema con EXTRA_PREFER_OFFLINE. Es solo
 *   una preferencia: según el teléfono, el audio puede ir a Google.
 *
 * Debe crearse y usarse en el hilo principal. Cada [start] escucha una frase
 * y termina tras un silencio; se puede volver a pulsar para seguir.
 */
class SpeechDictation(
    private val context: Context,
    private val onPartial: (String) -> Unit,
    private val onFinal: (String) -> Unit,
    private val onError: (String) -> Unit,
    private val onEnd: () -> Unit,
    private val onEstado: (EstadoDictado) -> Unit = {},
) {
    private val listener = object : RecognitionListener {
        override fun onPartialResults(partialResults: Bundle?) {
            onPartial(primerResultado(partialResults))
        }

        override fun onResults(results: Bundle?) {
            escuchandoCon = null
            val texto = primerResultado(results)
            if (texto.isNotBlank()) onFinal(texto)
            onEnd()
        }

        override fun onError(error: Int) {
            escuchandoCon = null
            manejarError(error)
            onEnd()
        }

        override fun onReadyForSpeech(params: Bundle?) = Unit
        override fun onBeginningOfSpeech() = Unit
        override fun onRmsChanged(rmsdB: Float) = Unit
        override fun onBufferReceived(buffer: ByteArray?) = Unit
        override fun onEndOfSpeech() = Unit
        override fun onEvent(eventType: Int, params: Bundle?) = Unit
    }

    private var enDispositivo: SpeechRecognizer? = null
    private var sistema: SpeechRecognizer? = null
    private var escuchandoCon: SpeechRecognizer? = null
    private var idioma = SeleccionDictado.IDIOMA_PREFERIDO
    private var idiomaParaDescargar: String? = null
    private var preferirSinConexion = true
    private var destruido = false

    /** Estado actual. Los cambios posteriores a la creación llegan por [onEstado]. */
    var estado: EstadoDictado = EstadoDictado(ModoDictado.NO_DISPONIBLE)
        private set

    init {
        val sdk = Build.VERSION.SDK_INT
        val capacidades = CapacidadesVoz(
            sdk = sdk,
            reconocedorSistema = SpeechRecognizer.isRecognitionAvailable(context),
            reconocedorEnDispositivo = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
                SpeechRecognizer.isOnDeviceRecognitionAvailable(context),
        )
        estado = when (SeleccionDictado.modoInicial(capacidades)) {
            ModoDictado.EN_DISPOSITIVO -> {
                enDispositivo = crearEnDispositivo()
                if (enDispositivo != null) EstadoDictado(ModoDictado.EN_DISPOSITIVO) else estadoSistema()
            }
            ModoDictado.SISTEMA -> estadoSistema()
            ModoDictado.NO_DISPONIBLE -> EstadoDictado(ModoDictado.NO_DISPONIBLE)
        }
        if (enDispositivo != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) comprobarIdioma()
    }

    fun start() {
        val reconocedor = when (estado.modo) {
            ModoDictado.EN_DISPOSITIVO -> enDispositivo
            ModoDictado.SISTEMA -> sistema
            ModoDictado.NO_DISPONIBLE -> null
        } ?: return
        escuchandoCon = reconocedor
        reconocedor.startListening(intentDictado(idioma, preferirSinConexion))
    }

    fun stop() {
        escuchandoCon?.stopListening()
    }

    /** Pide al sistema el paquete de español para dictar en el teléfono (Android 13+). */
    fun descargarIdioma() {
        val reconocedor = enDispositivo ?: return
        val etiqueta = idiomaParaDescargar ?: return
        val intent = intentDictado(etiqueta, preferirSinConexion = true)
        when {
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE -> {
                publicar(estado.copy(idiomaDescargable = false, descargando = true))
                descargarConAvisos(reconocedor, intent)
            }
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU -> {
                publicar(estado.copy(idiomaDescargable = false, descargando = true))
                reconocedor.triggerModelDownload(intent)
            }
        }
    }

    fun destroy() {
        destruido = true
        enDispositivo?.destroy()
        sistema?.destroy()
        enDispositivo = null
        sistema = null
        escuchandoCon = null
    }

    private fun manejarError(error: Int) {
        when (SeleccionDictado.reaccionAError(estado.modo, error, preferirSinConexion)) {
            ReaccionError.CAMBIAR_A_SISTEMA -> {
                publicar(estadoSistema(estado.idiomaDescargable, estado.descargando))
                avisar(
                    if (estado.modo == ModoDictado.SISTEMA) MENSAJE_CAMBIO_A_SISTEMA
                    else "El dictado no está disponible en este teléfono. Escribe el brief.",
                )
            }
            ReaccionError.QUITAR_PREFERENCIA_SIN_CONEXION -> {
                preferirSinConexion = false
                avisar(MENSAJE_SIN_PAQUETE_OFFLINE)
            }
            ReaccionError.MOSTRAR -> speechErrorMessage(error)?.let(::avisar)
        }
    }

    @RequiresApi(Build.VERSION_CODES.TIRAMISU)
    private fun comprobarIdioma() {
        val reconocedor = enDispositivo ?: return
        reconocedor.checkRecognitionSupport(
            intentDictado(SeleccionDictado.IDIOMA_PREFERIDO, preferirSinConexion = true),
            ContextCompat.getMainExecutor(context),
            object : RecognitionSupportCallback {
                override fun onSupportResult(recognitionSupport: RecognitionSupport) {
                    aplicarSoporte(
                        SeleccionDictado.soporteIdioma(
                            instalados = recognitionSupport.installedOnDeviceLanguages,
                            pendientes = recognitionSupport.pendingOnDeviceLanguages,
                            descargables = recognitionSupport.supportedOnDeviceLanguages,
                        ),
                    )
                }

                // Sin respuesta del servicio se intenta igual; si falla al escuchar, se pasa al sistema.
                override fun onError(error: Int) = Unit
            },
        )
    }

    private fun aplicarSoporte(soporte: SoporteIdioma) {
        if (destruido) return
        when (soporte) {
            is SoporteIdioma.Listo -> {
                idioma = soporte.idioma
                idiomaParaDescargar = null
                publicar(EstadoDictado(ModoDictado.EN_DISPOSITIVO))
            }
            is SoporteIdioma.Descargando -> {
                idiomaParaDescargar = soporte.idioma
                publicar(estadoSistema(descargando = true))
            }
            is SoporteIdioma.Descargable -> {
                idiomaParaDescargar = soporte.idioma
                publicar(estadoSistema(idiomaDescargable = true))
            }
            SoporteIdioma.NoSoportado -> {
                idiomaParaDescargar = null
                publicar(estadoSistema())
            }
        }
    }

    @RequiresApi(Build.VERSION_CODES.UPSIDE_DOWN_CAKE)
    private fun descargarConAvisos(reconocedor: SpeechRecognizer, intent: Intent) {
        reconocedor.triggerModelDownload(
            intent,
            ContextCompat.getMainExecutor(context),
            object : ModelDownloadListener {
                override fun onProgress(completedPercent: Int) = Unit

                override fun onSuccess() {
                    if (!destruido) comprobarIdioma()
                }

                // Programada para más tarde: queda como "descargando" hasta volver a abrir la pantalla.
                override fun onScheduled() = Unit

                override fun onError(error: Int) {
                    if (destruido) return
                    publicar(estado.copy(idiomaDescargable = true, descargando = false))
                    avisar("No se pudo descargar el español. Puedes dictar igual o escribir el brief.")
                }
            },
        )
    }

    /** Pasa al reconocedor del sistema; si no existe, el dictado queda no disponible. */
    private fun estadoSistema(idiomaDescargable: Boolean = false, descargando: Boolean = false): EstadoDictado {
        if (sistema == null && SpeechRecognizer.isRecognitionAvailable(context)) {
            sistema = SpeechRecognizer.createSpeechRecognizer(context).also {
                it.setRecognitionListener(listener)
            }
        }
        idioma = SeleccionDictado.IDIOMA_PREFERIDO
        val modo = if (sistema != null) ModoDictado.SISTEMA else ModoDictado.NO_DISPONIBLE
        return EstadoDictado(modo, idiomaDescargable, descargando)
    }

    private fun crearEnDispositivo(): SpeechRecognizer? {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return null
        return runCatching { SpeechRecognizer.createOnDeviceSpeechRecognizer(context) }
            .getOrNull()
            ?.also { it.setRecognitionListener(listener) }
    }

    private fun publicar(nuevo: EstadoDictado) {
        if (destruido) return
        estado = nuevo
        onEstado(nuevo)
    }

    private fun avisar(mensaje: String) = onError(mensaje)

    private fun intentDictado(idioma: String, preferirSinConexion: Boolean) =
        Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            SeleccionDictado.extrasDictado(idioma, preferirSinConexion).forEach { (clave, valor) ->
                when (valor) {
                    is Boolean -> putExtra(clave, valor)
                    else -> putExtra(clave, valor.toString())
                }
            }
        }

    private fun primerResultado(bundle: Bundle?): String =
        bundle?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull().orEmpty()

    private companion object {
        const val MENSAJE_CAMBIO_A_SISTEMA =
            "El dictado en el teléfono no está listo para español. Pulsa Dictar otra vez: " +
                "se usará el reconocedor de Google, que puede enviar el audio a sus servidores."
        const val MENSAJE_SIN_PAQUETE_OFFLINE =
            "Este teléfono no tiene español sin conexión. Pulsa Dictar otra vez para transcribir en línea."
    }
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
