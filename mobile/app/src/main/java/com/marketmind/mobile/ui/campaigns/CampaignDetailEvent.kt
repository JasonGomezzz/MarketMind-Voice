package com.marketmind.mobile.ui.campaigns

sealed interface CampaignDetailEvent {
    data class ShowSnackbar(val message: String) : CampaignDetailEvent
    data object NavigateBack : CampaignDetailEvent
}
