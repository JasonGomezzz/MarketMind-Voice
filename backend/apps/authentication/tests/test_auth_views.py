"""Tests de RegisterView, LoginView, LogoutView y MeView."""

import pytest
from rest_framework.test import APIClient

from apps.authentication.models import User, UserRole

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/token/"
LOGOUT_URL = "/api/auth/logout/"
ME_URL = "/api/auth/me/"


@pytest.mark.django_db
class TestRegisterView:
    def test_register_success(self):
        client = APIClient()
        response = client.post(REGISTER_URL, {
            "email": "nuevo@test.com",
            "nombre": "Nuevo Usuario",
            "password": "Test1234!",
            "rol": "marketero",
        }, format="json")
        assert response.status_code == 201
        assert response.data["success"] is True
        assert User.objects.filter(email="nuevo@test.com").exists()

    def test_register_returns_user_data(self):
        client = APIClient()
        response = client.post(REGISTER_URL, {
            "email": "data@test.com",
            "nombre": "Data User",
            "password": "Test1234!",
            "rol": "cliente",
        }, format="json")
        assert response.status_code == 201
        user_data = response.data["data"]["user"]
        assert user_data["email"] == "data@test.com"
        assert user_data["rol"] == "cliente"

    def test_register_duplicate_email(self, db):
        User.objects.create_user(
            email="dup@test.com",
            password="Test1234!",
            nombre="Existing",
            rol=UserRole.MARKETERO,
        )
        client = APIClient()
        response = client.post(REGISTER_URL, {
            "email": "dup@test.com",
            "nombre": "Otro",
            "password": "Test1234!",
            "rol": "marketero",
        }, format="json")
        assert response.status_code == 400
        assert response.data["success"] is False

    def test_register_invalid_email(self):
        client = APIClient()
        response = client.post(REGISTER_URL, {
            "email": "not-an-email",
            "nombre": "User",
            "password": "Test1234!",
            "rol": "marketero",
        }, format="json")
        assert response.status_code == 400

    def test_register_invalid_rol(self):
        client = APIClient()
        response = client.post(REGISTER_URL, {
            "email": "user@test.com",
            "nombre": "User",
            "password": "Test1234!",
            "rol": "god",
        }, format="json")
        assert response.status_code == 400

    def test_register_short_password(self):
        client = APIClient()
        response = client.post(REGISTER_URL, {
            "email": "short@test.com",
            "nombre": "User",
            "password": "abc",
            "rol": "marketero",
        }, format="json")
        assert response.status_code == 400

    def test_register_missing_fields(self):
        client = APIClient()
        response = client.post(REGISTER_URL, {}, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginView:
    def _create_user(self):
        return User.objects.create_user(
            email="login@test.com",
            password="Test1234!",
            nombre="Login User",
            rol=UserRole.MARKETERO,
        )

    def test_login_success_returns_tokens(self):
        self._create_user()
        client = APIClient()
        response = client.post(LOGIN_URL, {
            "email": "login@test.com",
            "password": "Test1234!",
        }, format="json")
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_returns_role_and_nombre(self):
        self._create_user()
        client = APIClient()
        response = client.post(LOGIN_URL, {
            "email": "login@test.com",
            "password": "Test1234!",
        }, format="json")
        assert response.status_code == 200
        assert response.data["role"] == "marketero"
        assert response.data["nombre"] == "Login User"

    def test_login_wrong_password(self):
        self._create_user()
        client = APIClient()
        response = client.post(LOGIN_URL, {
            "email": "login@test.com",
            "password": "WrongPass!",
        }, format="json")
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        client = APIClient()
        response = client.post(LOGIN_URL, {
            "email": "nobody@test.com",
            "password": "Test1234!",
        }, format="json")
        assert response.status_code == 401

    def test_login_inactive_user(self):
        user = self._create_user()
        user.is_active = False
        user.save()
        client = APIClient()
        response = client.post(LOGIN_URL, {
            "email": "login@test.com",
            "password": "Test1234!",
        }, format="json")
        assert response.status_code == 401


@pytest.mark.django_db
class TestLogoutView:
    def _get_tokens(self) -> dict:
        User.objects.create_user(
            email="logout@test.com",
            password="Test1234!",
            nombre="Logout User",
            rol=UserRole.MARKETERO,
        )
        client = APIClient()
        resp = client.post(LOGIN_URL, {
            "email": "logout@test.com",
            "password": "Test1234!",
        }, format="json")
        return resp.data

    def test_logout_success(self):
        tokens = self._get_tokens()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = client.post(LOGOUT_URL, {"refresh": tokens["refresh"]}, format="json")
        assert response.status_code == 200
        assert response.data["success"] is True

    def test_logout_missing_refresh(self, user_marketero):
        client = APIClient()
        client.force_authenticate(user=user_marketero)
        response = client.post(LOGOUT_URL, {}, format="json")
        assert response.status_code == 400
        assert response.data["success"] is False

    def test_logout_invalid_token(self, user_marketero):
        client = APIClient()
        client.force_authenticate(user=user_marketero)
        response = client.post(LOGOUT_URL, {"refresh": "bad-token"}, format="json")
        assert response.status_code == 400

    def test_logout_unauthenticated(self):
        client = APIClient()
        response = client.post(LOGOUT_URL, {"refresh": "something"}, format="json")
        assert response.status_code == 401


@pytest.mark.django_db
class TestMeView:
    def test_me_returns_user(self, user_marketero, api_client):
        response = api_client.get(ME_URL)
        assert response.status_code == 200
        assert response.data["success"] is True
        user_data = response.data["data"]["user"]
        assert user_data["email"] == user_marketero.email
        assert user_data["rol"] == UserRole.MARKETERO

    def test_me_unauthenticated(self):
        client = APIClient()
        response = client.get(ME_URL)
        assert response.status_code == 401

    def test_me_includes_tokens_disponibles(self, user_marketero, api_client):
        response = api_client.get(ME_URL)
        assert response.status_code == 200
        assert "tokens_disponibles" in response.data["data"]["user"]


CHANGE_PASSWORD_URL = "/api/auth/me/change-password/"


@pytest.mark.django_db
class TestUpdateProfile:
    def test_patch_nombre_actualiza_perfil(self, user_marketero, api_client):
        response = api_client.patch(ME_URL, {"nombre": "Nombre Nuevo"}, format="json")
        assert response.status_code == 200
        user_marketero.refresh_from_db()
        assert user_marketero.nombre == "Nombre Nuevo"

    def test_patch_nombre_vacio_400(self, api_client):
        response = api_client.patch(ME_URL, {"nombre": ""}, format="json")
        assert response.status_code == 400

    def test_patch_no_permite_cambiar_rol(self, user_marketero, api_client):
        api_client.patch(ME_URL, {"nombre": "Otro", "rol": "superadmin"}, format="json")
        user_marketero.refresh_from_db()
        assert user_marketero.rol == UserRole.MARKETERO

    def test_patch_unauthenticated_401(self):
        client = APIClient()
        response = client.patch(ME_URL, {"nombre": "X Y"}, format="json")
        assert response.status_code == 401


@pytest.mark.django_db
class TestChangePassword:
    def test_cambio_correcto_200(self, user_marketero, api_client):
        response = api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": "Test1234!", "new_password": "NuevaClave2026!"},
            format="json",
        )
        assert response.status_code == 200
        user_marketero.refresh_from_db()
        assert user_marketero.check_password("NuevaClave2026!")

    def test_password_actual_incorrecta_400(self, user_marketero, api_client):
        response = api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": "incorrecta", "new_password": "NuevaClave2026!"},
            format="json",
        )
        assert response.status_code == 400
        user_marketero.refresh_from_db()
        assert user_marketero.check_password("Test1234!")

    def test_nueva_password_corta_400(self, api_client):
        response = api_client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": "Test1234!", "new_password": "corta"},
            format="json",
        )
        assert response.status_code == 400

    def test_unauthenticated_401(self):
        client = APIClient()
        response = client.post(
            CHANGE_PASSWORD_URL,
            {"current_password": "x", "new_password": "NuevaClave2026!"},
            format="json",
        )
        assert response.status_code == 401
