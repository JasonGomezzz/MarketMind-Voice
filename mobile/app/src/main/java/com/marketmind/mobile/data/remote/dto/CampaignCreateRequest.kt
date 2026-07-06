package com.marketmind.mobile.data.remote.dto

import com.google.gson.annotations.SerializedName

data class CampaignCreateRequest(
    val titulo: String,
    @SerializedName("cliente_nombre")
    val clienteNombre: String,
    @SerializedName("cliente_email")
    val clienteEmail: String,
    val industria: String,
    val tono: String,
    val plataforma: String,
    val prompt: String,
)

data class CampaignEnvelopeDto(
    val campaign: CampaignDto,
)
