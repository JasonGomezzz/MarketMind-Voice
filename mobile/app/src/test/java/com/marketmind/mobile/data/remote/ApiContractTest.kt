package com.marketmind.mobile.data.remote

import com.google.gson.Gson
import com.marketmind.mobile.data.remote.dto.ApiEnvelope
import com.marketmind.mobile.data.remote.dto.ConfirmIntentRequest
import com.marketmind.mobile.data.remote.dto.IntentEnvelopeDto
import com.marketmind.mobile.data.remote.dto.InterpretRequest
import com.marketmind.mobile.data.remote.dto.RefreshResponse
import com.marketmind.mobile.data.remote.dto.StatusUpdateRequestDto
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import com.google.gson.reflect.TypeToken
import org.junit.Test

class ApiContractTest {
    private val gson = Gson()

    @Test
    fun djangoRefreshRetainsTheRotatedRefreshToken() {
        val response = gson.fromJson(
            """{"access":"new-access","refresh":"rotated-refresh"}""",
            RefreshResponse::class.java,
        )

        assertEquals("new-access", response.access)
        assertEquals("rotated-refresh", response.refresh)
    }

    @Test
    fun refreshResponseAlsoSupportsServersWithoutRotation() {
        val response = gson.fromJson(
            """{"access":"new-access"}""",
            RefreshResponse::class.java,
        )

        assertEquals("new-access", response.access)
        assertNull(response.refresh)
    }

    @Test
    fun everyReviewSendsTheRatingRequiredBySpring() {
        listOf("aprobado", "rechazado").forEach { estado ->
            val request = StatusUpdateRequestDto(
                estado = estado,
                version = 3,
                valoracion = 4,
                feedback = if (estado == "rechazado") "Cambiar el texto del anuncio" else null,
            )
            val payload = gson.toJsonTree(request).asJsonObject

            assertEquals(estado, payload["estado"].asString)
            assertEquals(3, payload["version"].asInt)
            assertEquals(4, payload["valoracion"].asInt)
            if (estado == "rechazado") {
                assertEquals("Cambiar el texto del anuncio", payload["feedback"].asString)
            }
        }
    }

    @Test
    fun interpretSendsTheTranscribedTextAndItsOrigin() {
        val payload = gson.toJsonTree(InterpretRequest(texto = "Campaña para una cafetería", origen = "voz")).asJsonObject

        assertEquals("Campaña para una cafetería", payload["texto"].asString)
        assertEquals("voz", payload["origen"].asString)
    }

    @Test
    fun confirmSendsSnakeCaseFieldsAndKeepsNulls() {
        val payload = Gson().newBuilder().serializeNulls().create().toJsonTree(
            ConfirmIntentRequest(mapOf("cliente_email" to "cliente@test.com", "tono" to null)),
        ).asJsonObject["campos"].asJsonObject

        assertEquals("cliente@test.com", payload["cliente_email"].asString)
        assertTrue(payload["tono"].isJsonNull)
    }

    @Test
    fun parsesTheIntentEnvelopeReturnedByDjango() {
        val json = """
            {"success": true, "message": "ok", "data": {"intent": {
              "id": 7, "estado": "borrador",
              "campos_finales": {"titulo": "Promo", "tono": null},
              "campos_faltantes": ["cliente_email"],
              "advertencias": ["No reconocí el tono «juvenil»."]
            }}}
        """.trimIndent()
        val type = object : TypeToken<ApiEnvelope<IntentEnvelopeDto>>() {}.type
        val envelope: ApiEnvelope<IntentEnvelopeDto> = gson.fromJson(json, type)
        val intent = envelope.data!!.intent

        assertEquals(7L, intent.id)
        assertEquals("Promo", intent.camposFinales!!["titulo"])
        assertNull(intent.camposFinales!!["tono"])
        assertEquals(listOf("cliente_email"), intent.camposFaltantes)
        assertEquals(1, intent.advertencias!!.size)
        assertNull(envelope.data!!.campaign)
    }
}
