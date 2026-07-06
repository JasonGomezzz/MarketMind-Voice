package com.marketmind.mobile.ui.navigation

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.marketmind.mobile.session.SessionEvent
import com.marketmind.mobile.ui.campaigns.CampaignDetailScreen
import com.marketmind.mobile.ui.client.ClientCampaignDetailScreen
import com.marketmind.mobile.ui.client.ClientHomeScreen
import com.marketmind.mobile.ui.home.HomeScreen
import com.marketmind.mobile.ui.login.LoginScreen
import kotlinx.coroutines.flow.collectLatest

private const val ROLE_CLIENTE = "cliente"

@Composable
fun NavGraph(
    navController: NavHostController,
    innerPadding: PaddingValues,
    modifier: Modifier = Modifier,
    appViewModel: AppViewModel = hiltViewModel(),
) {
    LaunchedEffect(Unit) {
        appViewModel.sessionEvents.collectLatest { event ->
            when (event) {
                SessionEvent.Expired -> navController.navigate(Routes.LOGIN) {
                    popUpTo(0) { inclusive = true }
                }
            }
        }
    }

    NavHost(
        navController = navController,
        startDestination = appViewModel.startDestination,
        modifier = modifier.padding(innerPadding),
    ) {
        composable(Routes.LOGIN) {
            LoginScreen(
                onLoginSuccess = { role ->
                    val destino = if (role == ROLE_CLIENTE) Routes.CLIENT_HOME else Routes.HOME
                    navController.navigate(destino) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }

        // ── Flujo MARKETERO (crea campañas vía Django) ──
        composable(Routes.HOME) {
            HomeScreen(
                onLogout = {
                    navController.navigate(Routes.LOGIN) {
                        popUpTo(0) { inclusive = true }
                    }
                },
                onCampaignClick = { id ->
                    navController.navigate(Routes.campaignDetail(id))
                },
            )
        }
        composable(
            route = Routes.CAMPAIGN_DETAIL,
            arguments = listOf(
                navArgument(Routes.CAMPAIGN_DETAIL_ARG_ID) { type = NavType.LongType }
            ),
        ) {
            CampaignDetailScreen(
                onBack = { navController.popBackStack() },
            )
        }

        // ── Flujo CLIENTE (revisa/aprueba/rechaza vía Spring :8080) ──
        composable(Routes.CLIENT_HOME) {
            ClientHomeScreen(
                onLogout = {
                    navController.navigate(Routes.LOGIN) {
                        popUpTo(0) { inclusive = true }
                    }
                },
                onCampaignClick = { id ->
                    navController.navigate(Routes.clientCampaignDetail(id))
                },
            )
        }
        composable(
            route = Routes.CLIENT_CAMPAIGN_DETAIL,
            arguments = listOf(
                navArgument(Routes.CLIENT_CAMPAIGN_DETAIL_ARG_ID) { type = NavType.LongType }
            ),
        ) {
            ClientCampaignDetailScreen(
                onBack = { navController.popBackStack() },
            )
        }
    }
}
