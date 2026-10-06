package com.marketmind.mobile.ui.social

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.OpenInNew
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.marketmind.mobile.data.remote.dto.PublicationDto
import com.marketmind.mobile.data.remote.dto.PublicationMetricDto
import com.marketmind.mobile.data.remote.dto.PublicationStatsDto
import com.marketmind.mobile.data.remote.dto.RedResumenDto
import com.marketmind.mobile.data.remote.dto.ResumenRedesDto

/**
 * Pestaña "Estadísticas" (marketero y cliente): resumen por red, publicaciones y el
 * detalle de cada una. Mismas reglas que la web: "sin dato" nunca se muestra como 0.
 */
@Composable
fun StatsContent(
    alcance: String,
    modifier: Modifier = Modifier,
    viewModel: StatsViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Box(modifier = modifier.fillMaxSize()) {
        when {
            state.cargando -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = SocialBrand)
            }
            state.error != null && state.resumen == null -> ErrorEstadisticas(
                mensaje = state.error.orEmpty(),
                onReintentar = viewModel::cargar,
            )
            else -> LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                item {
                    Cabecera(
                        alcance = alcance,
                        resumen = state.resumen,
                        actualizando = state.actualizando,
                        mensaje = state.mensaje,
                        onActualizar = viewModel::actualizarMetricas,
                    )
                }
                items(listOf("instagram", "facebook")) { red ->
                    TarjetaRed(red = red, datos = state.resumen?.redes?.get(red))
                }
                item {
                    Text(
                        "Publicaciones",
                        color = SocialTextDark,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.ExtraBold,
                        modifier = Modifier.padding(top = 8.dp),
                    )
                }
                if (state.publicaciones.isEmpty()) {
                    item { SinPublicaciones() }
                } else {
                    items(state.publicaciones, key = { it.id }) { p ->
                        FilaPublicacion(publicacion = p, onClick = { viewModel.abrir(p.id) })
                    }
                    item {
                        Text(
                            "— todavía no se leyeron métricas · sin dato: Meta no informa esa cifra",
                            color = SocialTextMuted,
                            fontSize = 12.sp,
                        )
                    }
                }
            }
        }
    }

    state.detalle?.let { detalle ->
        DetallePublicacion(
            datos = detalle.datos,
            error = detalle.error,
            onCerrar = viewModel::cerrarDetalle,
        )
    }
}

@Composable
private fun Cabecera(
    alcance: String,
    resumen: ResumenRedesDto?,
    actualizando: Boolean,
    mensaje: String?,
    onActualizar: () -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            "$alcance Las cifras vienen de Meta y pueden tardar hasta 48 horas.",
            color = SocialTextMuted,
            fontSize = 14.sp,
        )
        resumen?.let {
            Text(
                "${it.totalPublicaciones} ${if (it.totalPublicaciones == 1) "publicada" else "publicadas"} · " +
                    "${it.pendientes} esperando aprobación · " +
                    "${it.fallidas} ${if (it.fallidas == 1) "no se pudo publicar" else "no se pudieron publicar"}",
                color = if (it.fallidas > 0) Color(0xFF93000A) else SocialTextDark,
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold,
            )
        }
        OutlinedButton(onClick = onActualizar, enabled = !actualizando) {
            if (actualizando) {
                CircularProgressIndicator(strokeWidth = 2.dp, modifier = Modifier.size(16.dp), color = SocialBrand)
            } else {
                Icon(Icons.Filled.Refresh, contentDescription = null, modifier = Modifier.size(18.dp))
            }
            Spacer(Modifier.width(8.dp))
            Text(if (actualizando) "Actualizando…" else "Actualizar métricas")
        }
        mensaje?.let { Text(it, color = SocialTextMuted, fontSize = 13.sp) }
    }
}

@OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
@Composable
private fun TarjetaRed(red: String, datos: RedResumenDto?) {
    val nombre = SocialFormat.etiquetaRed(red)
    val total = datos?.publicaciones ?: 0
    val metricas = SocialFormat.metricasDeRed(red)

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(24.dp))
            .background(Color.White)
            .border(1.dp, Color(0xFFE4E1ED), RoundedCornerShape(24.dp))
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            RedLogo(red = red, size = 48.dp)
            Spacer(Modifier.width(14.dp))
            Column {
                Text(nombre, color = SocialTextDark, fontSize = 22.sp, fontWeight = FontWeight.ExtraBold)
                Text(
                    (if (total == 1) "1 publicación" else "$total publicaciones") +
                        (if (total > 0) " · ${datos?.publicacionesMes ?: 0} este mes" else ""),
                    color = SocialTextMuted,
                    fontSize = 13.sp,
                )
            }
        }
        if (total == 0) {
            Text(
                "Aún no hay publicaciones en $nombre. Aparecen cuando el cliente aprueba una campaña con $nombre como destino.",
                color = SocialTextMuted,
                fontSize = 14.sp,
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(16.dp))
                    .background(SocialSurfaceSoft)
                    .padding(16.dp),
            )
        } else {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                metricas.principales.forEach { m ->
                    CifraMetrica(m.etiqueta, SocialFormat.valor(datos, m.campo), grande = true, modifier = Modifier.weight(1f))
                }
            }
            HorizontalDivider(color = Color(0xFFE4E1ED))
            FlowRow(horizontalArrangement = Arrangement.spacedBy(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                metricas.secundarias.forEach { m ->
                    CifraMetrica(m.etiqueta, SocialFormat.valor(datos, m.campo))
                }
            }
            Text(
                if ((datos?.conMetricas ?: 0) == 0) "Meta todavía no entregó métricas de estas publicaciones."
                else "Totales de ${datos?.conMetricas} de $total · leídos de Meta ${SocialFormat.haceCuanto(datos?.metricasAl).orEmpty()}",
                color = SocialTextMuted,
                fontSize = 12.sp,
            )
        }
    }
}

