package com.marketmind.mobile.data.remote.dto

data class StatusUpdateRequestDto(
    val estado: String,
    val version: Int,
    val feedback: String? = null,
)
