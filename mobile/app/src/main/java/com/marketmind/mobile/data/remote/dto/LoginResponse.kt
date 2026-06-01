package com.marketmind.mobile.data.remote.dto

data class LoginResponse(
    val access: String,
    val refresh: String,
    val role: String,
    val nombre: String,
)
