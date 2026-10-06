package com.marketmind.mobile.ui.social

import com.marketmind.mobile.data.remote.dto.PublicationDto
import com.marketmind.mobile.data.remote.dto.PublicationMetricDto
import com.marketmind.mobile.data.remote.dto.RedResumenDto
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.Locale

/**
 * Textos y reglas de las redes sociales, sin dependencias de Android (probados en SocialFormatTest).
 * Mismas reglas que la web: lo que Meta no informa es "sin dato", nunca 0.
 */
object SocialFormat {

    enum class Tono { Ok, Error, Neutral }

    data class Estado(val texto: String, val tono: Tono)

    /** Una métrica a mostrar: el campo del backend y su etiqueta en esa red. */
    data class Metrica(val campo: String, val etiqueta: String)

    data class MetricasDeRed(val principales: List<Metrica>, val secundarias: List<Metrica>)

    private val LOCALE_PE: Locale = Locale.forLanguageTag("es-PE")

    fun etiquetaRed(red: String): String = when (red) {
        "instagram" -> "Instagram"
        "facebook" -> "Facebook"
        else -> red
    }

    fun estadoPublicacion(estado: String): Estado = when (estado) {
        "esperando_aprobacion" -> Estado("Se publicará al aprobar", Tono.Neutral)
        "publicando" -> Estado("Publicando…", Tono.Neutral)
        "publicado" -> Estado("Publicado", Tono.Ok)
        "fallido" -> Estado("No se pudo publicar", Tono.Error)
        "cancelado" -> Estado("Cancelado", Tono.Neutral)
        else -> Estado(estado, Tono.Neutral)
    }

    /** ¿Puede el marketero pulsar "Publicar ahora / Reintentar"? */
    fun puedeReintentar(publicacion: PublicationDto, estadoCampana: String): Boolean =
        estadoCampana == "aprobado" &&
            publicacion.estado in setOf("fallido", "esperando_aprobacion") &&
            publicacion.intentos < 3

    fun formatoMetrica(valor: Int?): String =
        valor?.let { NumberFormat.getIntegerInstance(LOCALE_PE).format(it) } ?: "sin dato"

    /** Facebook llama "reacciones" a sus me gusta y no tiene guardados. */
    fun metricasDeRed(red: String?): MetricasDeRed = if (red == "facebook") {
        MetricasDeRed(
            principales = listOf(Metrica("me_gusta", "Reacciones"), Metrica("comentarios", "Comentarios"), Metrica("compartidos", "Compartidos")),
            secundarias = listOf(Metrica("alcance", "Alcance"), Metrica("vistas", "Vistas"), Metrica("interacciones", "Clics")),
        )
    } else {
        MetricasDeRed(
            principales = listOf(Metrica("me_gusta", "Me gusta"), Metrica("comentarios", "Comentarios"), Metrica("compartidos", "Compartidos")),
            secundarias = listOf(
                Metrica("alcance", "Alcance"),
                Metrica("vistas", "Vistas"),
                Metrica("guardados", "Guardados"),
                Metrica("interacciones", "Interacciones"),
            ),
        )
    }

    fun valor(m: PublicationMetricDto?, campo: String): Int? = when (campo) {
        "me_gusta" -> m?.meGusta
        "comentarios" -> m?.comentarios
        "compartidos" -> m?.compartidos
        "guardados" -> m?.guardados
        "alcance" -> m?.alcance
        "vistas" -> m?.vistas
        "interacciones" -> m?.interacciones
        else -> null
    }

    fun valor(r: RedResumenDto?, campo: String): Int? = when (campo) {
        "me_gusta" -> r?.meGusta
        "comentarios" -> r?.comentarios
        "compartidos" -> r?.compartidos
        "guardados" -> r?.guardados
        "alcance" -> r?.alcance
        "vistas" -> r?.vistas
        "interacciones" -> r?.interacciones
        else -> null
    }

    /** Milisegundos desde epoch de una fecha ISO de Django ("2026-10-06T18:58:29.123456Z"). */
    fun aEpochMs(iso: String?): Long? {
        if (iso.isNullOrBlank()) return null
        val sinFraccion = iso.replace(Regex("\\.\\d+"), "").replace(Regex("Z$"), "+00:00")
        return runCatching {
            SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX", Locale.US).parse(sinFraccion)?.time
        }.getOrNull()
    }

    /** "hace 5 min", "hace 3 h", "hace 2 días" o la fecha corta. */
    fun haceCuanto(iso: String?, ahoraMs: Long = System.currentTimeMillis()): String? {
        val ms = aEpochMs(iso) ?: return null
        val minutos = (ahoraMs - ms) / 60_000
        return when {
            minutos < 1 -> "hace un momento"
            minutos < 60 -> "hace $minutos min"
            minutos < 60 * 24 -> "hace ${minutos / 60} h"
            minutos < 60 * 24 * 7 -> (minutos / (60 * 24)).let { if (it == 1L) "hace 1 día" else "hace $it días" }
            else -> SimpleDateFormat("d MMM yyyy", LOCALE_PE).format(ms)
        }
    }

    /** "6 oct. 2026, 13:58" en la zona del teléfono. */
    fun fechaCorta(iso: String?): String? =
        aEpochMs(iso)?.let { SimpleDateFormat("d MMM yyyy, HH:mm", LOCALE_PE).format(it) }
}
