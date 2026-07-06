package com.marketmind.mobile.ui.navigation

import androidx.lifecycle.ViewModel
import com.marketmind.mobile.data.local.TokenManager
import com.marketmind.mobile.session.SessionEvent
import com.marketmind.mobile.session.SessionManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharedFlow
import javax.inject.Inject

@HiltViewModel
class AppViewModel @Inject constructor(
    tokenManager: TokenManager,
    sessionManager: SessionManager,
) : ViewModel() {

    // Marketero y cliente usan el mobile, pero ven pantallas distintas:
    // el marketero crea campañas (Django); el cliente revisa/aprueba (Spring).
    val startDestination: String = if (tokenManager.isLoggedIn()) {
        if (tokenManager.getRole() == ROLE_CLIENTE) Routes.CLIENT_HOME else Routes.HOME
    } else {
        tokenManager.clear()
        Routes.LOGIN
    }

    private companion object {
        const val ROLE_CLIENTE = "cliente"
    }

    val sessionEvents: SharedFlow<SessionEvent> = sessionManager.events
}
