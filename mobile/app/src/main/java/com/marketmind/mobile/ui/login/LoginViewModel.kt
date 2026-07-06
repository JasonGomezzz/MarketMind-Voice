package com.marketmind.mobile.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketmind.mobile.data.repository.AuthRepository
import com.marketmind.mobile.data.repository.HttpFailureException
import com.marketmind.mobile.data.repository.InvalidCredentialsException
import com.marketmind.mobile.data.repository.UnauthorizedMobileRoleException
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.IOException
import javax.inject.Inject

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val repository: AuthRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<LoginUiState>(LoginUiState.Idle)
    val state: StateFlow<LoginUiState> = _state.asStateFlow()

    fun login(email: String, password: String) {
        val trimmedEmail = email.trim()
        if (trimmedEmail.isBlank() || password.isBlank()) {
            _state.value = LoginUiState.Error("Completa email y contraseña.")
            return
        }
        _state.value = LoginUiState.Loading
        viewModelScope.launch {
            repository.login(trimmedEmail, password).fold(
                onSuccess = { result ->
                    _state.value = LoginUiState.Success(role = result.role, nombre = result.nombre)
                },
                onFailure = { e ->
                    _state.value = when (e) {
                        is InvalidCredentialsException -> LoginUiState.Error("Credenciales inválidas.")
                        is UnauthorizedMobileRoleException -> LoginUiState.Error("Mobile solo está disponible para usuarios marketero.")
                        is IOException -> LoginUiState.Error("Sin conexión. Verifica tu red.")
                        is HttpFailureException -> LoginUiState.Error("Error del servidor (${e.code}). Intenta de nuevo.")
                        else -> LoginUiState.Error("Error inesperado. Intenta de nuevo.")
                    }
                }
            )
        }
    }

    fun register(nombre: String, email: String, password: String, confirmPassword: String, role: String) {
        val trimmedName = nombre.trim()
        val trimmedEmail = email.trim()
        if (trimmedName.isBlank() || trimmedEmail.isBlank() || password.isBlank()) {
            _state.value = LoginUiState.Error("Completa nombre, email y contraseña.")
            return
        }
        if (password.length < 8) {
            _state.value = LoginUiState.Error("La contraseña debe tener al menos 8 caracteres.")
            return
        }
        if (password != confirmPassword) {
            _state.value = LoginUiState.Error("Las contraseñas no coinciden.")
            return
        }

        _state.value = LoginUiState.Loading
        viewModelScope.launch {
            repository.register(trimmedName, trimmedEmail, password, role).fold(
                onSuccess = { result ->
                    _state.value = LoginUiState.Success(role = result.role, nombre = result.nombre)
                },
                onFailure = { e ->
                    _state.value = when (e) {
                        is UnauthorizedMobileRoleException -> LoginUiState.Error("Cuenta creada, pero mobile solo permite ingresar como marketero.")
                        is IOException -> LoginUiState.Error("Sin conexión. Verifica tu red.")
                        is HttpFailureException -> when (e.code) {
                            400 -> LoginUiState.Error("No se pudo crear la cuenta. Revisa los datos o usa otro email.")
                            else -> LoginUiState.Error("Error del servidor (${e.code}). Intenta de nuevo.")
                        }
                        else -> LoginUiState.Error("Error inesperado. Intenta de nuevo.")
                    }
                }
            )
        }
    }

    fun consumeError() {
        if (_state.value is LoginUiState.Error) {
            _state.value = LoginUiState.Idle
        }
    }
}
