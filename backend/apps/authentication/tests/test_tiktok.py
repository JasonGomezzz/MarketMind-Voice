from datetime import timedelta
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.fernet import Fernet
from django.utils import timezone
from rest_framework.test import APIClient

from apps.authentication.models import TikTokAccount, TikTokAuthorization, User
from apps.authentication.tiktok import access_token_for, exchange, token_request

pytestmark = pytest.mark.django_db


@pytest.fixture
def tiktok_settings(settings):
    settings.TIKTOK_CLIENT_KEY = 'client-key'
    settings.TIKTOK_CLIENT_SECRET = 'client-secret'
    settings.TIKTOK_REDIRECT_URI = 'https://demo.example/api/auth/tiktok/callback/'
    settings.FRONTEND_BASE_URL = 'http://localhost:5173'
    settings.SOCIAL_TOKEN_ENCRYPTION_KEY = Fernet.generate_key().decode()
    return settings


def tokens():
    return {'open_id': 'open-user', 'access_token': 'access-secret', 'refresh_token': 'refresh-secret',
            'expires_in': 86400, 'refresh_expires_in': 31536000,
            'scope': 'user.info.basic,video.upload', 'token_type': 'Bearer'}


def connect(api_client):
    response = api_client.post('/api/auth/tiktok/connect/', HTTP_ORIGIN='http://localhost:5173')
    assert response.status_code == 200
    return parse_qs(urlsplit(response.data['data']['authorization_url']).query)['state'][0]


def test_connect_config_origin_and_state(api_client, tiktok_settings):
    state = connect(api_client)
    ticket = TikTokAuthorization.objects.get()
    assert ticket.state_hash != state
    assert ticket.return_origin == 'http://localhost:5173'
    assert api_client.post('/api/auth/tiktok/connect/', HTTP_ORIGIN='https://evil.example').status_code == 403
    tiktok_settings.TIKTOK_REDIRECT_URI = 'http://localhost/settings'
    assert api_client.post('/api/auth/tiktok/connect/').status_code == 503


@patch('apps.authentication.tiktok.exchange')
def test_relay_does_not_exchange_and_completion_is_owner_bound(mock_exchange, api_client, tiktok_settings, user_marketero):
    mock_exchange.return_value = (tokens(), 'Toy Lokazo')
    state = connect(api_client)
    callback = APIClient().get('/api/auth/tiktok/callback/', {'state': state, 'code': 'code-once'})
    assert callback.status_code == 302
    assert parse_qs(urlsplit(callback['Location']).fragment) == {'provider': ['tiktok'], 'state': [state], 'code': ['code-once']}
    assert callback['Cache-Control'] == 'no-store'
    assert callback['Referrer-Policy'] == 'no-referrer'
    mock_exchange.assert_not_called()
    other = User.objects.create_user(email='other-tiktok@test.com', password='Test1234!', nombre='Other', rol='marketero')
    foreign = APIClient()
    foreign.force_authenticate(other)
    payload = {'state': state, 'code': 'code-once'}
    assert foreign.post('/api/auth/tiktok/complete/', payload).status_code == 400
    assert api_client.post('/api/auth/tiktok/complete/', payload, HTTP_ORIGIN='https://evil.example').status_code == 400
    assert not TikTokAuthorization.objects.get().used
    assert api_client.post('/api/auth/tiktok/complete/', payload).status_code == 200
    mock_exchange.assert_called_once_with('code-once')
    assert TikTokAuthorization.objects.get().used
    account = TikTokAccount.objects.get(owner=user_marketero)
    assert 'access-secret' not in account.encrypted_access_token
    assert 'refresh-secret' not in account.encrypted_refresh_token
    listed = api_client.get('/api/auth/tiktok/accounts/').data['data']['accounts'][0]
    assert set(listed) == {'id', 'display_name', 'expired', 'can_refresh'}
    assert foreign.get('/api/auth/tiktok/accounts/').data['data']['accounts'] == []
    assert foreign.delete(f'/api/auth/tiktok/accounts/{account.pk}/').status_code == 404
    assert api_client.post('/api/auth/tiktok/complete/', payload).status_code == 400
    assert api_client.delete(f'/api/auth/tiktok/accounts/{account.pk}/').status_code == 200
    assert not TikTokAccount.objects.exists()
    assert not TikTokAuthorization.objects.exists()


@pytest.mark.parametrize('change', ['expired', 'suspended', 'token_version', 'role'])
@patch('apps.authentication.tiktok.exchange')
def test_invalid_ticket_cannot_connect(mock_exchange, change, api_client, tiktok_settings, user_marketero):
    state = connect(api_client)
    if change == 'expired':
        TikTokAuthorization.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    else:
        updates = {'suspended': {'is_active': False}, 'token_version': {'token_version': 99}, 'role': {'rol': 'cliente'}}
        User.objects.filter(pk=user_marketero.pk).update(**updates[change])
    assert APIClient().get('/api/auth/tiktok/callback/', {'state': state, 'code': 'private'}).status_code == 400
    mock_exchange.assert_not_called()


