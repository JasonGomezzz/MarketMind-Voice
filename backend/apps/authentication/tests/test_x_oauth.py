from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.fernet import Fernet
from rest_framework.test import APIClient

from apps.authentication.models import XAccount, XAuthorization, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def x_settings(settings):
    settings.X_CLIENT_ID = 'client-id'
    settings.X_CLIENT_SECRET = 'client-secret'
    settings.X_REDIRECT_URI = 'https://demo.example/api/auth/x/callback/'
    settings.FRONTEND_BASE_URL = 'http://localhost:5173'
    settings.SOCIAL_TOKEN_ENCRYPTION_KEY = Fernet.generate_key().decode()
    return settings


def test_connect_pkce_state_origin_and_config(api_client, x_settings):
    response = api_client.post('/api/auth/x/connect/', HTTP_ORIGIN='http://localhost:5173')
    assert response.status_code == 200
    url = urlsplit(response.data['data']['authorization_url'])
    values = parse_qs(url.query)
    assert url.scheme == 'https' and url.netloc == 'x.com'
    assert values['code_challenge_method'] == ['S256']
    assert values['redirect_uri'] == [x_settings.X_REDIRECT_URI]
    assert values['scope'] == ['tweet.read users.read tweet.write media.write offline.access']
    assert 'client-secret' not in url.geturl()
    assert XAuthorization.objects.get().state_hash != values['state'][0]
    assert api_client.post('/api/auth/x/connect/', HTTP_ORIGIN='https://evil.example').status_code == 403
    x_settings.X_REDIRECT_URI = 'http://localhost:5173/settings'
    assert api_client.post('/api/auth/x/connect/').status_code == 503


@patch('apps.authentication.x_oauth.exchange', return_value=('123', 'ToyLokazo', 'access', 'refresh', 7200))
def test_callback_stores_encrypted_token_for_owner_once(exchange, api_client, x_settings, user_marketero):
    url = api_client.post('/api/auth/x/connect/').data['data']['authorization_url']
    state = parse_qs(urlsplit(url).query)['state'][0]
    callback = APIClient().get('/api/auth/x/callback/', {'state': state, 'code': 'single-use-code'})
    assert callback.status_code == 302
    assert parse_qs(urlsplit(callback['Location']).fragment) == {
        'provider': ['x'], 'state': [state], 'result': ['connected']}
    assert callback['Cache-Control'] == 'no-store'
    assert callback['Referrer-Policy'] == 'no-referrer'
    assert XAuthorization.objects.get().used
    assert exchange.call_count == 1
    account = XAccount.objects.get(owner=user_marketero)
    assert account.username == 'ToyLokazo'
    assert 'access' not in account.encrypted_access_token
    assert 'refresh' not in account.encrypted_refresh_token
    assert APIClient().get('/api/auth/x/callback/', {'state': state, 'code': 'again'}).status_code == 400
    other = User.objects.create_user(email='other-x@test.com', password='Test1234!', nombre='Other', rol='marketero')
    client = APIClient()
    client.force_authenticate(other)
    assert client.get('/api/auth/x/accounts/').data['data']['accounts'] == []
    assert client.delete(f'/api/auth/x/accounts/{account.pk}/').status_code == 404


@patch('apps.authentication.x_oauth.exchange', return_value=None)
def test_failed_exchange_does_not_connect(exchange, api_client, x_settings):
    url = api_client.post('/api/auth/x/connect/').data['data']['authorization_url']
    state = parse_qs(urlsplit(url).query)['state'][0]
    callback = APIClient().get('/api/auth/x/callback/', {'state': state, 'code': 'bad'})
    assert parse_qs(urlsplit(callback['Location']).fragment)['result'] == ['error']
    assert not XAccount.objects.exists()
