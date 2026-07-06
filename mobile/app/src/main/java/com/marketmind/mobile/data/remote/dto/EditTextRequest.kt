package com.marketmind.mobile.data.remote.dto

import com.google.gson.annotations.SerializedName

/**
 * Body del PATCH /api/campaigns/{id}/ para editar manualmente el copy.
 * El backend (CampaignEditSerializer) solo acepta prompt y texto_generado.
 */
data class EditTextRequest(
    @SerializedName("texto_generado")
    val textoGenerado: String,
)