@Composable
private fun FilaPublicacion(publicacion: PublicationDto, onClick: () -> Unit) {
    val p = publicacion
    val m = p.ultimaMetrica
    val principales = SocialFormat.metricasDeRed(p.red).principales
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White)
            .border(1.dp, Color(0xFFE4E1ED), RoundedCornerShape(16.dp))
            .clickable(onClickLabel = "Ver estadísticas", onClick = onClick)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            RedLogo(red = p.red, size = 32.dp)
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    p.campaignTitulo.orEmpty().ifBlank { "Campaña" },
                    color = SocialTextDark,
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    listOfNotNull(p.cuentaNombre, p.clienteNombre?.takeIf { it.isNotBlank() }).joinToString(" · "),
                    color = SocialTextMuted,
                    fontSize = 12.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            EstadoPublicacionPill(p.estado)
            p.versionAprobada?.let { Text("Versión $it aprobada", color = SocialTextMuted, fontSize = 12.sp) }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
            principales.forEach { metrica ->
                val valor = SocialFormat.valor(m, metrica.campo)
                Column(Modifier.weight(1f)) {
                    Text(metrica.etiqueta, color = SocialTextMuted, fontSize = 12.sp)
                    Text(
                        when {
                            m == null -> "—"
                            valor == null -> "sin dato"
                            else -> SocialFormat.formatoMetrica(valor)
                        },
                        color = if (m != null && valor != null) SocialTextDark else SocialTextMuted,
                        fontSize = if (m != null && valor != null) 16.sp else 13.sp,
                        fontWeight = if (m != null && valor != null) FontWeight.ExtraBold else FontWeight.Medium,
                        modifier = if (m == null) Modifier.semantics { contentDescription = "sin lectura todavía" } else Modifier,
                    )
                }
            }
        }
        Text("Ver estadísticas", color = SocialBrand, fontWeight = FontWeight.Bold, fontSize = 13.sp)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DetallePublicacion(
    datos: PublicationStatsDto?,
    error: String?,
    onCerrar: () -> Unit,
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    ModalBottomSheet(onDismissRequest = onCerrar, sheetState = sheetState, containerColor = Color.White) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp),
        ) {
            when {
                error != null -> Text(error, color = Color(0xFF93000A))
                datos == null -> Box(Modifier.fillMaxWidth().height(160.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = SocialBrand)
                }
                else -> ContenidoDetalle(datos)
            }
        }
    }
}

@OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
@Composable
private fun ContenidoDetalle(datos: PublicationStatsDto) {
    val p = datos.publicacion
    val metrica = p.ultimaMetrica
    val historial = datos.historial.orEmpty()
    val uriHandler = LocalUriHandler.current
    val metricas = SocialFormat.metricasDeRed(p.red)

    Row(verticalAlignment = Alignment.CenterVertically) {
        RedLogo(red = p.red, size = 36.dp)
        Spacer(Modifier.width(12.dp))
        Column {
            Text(p.campaignTitulo.orEmpty(), color = SocialTextDark, fontSize = 18.sp, fontWeight = FontWeight.ExtraBold)
            Text("${p.cuentaNombre} · ${SocialFormat.etiquetaRed(p.red)}", color = SocialTextMuted, fontSize = 13.sp)
        }
    }

    // Aprobada → publicada → medida: cada número nace de una versión que el cliente aprobó.
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        PasoCadena(
            hecho = p.versionAprobada != null,
            titulo = "Aprobada por el cliente",
            detalle = p.versionAprobada?.let { "Versión $it de la campaña" } ?: "Esperando la aprobación",
        )
        PasoCadena(
            hecho = p.estado == "publicado",
            fallo = p.estado == "fallido",
            titulo = if (p.estado == "publicado") "Publicada en ${p.cuentaNombre}" else SocialFormat.estadoPublicacion(p.estado).texto,
            detalle = if (p.estado == "publicado") SocialFormat.fechaCorta(p.publicadoAt) else p.error?.takeIf { it.isNotBlank() },
        )
        PasoCadena(
            hecho = metrica != null,
            titulo = "Medida en Meta",
            detalle = if (metrica != null) {
                "${if (historial.size == 1) "1 lectura" else "${historial.size} lecturas"}, la última ${SocialFormat.haceCuanto(metrica.obtenidaAt).orEmpty()}"
            } else {
                "Sin lecturas todavía"
            },
        )
    }

    if (p.estado == "publicado" && !p.permalink.isNullOrBlank()) {
        Button(
            onClick = { uriHandler.openUri(p.permalink) },
            colors = ButtonDefaults.buttonColors(containerColor = SocialBrand),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Icon(Icons.AutoMirrored.Filled.OpenInNew, contentDescription = null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(8.dp))
            Text("Ver en ${SocialFormat.etiquetaRed(p.red)}")
        }
    }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Métricas", color = SocialTextDark, fontSize = 16.sp, fontWeight = FontWeight.Bold)
        datos.aviso?.takeIf { it.isNotBlank() }?.let { Text(it, color = SocialTextMuted, fontSize = 13.sp) }
        if (metrica == null) {
            Text(
                if (p.estado == "publicado") "Meta todavía no entrega métricas de esta publicación; pueden tardar hasta 48 horas."
                else "Las métricas aparecen cuando la publicación ya está en la red social.",
                color = SocialTextMuted,
                fontSize = 14.sp,
            )
        } else {
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(24.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                (metricas.principales + metricas.secundarias).forEach { m ->
                    CifraMetrica(m.etiqueta, SocialFormat.valor(metrica, m.campo), modifier = Modifier.width(96.dp))
                }
            }
        }
    }

    if (historial.size > 1) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Historial de lecturas", color = SocialTextDark, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            historial.forEach { h -> FilaHistorial(h, metricas.principales.first().etiqueta) }
        }
    }

    p.copyAprobado?.takeIf { it.isNotBlank() }?.let { copy ->
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                if (p.estado == "publicado") "Texto publicado" else "Texto aprobado",
                color = SocialTextDark,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
            )
            Text(
                copy,
                color = SocialTextDark,
                fontSize = 14.sp,
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(SocialSurfaceSoft)
                    .padding(14.dp),
            )
        }
    }
}

@Composable
private fun PasoCadena(hecho: Boolean, titulo: String, detalle: String?, fallo: Boolean = false) {
    Row(verticalAlignment = Alignment.Top) {
        Box(
            modifier = Modifier
                .size(26.dp)
                .clip(CircleShape)
                .background(
                    when {
                        fallo -> Color(0xFFBA1A1A)
                        hecho -> Color(0xFF2E7D32)
                        else -> Color(0xFFE9E6F3)
                    }
                ),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                if (fallo) Icons.Filled.ErrorOutline else Icons.Filled.CheckCircle,
                contentDescription = null,
                tint = if (fallo || hecho) Color.White else Color(0xFF767586),
                modifier = Modifier.size(16.dp),
            )
        }
        Spacer(Modifier.width(12.dp))
        Column {
            Text(titulo, color = SocialTextDark, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            detalle?.let {
                Text(it, color = if (fallo) Color(0xFF93000A) else SocialTextMuted, fontSize = 13.sp)
            }
        }
    }
}

@Composable
private fun FilaHistorial(m: PublicationMetricDto, etiquetaMeGusta: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(SocialSurfaceSoft)
            .padding(horizontal = 12.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(SocialFormat.fechaCorta(m.obtenidaAt).orEmpty(), color = SocialTextMuted, fontSize = 12.sp)
        Text(
            "$etiquetaMeGusta ${SocialFormat.formatoMetrica(m.meGusta)} · Coment. ${SocialFormat.formatoMetrica(m.comentarios)}",
            color = SocialTextDark,
            fontSize = 12.sp,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

@Composable
private fun SinPublicaciones() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .border(1.dp, Color(0xFFC7C4D7), RoundedCornerShape(16.dp))
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Icon(Icons.Filled.BarChart, contentDescription = null, tint = Color(0xFF767586), modifier = Modifier.size(32.dp))
        Text("Aún no hay publicaciones", color = SocialTextDark, fontWeight = FontWeight.Bold)
        Text(
            "Cuando se apruebe una campaña con destino en Instagram o Facebook, aquí verás cómo le va.",
            color = SocialTextMuted,
            fontSize = 13.sp,
        )
    }
}

@Composable
private fun ErrorEstadisticas(mensaje: String, onReintentar: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text("No pudimos cargar las estadísticas", color = SocialTextDark, fontWeight = FontWeight.Bold)
        Text(mensaje, color = SocialTextMuted, fontSize = 14.sp, modifier = Modifier.padding(top = 8.dp))
        Button(
            onClick = onReintentar,
            colors = ButtonDefaults.buttonColors(containerColor = SocialBrand),
            modifier = Modifier.padding(top = 16.dp),
        ) { Text("Reintentar") }
    }
}
