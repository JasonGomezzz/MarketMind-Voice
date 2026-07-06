package com.marketmind.mobile.ui.client

sealed interface ClientCampaignDetailEvent {
    data class ShowSnackbar(val message: String) : ClientCampaignDetailEvent
    data object NavigateBack : ClientCampaignDetailEvent
}
