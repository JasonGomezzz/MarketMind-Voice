package com.marketmind.mobile.ui.voice

import android.speech.SpeechRecognizer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class IntentFormMapperTest {

    private val opciones = mapOf(
        "industria" to listOf("gastronomia", "moda"),
        "tono" to listOf("casual", "profesional"),
        "plataforma" to listOf("facebook", "instagram", "linkedin"),
    )

    @Test
    fun onlyFillsListFieldsWithOptionsTheAppOffers() {
        val resultado = IntentFormMapper.paraFormulario(
            mapOf(
                "titulo" to "  2x1 en capuchinos ",
                "cliente_nombre" to null,
                "cliente_email" to "",
                "industria" to "gastronomia",
                "tono" to "juvenil",
                "plataforma" to "tiktok",
                "prompt" to "Campaña 2x1 para universitarios",
                "estado" to "aprobado",
            ),
            opciones,
        )

        assertEquals(
            mapOf(
                "titulo" to "2x1 en capuchinos",
                "industria" to "gastronomia",
                "prompt" to "Campaña 2x1 para universitarios",
            ),
            resultado.valores,
        )
        assertEquals(listOf("cliente_nombre", "cliente_email", "tono", "plataforma"), resultado.pendientes)
        assertEquals(
            listOf("nombre del cliente", "email del cliente", "tono", "plataforma"),
            resultado.pendientesLegibles,
        )
    }

    @Test
    fun toleratesAMissingIntent() {
        val resultado = IntentFormMapper.paraFormulario(null, opciones)
        assertTrue(resultado.valores.isEmpty())
        assertEquals(7, resultado.pendientes.size)
    }

    @Test
    fun dictationIsAppendedWithSingleSpacesAndCapped() {
        assertEquals("hola", IntentFormMapper.agregarDictado("", "  hola "))
        assertEquals(
            "campaña para Instagram",
            IntentFormMapper.agregarDictado("campaña  para", "Instagram"),
        )
        assertEquals(2000, IntentFormMapper.agregarDictado("a".repeat(2000), "extra").length)
    }

    @Test
    fun recognizerErrorsBecomeActionableMessages() {
        assertTrue(speechErrorMessage(SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS)!!.contains("permiso"))
        assertTrue(speechErrorMessage(SpeechRecognizer.ERROR_NETWORK)!!.contains("conexión"))
        assertNull(speechErrorMessage(SpeechRecognizer.ERROR_CLIENT))
    }
}
