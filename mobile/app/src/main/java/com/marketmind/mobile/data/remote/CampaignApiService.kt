package com.marketmind.mobile.data.remote

import com.marketmind.mobile.data.remote.dto.ApiEnvelope
import com.marketmind.mobile.data.remote.dto.CampaignCreateRequest
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.data.remote.dto.CampaignEnvelopeDto
import com.marketmind.mobile.data.remote.dto.CampaignStatsDto
import com.marketmind.mobile.data.remote.dto.ConfirmIntentRequest
import com.marketmind.mobile.data.remote.dto.DjangoPageDto
import com.marketmind.mobile.data.remote.dto.EditTextRequest
import com.marketmind.mobile.data.remote.dto.IntentEnvelopeDto
import com.marketmind.mobile.data.remote.dto.InterpretRequest
import com.marketmind.mobile.data.remote.dto.SubmitRequest
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
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
        @Body body: SubmitRequest,
    ): ApiEnvelope<CampaignEnvelopeDto>

    @POST("api/campaigns/{id}/improve-text/")
    suspend fun improveText(
        @Path("id") id: Long,
    ): ApiEnvelope<CampaignEnvelopeDto>

    @PATCH("api/campaigns/{id}/")
    suspend fun editText(
        @Path("id") id: Long,
        @Body body: EditTextRequest,
    ): ApiEnvelope<CampaignEnvelopeDto>

    @DELETE("api/campaigns/{id}/")
    suspend fun deleteCampaign(
        @Path("id") id: Long,
    )

    // Voz → campaña: interpretar no genera ni descuenta crédito; confirmar sí.
    @POST("api/intents/interpret/")
    suspend fun interpretBrief(
        @Body body: InterpretRequest,
    ): ApiEnvelope<IntentEnvelopeDto>

    @POST("api/intents/{id}/confirm/")
    suspend fun confirmIntent(
        @Path("id") id: Long,
        @Body body: ConfirmIntentRequest,
    ): ApiEnvelope<IntentEnvelopeDto>
}
