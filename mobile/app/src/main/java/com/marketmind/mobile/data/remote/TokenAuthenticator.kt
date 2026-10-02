package com.marketmind.mobile.data.remote

import com.marketmind.mobile.data.local.TokenManager
import com.marketmind.mobile.data.remote.dto.RefreshRequest
import com.marketmind.mobile.di.AuthHttp
import com.marketmind.mobile.session.SessionEvent
import com.marketmind.mobile.session.SessionManager
import kotlinx.coroutines.runBlocking
import okhttp3.Authenticator
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route
import retrofit2.Retrofit
import javax.inject.Inject

class TokenAuthenticator @Inject constructor(
    private val tokenManager: TokenManager,
    private val sessionManager: SessionManager,
    @AuthHttp private val authRetrofit: Retrofit,
) : Authenticator {

    private val refreshApi: AuthApiService by lazy {
        authRetrofit.create(AuthApiService::class.java)
    }

    @Synchronized
    override fun authenticate(route: Route?, response: Response): Request? {
        if (response.request.url.encodedPath.endsWith("/api/auth/token/refresh/")) {
            tokenManager.clear()
            sessionManager.tryEmit(SessionEvent.Expired)
            return null
        }

        if (responseCount(response) >= 2) {
            return null
        }

        val refreshToken = tokenManager.getRefreshToken()
        if (refreshToken.isNullOrBlank()) {
            tokenManager.clear()
            sessionManager.tryEmit(SessionEvent.Expired)
            return null
        }

        val refreshResponse = runCatching {
            runBlocking { refreshApi.refresh(RefreshRequest(refreshToken)) }
        }.getOrNull()

        if (refreshResponse == null || !refreshResponse.isSuccessful) {
            tokenManager.clear()
            sessionManager.tryEmit(SessionEvent.Expired)
            return null
        }

        val refreshedTokens = refreshResponse.body()
        val newAccess = refreshedTokens?.access
        if (newAccess.isNullOrBlank()) {
            tokenManager.clear()
            sessionManager.tryEmit(SessionEvent.Expired)
            return null
        }

        tokenManager.updateTokens(newAccess, refreshedTokens.refresh)

        return response.request.newBuilder()
            .header("Authorization", "Bearer $newAccess")
            .build()
    }

    private fun responseCount(response: Response): Int {
        var prior = response.priorResponse
        var count = 1
        while (prior != null) {
            count++
            prior = prior.priorResponse
        }
        return count
    }
}
