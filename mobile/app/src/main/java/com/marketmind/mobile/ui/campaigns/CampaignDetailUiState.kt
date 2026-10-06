package com.marketmind.mobile.ui.campaigns

import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.PublicationDto
import com.marketmind.mobile.data.remote.dto.SocialConnectionDto

sealed interface CampaignDetailUiState {
    data object Loading : CampaignDetailUiState
    data class Success(
        val campaign: CampaignDto,
        val submitting: Boolean = false,
        val deleting: Boolean = false,
        /** Publicaciones de la campaña en Instagram/Facebook (vacío si no tiene destinos). */
        val publicaciones: List<PublicationDto> = emptyList(),
        val publicando: Long? = null,
        /** Hoja "Enviar al cliente" abierta; destinos null mientras cargan. */
        val eligiendoDestinos: Boolean = false,
        val destinos: List<SocialConnectionDto>? = null,
        val elegidos: Set<Long> = emptySet(),
    ) : CampaignDetailUiState
    data class Error(val message: String) : CampaignDetailUiState
}
