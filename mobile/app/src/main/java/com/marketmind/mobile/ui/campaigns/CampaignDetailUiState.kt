package com.marketmind.mobile.ui.campaigns

import com.marketmind.mobile.data.remote.dto.CampaignDto

sealed interface CampaignDetailUiState {
    data object Loading : CampaignDetailUiState
    data class Success(
        val campaign: CampaignDto,
        val submitting: Boolean = false,
    ) : CampaignDetailUiState
    data class Error(val message: String) : CampaignDetailUiState
}
