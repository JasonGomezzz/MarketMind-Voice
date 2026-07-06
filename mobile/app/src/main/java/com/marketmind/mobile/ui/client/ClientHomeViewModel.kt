package com.marketmind.mobile.ui.client

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketmind.mobile.data.repository.AuthRepository
import com.marketmind.mobile.data.repository.ClientCampaignRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel del feed del CLIENTE (campañas pendientes de aprobación).
 * Consume Spring Boot (:8080) vía [ClientCampaignRepository]; el cliente NO
 * crea campañas, solo revisa las que el marketero le envió.
 */
@HiltViewModel
class ClientHomeViewModel @Inject constructor(
    private val clientCampaignRepository: ClientCampaignRepository,
    private val authRepository: AuthRepository,
) : ViewModel() {

    val nombre: String? = authRepository.getNombre()
    val role: String? = authRepository.getRole()

    private val _email = MutableStateFlow<String?>(null)
    val email: StateFlow<String?> = _email.asStateFlow()

    private val _uiState = MutableStateFlow<ClientHomeUiState>(ClientHomeUiState.Loading)
    val uiState: StateFlow<ClientHomeUiState> = _uiState.asStateFlow()

    init {
        load()
        loadEmail()
    }

    private fun loadEmail() {
        viewModelScope.launch {
            authRepository.me().onSuccess { _email.value = it.email }
        }
    }

    fun load() {
        viewModelScope.launch {
            if (_uiState.value !is ClientHomeUiState.Success) {
                _uiState.value = ClientHomeUiState.Loading
            }
            fetch()
        }
    }

    fun refresh() {
        viewModelScope.launch {
            val current = _uiState.value
            if (current is ClientHomeUiState.Success) {
                _uiState.value = current.copy(refreshing = true)
            }
            fetch()
        }
    }

    private suspend fun fetch() {
        clientCampaignRepository.getPending()
            .onSuccess { items ->
                _uiState.value = if (items.isEmpty()) {
                    ClientHomeUiState.Empty
                } else {
                    ClientHomeUiState.Success(items = items, refreshing = false)
                }
            }
            .onFailure { throwable ->
                _uiState.value = ClientHomeUiState.Error(
                    message = throwable.message ?: "Error desconocido al cargar campañas.",
                )
            }
    }

    fun logout() {
        authRepository.logout()
    }
}
