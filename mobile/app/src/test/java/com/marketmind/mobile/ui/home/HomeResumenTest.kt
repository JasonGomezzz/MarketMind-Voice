package com.marketmind.mobile.ui.home

import com.marketmind.mobile.data.remote.dto.CampaignStatsDto
import org.junit.Assert.assertEquals
import org.junit.Test

class HomeResumenTest {

    @Test
    fun prioritizesCampaignsReadyToSendAndShowsTheRealApprovalRate() {
        val resumen = resumenInicio(CampaignStatsDto(generado = 2, pendienteAprobacion = 1, aprobado = 3, rechazado = 1))
        assertEquals("2 campañas generadas listas para enviar al cliente.", resumen.titulo)
        assertEquals("Aprobación de tus clientes: 75% (3 de 4 decididas)", resumen.detalle)
    }

    @Test
    fun withoutDecisionsItShowsCreditsInsteadOfARate() {
        val resumen = resumenInicio(CampaignStatsDto(pendienteAprobacion = 1, tokensDisponibles = 5))
        assertEquals("1 campaña espera la aprobación del cliente.", resumen.titulo)
        assertEquals("Créditos de IA disponibles: 5", resumen.detalle)
    }

    @Test
    fun emptyAccountInvitesToDictate() {
        assertEquals(
            "Dicta una idea en la pestaña IA para crear tu próxima campaña.",
            resumenInicio(CampaignStatsDto()).titulo,
        )
    }

    @Test
    fun statusLabelsAreTheRealStatesInSpanish() {
        assertEquals("Generada", etiquetaEstadoCorta("generado"))
        assertEquals("Por aprobar", etiquetaEstadoCorta("pendiente_aprobacion"))
        assertEquals("nuevo", etiquetaEstadoCorta("nuevo"))
    }
}
