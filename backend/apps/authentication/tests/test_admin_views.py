"""Tests de AdminUsersListView, AdminUserDetailView y AdminResetQuotaView."""

import pytest
from rest_framework.test import APIClient

from apps.authentication.models import User, UserRole

USERS_URL = "/api/admin/users/"


def user_detail_url(pk: int) -> str:
    return f"/api/admin/users/{pk}/"


def reset_quota_url(pk: int) -> str:
    return f"/api/admin/users/{pk}/reset-quota/"


@pytest.mark.django_db
class TestAdminUsersListView:
    def test_superadmin_gets_200(self, superadmin_client):
        response = superadmin_client.get(USERS_URL)
        assert response.status_code == 200

    def test_list_returns_all_users(self, superadmin_client, user_marketero, superadmin):
        response = superadmin_client.get(USERS_URL)
        assert response.status_code == 200
        emails = [u["email"] for u in response.data["results"]]
        assert user_marketero.email in emails
        assert superadmin.email in emails

    def test_marketero_gets_403(self, api_client):
        response = api_client.get(USERS_URL)
        assert response.status_code == 403

    def test_cliente_gets_403(self, cliente):
        client = APIClient()
        client.force_authenticate(user=cliente)
        response = client.get(USERS_URL)
        assert response.status_code == 403

    def test_unauthenticated_gets_401(self):
        client = APIClient()
        response = client.get(USERS_URL)
        assert response.status_code == 401


@pytest.mark.django_db
class TestAdminUserDetailView:
    def test_superadmin_suspends_user(self, superadmin_client, user_marketero):
        url = user_detail_url(user_marketero.pk)
        response = superadmin_client.patch(url, {"is_active": False}, format="json")
        assert response.status_code == 200
        assert response.data["success"] is True
        user_marketero.refresh_from_db()
        assert user_marketero.is_active is False

    def test_superadmin_reactivates_user(self, superadmin_client, user_marketero):
        user_marketero.is_active = False
        user_marketero.save()
        url = user_detail_url(user_marketero.pk)
        response = superadmin_client.patch(url, {"is_active": True}, format="json")
        assert response.status_code == 200
        user_marketero.refresh_from_db()
        assert user_marketero.is_active is True

    def test_suspend_increments_token_version(self, superadmin_client, user_marketero):
        old_version = user_marketero.token_version
        url = user_detail_url(user_marketero.pk)
        superadmin_client.patch(url, {"is_active": False}, format="json")
        user_marketero.refresh_from_db()
        assert user_marketero.token_version == old_version + 1

    def test_superadmin_cannot_modify_self(self, superadmin_client, superadmin):
        url = user_detail_url(superadmin.pk)
        response = superadmin_client.patch(url, {"is_active": False}, format="json")
        assert response.status_code == 400

    def test_user_not_found_returns_404(self, superadmin_client):
        url = user_detail_url(99999)
        response = superadmin_client.patch(url, {"is_active": False}, format="json")
        assert response.status_code == 404

    def test_marketero_cannot_patch(self, api_client, user_marketero):
        url = user_detail_url(user_marketero.pk)
        response = api_client.patch(url, {"is_active": False}, format="json")
        assert response.status_code == 403


@pytest.mark.django_db
class TestAdminResetQuotaView:
    def test_reset_quota_sets_100(self, superadmin_client, user_marketero):
        user_marketero.tokens_disponibles = 5
        user_marketero.save()
        url = reset_quota_url(user_marketero.pk)
        response = superadmin_client.patch(url)
        assert response.status_code == 200
        user_marketero.refresh_from_db()
        assert user_marketero.tokens_disponibles == 100

    def test_reset_quota_returns_user(self, superadmin_client, user_marketero):
        url = reset_quota_url(user_marketero.pk)
        response = superadmin_client.patch(url)
        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["data"]["user"]["tokens_disponibles"] == 100

    def test_reset_quota_user_not_found(self, superadmin_client):
        url = reset_quota_url(99999)
        response = superadmin_client.patch(url)
        assert response.status_code == 404

    def test_marketero_cannot_reset_quota(self, api_client, user_marketero):
        url = reset_quota_url(user_marketero.pk)
        response = api_client.patch(url)
        assert response.status_code == 403
