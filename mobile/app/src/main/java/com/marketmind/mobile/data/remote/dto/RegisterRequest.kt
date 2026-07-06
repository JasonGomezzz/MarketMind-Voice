package com.marketmind.mobile.data.remote.dto

data class RegisterRequest(
    val email: String,
    val nombre: String,
    val password: String,
    val rol: String = "marketero",
)
