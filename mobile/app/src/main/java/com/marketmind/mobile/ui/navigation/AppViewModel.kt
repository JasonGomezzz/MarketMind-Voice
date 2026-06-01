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

    val startDestination: String =
        if (tokenManager.isLoggedIn()) Routes.HOME else Routes.LOGIN

    val sessionEvents: SharedFlow<SessionEvent> = sessionManager.events
}
