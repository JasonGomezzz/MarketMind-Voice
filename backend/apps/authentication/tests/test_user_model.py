"""Tests del modelo User y UserManager."""

import pytest
from django.db import IntegrityError

from apps.authentication.models import User, UserRole


@pytest.mark.django_db
class TestUserManager:
    def test_create_user_sets_fields(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="Test1234!",
            nombre="Test User",
            rol=UserRole.MARKETERO,
        )
        assert user.email == "test@example.com"
        assert user.nombre == "Test User"
        assert user.rol == UserRole.MARKETERO
        assert user.is_active is True
        assert user.pk is not None

    def test_create_user_hashes_password(self):
        user = User.objects.create_user(
            email="hash@example.com",
            password="Test1234!",
            nombre="Hash User",
            rol=UserRole.CLIENTE,
        )
        assert user.check_password("Test1234!") is True
        assert user.password != "Test1234!"

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(
            email="UPPER@EXAMPLE.COM",
            password="Test1234!",
            nombre="Norm User",
            rol=UserRole.CLIENTE,
        )
        # Django normalize_email lowercases the domain part only (RFC 5321)
        assert user.email == "UPPER@example.com"

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match="email es obligatorio"):
            User.objects.create_user(
                email="",
                password="Test1234!",
                nombre="No Email",
                rol=UserRole.CLIENTE,
            )

    def test_create_user_invalid_rol(self):
        with pytest.raises(ValueError, match="Rol inválido"):
            User.objects.create_user(
                email="bad@example.com",
                password="Test1234!",
                nombre="Bad Rol",
                rol="no_existe",
            )

    def test_create_superuser_flags(self):
        user = User.objects.create_superuser(
            email="sa@example.com",
            password="Admin1234!",
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.rol == UserRole.SUPERADMIN

    def test_create_superuser_default_nombre(self):
        user = User.objects.create_superuser(
            email="sa2@example.com",
            password="Admin1234!",
        )
        assert user.nombre == "Super Admin"

    def test_tokens_disponibles_default(self):
        user = User.objects.create_user(
            email="tokens@example.com",
            password="Test1234!",
            nombre="Token User",
            rol=UserRole.CLIENTE,
        )
        assert user.tokens_disponibles == 100

    def test_token_version_default(self):
        user = User.objects.create_user(
            email="version@example.com",
            password="Test1234!",
            nombre="Version User",
            rol=UserRole.MARKETERO,
        )
        assert user.token_version == 0

    def test_email_unique_constraint(self):
        User.objects.create_user(
            email="dup@example.com",
            password="Test1234!",
            nombre="User 1",
            rol=UserRole.CLIENTE,
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email="dup@example.com",
                password="Test1234!",
                nombre="User 2",
                rol=UserRole.CLIENTE,
            )


@pytest.mark.django_db
class TestUserRoleProperties:
    def test_is_superadmin(self):
        user = User.objects.create_user(
            email="sa@example.com",
            password="Test1234!",
            nombre="SA",
            rol=UserRole.SUPERADMIN,
        )
        assert user.is_superadmin is True
        assert user.is_marketero is False
        assert user.is_cliente is False

    def test_is_marketero(self):
        user = User.objects.create_user(
            email="m@example.com",
            password="Test1234!",
            nombre="M",
            rol=UserRole.MARKETERO,
        )
        assert user.is_superadmin is False
        assert user.is_marketero is True
        assert user.is_cliente is False

    def test_is_cliente(self):
        user = User.objects.create_user(
            email="c@example.com",
            password="Test1234!",
            nombre="C",
            rol=UserRole.CLIENTE,
        )
        assert user.is_superadmin is False
        assert user.is_marketero is False
        assert user.is_cliente is True

    def test_str(self):
        user = User.objects.create_user(
            email="str@example.com",
            password="Test1234!",
            nombre="Str User",
            rol=UserRole.MARKETERO,
        )
        result = str(user)
        assert "str@example.com" in result
        assert "marketero" in result
