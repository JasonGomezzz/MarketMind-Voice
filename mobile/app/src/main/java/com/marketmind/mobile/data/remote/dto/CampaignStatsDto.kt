package com.marketmind.mobile.data.remote.dto

import com.google.gson.annotations.SerializedName

data class CampaignStatsDto(
    val total: Int = 0,
    @SerializedName("tokens_disponibles")
    val tokensDisponibles: Int = 0,
    val borrador: Int = 0,
    @SerializedName("pendiente_ia")
    val pendienteIa: Int = 0,
    val generado: Int = 0,
    @SerializedName("pendiente_aprobacion")
    val pendienteAprobacion: Int = 0,
    val aprobado: Int = 0,
    val rechazado: Int = 0,
)
