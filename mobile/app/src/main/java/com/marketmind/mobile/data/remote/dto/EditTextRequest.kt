package com.marketmind.mobile.data.remote.dto

import com.google.gson.annotations.SerializedName

/**
 * Body del PATCH /api/campaigns/{id}/ para editar manualmente el copy.
 * `version` es la que se leyó de la campaña (bloqueo optimista): si alguien
 * la cambió antes, Django responde 409 y no guarda.
 */
data class EditTextRequest(
    @SerializedName("texto_generado")
    val textoGenerado: String,
    val version: Int,
)
