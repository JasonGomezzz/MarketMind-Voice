package com.marketmind.mobile.data.remote

import com.google.gson.Gson
import com.marketmind.mobile.data.remote.dto.ApiEnvelope
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.PublicacionesEnvelopeDto
import com.marketmind.mobile.data.remote.dto.ResumenRedesDto
import com.marketmind.mobile.data.remote.dto.SubmitRequest
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

    @Test
    fun submitSendsTheChosenDestinationIds() {
        val payload = gson.toJsonTree(SubmitRequest(destinos = listOf(3L, 8L))).asJsonObject

        assertEquals(listOf(3L, 8L), payload["destinos"].asJsonArray.map { it.asLong })
        assertEquals(0, gson.toJsonTree(SubmitRequest(emptyList())).asJsonObject["destinos"].asJsonArray.size())
    }

    @Test
    fun parsesPublicationsWithNullMetricsFromDjango() {
        val json = """
            {"success": true, "message": "ok", "data": {"publicaciones": [{
              "id": 4, "campaign": 11, "campaign_titulo": "2x1 en capuchinos", "red": "facebook",
              "cuenta_nombre": "NexoMark IA", "estado": "publicado", "permalink": "https://facebook.com/p/1",
              "intentos": 1, "version_aprobada": 3, "publicado_at": "2026-10-06T18:58:29Z",
              "ultima_metrica": {"me_gusta": 6, "comentarios": 1, "compartidos": null, "obtenida_at": "2026-10-06T19:10:00Z"}
            }]}}
        """.trimIndent()
        val type = object : TypeToken<ApiEnvelope<PublicacionesEnvelopeDto>>() {}.type
        val envelope: ApiEnvelope<PublicacionesEnvelopeDto> = gson.fromJson(json, type)
        val publicacion = envelope.data!!.publicaciones!!.single()

        assertEquals("NexoMark IA", publicacion.cuentaNombre)
        assertEquals(3, publicacion.versionAprobada)
        assertEquals(6, publicacion.ultimaMetrica!!.meGusta)
        assertNull(publicacion.ultimaMetrica!!.compartidos)
    }

    @Test
    fun parsesTheNetworkSummaryKeepingMissingTotalsAsNull() {
        val json = """
            {"success": true, "message": "ok", "data": {"redes": {
              "instagram": {"publicaciones": 2, "publicaciones_mes": 1, "con_metricas": 2, "me_gusta": 15, "compartidos": null},
              "facebook": {"publicaciones": 0, "publicaciones_mes": 0, "con_metricas": 0}
            }, "total_publicaciones": 2, "fallidas": 1, "pendientes": 0}}
        """.trimIndent()
        val type = object : TypeToken<ApiEnvelope<ResumenRedesDto>>() {}.type
        val resumen: ResumenRedesDto = gson.fromJson<ApiEnvelope<ResumenRedesDto>>(json, type).data!!

        assertEquals(15, resumen.redes!!["instagram"]!!.meGusta)
        assertNull(resumen.redes!!["instagram"]!!.compartidos)
        assertNull(resumen.redes!!["facebook"]!!.meGusta)
        assertEquals(1, resumen.fallidas)
    }

    @Test
    fun clientCampaignFromSpringCarriesItsDestinations() {
        val json = """
            {"id": 11, "titulo": "2x1", "clienteNombre": "Café Aurora", "clienteEmail": "cliente@test.com",
             "estado": "pendiente_aprobacion", "version": 2,
             "destinos": [{"red": "instagram", "cuentaNombre": "@nexomarkia", "estado": "esperando_aprobacion", "permalink": null}]}
        """.trimIndent()
        val campaign = gson.fromJson(json, CampaignDto::class.java)

        assertEquals("cliente@test.com", campaign.clienteEmail)
        assertEquals("@nexomarkia", campaign.destinos!!.single().cuentaNombre)
    }
}
