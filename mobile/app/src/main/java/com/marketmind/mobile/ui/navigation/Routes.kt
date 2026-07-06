package com.marketmind.mobile.ui.navigation

object Routes {
    const val LOGIN = "login"

    // Marketero (crea campañas vía Django)
    const val HOME = "home"
    const val CAMPAIGN_DETAIL = "campaign/{id}"
    const val CAMPAIGN_DETAIL_ARG_ID = "id"
    fun campaignDetail(id: Long): String = "campaign/$id"

    // Cliente (revisa/aprueba/rechaza vía Spring :8080)
    const val CLIENT_HOME = "client_home"
    const val CLIENT_CAMPAIGN_DETAIL = "client_campaign/{id}"
    const val CLIENT_CAMPAIGN_DETAIL_ARG_ID = "id"
    fun clientCampaignDetail(id: Long): String = "client_campaign/$id"
}
