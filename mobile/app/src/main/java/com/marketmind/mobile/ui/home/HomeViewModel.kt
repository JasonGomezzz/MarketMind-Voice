package com.marketmind.mobile.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketmind.mobile.data.repository.AuthRepository
import com.marketmind.mobile.data.repository.CampaignRepository
import dagger.hilt.android.lifecycle.HiltViewModel
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

    private suspend fun fetch(markRefreshing: Boolean) {
        campaignRepository.getPending()
            .onSuccess { items ->
                _uiState.value = if (items.isEmpty()) {
                    HomeUiState.Empty
                } else {
                    HomeUiState.Success(items = items, refreshing = false)
                }
            }
            .onFailure { throwable ->
                _uiState.value = HomeUiState.Error(
                    message = throwable.message ?: "Error desconocido al cargar campañas."
                )
            }
    }

    fun logout() {
        authRepository.logout()
    }
}
