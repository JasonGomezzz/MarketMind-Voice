package com.marketmind.mobile.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.CampaignCreateRequest
import com.marketmind.mobile.data.remote.dto.CampaignStatsDto
import com.marketmind.mobile.data.repository.AuthRepository
import com.marketmind.mobile.data.repository.CampaignRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val campaignRepository: CampaignRepository,
    private val authRepository: AuthRepository,
) : ViewModel() {

    val nombre: String? = authRepository.getNombre()
    val role: String? = authRepository.getRole()

    private val _uiState = MutableStateFlow<HomeUiState>(HomeUiState.Loading)
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()
    private var pollingJob: Job? = null

    init {
        load()
    }

    fun load() {
        viewModelScope.launch {
            if (_uiState.value !is HomeUiState.Success) {
                _uiState.value = HomeUiState.Loading
            }
            fetch(markRefreshing = false)
        }
    }

    fun refresh() {
        viewModelScope.launch {
            val current = _uiState.value
            if (current is HomeUiState.Success) {
                _uiState.value = current.copy(refreshing = true)
            }
            fetch(markRefreshing = true)
        }
    }

    private suspend fun fetch(markRefreshing: Boolean, updatePolling: Boolean = true) {
        val user = authRepository.me().getOrElse { throwable ->
            _uiState.value = HomeUiState.Error(
                message = throwable.message ?: "Error desconocido al cargar la cuenta."
            )
            return
        }
        val items = campaignRepository.getMine().getOrElse { throwable ->
            _uiState.value = HomeUiState.Error(
                message = throwable.message ?: "Error desconocido al cargar campañas."
            )
            return
        }
        val stats = campaignRepository.getStats().getOrElse { CampaignStatsDto(total = items.size) }
        _uiState.value = HomeUiState.Success(
            user = user,
            items = items,
            stats = stats,
            refreshing = false,
        )
        if (updatePolling) {
            syncGenerationPolling(items)
        }
    }

    private fun syncGenerationPolling(items: List<CampaignDto>) {
        if (items.any { it.estado == "pendiente_ia" }) {
            startGenerationPolling()
        } else {
            pollingJob?.cancel()
            pollingJob = null
        }
    }

    private fun startGenerationPolling() {
        if (pollingJob?.isActive == true) return
        pollingJob = viewModelScope.launch {
            while (true) {
                delay(3_000)
                fetch(markRefreshing = false, updatePolling = false)
                val current = _uiState.value as? HomeUiState.Success ?: break
                if (current.items.none { it.estado == "pendiente_ia" }) break
            }
            pollingJob = null
        }
    }

    fun createCampaign(
        titulo: String,
        clienteNombre: String,
        clienteEmail: String,
        industria: String,
        tono: String,
        plataforma: String,
        prompt: String,
    ) {
        val current = _uiState.value as? HomeUiState.Success ?: return
        if (current.creating || current.items.any { it.estado == "pendiente_ia" }) return
        if (
            titulo.isBlank() ||
            clienteNombre.isBlank() ||
            clienteEmail.isBlank() ||
            industria.isBlank() ||
            tono.isBlank() ||
            plataforma.isBlank() ||
            prompt.isBlank()
        ) {
            _uiState.value = current.copy(message = "Completa todos los campos antes de generar.")
            return
        }
        viewModelScope.launch {
            _uiState.value = current.copy(creating = true, message = null)
            val request = CampaignCreateRequest(
                titulo = titulo.trim(),
                clienteNombre = clienteNombre.trim(),
                clienteEmail = clienteEmail.trim(),
                industria = industria.trim().lowercase(),
                tono = tono.trim().lowercase(),
                plataforma = plataforma.trim().lowercase(),
                prompt = prompt.trim(),
            )
            campaignRepository.createCampaign(request)
                .onSuccess {
                    fetch(markRefreshing = true)
                }
                .onFailure { throwable ->
                    _uiState.value = current.copy(
                        creating = false,
                        message = throwable.message ?: "No se pudo crear la campaña.",
                    )
                }
        }
    }

    fun clearMessage() {
        val current = _uiState.value
        if (current is HomeUiState.Success && current.message != null) {
            _uiState.value = current.copy(message = null)
        }
    }

    /**
     * Edición manual del copy (letra por letra). [onResult] recibe la campaña
     * actualizada (o null si falló) para refrescar el editor.
     */
    fun editText(
        campaignId: Long,
        texto: String,
        onResult: (com.marketmind.mobile.data.remote.dto.CampaignDto?) -> Unit,
    ) {
        viewModelScope.launch {
            campaignRepository.editText(campaignId, texto)
                .onSuccess { updated ->
                    onResult(updated)
                    fetch(markRefreshing = true)
                }
                .onFailure { throwable ->
                    val current = _uiState.value
                    if (current is HomeUiState.Success) {
                        _uiState.value = current.copy(
                            message = throwable.message ?: "No se pudo guardar el texto.",
                        )
                    }
                    onResult(null)
                }
        }
    }

    /**
     * Mejora el copy de una campaña con IA (Gemini) sin tocar la imagen.
     * [onResult] recibe la campaña con el texto mejorado (o null si falló);
     * la pantalla la usa para refrescar el editor.
     */
    fun improveText(campaignId: Long, onResult: (com.marketmind.mobile.data.remote.dto.CampaignDto?) -> Unit) {
        viewModelScope.launch {
            campaignRepository.improveText(campaignId)
                .onSuccess { updated ->
                    onResult(updated)
                    // refrescar la lista para que el nuevo texto se refleje en el feed
                    fetch(markRefreshing = true)
                }
                .onFailure { throwable ->
                    val current = _uiState.value
                    if (current is HomeUiState.Success) {
                        _uiState.value = current.copy(
                            message = throwable.message ?: "No se pudo mejorar el copy.",
                        )
                    }
                    onResult(null)
                }
        }
    }

    fun logout() {
        authRepository.logout()
    }
}
