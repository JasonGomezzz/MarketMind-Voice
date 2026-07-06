package com.marketmind.mobile.ui.client

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketmind.mobile.data.repository.ClientCampaignRepository
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

/**
 * ViewModel del detalle de campaña del CLIENTE.
 * Carga el detalle vía Spring Boot (:8080) y permite aprobar/rechazar.
 * El rechazo exige feedback obligatorio (10..500 chars, validado en Spring).
 * Usa el campo [CampaignDto.version] para el optimistic locking (@Version JPA).
 */
@HiltViewModel
class ClientCampaignDetailViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val repository: ClientCampaignRepository,
) : ViewModel() {

    private val campaignId: Long = checkNotNull(
        savedStateHandle.get<Long>(Routes.CLIENT_CAMPAIGN_DETAIL_ARG_ID),
    ) { "campaignId es obligatorio en ClientCampaignDetailScreen" }

    private val _uiState = MutableStateFlow<ClientCampaignDetailUiState>(ClientCampaignDetailUiState.Loading)
    val uiState: StateFlow<ClientCampaignDetailUiState> = _uiState.asStateFlow()

    private val _events = Channel<ClientCampaignDetailEvent>(Channel.BUFFERED)
    val events: Flow<ClientCampaignDetailEvent> = _events.receiveAsFlow()

    init {
        load()
    }

    fun retry() = load()

    fun approve() = submit(estado = "aprobado", successMessage = "Campaña aprobada ✓")

    fun reject(feedback: String) = submit(
        estado = "rechazado",
        successMessage = "Campaña rechazada",
        feedback = feedback,
    )

    private fun submit(estado: String, successMessage: String, feedback: String? = null) {
        val current = _uiState.value as? ClientCampaignDetailUiState.Success ?: return
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
                    _events.send(ClientCampaignDetailEvent.ShowSnackbar(successMessage))
                    _events.send(ClientCampaignDetailEvent.NavigateBack)
                }
                .onFailure { err ->
                    _uiState.value = current.copy(submitting = false)
                    _events.send(
                        ClientCampaignDetailEvent.ShowSnackbar(
                            err.message ?: "Error desconocido al actualizar la campaña.",
                        ),
                    )
                }
        }
    }

    private fun load() {
        viewModelScope.launch {
            _uiState.value = ClientCampaignDetailUiState.Loading
            repository.getCampaignById(campaignId)
                .onSuccess { _uiState.value = ClientCampaignDetailUiState.Success(it) }
                .onFailure {
                    _uiState.value = ClientCampaignDetailUiState.Error(
                        it.message ?: "Error desconocido al cargar la campaña.",
                    )
                }
        }
    }
}
