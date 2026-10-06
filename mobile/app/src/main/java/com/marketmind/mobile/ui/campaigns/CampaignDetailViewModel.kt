package com.marketmind.mobile.ui.campaigns

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketmind.mobile.data.remote.dto.PublicationDto
import com.marketmind.mobile.data.repository.CampaignRepository
import com.marketmind.mobile.data.repository.SocialRepository
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
    private val socialRepository: SocialRepository,
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

    /** Abre la hoja de envío y carga las cuentas donde se puede publicar al aprobar. */
    fun sendToClient() {
        val current = _uiState.value as? CampaignDetailUiState.Success ?: return
        if (current.submitting || current.deleting) return
        _uiState.value = current.copy(eligiendoDestinos = true, destinos = null, elegidos = emptySet())
        val email = current.campaign.clienteEmail
        viewModelScope.launch {
            val destinos = if (email.isNullOrBlank()) emptyList() else socialRepository.destinos(email).getOrDefault(emptyList())
            updateSuccess { it.copy(destinos = destinos) }
        }
    }

    fun toggleDestino(id: Long) = updateSuccess {
        it.copy(elegidos = if (id in it.elegidos) it.elegidos - id else it.elegidos + id)
    }

    fun cancelSend() = updateSuccess { it.copy(eligiendoDestinos = false) }

    fun confirmSend() {
        val current = _uiState.value as? CampaignDetailUiState.Success ?: return
        submit(
            successMessage = if (current.elegidos.isEmpty()) "Campaña enviada al cliente"
            else "Campaña enviada: se publicará cuando el cliente apruebe",
            destinos = current.elegidos.toList(),
        )
    }

    /** "Publicar ahora / Reintentar" de una publicación ya aprobada. */
    fun publish(publicacion: PublicationDto) {
        val current = _uiState.value as? CampaignDetailUiState.Success ?: return
        if (current.publicando != null) return
        _uiState.value = current.copy(publicando = publicacion.id)
        viewModelScope.launch {
            socialRepository.publicar(publicacion.id)
                .onSuccess { _events.send(CampaignDetailEvent.ShowSnackbar("Publicado en ${publicacion.cuentaNombre}")) }
                .onFailure { _events.send(CampaignDetailEvent.ShowSnackbar(it.message ?: "No se pudo publicar.")) }
            updateSuccess { it.copy(publicando = null) }
            loadPublicaciones()
        }
    }

    private fun updateSuccess(transform: (CampaignDetailUiState.Success) -> CampaignDetailUiState.Success) {
        val current = _uiState.value as? CampaignDetailUiState.Success ?: return
        _uiState.value = transform(current)
    }

    private fun loadPublicaciones() {
        viewModelScope.launch {
            socialRepository.publicaciones(campaignId)
                .onSuccess { lista -> updateSuccess { it.copy(publicaciones = lista) } }
        }
    }

    fun deleteCampaign() {
        val current = _uiState.value as? CampaignDetailUiState.Success ?: return
        if (current.submitting || current.deleting) return

        viewModelScope.launch {
            _uiState.value = current.copy(deleting = true)
            repository.deleteCampaign(id = current.campaign.id)
                .onSuccess {
                    _events.send(CampaignDetailEvent.ShowSnackbar("Campaña eliminada"))
                    _events.send(CampaignDetailEvent.NavigateBack)
                }
                .onFailure { err ->
                    _uiState.value = current.copy(deleting = false)
                    _events.send(
                        CampaignDetailEvent.ShowSnackbar(
                            err.message ?: "No se pudo eliminar la campaña."
                        )
                    )
                }
        }
    }

    private fun submit(successMessage: String, destinos: List<Long>) {
        val current = _uiState.value as? CampaignDetailUiState.Success ?: return
        if (current.submitting || current.deleting) return

        viewModelScope.launch {
            _uiState.value = current.copy(submitting = true)
            repository.submitToClient(id = current.campaign.id, destinos = destinos)
                .onSuccess {
                    _events.send(CampaignDetailEvent.ShowSnackbar(successMessage))
                    _events.send(CampaignDetailEvent.NavigateBack)
                }
                .onFailure { err ->
                    _uiState.value = current.copy(submitting = false, eligiendoDestinos = false)
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
                .onSuccess {
                    _uiState.value = CampaignDetailUiState.Success(it)
                    loadPublicaciones()
                }
                .onFailure {
                    _uiState.value = CampaignDetailUiState.Error(
                        it.message ?: "Error desconocido al cargar la campaña."
                    )
                }
        }
    }
}
