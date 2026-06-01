package com.marketmind.mobile.data.remote

import com.marketmind.mobile.data.remote.dto.ApiEnvelope
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.PageDto
import retrofit2.http.GET
import retrofit2.http.Query

interface CampaignApiService {

    @GET("api/v1/campaigns/pending")
    suspend fun getPending(
        @Query("page") page: Int = 0,
        @Query("size") size: Int = 20,
    ): ApiEnvelope<PageDto<CampaignDto>>
}
