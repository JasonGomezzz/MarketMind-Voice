package com.marketmind.mobile.di

import com.marketmind.mobile.BuildConfig
import com.marketmind.mobile.data.remote.AuthApiService
import com.marketmind.mobile.data.remote.AuthInterceptor
import com.marketmind.mobile.data.remote.TokenAuthenticator
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideHttpLoggingInterceptor(): HttpLoggingInterceptor {
        val level = if (BuildConfig.DEBUG) {
            HttpLoggingInterceptor.Level.BODY
        } else {
            HttpLoggingInterceptor.Level.NONE
        }
        return HttpLoggingInterceptor().apply { this.level = level }
    }

    // ──────────────── Cliente "auth" (sin authenticator) ────────────────
    // Lo usa el TokenAuthenticator para refrescar el access token, y también
    // sirve para login. NUNCA instala TokenAuthenticator aquí: ese es el
    // que rompe el ciclo de Hilt y evita el loop infinito de refresh.

    @Provides
    @Singleton
    @AuthHttp
    fun provideAuthOkHttpClient(
        logging: HttpLoggingInterceptor,
    ): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(logging)
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    @Provides
    @Singleton
    @AuthHttp
    fun provideAuthRetrofit(
        @AuthHttp client: OkHttpClient,
    ): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.BASE_URL_DJANGO)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    @Provides
    @Singleton
    fun provideAuthApiService(
        @AuthHttp retrofit: Retrofit,
    ): AuthApiService = retrofit.create(AuthApiService::class.java)

    // ──────────────── Cliente "api" (con authenticator) ────────────────
    // Para todas las llamadas autenticadas futuras (HU12+).

    @Provides
    @Singleton
    @ApiHttp
    fun provideApiOkHttpClient(
        logging: HttpLoggingInterceptor,
        authInterceptor: AuthInterceptor,
        tokenAuthenticator: TokenAuthenticator,
    ): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(logging)
        .addInterceptor(authInterceptor)
        .authenticator(tokenAuthenticator)
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    @Provides
    @Singleton
    @ApiHttp
    fun provideApiRetrofit(
        @ApiHttp client: OkHttpClient,
    ): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.BASE_URL_DJANGO)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
}
