package com.marketmind.mobile.ui.social

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.marketmind.mobile.R

internal val SocialBrand = Color(0xFF4D4AF0)
internal val SocialTextDark = Color(0xFF12132A)
internal val SocialTextMuted = Color(0xFF5E6173)
internal val SocialSurfaceSoft = Color(0xFFF3F1FF)
private val OkFondo = Color(0xFFDCF3DD)
private val OkTexto = Color(0xFF1F6A24)
private val ErrorFondo = Color(0xFFFFDAD6)
private val ErrorTexto = Color(0xFF93000A)
private val NeutroFondo = Color(0xFFE9E6F3)
private val NeutroTexto = Color(0xFF464554)

/** Logo de la red (los mismos PNG de la web). */
@Composable
fun RedLogo(red: String, size: Dp, modifier: Modifier = Modifier) {
    val logo = when (red) {
        "instagram" -> R.drawable.ig_logo
        "facebook" -> R.drawable.facebook_logo
        else -> null
    }
    if (logo == null) {
        Icon(Icons.Filled.Share, contentDescription = null, tint = SocialBrand, modifier = modifier.size(size))
    } else {
        Image(
            painter = painterResource(logo),
            contentDescription = null,
            modifier = modifier
                .size(size)
                .clip(RoundedCornerShape(size / 4)),
        )
    }
}

@Composable
fun EstadoPublicacionPill(estado: String, modifier: Modifier = Modifier) {
    val (texto, tono) = SocialFormat.estadoPublicacion(estado)
    val (fondo, color) = when (tono) {
        SocialFormat.Tono.Ok -> OkFondo to OkTexto
        SocialFormat.Tono.Error -> ErrorFondo to ErrorTexto
        SocialFormat.Tono.Neutral -> NeutroFondo to NeutroTexto
    }
    Text(
        text = texto,
        color = color,
        fontSize = 12.sp,
        fontWeight = FontWeight.Bold,
        modifier = modifier
            .clip(RoundedCornerShape(50))
            .background(fondo)
            .padding(horizontal = 10.dp, vertical = 4.dp),
    )
}

/** Cifra con su etiqueta. Si Meta no la informa se lee "sin dato", más discreto pero legible. */
@Composable
fun CifraMetrica(etiqueta: String, valor: Int?, grande: Boolean = false, modifier: Modifier = Modifier) {
    Column(modifier = modifier) {
        Text(etiqueta, color = SocialTextMuted, fontSize = 13.sp)
        if (valor == null) {
            Text(
                "sin dato",
                color = SocialTextMuted,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.padding(top = if (grande) 8.dp else 2.dp),
            )
        } else {
            Text(
                SocialFormat.formatoMetrica(valor),
                color = SocialTextDark,
                fontSize = if (grande) 30.sp else 17.sp,
                fontWeight = FontWeight.ExtraBold,
            )
        }
    }
}
