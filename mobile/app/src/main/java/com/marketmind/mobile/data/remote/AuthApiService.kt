package com.marketmind.mobile.data.remote

import com.marketmind.mobile.data.remote.dto.LoginRequest
import com.marketmind.mobile.data.remote.dto.LoginResponse
import com.marketmind.mobile.data.remote.dto.RefreshRequest
import com.marketmind.mobile.data.remote.dto.RefreshResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface AuthApiService {

    @POST("api/auth/token/")
    suspend fun login(@Body body: LoginRequest): Response<LoginResponse>

    @POST("api/auth/token/refresh/")
    suspend fun refresh(@Body body: RefreshRequest): Response<RefreshResponse>
}
