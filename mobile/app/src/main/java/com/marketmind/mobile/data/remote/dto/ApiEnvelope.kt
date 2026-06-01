package com.marketmind.mobile.data.remote.dto

data class ApiEnvelope<T>(
    val success: Boolean,
    val message: String?,
    val data: T?,
)
