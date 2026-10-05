import pytest
from rest_framework.test import APIClient
from apps.authentication.models import CreditRequest

pytestmark = pytest.mark.django_db
OWN = '/api/auth/credit-requests/'
ADMIN = '/api/admin/credit-requests/'


def test_request_is_persisted_and_duplicate_is_idempotent(api_client, user_marketero):
    assert api_client.post(OWN).status_code == 201
    assert api_client.post(OWN).status_code == 200
    assert CreditRequest.objects.filter(requester=user_marketero).count() == 1
    assert api_client.get(OWN).data['count'] == 1
    user_marketero.refresh_from_db()
    assert user_marketero.tokens_disponibles == 10


def test_approve_adds_credits_once_and_audits(api_client, superadmin_client, user_marketero, superadmin):
    pk = api_client.post(OWN).data['data']['id']
    url = f'{ADMIN}{pk}/'
    assert superadmin_client.patch(url, {'status': 'approved', 'credits': 50}, format='json').status_code == 200
    assert superadmin_client.patch(url, {'status': 'approved', 'credits': 50}, format='json').status_code == 409
    user_marketero.refresh_from_db()
    assert user_marketero.tokens_disponibles == 60
    item = CreditRequest.objects.get(pk=pk)
    assert item.resolved_by == superadmin
    assert item.resolved_at is not None
    assert item.credits_granted == 50
    assert api_client.post(OWN).status_code == 201


def test_reject_preserves_balance(api_client, superadmin_client, user_marketero):
    pk = api_client.post(OWN).data['data']['id']
    assert superadmin_client.patch(f'{ADMIN}{pk}/', {'status': 'rejected'}, format='json').status_code == 200
    user_marketero.refresh_from_db()
    assert user_marketero.tokens_disponibles == 10
    assert CreditRequest.objects.get(pk=pk).credits_granted == 0


@pytest.mark.parametrize('payload', [
    {'status': 'approved'}, {'status': 'approved', 'credits': 0},
    {'status': 'approved', 'credits': 10001}, {'status': 'approved', 'credits': 1.5},
    {'status': 'pending'}, {'status': 'rejected', 'credits': 10},
])
def test_invalid_decision_does_not_change_request(api_client, superadmin_client, payload):
    pk = api_client.post(OWN).data['data']['id']
    assert superadmin_client.patch(f'{ADMIN}{pk}/', payload, format='json').status_code == 400
    assert CreditRequest.objects.get(pk=pk).status == 'pending'


def test_permissions_and_ownership(api_client, superadmin_client, cliente):
    pk = api_client.post(OWN).data['data']['id']
    assert api_client.get(ADMIN).status_code == 403
    assert api_client.patch(f'{ADMIN}{pk}/', {'status': 'approved', 'credits': 100}, format='json').status_code == 403
    assert superadmin_client.get(OWN).data['count'] == 0
    assert superadmin_client.get(ADMIN).data['count'] == 1
    client = APIClient()
    assert client.post(OWN).status_code == 401
    client.force_authenticate(user=cliente)
    assert client.post(OWN).status_code == 403
    assert client.get(OWN).status_code == 403


def test_suspended_user_cannot_receive_credits(api_client, superadmin_client, user_marketero):
    pk = api_client.post(OWN).data['data']['id']
    user_marketero.is_active = False
    user_marketero.save(update_fields=['is_active'])
    assert superadmin_client.patch(f'{ADMIN}{pk}/', {'status': 'approved', 'credits': 100}, format='json').status_code == 400
    assert CreditRequest.objects.get(pk=pk).status == 'pending'
