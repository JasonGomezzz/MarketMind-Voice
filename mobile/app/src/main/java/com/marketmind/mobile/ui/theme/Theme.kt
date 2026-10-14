package com.marketmind.mobile.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.ui.unit.dp

private val DarkColorScheme = darkColorScheme(
    primary = NexoTeal,
    onPrimary = NexoNavy,
    primaryContainer = Color(0xFF173F47),
    onPrimaryContainer = Color(0xFFD1F4EE),
    secondary = NexoTealLight,
    tertiary = NexoTealLight,
    background = NexoBackgroundDark,
    onBackground = NexoTextLight,
    surface = NexoNavy,
    onSurface = NexoTextLight,
    onSurfaceVariant = Color(0xFFBDCFD7),
    surfaceVariant = Color(0xFF203B52),
    outline = Color(0xFF90ACBA)
)

private val LightColorScheme = lightColorScheme(
    primary = NexoTealAccessible,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD1F4EE),
    onPrimaryContainer = NexoNavy,
    secondary = NexoNavy,
    tertiary = NexoTealAccessible,
    background = NexoBackgroundLight,
    onBackground = NexoNavy,
    surface = Color.White,
    onSurface = NexoNavy,
    onSurfaceVariant = Color(0xFF425C67),
    surfaceVariant = Color(0xFFE5EFEF),
    outline = Color(0xFF607983)
)

@Composable
fun MarketMindMobileTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    // Dynamic color is available on Android 12+
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
      dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
        val context = LocalContext.current
        if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
      }
      darkTheme -> DarkColorScheme
      else -> LightColorScheme
    }

    MaterialTheme(
      colorScheme = colorScheme,
      shapes = Shapes(
        extraSmall = RoundedCornerShape(4.dp),
        small = RoundedCornerShape(4.dp),
        medium = RoundedCornerShape(4.dp),
        large = RoundedCornerShape(4.dp),
        extraLarge = RoundedCornerShape(4.dp)
      ),
      typography = Typography,
      content = content
    )
}
