package com.marketmind.mobile.session

sealed interface SessionEvent {
    data object Expired : SessionEvent
}
