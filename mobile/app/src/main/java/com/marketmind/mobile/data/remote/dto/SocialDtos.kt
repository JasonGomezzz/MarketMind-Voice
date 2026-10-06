package com.marketmind.mobile.data.remote.dto

import com.google.gson.annotations.SerializedName

/*
 * Redes sociales (Django /api/social/). Gson no aplica valores por defecto de Kotlin:
 * las listas son anulables y se leen con orEmpty(). Una métrica que Meta no informa
 * llega como null y se muestra "sin dato", nunca 0.
 */

data class SocialConnectionDto(
    val id: Long,
    val red: String,
    @SerializedName("cuenta_nombre") val cuentaNombre: String,
    val estado: String,
    @SerializedName("propietario_rol") val propietarioRol: String? = null,
)

data class ConexionesEnvelopeDto(
    val conexiones: List<SocialConnectionDto>? = null,
)

data class PublicationMetricDto(
    @SerializedName("me_gusta") val meGusta: Int? = null,
    val comentarios: Int? = null,
    val compartidos: Int? = null,
    val guardados: Int? = null,
    val alcance: Int? = null,
    val vistas: Int? = null,
    val interacciones: Int? = null,
    @SerializedName("obtenida_at") val obtenidaAt: String? = null,
)

data class PublicationDto(
    val id: Long,
    val campaign: Long,
    @SerializedName("campaign_titulo") val campaignTitulo: String? = null,
    @SerializedName("cliente_nombre") val clienteNombre: String? = null,
    val red: String,
    @SerializedName("cuenta_nombre") val cuentaNombre: String,
    val estado: String,
    val permalink: String? = null,
    val error: String? = null,
    val intentos: Int = 0,
    @SerializedName("version_aprobada") val versionAprobada: Int? = null,
    @SerializedName("publicado_at") val publicadoAt: String? = null,
    @SerializedName("ultima_metrica") val ultimaMetrica: PublicationMetricDto? = null,
    @SerializedName("copy_aprobado") val copyAprobado: String? = null,
)

data class PublicacionesEnvelopeDto(
    val publicaciones: List<PublicationDto>? = null,
)

data class PublicacionEnvelopeDto(
    val publicacion: PublicationDto? = null,
)

data class PublicationStatsDto(
    val publicacion: PublicationDto,
    val historial: List<PublicationMetricDto>? = null,
    val aviso: String? = null,
)

data class RedResumenDto(
    val publicaciones: Int = 0,
    @SerializedName("publicaciones_mes") val publicacionesMes: Int = 0,
    @SerializedName("con_metricas") val conMetricas: Int = 0,
    @SerializedName("metricas_al") val metricasAl: String? = null,
    @SerializedName("me_gusta") val meGusta: Int? = null,
    val comentarios: Int? = null,
    val compartidos: Int? = null,
    val guardados: Int? = null,
    val alcance: Int? = null,
    val vistas: Int? = null,
    val interacciones: Int? = null,
)

data class ResumenRedesDto(
    val redes: Map<String, RedResumenDto>? = null,
    @SerializedName("total_publicaciones") val totalPublicaciones: Int = 0,
    val fallidas: Int = 0,
    val pendientes: Int = 0,
)

data class ActualizacionMetricasDto(
    val actualizadas: Int = 0,
    @SerializedName("sin_datos") val sinDatos: Int = 0,
)

/** Cuerpo de submit: cuentas donde se publicará al aprobar (puede ir vacío). */
data class SubmitRequest(
    val destinos: List<Long>,
)

/** Destino que Spring devuelve en el detalle de campaña del cliente. */
data class DestinoDto(
    val red: String,
    @SerializedName(value = "cuentaNombre", alternate = ["cuenta_nombre"]) val cuentaNombre: String,
    val estado: String? = null,
    val permalink: String? = null,
)
