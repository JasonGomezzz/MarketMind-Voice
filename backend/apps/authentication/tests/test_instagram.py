from datetime import timedelta
from unittest.mock import patch, Mock
from urllib.parse import parse_qs, urlsplit

import pytest
import requests
from cryptography.fernet import Fernet
from django.utils import timezone
from rest_framework.test import APIClient

from apps.authentication.models import InstagramAccount, InstagramAuthorization, User
from apps.authentication.instagram import exchange_code, InstagramError

pytestmark = pytest.mark.django_db


@pytest.fixture
def instagram_settings(settings):
    settings.INSTAGRAM_APP_ID = 'test-app'
    settings.INSTAGRAM_APP_SECRET = 'test-secret'
    settings.INSTAGRAM_REDIRECT_URI = 'https://demo.example/settings'
    settings.FRONTEND_BASE_URL = 'https://demo.example'
    settings.INSTAGRAM_FRONTEND_ORIGIN = ''
    settings.SOCIAL_TOKEN_ENCRYPTION_KEY = Fernet.generate_key().decode()
    return settings


def begin(client):
    response = client.post('/api/auth/instagram/connect/')
    assert response.status_code == 200
    url = response.data['data']['authorization_url']
    return parse_qs(urlsplit(url).query)['state'][0]


def complete(client, state):
    return client.post('/api/auth/instagram/complete/', {'state': state, 'code': 'test-code'}, format='json')


def test_connection_disabled_without_configuration(api_client):
    assert api_client.get('/api/auth/instagram/accounts/').data['data']['configured'] is False
    assert api_client.post('/api/auth/instagram/connect/').status_code == 503


def test_https_same_origin_required(api_client, instagram_settings):
    instagram_settings.INSTAGRAM_REDIRECT_URI = 'https://other.example/settings'
    assert api_client.post('/api/auth/instagram/connect/').status_code == 503
    instagram_settings.INSTAGRAM_REDIRECT_URI = 'http://localhost:5173/settings'
    assert api_client.post('/api/auth/instagram/connect/').status_code == 503


def test_wrong_browser_origin_cannot_start_connection(api_client, instagram_settings):
    assert api_client.post('/api/auth/instagram/connect/', HTTP_ORIGIN='http://localhost:5173').status_code == 403
    assert api_client.post('/api/auth/instagram/connect/', HTTP_ORIGIN='https://demo.example').status_code == 200


def test_client_and_anonymous_cannot_manage_connections(cliente, instagram_settings):
    client = APIClient()
    assert client.get('/api/auth/instagram/accounts/').status_code == 401
    client.force_authenticate(user=cliente)
    assert client.post('/api/auth/instagram/connect/').status_code == 403
    assert client.post('/api/auth/instagram/complete/').status_code == 403


@patch('apps.authentication.instagram.exchange_code')
def test_connect_encrypts_token_allows_multiple_accounts_and_no_replay(exchange, api_client, instagram_settings, user_marketero):
    exchange.return_value = ({'user_id': 'ig-one', 'username': 'first'}, 'private-token', 3600)
    state = begin(api_client)
    response = complete(api_client, state)
    assert response.status_code == 200
    assert 'private-token' not in str(response.data)
    account = InstagramAccount.objects.get(owner=user_marketero)
    assert account.encrypted_token != 'private-token'
    assert Fernet(instagram_settings.SOCIAL_TOKEN_ENCRYPTION_KEY.encode()).decrypt(account.encrypted_token.encode()) == b'private-token'
    assert complete(api_client, state).status_code == 400
    assert exchange.call_count == 1
    exchange.return_value = ({'user_id': 'ig-two', 'username': 'second'}, 'another-token', 3600)
    assert complete(api_client, begin(api_client)).status_code == 200
    assert InstagramAccount.objects.filter(owner=user_marketero).count() == 2
    listed = api_client.get('/api/auth/instagram/accounts/').data['data']['accounts']
    assert len(listed) == 2
    assert all('encrypted_token' not in row for row in listed)


