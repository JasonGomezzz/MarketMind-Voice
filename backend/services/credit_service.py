"""
Créditos de IA con operaciones atómicas en la base de datos.

Antes se hacía `user.tokens_disponibles -= 1` en memoria y luego save(): dos
peticiones simultáneas podían leer el mismo saldo y gastar dos veces el último
crédito, o una devolución podía pisar un descuento concurrente. Aquí cada cambio
es un único UPDATE con F(), y el cobro solo ocurre si queda saldo
(`tokens_disponibles > 0` en el mismo UPDATE).
"""

from django.db.models import F

from apps.authentication.models import User


def consumir_credito(user: User) -> bool:
    """Descuenta 1 crédito si hay saldo. Devuelve False (sin cobrar) si no lo hay."""
    cobrado = User.objects.filter(pk=user.pk, tokens_disponibles__gt=0).update(
        tokens_disponibles=F("tokens_disponibles") - 1
    )
    user.refresh_from_db(fields=["tokens_disponibles"])
    return cobrado == 1


def agregar_creditos(user: User, cantidad: int = 1) -> None:
    """Devuelve o suma créditos sin pisar cambios concurrentes."""
    User.objects.filter(pk=user.pk).update(tokens_disponibles=F("tokens_disponibles") + cantidad)
    user.refresh_from_db(fields=["tokens_disponibles"])
