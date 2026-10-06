"""Prueba con PostgreSQL real: N peticiones simultáneas intentan gastar el último crédito.

SQLite (los tests de Django) no reproduce bloqueos ni concurrencia, por eso esta
prueba va aparte. Usa SOLO la base aislada de pruebas y borra lo que crea.

Desde la raíz del repo, con PostgreSQL de Docker arriba:

    DB_NAME=marketmind_review_20260918_7afba9 backend/venv/bin/python scripts/dev/prueba_credito_concurrente.py
"""

import os
import sys
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")

BASE_AISLADA = "marketmind_review_20260918_7afba9"
if os.environ.get("DB_NAME") != BASE_AISLADA:
    sys.exit(f"Por seguridad solo corre contra la base aislada: DB_NAME={BASE_AISLADA}")

import django  # noqa: E402

django.setup()

from django.db import connection, connections  # noqa: E402

from apps.authentication.models import User, UserRole  # noqa: E402
from services.credit_service import consumir_credito  # noqa: E402

HILOS = 12


def main() -> None:
    assert connection.vendor == "postgresql", connection.vendor
    email = f"concurrencia-{uuid.uuid4().hex[:8]}@test.local"
    user = User.objects.create_user(email=email, password=uuid.uuid4().hex, nombre="Prueba concurrencia",
                                    rol=UserRole.MARKETERO)
    User.objects.filter(pk=user.pk).update(tokens_disponibles=1)

    barrera = threading.Barrier(HILOS)
    resultados: list[bool] = []
    candado = threading.Lock()

    def intentar() -> None:
        copia = User.objects.get(pk=user.pk)  # cada hilo ve "1 crédito" en memoria
        barrera.wait()
        cobrado = consumir_credito(copia)
        with candado:
            resultados.append(cobrado)
        connections.close_all()

    try:
        hilos = [threading.Thread(target=intentar) for _ in range(HILOS)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        final = User.objects.values_list("tokens_disponibles", flat=True).get(pk=user.pk)
        print(f"Base: {connection.settings_dict['NAME']} ({connection.vendor})")
        print(f"{HILOS} peticiones simultáneas con 1 crédito → cobradas: {resultados.count(True)}, rechazadas: {resultados.count(False)}, saldo final: {final}")
        ok = resultados.count(True) == 1 and final == 0
        print("OK: el último crédito se gastó una sola vez" if ok else "FALLO: se gastó más de una vez")
        sys.exit(0 if ok else 1)
    finally:
        User.objects.filter(pk=user.pk).delete()


if __name__ == "__main__":
    main()
