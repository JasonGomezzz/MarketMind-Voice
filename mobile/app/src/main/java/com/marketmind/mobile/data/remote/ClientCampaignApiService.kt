package com.marketmind.mobile.data.remote

import com.marketmind.mobile.data.remote.dto.ApiEnvelope
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.PageDto
import com.marketmind.mobile.data.remote.dto.StatusUpdateRequestDto
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Endpoints del CLIENTE contra Spring Boot (:8080).
 *
 * El cliente NO crea campañas: solo revisa las que el marketero le envió
 * (estado pendiente_aprobacion) y las aprueba o rechaza. Spring valida el
 * JWT (mismo SECRET_KEY que Django) y solo escribe el campo estado + feedback.
 */
interface ClientCampaignApiService {

    /** HU12 — campañas pendientes de aprobación del cliente autenticado. */
    @GET("api/v1/campaigns/pending")
    suspend fun getPending(
        @Query("page") page: Int = 0,
        @Query("size") size: Int = 20,
    ): ApiEnvelope<PageDto<CampaignDto>>

    /** HU13 — detalle de una campaña (con imagen) para revisar. */
    @GET("api/v1/campaigns/{id}")
    suspend fun getCampaignById(
        @Path("id") id: Long,
    ): ApiEnvelope<CampaignDto>

    /** HU14/HU15 — aprobar o rechazar (feedback obligatorio al rechazar). */
    @PATCH("api/v1/campaigns/{id}/status")
    suspend fun updateStatus(
        @Path("id") id: Long,
        @Body body: StatusUpdateRequestDto,
    ): ApiEnvelope<CampaignDto>
}