@patch('apps.authentication.tiktok.exchange', side_effect=ValueError('provider-private-details'))
def test_failure_consumes_ticket_without_leaking_error(mock_exchange, api_client, tiktok_settings):
    state = connect(api_client)
    response = api_client.post('/api/auth/tiktok/complete/', {'state': state, 'code': 'bad'})
    assert response.status_code == 400
    assert 'provider-private-details' not in str(response.data)
    assert TikTokAuthorization.objects.get().used
    assert not TikTokAccount.objects.exists()


def test_denied_callback_is_sanitized(api_client, tiktok_settings):
    state = connect(api_client)
    response = APIClient().get('/api/auth/tiktok/callback/', {'state': state, 'error': 'provider-private-details'})
    values = parse_qs(urlsplit(response['Location']).fragment)
    assert values['error'] == ['denied']
    assert 'provider-private-details' not in response['Location']


@patch('apps.authentication.tiktok.requests.post')
@pytest.mark.parametrize('field,value', [('scope', 'user.info.basic'), ('expires_in', True), ('open_id', ''), ('refresh_token', ''), ('refresh_expires_in', -1), ('token_type', 'other')])
def test_invalid_provider_tokens_rejected(mock_post, field, value, tiktok_settings):
    mock_post.return_value = Mock(status_code=200)
    mock_post.return_value.json.return_value = {**tokens(), field: value}
    with pytest.raises(ValueError):
        token_request({'grant_type': 'authorization_code', 'code': 'c'})


@patch('apps.authentication.tiktok.requests.get')
@patch('apps.authentication.tiktok.requests.post')
def test_profile_identity_must_match_token(mock_post, mock_get, tiktok_settings):
    mock_post.return_value = Mock(status_code=200)
    mock_post.return_value.json.return_value = tokens()
    mock_get.return_value = Mock(status_code=200)
    mock_get.return_value.json.return_value = {'error': {'code': 'ok'}, 'data': {'user': {'open_id': 'someone-else', 'display_name': 'Other'}}}
    with pytest.raises(ValueError):
        exchange('code')
    assert mock_post.call_args.kwargs['allow_redirects'] is False
    assert mock_get.call_args.kwargs['allow_redirects'] is False


@patch('apps.authentication.tiktok.token_request')
@patch('apps.authentication.tiktok.exchange')
def test_refresh_rotation_and_expiry(mock_exchange, mock_request, api_client, tiktok_settings):
    mock_exchange.return_value = (tokens(), 'Toy')
    state = connect(api_client)
    assert api_client.post('/api/auth/tiktok/complete/', {'state': state, 'code': 'c'}).status_code == 200
    account = TikTokAccount.objects.get()
    assert access_token_for(account) == 'access-secret'
    mock_request.assert_not_called()
    TikTokAccount.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    mock_request.return_value = {**tokens(), 'access_token': 'renewed-access', 'refresh_token': 'renewed-refresh'}
    assert access_token_for(account) == 'renewed-access'
    account.refresh_from_db()
    assert 'renewed-refresh' not in account.encrypted_refresh_token
    TikTokAccount.objects.update(expires_at=timezone.now() - timedelta(seconds=1), refresh_expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(ValueError):
        access_token_for(account)


@pytest.mark.parametrize('endpoint,method', [
    ('accounts/', 'get'), ('connect/', 'post'), ('complete/', 'post'), ('accounts/1/', 'delete')])
def test_tiktok_requires_authenticated_marketer(endpoint, method, tiktok_settings, cliente):
    client = APIClient()
    assert getattr(client, method)('/api/auth/tiktok/' + endpoint).status_code in (401, 403)
    client.force_authenticate(cliente)
    assert getattr(client, method)('/api/auth/tiktok/' + endpoint).status_code == 403


def test_tiktok_preview_has_callback_but_no_campaign_endpoints(settings):
    settings.ROOT_URLCONF = 'core.instagram_preview_urls'
    client = APIClient()
    assert client.get('/api/auth/tiktok/callback/', {'state': 'invalid', 'code': 'c'}).status_code == 400
    assert client.get('/api/campaigns/').status_code == 404


def test_tiktok_callback_logs_are_redacted():
    import logging
    from core.logging_filters import RedactOAuthQueryFilter
    record = logging.LogRecord('django.server', logging.INFO, '', 0, '%s',
        ('GET /api/auth/tiktok/callback/?code=private&state=private HTTP/1.1',), None)
    assert RedactOAuthQueryFilter().filter(record)
    assert 'private' not in record.getMessage()
    assert '[redacted]' in record.getMessage()
