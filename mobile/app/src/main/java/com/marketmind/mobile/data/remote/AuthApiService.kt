package com.marketmind.mobile.data.remote

import com.marketmind.mobile.data.remote.dto.LoginRequest
import com.marketmind.mobile.data.remote.dto.LoginResponse
import com.marketmind.mobile.data.remote.dto.RefreshRequest
import com.marketmind.mobile.data.remote.dto.RefreshResponse
import com.marketmind.mobile.data.remote.dto.ApiEnvelope
import com.marketmind.mobile.data.remote.dto.RegisterRequest
import com.marketmind.mobile.data.remote.dto.UserEnvelopeDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface AuthApiService {

    @POST("api/auth/token/")
    suspend fun login(@Body body: LoginRequest): Response<LoginResponse>

    @POST("api/auth/register/")
    suspend fun register(@Body body: RegisterRequest): Response<ApiEnvelope<UserEnvelopeDto>>

    @POST("api/auth/token/refresh/")
    suspend fun refresh(@Body body: RefreshRequest): Response<RefreshResponse>

    @GET("api/auth/me/")
    suspend fun me(): ApiEnvelope<UserEnvelopeDto>
}
