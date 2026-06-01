package com.marketmind.mobile.data.repository

import com.marketmind.mobile.data.remote.CampaignApiService
import com.marketmind.mobile.data.remote.dto.CampaignDto
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
}

class CampaignFetchException(message: String) : Exception(message)
