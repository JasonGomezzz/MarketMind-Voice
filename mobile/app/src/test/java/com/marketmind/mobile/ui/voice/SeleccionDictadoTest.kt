package com.marketmind.mobile.ui.voice

import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class SeleccionDictadoTest {

    private fun capacidades(sdk: Int, sistema: Boolean, enDispositivo: Boolean) =
        CapacidadesVoz(sdk = sdk, reconocedorSistema = sistema, reconocedorEnDispositivo = enDispositivo)

    @Test
    fun prefersTheOnDeviceRecognizerFromAndroid12() {
        assertEquals(ModoDictado.EN_DISPOSITIVO, SeleccionDictado.modoInicial(capacidades(31, true, true)))
        assertEquals(ModoDictado.EN_DISPOSITIVO, SeleccionDictado.modoInicial(capacidades(36, false, true)))
    }

    @Test
    fun fallsBackToTheSystemRecognizerWhenThereIsNoOnDeviceOne() {
        assertEquals(ModoDictado.SISTEMA, SeleccionDictado.modoInicial(capacidades(34, true, false)))
        // Antes de Android 12 no existe la API en el dispositivo aunque algo diga lo contrario.
        assertEquals(ModoDictado.SISTEMA, SeleccionDictado.modoInicial(capacidades(30, true, true)))
    }

    @Test
    fun reportsNoDictationWithoutAnyRecognizer() {
        assertEquals(ModoDictado.NO_DISPONIBLE, SeleccionDictado.modoInicial(capacidades(24, false, false)))
        assertEquals(ModoDictado.NO_DISPONIBLE, SeleccionDictado.modoInicial(capacidades(30, false, true)))
    }

    @Test
    fun usesPeruvianSpanishWhenItIsInstalled() {
        assertEquals(
            SoporteIdioma.Listo("es-PE"),
            SeleccionDictado.soporteIdioma(listOf("en-US", "es-US", "es-PE"), emptyList(), emptyList()),
        )
    }

    @Test
    fun acceptsTheClosestInstalledSpanishVariant() {
        assertEquals(
            SoporteIdioma.Listo("es-US"),
            SeleccionDictado.soporteIdioma(listOf("en-US", "es-ES", "es-US"), emptyList(), emptyList()),
        )
        assertEquals(
            SoporteIdioma.Listo("es_ES"),
            SeleccionDictado.soporteIdioma(listOf("en-US", "es_ES"), emptyList(), emptyList()),
        )
    }

    @Test
    fun installedSpanishWinsOverPendingAndDownloadableOnes() {
        assertEquals(
            SoporteIdioma.Descargando("es-PE"),
            SeleccionDictado.soporteIdioma(listOf("en-US"), listOf("es-PE"), listOf("es-ES")),
        )
        assertEquals(
            SoporteIdioma.Descargable("es-419"),
            SeleccionDictado.soporteIdioma(listOf("en-US"), emptyList(), listOf("es-ES", "es-419")),
        )
    }

    @Test
    fun reportsSpanishNotSupportedOnDevice() {
        assertEquals(
            SoporteIdioma.NoSoportado,
            SeleccionDictado.soporteIdioma(listOf("en-US"), emptyList(), listOf("pt-BR")),
        )
        assertNull(SeleccionDictado.idiomaEspanol(listOf("en-US", "pt-BR")))
        // Una etiqueta genérica de español sirve si no hay otra variante.
        assertEquals("es", SeleccionDictado.idiomaEspanol(listOf("en-US", "es")))
    }

    @Test
    fun missingOnDeviceLanguageSwitchesToTheSystemRecognizer() {
        listOf(
            SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED,
            SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE,
            SpeechRecognizer.ERROR_SERVER_DISCONNECTED,
        ).forEach { error ->
            assertEquals(
                ReaccionError.CAMBIAR_A_SISTEMA,
                SeleccionDictado.reaccionAError(ModoDictado.EN_DISPOSITIVO, error, preferirSinConexion = true),
            )
        }
    }

    @Test
    fun missingOfflinePackDropsThePreferenceOnlyOnce() {
        assertEquals(
            ReaccionError.QUITAR_PREFERENCIA_SIN_CONEXION,
            SeleccionDictado.reaccionAError(
                ModoDictado.SISTEMA,
                SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE,
                preferirSinConexion = true,
            ),
        )
        assertEquals(
            ReaccionError.MOSTRAR,
            SeleccionDictado.reaccionAError(
                ModoDictado.SISTEMA,
                SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE,
                preferirSinConexion = false,
            ),
        )
    }

    @Test
    fun ordinaryErrorsAreShownWithoutChangingTheEngine() {
        listOf(
            SpeechRecognizer.ERROR_NO_MATCH,
            SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS,
            SpeechRecognizer.ERROR_RECOGNIZER_BUSY,
        ).forEach { error ->
            assertEquals(
                ReaccionError.MOSTRAR,
                SeleccionDictado.reaccionAError(ModoDictado.EN_DISPOSITIVO, error, preferirSinConexion = true),
            )
            assertEquals(
                ReaccionError.MOSTRAR,
                SeleccionDictado.reaccionAError(ModoDictado.SISTEMA, error, preferirSinConexion = true),
            )
        }
    }

    @Test
    fun privacyNoticeOnlyPromisesWhatTheEngineDoes() {
        val enDispositivo = SeleccionDictado.avisoPrivacidad(ModoDictado.EN_DISPOSITIVO)!!
        val sistema = SeleccionDictado.avisoPrivacidad(ModoDictado.SISTEMA)!!
        assertTrue(enDispositivo.contains("en este teléfono"))
        assertFalse(enDispositivo.contains("Google"))
        assertTrue(sistema.contains("puede enviar el audio a Google"))
        listOf(enDispositivo, sistema).forEach { assertTrue(it.contains("solo recibe el texto")) }
        assertNull(SeleccionDictado.avisoPrivacidad(ModoDictado.NO_DISPONIBLE))
    }

    @Test
    fun dictationIntentAsksForOfflineSpanishWithPartialResults() {
        val extras = SeleccionDictado.extrasDictado("es-PE", preferirSinConexion = true)
        assertEquals("es-PE", extras[RecognizerIntent.EXTRA_LANGUAGE])
        assertEquals(true, extras[RecognizerIntent.EXTRA_PREFER_OFFLINE])
        assertEquals(true, extras[RecognizerIntent.EXTRA_PARTIAL_RESULTS])
        assertEquals(RecognizerIntent.LANGUAGE_MODEL_FREE_FORM, extras[RecognizerIntent.EXTRA_LANGUAGE_MODEL])
        assertEquals(
            false,
            SeleccionDictado.extrasDictado("es-PE", preferirSinConexion = false)[RecognizerIntent.EXTRA_PREFER_OFFLINE],
        )
    }
}
