package com.marketmind.mobile.data.remote.dto

data class PageDto<T>(
    val content: List<T>,
    val totalElements: Long,
    val last: Boolean,
    val number: Int,
)
