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
import com.marketmind.mobile.ui.home.HomeScreen
import com.marketmind.mobile.ui.login.LoginScreen
import kotlinx.coroutines.flow.collectLatest

@Composable
fun NavGraph(
    navController: NavHostController,
    innerPadding: PaddingValues,
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
        modifier = Modifier.padding(innerPadding),
    ) {
        composable(Routes.LOGIN) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Routes.HOME) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }
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
    }
}
