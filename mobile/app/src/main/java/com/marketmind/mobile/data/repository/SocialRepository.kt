package com.marketmind.mobile.data.repository

import com.google.gson.Gson
import com.google.gson.JsonParseException
import com.marketmind.mobile.data.remote.SocialApiService
import com.marketmind.mobile.data.remote.dto.ActualizacionMetricasDto
import com.marketmind.mobile.data.remote.dto.ApiEnvelope
import com.marketmind.mobile.data.remote.dto.PublicationDto
import com.marketmind.mobile.data.remote.dto.PublicationStatsDto
import com.marketmind.mobile.data.remote.dto.ResumenRedesDto
import com.marketmind.mobile.data.remote.dto.SocialConnectionDto
import retrofit2.HttpException
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

class SocialException(message: String) : Exception(message)

/** Conexiones, publicaciones y métricas de Instagram y Facebook (Django). */
@Singleton
class SocialRepository @Inject constructor(
    private val api: SocialApiService,
) {
    private val gson = Gson()

    suspend fun destinos(clienteEmail: String): Result<List<SocialConnectionDto>> =
        llamar { api.destinos(clienteEmail).exigir().conexiones.orEmpty() }

    suspend fun publicaciones(campaignId: Long? = null): Result<List<PublicationDto>> =
        llamar { api.publicaciones(campaignId).exigir().publicaciones.orEmpty() }

    suspend fun publicar(id: Long): Result<PublicationDto> =
        llamar { api.publicar(id).exigir().publicacion ?: throw SocialException("Respuesta inválida del servidor.") }

    suspend fun estadisticas(id: Long): Result<PublicationStatsDto> =
        llamar { api.estadisticas(id).exigir() }

    suspend fun resumen(): Result<ResumenRedesDto> =
        llamar { api.resumen().exigir() }

    suspend fun actualizarMetricas(): Result<ActualizacionMetricasDto> =
        llamar { api.actualizarMetricas().exigir() }

    private fun <T> ApiEnvelope<T>.exigir(): T {
        val contenido = data
        if (!success || contenido == null) throw SocialException(message ?: "Respuesta inválida del servidor.")
        return contenido
    }

    private suspend fun <T> llamar(bloque: suspend () -> T): Result<T> = try {
        Result.success(bloque())
    } catch (social: SocialException) {
        Result.failure(social)
    } catch (http: HttpException) {
        Result.failure(SocialException(mensajeDe(http)))
    } catch (io: IOException) {
        Result.failure(SocialException("No se pudo conectar con el servidor. Revisa tu conexión."))
    } catch (parse: JsonParseException) {
        Result.failure(SocialException("La respuesta del servidor no tiene el formato esperado."))
    }

    /** Django responde { success, message, data } también en los errores: se muestra su mensaje. */
    private fun mensajeDe(http: HttpException): String {
        val delServidor = try {
            http.response()?.errorBody()?.string()
                ?.let { gson.fromJson(it, ApiEnvelope::class.java)?.message }
        } catch (_: Exception) {
            null
        }
        return delServidor?.takeIf { it.isNotBlank() } ?: when (http.code()) {
            401 -> "Tu sesión expiró. Vuelve a iniciar sesión."
            403 -> "No tienes permiso para esta acción."
            404 -> "No se encontró la publicación."
            in 500..599 -> "El servidor no respondió correctamente. Intenta más tarde."
            else -> "Error de servidor (HTTP ${http.code()})."
        }
    }
}
