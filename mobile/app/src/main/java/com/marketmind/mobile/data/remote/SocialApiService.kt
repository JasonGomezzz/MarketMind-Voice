package com.marketmind.mobile.data.remote

import com.marketmind.mobile.data.remote.dto.ActualizacionMetricasDto
import com.marketmind.mobile.data.remote.dto.ApiEnvelope
import com.marketmind.mobile.data.remote.dto.ConexionesEnvelopeDto
import com.marketmind.mobile.data.remote.dto.PublicacionEnvelopeDto
import com.marketmind.mobile.data.remote.dto.PublicacionesEnvelopeDto
import com.marketmind.mobile.data.remote.dto.PublicationStatsDto
import com.marketmind.mobile.data.remote.dto.ResumenRedesDto
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Redes sociales contra Django (:8000). Sirve a los tres roles: Django recorta
 * lo que ve cada uno (cliente: lo suyo; marketero: sus clientes; superadmin: todo).
 */
interface SocialApiService {

    /** Cuentas donde se puede publicar una campaña de ese cliente (marketero). */
    @GET("api/social/connections/destinos/")
    suspend fun destinos(
        @Query("cliente_email") clienteEmail: String,
    ): ApiEnvelope<ConexionesEnvelopeDto>

    @GET("api/social/publications/")
    suspend fun publicaciones(
        @Query("campaign") campaignId: Long? = null,
    ): ApiEnvelope<PublicacionesEnvelopeDto>

    /** "Publicar ahora / Reintentar" (solo marketero). */
    @POST("api/social/publications/{id}/publish/")
    suspend fun publicar(
        @Path("id") id: Long,
    ): ApiEnvelope<PublicacionEnvelopeDto>

    /** Métricas de una publicación; refresh=1 pide a Meta si la última lectura tiene más de 10 min. */
    @GET("api/social/publications/{id}/stats/")
    suspend fun estadisticas(
        @Path("id") id: Long,
        @Query("refresh") refresh: Int = 1,
    ): ApiEnvelope<PublicationStatsDto>

    @GET("api/social/publications/summary/")
    suspend fun resumen(): ApiEnvelope<ResumenRedesDto>

    @POST("api/social/publications/refresh/")
    suspend fun actualizarMetricas(): ApiEnvelope<ActualizacionMetricasDto>
}
