package com.marketmind.mobile.ui.client

import com.marketmind.mobile.data.remote.dto.CampaignDto

sealed interface ClientHomeUiState {
    data object Loading : ClientHomeUiState
    data class Success(
        val items: List<CampaignDto>,
        val refreshing: Boolean = false,
    ) : ClientHomeUiState
    data object Empty : ClientHomeUiState
    data class Error(val message: String) : ClientHomeUiState
}
