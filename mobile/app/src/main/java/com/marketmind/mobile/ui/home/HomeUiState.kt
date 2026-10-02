package com.marketmind.mobile.ui.home

import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.CampaignIntentDto
import com.marketmind.mobile.data.remote.dto.CampaignStatsDto
import com.marketmind.mobile.data.repository.UserSession

sealed interface HomeUiState {
    data object Loading : HomeUiState
    data class Success(
        val user: UserSession,
        val items: List<CampaignDto>,
        val stats: CampaignStatsDto,
        val refreshing: Boolean = false,
        val creating: Boolean = false,
        val message: String? = null,
        // Brief interpretado (voz o texto) pendiente de confirmar en el formulario.
        val interpreting: Boolean = false,
        val intent: CampaignIntentDto? = null,
    ) : HomeUiState
    data object Empty : HomeUiState
    data class Error(val message: String) : HomeUiState
}
