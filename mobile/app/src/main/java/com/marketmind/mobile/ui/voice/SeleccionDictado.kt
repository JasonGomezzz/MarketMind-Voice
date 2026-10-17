package com.marketmind.mobile.ui.voice

import android.annotation.SuppressLint
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer

/**
 * Dónde se transcribe la voz del brief. Se muestra al usuario, así que tiene
 * que describir lo que de verdad hace el reconocedor elegido.
 */
enum class ModoDictado {
    /** Reconocedor en el dispositivo (Android 12+): el audio no sale del teléfono. */
    EN_DISPOSITIVO,

    /**
     * Reconocedor del sistema con EXTRA_PREFER_OFFLINE. Es una preferencia que
     * el motor puede ignorar: el audio puede ir a los servidores de Google.
     */
    SISTEMA,

    /** No hay reconocedor: solo se puede escribir el brief. */
    NO_DISPONIBLE,
}

/** Qué ofrece el teléfono, leído de SpeechRecognizer. */
data class CapacidadesVoz(
    val sdk: Int,
    val reconocedorSistema: Boolean,
    val reconocedorEnDispositivo: Boolean,
)

/** Estado del idioma en el reconocedor en el dispositivo (checkRecognitionSupport, API 33+). */
sealed interface SoporteIdioma {
    data class Listo(val idioma: String) : SoporteIdioma
    data class Descargando(val idioma: String) : SoporteIdioma
    data class Descargable(val idioma: String) : SoporteIdioma
    data object NoSoportado : SoporteIdioma
}

/** Qué hacer cuando el reconocedor devuelve un error. */
enum class ReaccionError {
    /** El reconocedor en el dispositivo no tiene el idioma: usar el del sistema. */
    CAMBIAR_A_SISTEMA,

    /** El motor no tiene español sin conexión: el siguiente intento va sin EXTRA_PREFER_OFFLINE. */
    QUITAR_PREFERENCIA_SIN_CONEXION,

    /** Error normal: mostrar el mensaje de [speechErrorMessage]. */
    MOSTRAR,
}

/**
 * Lógica pura para elegir el reconocedor de voz, sin tocar el dispositivo,
 * para poder probarla en la JVM. [SpeechDictation] la aplica.
 *
 * Referencias (developer.android.com, consultadas el 2026-10-16):
 * SpeechRecognizer.createOnDeviceSpeechRecognizer e isOnDeviceRecognitionAvailable
 * (API 31), checkRecognitionSupport y triggerModelDownload (API 33),
 * RecognizerIntent.EXTRA_PREFER_OFFLINE (API 23, "puede no tener efecto").
 * Las constantes de error de API 31 son enteros que se copian al compilar.
 */
@SuppressLint("InlinedApi")
object SeleccionDictado {
    const val IDIOMA_PREFERIDO = "es-PE"
    /** Build.VERSION_CODES.S: primer nivel con createOnDeviceSpeechRecognizer. */
    const val SDK_EN_DISPOSITIVO = 31

    /** Variantes de español aceptables si el teléfono no tiene es-PE, de más a menos cercana. */
    private val ESPANOL_CERCANO = listOf("es-419", "es-US", "es-MX", "es-CO", "es-AR", "es-CL", "es-ES")

    fun modoInicial(capacidades: CapacidadesVoz): ModoDictado = when {
        capacidades.sdk >= SDK_EN_DISPOSITIVO && capacidades.reconocedorEnDispositivo ->
            ModoDictado.EN_DISPOSITIVO
        capacidades.reconocedorSistema -> ModoDictado.SISTEMA
        else -> ModoDictado.NO_DISPONIBLE
    }

    /**
     * Elige el idioma para el reconocedor en el dispositivo con lo que reporta
     * RecognitionSupport. Lo instalado gana a lo que se está descargando, y
     * esto a lo que aún hay que descargar.
     */
    fun soporteIdioma(
        instalados: List<String>,
        pendientes: List<String>,
        descargables: List<String>,
        preferido: String = IDIOMA_PREFERIDO,
    ): SoporteIdioma {
        idiomaEspanol(instalados, preferido)?.let { return SoporteIdioma.Listo(it) }
        idiomaEspanol(pendientes, preferido)?.let { return SoporteIdioma.Descargando(it) }
        idiomaEspanol(descargables, preferido)?.let { return SoporteIdioma.Descargable(it) }
        return SoporteIdioma.NoSoportado
    }

    /**
     * La etiqueta (tal como la reporta el teléfono) más cercana a [preferido]:
     * la exacta, una variante latinoamericana o, al final, cualquier español.
     */
    fun idiomaEspanol(disponibles: List<String>, preferido: String = IDIOMA_PREFERIDO): String? {
        val porClave = disponibles.associateBy(::normalizar)
        porClave[normalizar(preferido)]?.let { return it }
        ESPANOL_CERCANO.firstNotNullOfOrNull { porClave[normalizar(it)] }?.let { return it }
        val idiomaBase = normalizar(preferido).substringBefore('-')
        return disponibles.firstOrNull { normalizar(it).substringBefore('-') == idiomaBase }
    }

    fun reaccionAError(modo: ModoDictado, error: Int, preferirSinConexion: Boolean): ReaccionError =
        when {
            modo == ModoDictado.EN_DISPOSITIVO && error in ERRORES_SIN_MODELO_EN_DISPOSITIVO ->
                ReaccionError.CAMBIAR_A_SISTEMA
            modo == ModoDictado.SISTEMA && preferirSinConexion && error in ERRORES_SIN_PAQUETE_OFFLINE ->
                ReaccionError.QUITAR_PREFERENCIA_SIN_CONEXION
            else -> ReaccionError.MOSTRAR
        }

    /** Texto breve y verificable de dónde se transcribe la voz; null si no hay dictado. */
    fun avisoPrivacidad(modo: ModoDictado): String? = when (modo) {
        ModoDictado.EN_DISPOSITIVO ->
            "La voz se transcribe en este teléfono. NexoMark solo recibe el texto."
        ModoDictado.SISTEMA ->
            "El reconocedor del teléfono puede enviar el audio a Google para transcribirlo. " +
                "NexoMark solo recibe el texto."
        ModoDictado.NO_DISPONIBLE -> null
    }

    /** Extras del Intent de dictado. Se separan del Intent para poder probarlos. */
    fun extrasDictado(idioma: String, preferirSinConexion: Boolean): Map<String, Any> = mapOf(
        RecognizerIntent.EXTRA_LANGUAGE_MODEL to RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
        RecognizerIntent.EXTRA_LANGUAGE to idioma,
        RecognizerIntent.EXTRA_PARTIAL_RESULTS to true,
        RecognizerIntent.EXTRA_PREFER_OFFLINE to preferirSinConexion,
    )

    private val ERRORES_SIN_MODELO_EN_DISPOSITIVO = setOf(
        SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED,
        SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE,
        SpeechRecognizer.ERROR_SERVER_DISCONNECTED,
    )

    private val ERRORES_SIN_PAQUETE_OFFLINE = setOf(
        SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED,
        SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE,
        SpeechRecognizer.ERROR_SERVER,
    )

    private fun normalizar(etiqueta: String) = etiqueta.trim().replace('_', '-').lowercase()
}
