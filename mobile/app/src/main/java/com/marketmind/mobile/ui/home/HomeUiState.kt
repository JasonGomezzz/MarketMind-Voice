package com.marketmind.mobile.ui.home

import com.marketmind.mobile.data.remote.dto.CampaignDto

sealed interface HomeUiState {
    data object Loading : HomeUiState
    data class Success(
        val items: List<CampaignDto>,
        val refreshing: Boolean = false,
    ) : HomeUiState
    data object Empty : HomeUiState
    data class Error(val message: String) : HomeUiState
}
