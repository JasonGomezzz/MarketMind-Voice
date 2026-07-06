package com.marketmind.mobile.data.repository

import com.marketmind.mobile.data.remote.CampaignApiService
import com.marketmind.mobile.data.remote.dto.CampaignCreateRequest
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.CampaignStatsDto
import com.google.gson.JsonSyntaxException
import retrofit2.HttpException
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CampaignRepository @Inject constructor(
    private val api: CampaignApiService,
) {

    suspend fun getMine(): Result<List<CampaignDto>> {
        return try {
            Result.success(api.getMine().results)
        } catch (http: HttpException) {
            Result.failure(
                when (http.code()) {
                    401 -> CampaignFetchException("Tu sesión expiró. Vuelve a iniciar sesión.")
                    403 -> CampaignFetchException("Mobile solo está disponible para marketeros.")
                    in 500..599 -> CampaignFetchException("El servidor no respondió correctamente. Intenta más tarde.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }

    suspend fun getStats(): Result<CampaignStatsDto> {
        return try {
            val envelope = api.getStats()
            val data = envelope.data
            if (envelope.success && data != null) {
                Result.success(data)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "Respuesta inválida del servidor."))
            }
        } catch (http: HttpException) {
            Result.failure(CampaignFetchException("Error de servidor (HTTP ${http.code()})."))
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }

    suspend fun createCampaign(request: CampaignCreateRequest): Result<CampaignDto> {
        return try {
            val envelope = api.createCampaign(request)
            val campaign = envelope.data?.campaign
            if (envelope.success && campaign != null) {
                Result.success(campaign)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "No se pudo crear la campaña."))
            }
        } catch (http: HttpException) {
            Result.failure(
                when (http.code()) {
                    400 -> CampaignFetchException("Datos inválidos. Revisa cliente, industria, tono y plataforma.")
                    402 -> CampaignFetchException("Sin tokens disponibles para generar con IA.")
                    403 -> CampaignFetchException("Solo los marketeros pueden crear campañas desde mobile.")
                    in 500..599 -> CampaignFetchException("El backend no pudo iniciar la IA. Intenta más tarde.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        } catch (parse: JsonSyntaxException) {
            Result.failure(CampaignFetchException("La respuesta de campañas no tiene el formato esperado."))
        } catch (illegal: IllegalStateException) {
            Result.failure(CampaignFetchException("La respuesta de campañas no tiene el formato esperado."))
        }
    }

    suspend fun getCampaignById(id: Long): Result<CampaignDto> {
        return try {
            val envelope = api.getDjangoCampaignById(id)
            val data = envelope.data?.campaign
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

    suspend fun submitToClient(id: Long): Result<CampaignDto> {
        return try {
            val envelope = api.submitCampaign(id)
            val data = envelope.data?.campaign
            if (envelope.success && data != null) {
                Result.success(data)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "No se pudo enviar la campaña."))
            }
        } catch (http: HttpException) {
            Result.failure(
                when (http.code()) {
                    403 -> CampaignFetchException("Solo el marketero puede enviar campañas al cliente.")
                    409 -> CampaignFetchException("Solo campañas generadas pueden enviarse al cliente.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }

    suspend fun deleteCampaign(id: Long): Result<Unit> {
        return try {
            api.deleteCampaign(id)
            Result.success(Unit)
        } catch (http: HttpException) {
            Result.failure(
                when (http.code()) {
                    401 -> CampaignFetchException("Tu sesión expiró. Vuelve a iniciar sesión.")
                    403 -> CampaignFetchException("No tienes permiso para eliminar esta campaña.")
                    404 -> CampaignFetchException("Campaña no encontrada.")
                    409 -> CampaignFetchException("Solo puedes eliminar campañas en borrador o generado.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }
}

class CampaignFetchException(message: String) : Exception(message)
