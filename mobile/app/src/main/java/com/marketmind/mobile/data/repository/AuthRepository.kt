package com.marketmind.mobile.data.repository

import com.marketmind.mobile.data.local.TokenManager
import com.marketmind.mobile.data.remote.AuthApiService
import com.marketmind.mobile.data.remote.dto.LoginRequest
import com.marketmind.mobile.data.remote.dto.RegisterRequest
import retrofit2.HttpException
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
                // El mobile es para marketero (crea campañas) Y cliente (aprueba/rechaza).
                // Se guarda la sesión sin filtrar por rol; cada rol ve sus pantallas.
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

    suspend fun me(): Result<UserSession> {
        return try {
            val envelope = api.me()
            val user = envelope.data?.user
            if (envelope.success && user != null) {
                Result.success(
                    UserSession(
                        email = user.email,
                        nombre = user.nombre,
                        role = user.role,
                        tokensDisponibles = user.tokensDisponibles ?: 0,
                    )
                )
            } else {
                Result.failure(IllegalStateException(envelope.message ?: "No se pudo obtener la cuenta."))
            }
        } catch (io: IOException) {
            Result.failure(io)
        } catch (http: HttpException) {
            if (http.code() == 401) {
                tokenManager.clear()
            }
            Result.failure(HttpFailureException(http.code()))
        }
    }

    suspend fun register(nombre: String, email: String, password: String, role: String): Result<LoginResult> {
        return try {
            val response = api.register(
                RegisterRequest(
                    email = email,
                    nombre = nombre,
                    password = password,
                    rol = role,
                )
            )
            if (response.isSuccessful) {
                login(email, password)
            } else {
                Result.failure(HttpFailureException(response.code()))
            }
        } catch (io: IOException) {
            Result.failure(io)
        }
    }

    private companion object {
        const val ROLE_MARKETERO = "marketero"
    }
}

data class LoginResult(
    val role: String,
    val nombre: String,
)

data class UserSession(
    val email: String,
    val nombre: String,
    val role: String,
    val tokensDisponibles: Int,
)

class InvalidCredentialsException : Exception("Credenciales inválidas.")
class HttpFailureException(val code: Int) : Exception("HTTP $code")
class UnauthorizedMobileRoleException : Exception("Mobile solo está disponible para usuarios marketero.")
