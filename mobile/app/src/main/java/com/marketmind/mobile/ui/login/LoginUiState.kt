package com.marketmind.mobile.ui.login

sealed interface LoginUiState {
    data object Idle : LoginUiState
    data object Loading : LoginUiState
    data class Success(val role: String) : LoginUiState
    data class Error(val message: String) : LoginUiState
}
