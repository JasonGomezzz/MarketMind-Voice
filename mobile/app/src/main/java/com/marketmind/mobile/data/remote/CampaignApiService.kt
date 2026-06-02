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

interface CampaignApiService {

    @GET("api/v1/campaigns/pending")
    suspend fun getPending(
        @Query("page") page: Int = 0,
        @Query("size") size: Int = 20,
    ): ApiEnvelope<PageDto<CampaignDto>>

    @GET("api/v1/campaigns/{id}")
    suspend fun getCampaignById(
        @Path("id") id: Long,
    ): ApiEnvelope<CampaignDto>

    @PATCH("api/v1/campaigns/{id}/status")
    suspend fun updateStatus(
        @Path("id") id: Long,
        @Body body: StatusUpdateRequestDto,
    ): ApiEnvelope<CampaignDto>
}
