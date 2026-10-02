package com.marketmind.mobile.data.remote.dto

import com.google.gson.annotations.SerializedName

/** POST /api/intents/interpret/ — el brief ya transcrito en el teléfono. */
data class InterpretRequest(
    val texto: String,
    /** "voz" si se dictó, "formulario" si se escribió. */
    val origen: String,
)

/** POST /api/intents/{id}/confirm/ — campos finales tras las correcciones. */
data class ConfirmIntentRequest(
    val campos: Map<String, String?>,
)

/**
 * Intención de campaña devuelta por Django.
 * Campos nullables: Gson no aplica valores por defecto de Kotlin.
 */
data class CampaignIntentDto(
    val id: Long,
    val estado: String?,
    @SerializedName("campos_finales")
    val camposFinales: Map<String, String?>?,
    @SerializedName("campos_faltantes")
    val camposFaltantes: List<String>?,
    val advertencias: List<String>?,
)

data class IntentEnvelopeDto(
    val intent: CampaignIntentDto,
    val campaign: CampaignDto?,
)
