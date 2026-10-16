"""Límites atómicos de la recuperación por correo e IP (portados de la rama de Piero)."""

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.authentication import password_reset
from apps.authentication.recovery_throttles import RecoveryRequestThrottle, recovery_key

pytestmark = pytest.mark.django_db
REQUEST = "/api/auth/password-reset/"
CONFIRM = "/api/auth/password-reset/confirm/"
CLOCK = "apps.authentication.recovery_throttles.time.time"


@pytest.fixture(autouse=True)
def envio_sincrono(monkeypatch, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    monkeypatch.setattr(password_reset, "_iniciar_hilo", password_reset.procesar_solicitud)


@pytest.fixture
def send(django_capture_on_commit_callbacks):
    def _send(email, ip="127.0.0.1", **headers):
        with django_capture_on_commit_callbacks(execute=True):
            return APIClient().post(REQUEST, {"email": email}, format="json", REMOTE_ADDR=ip, **headers)
    return _send


def test_cuota_por_correo_sobrevive_al_cambio_de_ip_y_se_reinicia_cada_hora(send):
    for index in range(5):
        with patch(CLOCK, return_value=3600 + index * 61):
            assert send("nadie@example.com", f"10.0.0.{index}").status_code == 200
    with patch(CLOCK, return_value=4000):
        response = send("NADIE@example.com", "10.0.0.99")
        assert response.status_code == 429
        assert response.data["data"]["retry_after"] == 3200
        assert send("otro@example.com", "10.0.0.99").status_code == 200
    with patch(CLOCK, return_value=7200):
        assert send("nadie@example.com").status_code == 200


def test_cuota_por_ip_cuenta_correos_distintos_e_ignora_cabeceras_falsas(send):
    for index in range(20):
        assert send(f"nadie{index}@example.com").status_code == 200
    assert send("extra@example.com", HTTP_X_FORWARDED_FOR="8.8.8.8").status_code == 429
    assert send("extra@example.com", ip="10.0.0.2").status_code == 200


def test_el_cooldown_vence_sin_reenviar_antes(send):
    with patch(CLOCK, return_value=3600):
        assert send("nadie@example.com").status_code == 200
    with patch(CLOCK, return_value=3630):
        response = send("nadie@example.com")
        assert response.status_code == 429
        assert response.data["data"]["retry_after"] == 30
    with patch(CLOCK, return_value=3661):
        assert send("nadie@example.com").status_code == 200


def test_cuentas_existentes_e_inexistentes_tienen_la_misma_politica(send, user_marketero):
    assert send(user_marketero.email).data == send("nadie@example.com").data
    assert send(user_marketero.email).data == send("nadie@example.com").data
    assert len(mail.outbox) == 1


def test_pedir_enlaces_no_bloquea_confirmar_y_confirmar_tiene_limite(send):
    for index in range(20):
        assert send(f"nadie{index}@example.com").status_code == 200
    client = APIClient()
    for _ in range(20):
        response = client.post(CONFIRM, {"token": "malo", "new_password": "NuevaClave2026!"}, format="json")
        assert response.status_code == 400
    assert client.post(CONFIRM, {}, format="json").status_code == 429


def test_si_la_cache_falla_responde_503_sin_enviar(user_marketero):
    with patch("apps.authentication.recovery_throttles.cache.add", side_effect=ConnectionError), \
            patch.object(password_reset, "programar_solicitud") as programar:
        response = APIClient().post(REQUEST, {"email": user_marketero.email}, format="json")
    assert response.status_code == 503
    assert response.data["success"] is False
    programar.assert_not_called()


def test_las_claves_no_contienen_datos_personales():
    key = recovery_key("email", "nadie@example.com")
    assert "nadie" not in key
    assert "@" not in key
    assert key != recovery_key("email", "otro@example.com")


def test_contador_por_hora_atomico_con_intentos_concurrentes():
    def attempt(_):
        return RecoveryRequestThrottle().hourly_limit("test:ip", "127.0.0.1", 20, 3600)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(50)))
    assert sum(results) == 20


def test_cooldown_se_reserva_atomicamente():
    def attempt(_):
        return cache.add(recovery_key("email:cooldown", "nadie@example.com"), 3660, timeout=60)

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(50))) == 1


def test_peticiones_en_paralelo_reservan_un_solo_envio():
    request = SimpleNamespace(method="POST", data={"email": "nadie@example.com"}, META={"REMOTE_ADDR": "127.0.0.1"})
    with patch(CLOCK, return_value=3600), ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: RecoveryRequestThrottle().allow_request(request, None), range(50)))
    assert sum(results) == 1
