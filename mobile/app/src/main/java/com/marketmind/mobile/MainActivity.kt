package com.marketmind.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.rememberNavController
import com.marketmind.mobile.ui.navigation.NavGraph
import com.marketmind.mobile.ui.theme.MarketMindMobileTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MarketMindMobileTheme {
                val navController = rememberNavController()
                NavGraph(
                    navController = navController,
                    innerPadding = PaddingValues(0.dp),
                    modifier = Modifier.fillMaxSize(),
                )
            }
        }
    }
}
