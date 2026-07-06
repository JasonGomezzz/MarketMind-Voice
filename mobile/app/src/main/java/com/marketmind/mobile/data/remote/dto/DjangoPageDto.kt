package com.marketmind.mobile.data.remote.dto

data class DjangoPageDto<T>(
    val count: Int,
    val next: String?,
    val previous: String?,
    val results: List<T>,
)
