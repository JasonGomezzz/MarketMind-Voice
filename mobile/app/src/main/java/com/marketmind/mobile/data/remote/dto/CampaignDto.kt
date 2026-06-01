package com.marketmind.mobile.data.remote.dto

data class CampaignDto(
    val id: Long,
    val titulo: String?,
    val clienteNombre: String?,
    val industria: String?,
    val tono: String?,
    val plataforma: String?,
    val prompt: String?,
    val textoGenerado: String?,
    val imagenUrl: String?,
    val tokensConsumidos: Int?,
    val intentosGeneracion: Int?,
    val estado: String,
    val marketeroId: Long?,
    val fechaCreacion: String?,
    val fechaActualizacion: String?,
    val version: Int,
)
