package com.marketmind.mobile.data.remote.dto

import com.google.gson.annotations.SerializedName

data class UserDto(
    val id: Long,
    val email: String,
    val nombre: String,
    @SerializedName(value = "role", alternate = ["rol"])
    val role: String,
    @SerializedName(value = "tokensDisponibles", alternate = ["tokens_disponibles"])
    val tokensDisponibles: Int? = null,
)

data class UserEnvelopeDto(
    val user: UserDto,
)