@patch('apps.authentication.instagram.exchange_code')
def test_cross_user_ticket_list_and_disconnect_are_isolated(exchange, api_client, instagram_settings, user_marketero):
    state = begin(api_client)
    other = User.objects.create_user(email='other@example.com', password='Test1234!', nombre='Other', rol='marketero')
    client = APIClient()
    client.force_authenticate(user=other)
    assert complete(client, state).status_code == 400
    exchange.assert_not_called()
    account = InstagramAccount.objects.create(owner=user_marketero, instagram_user_id='123', username='mine', encrypted_token='opaque', expires_at=timezone.now() + timedelta(days=1))
    assert client.get('/api/auth/instagram/accounts/').data['data']['accounts'] == []
    assert client.delete(f'/api/auth/instagram/accounts/{account.pk}/').status_code == 404
    assert api_client.delete(f'/api/auth/instagram/accounts/{account.pk}/').status_code == 200


@patch('apps.authentication.instagram.exchange_code')
def test_expired_and_revoked_tickets_block_exchange(exchange, api_client, instagram_settings, user_marketero):
    state = begin(api_client)
    InstagramAuthorization.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    assert complete(api_client, state).status_code == 400
    state = begin(api_client)
    user_marketero.token_version += 1
    user_marketero.save(update_fields=['token_version'])
    assert complete(api_client, state).status_code == 400
    exchange.assert_not_called()


@patch('apps.authentication.instagram.exchange_code', side_effect=InstagramError())
def test_failed_exchange_returns_safe_message_and_requires_new_ticket(exchange, api_client, instagram_settings):
    state = begin(api_client)
    assert complete(api_client, state).status_code == 502
    assert complete(api_client, state).status_code == 400
    assert complete(api_client, None).status_code == 400


@patch('apps.authentication.instagram.requests.post')
@patch('apps.authentication.instagram.requests.get')
def test_exchange_http_contract(get, post, instagram_settings):
    post.return_value = Mock(json=lambda: {'data': [{'access_token': 'short', 'user_id': '123', 'permissions': ['instagram_business_basic', 'instagram_business_content_publish']}]})
    get.side_effect = [Mock(json=lambda: {'access_token': 'long', 'expires_in': 3600}), Mock(json=lambda: {'user_id': '123', 'username': 'demo'})]
    assert exchange_code('code') == ({'user_id': '123', 'username': 'demo'}, 'long', 3600)
    assert post.call_args.kwargs['data']['redirect_uri'] == instagram_settings.INSTAGRAM_REDIRECT_URI
    assert get.call_args.kwargs['headers'] == {'Authorization': 'Bearer long'}


@patch('apps.authentication.instagram.requests.post')
@patch('apps.authentication.instagram.requests.get')
def test_exchange_rejects_profile_identity_mismatch(get, post, instagram_settings):
    post.return_value = Mock(json=lambda: {'access_token': 'short', 'user_id': '123', 'permissions': 'instagram_business_basic,instagram_business_content_publish'})
    get.side_effect = [Mock(json=lambda: {'access_token': 'long', 'expires_in': 3600}), Mock(json=lambda: {'user_id': 'other', 'username': 'demo'})]
    with pytest.raises(InstagramError) as error:
        exchange_code('code')
    assert error.value.stage == 'identity'


@patch('apps.authentication.instagram.requests.post')
def test_upstream_failure_and_missing_publish_permission_are_sanitized(post, instagram_settings):
    post.side_effect = requests.RequestException('private-token-url')
    with pytest.raises(InstagramError) as error:
        exchange_code('code')
    assert 'private-token-url' not in str(error.value)
    assert error.value.stage == 'code_exchange'
    post.side_effect = None
    post.return_value = Mock(json=lambda: {'access_token': 'short', 'permissions': ['instagram_business_basic']})
    with pytest.raises(InstagramError) as error:
        exchange_code('code')
    assert error.value.stage == 'permissions'
