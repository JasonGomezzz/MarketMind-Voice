"""El refresh JWT respeta token_version e is_active (HU18)."""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db

LOGIN_URL = "/api/auth/token/"
REFRESH_URL = "/api/auth/token/refresh/"


def _login(user, password="Test1234!"):
    response = APIClient().post(LOGIN_URL, {"email": user.email, "password": password}, format="json")
    assert response.status_code == 200
    return response.data


def test_refresh_valido_rota_y_conserva_token_version(user_marketero):
    tokens = _login(user_marketero)
    response = APIClient().post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")
    assert response.status_code == 200
    assert response.data["access"]
    nuevo = RefreshToken(response.data["refresh"])
    assert nuevo["token_version"] == user_marketero.token_version
    # El refresh rotado sigue sirviendo mientras la versión no cambie.
    segundo = APIClient().post(REFRESH_URL, {"refresh": response.data["refresh"]}, format="json")
    assert segundo.status_code == 200


def test_refresh_falla_si_cambio_token_version(user_marketero):
    tokens = _login(user_marketero)
    user_marketero.token_version += 1
    user_marketero.save(update_fields=["token_version"])

    response = APIClient().post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")

    assert response.status_code == 401
    assert response.data["success"] is False
    assert "sesión ya no es válida" in response.data["message"]


def test_refresh_falla_si_la_cuenta_esta_suspendida(user_marketero):
    tokens = _login(user_marketero)
    user_marketero.is_active = False
    user_marketero.save(update_fields=["is_active"])

    response = APIClient().post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")

    assert response.status_code == 401


def test_refresh_sin_claim_de_version_cuenta_como_cero(user_marketero):
    # Tokens antiguos sin el claim valen solo si la cuenta sigue en la versión 0.
    refresh = RefreshToken.for_user(user_marketero)
    assert APIClient().post(REFRESH_URL, {"refresh": str(refresh)}, format="json").status_code == 200
    user_marketero.token_version = 1
    user_marketero.save(update_fields=["token_version"])
    refresh = RefreshToken.for_user(user_marketero)
    assert APIClient().post(REFRESH_URL, {"refresh": str(refresh)}, format="json").status_code == 401


def test_refresh_invalido_sigue_respondiendo_401():
    response = APIClient().post(REFRESH_URL, {"refresh": "no-es-un-token"}, format="json")
    assert response.status_code == 401
