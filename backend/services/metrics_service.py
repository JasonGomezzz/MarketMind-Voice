"""
MarketMind Voice — Estadísticas de publicaciones (Fase 4).

- refrescar_metricas: pide a Meta las métricas de una publicación y guarda una
  foto (PublicationMetric). Respeta un intervalo mínimo para no gastar el
  límite de llamadas de la API.
- resumen_por_red: lo que muestra el dashboard: publicaciones por red,
  totales de la última foto de cada una y serie mensual.

Un dato que Meta no entrega es None; los totales lo ignoran y si ninguna
publicación tiene el dato, el total también es None.
"""

from collections import defaultdict
from datetime import timedelta

from django.db.models import Prefetch, QuerySet
from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.utils import timezone

from apps.social.models import (
    ConexionEstado,
    PublicacionEstado,
    Publication,
    PublicationMetric,
    RedSocial,
)
from services import meta_graph
from services.social_tokens import TokenIlegible, descifrar

INTERVALO_MINIMO = timedelta(minutes=10)
CAMPOS = ["me_gusta", "comentarios", "compartidos", "guardados", "alcance", "vistas", "interacciones"]
MESES_SERIE = 6


class MetricasNoDisponibles(Exception):
    pass


def ultima_metrica(publicacion: Publication) -> PublicationMetric | None:
    return publicacion.metricas.order_by("-obtenida_at").first()


def refrescar_metricas(publicacion: Publication, forzar: bool = False) -> PublicationMetric:
    """Devuelve la foto más reciente; consulta a Meta solo si la última es vieja."""
    if publicacion.estado != PublicacionEstado.PUBLICADO or not publicacion.externo_id:
        raise MetricasNoDisponibles("La publicación todavía no está en la red social.")

    ultima = ultima_metrica(publicacion)
    if ultima and not forzar and timezone.now() - ultima.obtenida_at < INTERVALO_MINIMO:
        return ultima

    conexion = publicacion.conexion
    if conexion is None or conexion.estado != ConexionEstado.ACTIVA:
        raise MetricasNoDisponibles("La cuenta fue desconectada; vuelve a conectarla para ver estadísticas.")
    try:
        token = descifrar(conexion.token_cifrado)
        if publicacion.red == RedSocial.INSTAGRAM:
            datos = meta_graph.metricas_instagram(publicacion.externo_id, token)
        else:
            datos = meta_graph.metricas_facebook(publicacion.externo_id, token)
    except (meta_graph.MetaError, TokenIlegible) as exc:
        if ultima:
            return ultima
        raise MetricasNoDisponibles(str(exc)) from exc

    return PublicationMetric.objects.create(
        publicacion=publicacion,
        crudo=datos.pop("crudo", {}),
        **{campo: _entero(datos.get(campo)) for campo in CAMPOS},
    )


def _entero(valor) -> int | None:
    try:
        return None if valor is None else int(valor)
    except (TypeError, ValueError):
        return None


def con_ultima_metrica(qs: QuerySet[Publication]) -> QuerySet[Publication]:
    """Precarga las fotos ordenadas para leer la última sin una consulta por publicación."""
    return qs.prefetch_related(
        Prefetch("metricas", queryset=PublicationMetric.objects.order_by("-obtenida_at"), to_attr="metricas_ordenadas")
    )


def _sumar(valores: list[int | None]) -> int | None:
    presentes = [v for v in valores if v is not None]
    return sum(presentes) if presentes else None


def resumen_por_red(qs: QuerySet[Publication]) -> dict:
    """Totales por red para el dashboard, usando la última foto de cada publicación."""
    publicadas = con_ultima_metrica(qs.filter(estado=PublicacionEstado.PUBLICADO))
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    redes = {}
    por_red: dict[str, list[Publication]] = defaultdict(list)
    for publicacion in publicadas:
        por_red[publicacion.red].append(publicacion)

    for red in RedSocial.values:
        lista = por_red.get(red, [])
        ultimas = [p.metricas_ordenadas[0] for p in lista if p.metricas_ordenadas]
        redes[red] = {
            "publicaciones": len(lista),
            "publicaciones_mes": sum(1 for p in lista if p.publicado_at and p.publicado_at >= inicio_mes),
            "con_metricas": len(ultimas),
            **{campo: _sumar([getattr(m, campo) for m in ultimas]) for campo in CAMPOS},
        }

    desde = (inicio_mes - timedelta(days=31 * (MESES_SERIE - 1))).replace(day=1)
    serie = (
        qs.filter(estado=PublicacionEstado.PUBLICADO, publicado_at__gte=desde)
        .annotate(mes=TruncMonth("publicado_at"))
        .values("mes", "red")
        .annotate(total=Count("id"))
        .order_by("mes")
    )
    meses: dict[str, dict] = {}
    for fila in serie:
        clave = fila["mes"].strftime("%Y-%m")
        meses.setdefault(clave, {"mes": clave, **{red: 0 for red in RedSocial.values}})[fila["red"]] = fila["total"]

    return {
        "redes": redes,
        "por_mes": sorted(meses.values(), key=lambda m: m["mes"]),
        "total_publicaciones": sum(r["publicaciones"] for r in redes.values()),
        "fallidas": qs.filter(estado=PublicacionEstado.FALLIDO).count(),
        "pendientes": qs.filter(estado=PublicacionEstado.ESPERANDO_APROBACION).count(),
    }
