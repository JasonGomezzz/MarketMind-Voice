package com.marketmind.mobile.data.remote.dto

data class RefreshResponse(
    val access: String,
    val refresh: String? = null,
)
