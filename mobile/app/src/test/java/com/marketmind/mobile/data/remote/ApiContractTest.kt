package com.marketmind.mobile.data.remote

import com.google.gson.Gson
import com.marketmind.mobile.data.remote.dto.RefreshResponse
import com.marketmind.mobile.data.remote.dto.StatusUpdateRequestDto
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
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
}
