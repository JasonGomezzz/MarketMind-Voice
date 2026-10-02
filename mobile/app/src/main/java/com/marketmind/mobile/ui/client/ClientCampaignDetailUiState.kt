package com.marketmind.mobile.ui.client

import com.marketmind.mobile.data.remote.dto.CampaignDto

sealed interface ClientCampaignDetailUiState {
    data object Loading : ClientCampaignDetailUiState
    data class Success(
        val campaign: CampaignDto,
        val submitting: Boolean = false,
        val rating: Int = 0,
    ) : ClientCampaignDetailUiState
    data class Error(val message: String) : ClientCampaignDetailUiState
}
