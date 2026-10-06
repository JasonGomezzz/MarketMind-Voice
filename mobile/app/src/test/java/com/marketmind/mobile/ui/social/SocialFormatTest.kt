package com.marketmind.mobile.ui.social

import com.marketmind.mobile.data.remote.dto.PublicationDto
import com.marketmind.mobile.data.remote.dto.PublicationMetricDto
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class SocialFormatTest {

    private fun publicacion(estado: String, intentos: Int = 0) = PublicationDto(
        id = 1, campaign = 7, red = "instagram", cuentaNombre = "@nexomarkia", estado = estado, intentos = intentos,
    )

    @Test
    fun missingMetaValuesAreNeverShownAsZero() {
        assertEquals("sin dato", SocialFormat.formatoMetrica(null))
        assertEquals("0", SocialFormat.formatoMetrica(0))
        assertEquals("sin dato", SocialFormat.formatoMetrica(SocialFormat.valor(PublicationMetricDto(meGusta = 4), "compartidos")))
        assertEquals("4", SocialFormat.formatoMetrica(SocialFormat.valor(PublicationMetricDto(meGusta = 4), "me_gusta")))
    }

    @Test
    fun facebookNamesLikesAsReactionsAndHasNoSaves() {
        val facebook = SocialFormat.metricasDeRed("facebook")
        assertEquals("Reacciones", facebook.principales.first().etiqueta)
        assertFalse(facebook.secundarias.any { it.campo == "guardados" })
        assertTrue(SocialFormat.metricasDeRed("instagram").secundarias.any { it.campo == "guardados" })
    }

    @Test
    fun retryOnlyForApprovedCampaignsWithAttemptsLeft() {
        assertTrue(SocialFormat.puedeReintentar(publicacion("fallido", intentos = 1), "aprobado"))
        assertTrue(SocialFormat.puedeReintentar(publicacion("esperando_aprobacion"), "aprobado"))
        assertFalse(SocialFormat.puedeReintentar(publicacion("fallido", intentos = 3), "aprobado"))
        assertFalse(SocialFormat.puedeReintentar(publicacion("publicado", intentos = 1), "aprobado"))
        assertFalse(SocialFormat.puedeReintentar(publicacion("esperando_aprobacion"), "pendiente_aprobacion"))
    }

    @Test
    fun statesAndNetworksHaveSpanishLabels() {
        assertEquals("Publicado", SocialFormat.estadoPublicacion("publicado").texto)
        assertEquals(SocialFormat.Tono.Error, SocialFormat.estadoPublicacion("fallido").tono)
        assertEquals("nuevo", SocialFormat.estadoPublicacion("nuevo").texto)
        assertEquals("Instagram", SocialFormat.etiquetaRed("instagram"))
        assertEquals("tiktok", SocialFormat.etiquetaRed("tiktok"))
    }

    @Test
    fun parsesDjangoDatesWithMicrosecondsAndTimezones() {
        val conZ = SocialFormat.aEpochMs("2026-10-06T18:58:29.123456Z")
        val conOffset = SocialFormat.aEpochMs("2026-10-06T13:58:29-05:00")
        assertEquals(conZ, conOffset)
        assertNull(SocialFormat.aEpochMs(null))
        assertNull(SocialFormat.aEpochMs("no es fecha"))
    }

    @Test
    fun relativeTimeSpeaksPlainSpanish() {
        val ahora = SocialFormat.aEpochMs("2026-10-06T19:00:00Z")!!
        assertEquals("hace 1 min", SocialFormat.haceCuanto("2026-10-06T18:58:30Z", ahora))
        assertEquals("hace 3 h", SocialFormat.haceCuanto("2026-10-06T16:00:00Z", ahora))
        assertEquals("hace 1 día", SocialFormat.haceCuanto("2026-10-05T18:00:00Z", ahora))
        assertNull(SocialFormat.haceCuanto(null, ahora))
    }
}
