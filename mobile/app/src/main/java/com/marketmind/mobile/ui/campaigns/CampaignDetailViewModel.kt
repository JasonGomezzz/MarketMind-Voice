package com.marketmind.mobile.ui.campaigns

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketmind.mobile.data.repository.CampaignRepository
import com.marketmind.mobile.ui.navigation.Routes
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
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

    private val _events = Channel<CampaignDetailEvent>(Channel.BUFFERED)
    val events: Flow<CampaignDetailEvent> = _events.receiveAsFlow()

    init {
        load()
    }

    fun retry() = load()

    fun approve() = submit(estado = "aprobado", successMessage = "Campaña aprobada ✓")

    fun reject(feedback: String) = submit(estado = "rechazado", successMessage = "Campaña rechazada", feedback = feedback)

    private fun submit(estado: String, successMessage: String, feedback: String? = null) {
        val current = _uiState.value as? CampaignDetailUiState.Success ?: return
        if (current.submitting) return

        viewModelScope.launch {
            _uiState.value = current.copy(submitting = true)
            repository.updateStatus(
                id = current.campaign.id,
                estado = estado,
                version = current.campaign.version,
                feedback = feedback,
            )
                .onSuccess {
                    _events.send(CampaignDetailEvent.ShowSnackbar(successMessage))
                    _events.send(CampaignDetailEvent.NavigateBack)
                }
                .onFailure { err ->
                    _uiState.value = current.copy(submitting = false)
                    _events.send(
                        CampaignDetailEvent.ShowSnackbar(
                            err.message ?: "Error desconocido al actualizar la campaña."
                        )
                    )
                }
        }
    }

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
