package com.marketmind.mobile.data.repository

import com.marketmind.mobile.data.remote.CampaignApiService
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.StatusUpdateRequestDto
import retrofit2.HttpException
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CampaignRepository @Inject constructor(
    private val api: CampaignApiService,
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
            Result.failure(
                when (http.code()) {
                    401 -> CampaignFetchException("Tu sesión expiró. Vuelve a iniciar sesión.")
                    403 -> CampaignFetchException("No tienes permiso para ver campañas pendientes.")
                    in 500..599 -> CampaignFetchException("El servidor no respondió correctamente. Intenta más tarde.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
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
            Result.failure(
                when (http.code()) {
                    401 -> CampaignFetchException("Tu sesión expiró. Vuelve a iniciar sesión.")
                    403 -> CampaignFetchException("No tienes permiso para ver esta campaña.")
                    404 -> CampaignFetchException("Campaña no encontrada.")
                    in 500..599 -> CampaignFetchException("El servidor no respondió correctamente. Intenta más tarde.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }

    suspend fun updateStatus(id: Long, estado: String, version: Int): Result<CampaignDto> {
        return try {
            val envelope = api.updateStatus(id, StatusUpdateRequestDto(estado = estado, version = version))
            val data = envelope.data
            if (envelope.success && data != null) {
                Result.success(data)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "Respuesta inválida del servidor."))
            }
        } catch (http: HttpException) {
            Result.failure(
                when (http.code()) {
                    400 -> CampaignFetchException("Datos inválidos. Recarga e intenta de nuevo.")
                    401 -> CampaignFetchException("Tu sesión expiró. Vuelve a iniciar sesión.")
                    403 -> CampaignFetchException("No tienes permiso para realizar esta acción.")
                    404 -> CampaignFetchException("Campaña no encontrada.")
                    409 -> CampaignFetchException("La campaña fue modificada o ya no se puede transicionar. Recarga e intenta de nuevo.")
                    in 500..599 -> CampaignFetchException("El servidor no respondió correctamente. Intenta más tarde.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }
}

class CampaignFetchException(message: String) : Exception(message)
