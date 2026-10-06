package com.marketmind.mobile.ui.home

import com.marketmind.mobile.data.remote.dto.CampaignStatsDto

/**
 * Textos del inicio del marketero calculados con sus números reales
 * (reemplaza una tarjeta con una cifra inventada). Probado en HomeResumenTest.
 */
internal data class ResumenInicio(val titulo: String, val detalle: String)

internal fun resumenInicio(stats: CampaignStatsDto): ResumenInicio {
    val titulo = when {
        stats.generado > 0 -> if (stats.generado == 1) "1 campaña generada lista para enviar al cliente."
        else "${stats.generado} campañas generadas listas para enviar al cliente."
        stats.pendienteAprobacion > 0 -> if (stats.pendienteAprobacion == 1) "1 campaña espera la aprobación del cliente."
        else "${stats.pendienteAprobacion} campañas esperan la aprobación del cliente."
        stats.pendienteIa > 0 -> "La IA está generando ${stats.pendienteIa} ${if (stats.pendienteIa == 1) "campaña" else "campañas"}."
        else -> "Dicta una idea en la pestaña IA para crear tu próxima campaña."
    }
    val decididas = stats.aprobado + stats.rechazado
    val detalle = if (decididas > 0) {
        "Aprobación de tus clientes: ${stats.aprobado * 100 / decididas}% (${stats.aprobado} de $decididas decididas)"
    } else {
        "Créditos de IA disponibles: ${stats.tokensDisponibles}"
    }
    return ResumenInicio(titulo, detalle)
}

/** Etiqueta corta del estado real de la campaña para las listas. */
internal fun etiquetaEstadoCorta(estado: String): String = when (estado) {
    "borrador" -> "Borrador"
    "pendiente_ia" -> "Generando"
    "generado" -> "Generada"
    "pendiente_aprobacion" -> "Por aprobar"
    "aprobado" -> "Aprobada"
    "rechazado" -> "Rechazada"
    "fracaso" -> "Fracaso"
    else -> estado
}
