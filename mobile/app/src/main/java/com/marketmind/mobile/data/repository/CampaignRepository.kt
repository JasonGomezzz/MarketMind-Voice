package com.marketmind.mobile.data.repository

import com.marketmind.mobile.data.remote.CampaignApiService
import com.marketmind.mobile.data.remote.dto.CampaignCreateRequest
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.CampaignIntentDto
import com.marketmind.mobile.data.remote.dto.CampaignStatsDto
import com.marketmind.mobile.data.remote.dto.ConfirmIntentRequest
import com.marketmind.mobile.data.remote.dto.EditTextRequest
import com.marketmind.mobile.data.remote.dto.InterpretRequest
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
                    409 -> CampaignFetchException("Esta campaña ya no se puede enviar (fue rechazada o ya está en revisión). Regénerala para volver a enviarla.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }

    /** Edición manual del copy por el marketero (letra por letra). */
    suspend fun editText(id: Long, texto: String): Result<CampaignDto> {
        return try {
            val envelope = api.editText(id, EditTextRequest(textoGenerado = texto))
            val data = envelope.data?.campaign
            if (envelope.success && data != null) {
                Result.success(data)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "No se pudo guardar el texto."))
            }
        } catch (http: HttpException) {
            Result.failure(
                when (http.code()) {
                    403 -> CampaignFetchException("Solo el marketero puede editar el copy.")
                    400 -> CampaignFetchException("El texto no es válido. Revisa la longitud.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }

    /** Mejora el copy con IA (Gemini), sin tocar la imagen. */
    suspend fun improveText(id: Long): Result<CampaignDto> {
        return try {
            val envelope = api.improveText(id)
            val data = envelope.data?.campaign
            if (envelope.success && data != null) {
                Result.success(data)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "No se pudo mejorar el copy."))
            }
        } catch (http: HttpException) {
            Result.failure(
                when (http.code()) {
                    403 -> CampaignFetchException("Solo el marketero puede mejorar el copy.")
                    409 -> CampaignFetchException("No hay texto generado para mejorar.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        }
    }

    /** Convierte el brief (dictado o escrito) en campos editables. No cobra crédito. */
    suspend fun interpretBrief(texto: String, porVoz: Boolean): Result<CampaignIntentDto> {
        return try {
            val envelope = api.interpretBrief(
                InterpretRequest(texto = texto.trim(), origen = if (porVoz) "voz" else "formulario"),
            )
            val intent = envelope.data?.intent
            if (envelope.success && intent != null) {
                Result.success(intent)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "No se pudo interpretar el brief."))
            }
        } catch (http: HttpException) {
            Result.failure(
                when (http.code()) {
                    400 -> CampaignFetchException("El brief debe tener entre 10 y 2000 caracteres.")
                    403 -> CampaignFetchException("Solo los marketeros pueden crear campañas.")
                    429 -> CampaignFetchException("Demasiadas interpretaciones seguidas. Espera un momento.")
                    502 -> CampaignFetchException("La IA no pudo interpretar el brief. Completa el formulario a mano.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        } catch (parse: JsonSyntaxException) {
            Result.failure(CampaignFetchException("La respuesta de la IA no tiene el formato esperado."))
        }
    }

    /** Crea la campaña a partir de la intención y dispara la generación. Repetirlo no cobra dos veces. */
    suspend fun confirmIntent(id: Long, campos: Map<String, String?>): Result<CampaignDto> {
        return try {
            val envelope = api.confirmIntent(id, ConfirmIntentRequest(campos))
            val campaign = envelope.data?.campaign
            if (envelope.success && campaign != null) {
                Result.success(campaign)
            } else {
                Result.failure(CampaignFetchException(envelope.message ?: "No se pudo crear la campaña."))
            }
        } catch (http: HttpException) {
            Result.failure(
                when (http.code()) {
                    400 -> CampaignFetchException("Faltan datos o hay campos inválidos. El email debe ser de un cliente registrado.")
                    402 -> CampaignFetchException("Sin tokens disponibles para generar con IA.")
                    403 -> CampaignFetchException("Solo los marketeros pueden crear campañas desde mobile.")
                    404, 409 -> CampaignFetchException("Este brief ya no está disponible. Vuelve a interpretarlo.")
                    in 500..599 -> CampaignFetchException("El backend no pudo iniciar la IA. Intenta más tarde.")
                    else -> CampaignFetchException("Error de servidor (HTTP ${http.code()}).")
                }
            )
        } catch (io: IOException) {
            Result.failure(CampaignFetchException("No se pudo conectar con el servidor. Revisa tu conexión."))
        } catch (parse: JsonSyntaxException) {
            Result.failure(CampaignFetchException("La respuesta de campañas no tiene el formato esperado."))
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
