package com.marketmind.mobile.ui.navigation

object Routes {
    const val LOGIN = "login"
    const val HOME = "home"

    const val CAMPAIGN_DETAIL = "campaign/{id}"
    const val CAMPAIGN_DETAIL_ARG_ID = "id"

    fun campaignDetail(id: Long): String = "campaign/$id"
}
