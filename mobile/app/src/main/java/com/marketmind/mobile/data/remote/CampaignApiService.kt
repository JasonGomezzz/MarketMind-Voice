package com.marketmind.mobile.data.remote

import com.marketmind.mobile.data.remote.dto.ApiEnvelope
import com.marketmind.mobile.data.remote.dto.CampaignCreateRequest
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.CampaignEnvelopeDto
import com.marketmind.mobile.data.remote.dto.CampaignStatsDto
import com.marketmind.mobile.data.remote.dto.DjangoPageDto
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface CampaignApiService {

    @GET("api/campaigns/")
    suspend fun getMine(): DjangoPageDto<CampaignDto>

    @GET("api/campaigns/stats/")
    suspend fun getStats(): ApiEnvelope<CampaignStatsDto>

    @POST("api/campaigns/")
    suspend fun createCampaign(
        @Body body: CampaignCreateRequest,
    ): ApiEnvelope<CampaignEnvelopeDto>

    @GET("api/campaigns/{id}/")
    suspend fun getDjangoCampaignById(
        @Path("id") id: Long,
    ): ApiEnvelope<CampaignEnvelopeDto>

    @POST("api/campaigns/{id}/submit/")
    suspend fun submitCampaign(
        @Path("id") id: Long,
    ): ApiEnvelope<CampaignEnvelopeDto>

    @DELETE("api/campaigns/{id}/")
    suspend fun deleteCampaign(
        @Path("id") id: Long,
    )
}
