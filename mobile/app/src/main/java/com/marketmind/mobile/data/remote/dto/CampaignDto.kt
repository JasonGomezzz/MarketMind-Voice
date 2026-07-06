package com.marketmind.mobile.data.remote.dto

import com.google.gson.annotations.SerializedName

data class CampaignDto(
    val id: Long,
    val titulo: String?,
    @SerializedName(value = "clienteNombre", alternate = ["cliente_nombre"])
    val clienteNombre: String?,
    val industria: String?,
    val tono: String?,
    val plataforma: String?,
    val prompt: String?,
    @SerializedName(value = "textoGenerado", alternate = ["texto_generado"])
    val textoGenerado: String?,
    @SerializedName(value = "imagenUrl", alternate = ["imagen_url"])
    val imagenUrl: String?,
    @SerializedName(value = "imagenB64", alternate = ["imagen_b64"])
    val imagenB64: String? = null,
    @SerializedName(value = "tokensConsumidos", alternate = ["tokens_consumidos"])
    val tokensConsumidos: Int?,
    @SerializedName(value = "intentosGeneracion", alternate = ["intentos_generacion"])
    val intentosGeneracion: Int?,
    val estado: String,
    @SerializedName(value = "feedbackRechazo", alternate = ["feedback_rechazo"])
    val feedbackRechazo: String? = null,
    @SerializedName(value = "marketeroId", alternate = ["marketero_id"])
    val marketeroId: Long?,
    @SerializedName(value = "fechaCreacion", alternate = ["fecha_creacion"])
    val fechaCreacion: String?,
    @SerializedName(value = "fechaActualizacion", alternate = ["fecha_actualizacion"])
    val fechaActualizacion: String?,
    val version: Int = 1,
)
