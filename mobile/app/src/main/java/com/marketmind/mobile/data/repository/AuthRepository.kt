package com.marketmind.mobile.data.repository

import com.marketmind.mobile.data.local.TokenManager
import com.marketmind.mobile.data.remote.AuthApiService
import com.marketmind.mobile.data.remote.dto.LoginRequest
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val api: AuthApiService,
    private val tokenManager: TokenManager,
) {

    suspend fun login(email: String, password: String): Result<LoginResult> {
        return try {
            val response = api.login(LoginRequest(email, password))
            if (response.isSuccessful) {
                val body = response.body()
                    ?: return Result.failure(IllegalStateException("Respuesta vacía del servidor."))
                tokenManager.saveSession(
                    access = body.access,
                    refresh = body.refresh,
                    role = body.role,
                    nombre = body.nombre,
                )
                Result.success(LoginResult(role = body.role, nombre = body.nombre))
            } else if (response.code() == 401) {
                Result.failure(InvalidCredentialsException())
            } else {
                Result.failure(HttpFailureException(response.code()))
            }
        } catch (io: IOException) {
            Result.failure(io)
        }
    }

    fun isLoggedIn(): Boolean = tokenManager.isLoggedIn()

    fun logout() {
        tokenManager.clear()
    }

    fun getNombre(): String? = tokenManager.getNombre()
    fun getRole(): String? = tokenManager.getRole()
}

data class LoginResult(
    val role: String,
    val nombre: String,
)

class InvalidCredentialsException : Exception("Credenciales inválidas.")
class HttpFailureException(val code: Int) : Exception("HTTP $code")
