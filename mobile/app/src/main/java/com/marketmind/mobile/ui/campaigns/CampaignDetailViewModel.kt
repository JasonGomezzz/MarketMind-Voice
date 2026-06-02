package com.marketmind.mobile.ui.campaigns

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketmind.mobile.data.repository.CampaignRepository
import com.marketmind.mobile.ui.navigation.Routes
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CampaignDetailViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val repository: CampaignRepository,
) : ViewModel() {

    private val campaignId: Long = checkNotNull(
        savedStateHandle.get<Long>(Routes.CAMPAIGN_DETAIL_ARG_ID)
    ) { "campaignId es obligatorio en CampaignDetailScreen" }

    private val _uiState = MutableStateFlow<CampaignDetailUiState>(CampaignDetailUiState.Loading)
    val uiState: StateFlow<CampaignDetailUiState> = _uiState.asStateFlow()

    init {
        load()
    }

    fun retry() = load()

    private fun load() {
        viewModelScope.launch {
            _uiState.value = CampaignDetailUiState.Loading
            repository.getCampaignById(campaignId)
                .onSuccess { _uiState.value = CampaignDetailUiState.Success(it) }
                .onFailure {
                    _uiState.value = CampaignDetailUiState.Error(
                        it.message ?: "Error desconocido al cargar la campaña."
                    )
                }
        }
    }
}
