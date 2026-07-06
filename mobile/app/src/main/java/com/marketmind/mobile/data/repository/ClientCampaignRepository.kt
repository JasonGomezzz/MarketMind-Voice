package com.marketmind.mobile.data.repository

import com.marketmind.mobile.data.remote.ClientCampaignApiService
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.StatusUpdateRequestDto
import retrofit2.HttpException
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Repositorio del CLIENTE contra Spring Boot (:8080).
 * Ver campañas pendientes, revisar detalle, aprobar/rechazar.
 * El JWT es el mismo que emite Django; Spring solo lo valida.
 */
@Singleton
class ClientCampaignRepository @Inject constructor(
    private val api: ClientCampaignApiService,
) {

    suspend fun getPending(): Result<List<CampaignDto>> {
        return try {
            val envelope = api.getPending()
            val page = envelope.data
            if (envelope.success && page != null) {
                Result.success(page.content)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "Respuesta inválida del servidor."))
            }
        } catch (http: HttpException) {
            Result.failure(mapHttp(http, "ver campañas pendientes"))
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }

    suspend fun getCampaignById(id: Long): Result<CampaignDto> {
        return try {
            val envelope = api.getCampaignById(id)
            val data = envelope.data
            if (envelope.success && data != null) {
                Result.success(data)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "Respuesta inválida del servidor."))
            }
        } catch (http: HttpException) {
            Result.failure(mapHttp(http, "ver esta campaña"))
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }

    suspend fun updateStatus(
        id: Long,
        estado: String,
        version: Int,
        feedback: String? = null,
    ): Result<CampaignDto> {
        return try {
            val envelope = api.updateStatus(
                id,
                StatusUpdateRequestDto(estado = estado, version = version, feedback = feedback),
            )
            val data = envelope.data
            if (envelope.success && data != null) {
                Result.success(data)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "Respuesta inválida del servidor."))
            }
        } catch (http: HttpException) {
            Result.failure(
                when (http.code()) {
                    409 -> CampaignFetchException(
                        "La campaña cambió desde que la abriste. Recarga e intenta de nuevo.",
                    )
                    else -> mapHttp(http, "realizar esta acción")
                },
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }

    private fun mapHttp(http: HttpException, accion: String): CampaignFetchException = CampaignFetchException(
        when (http.code()) {
            400 -> "Datos inválidos. Recarga e intenta de nuevo."
            401 -> "Tu sesión expiró. Vuelve a iniciar sesión."
            403 -> "No tienes permiso para $accion."
            404 -> "Campaña no encontrada."
            in 500..599 -> "El servidor no respondió correctamente. Intenta más tarde."
            else -> "Error de servidor (HTTP ${http.code()})."
        },
    )
}
