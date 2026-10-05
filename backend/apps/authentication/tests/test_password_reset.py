import re
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db
REQUEST = '/api/auth/password-reset/'
CONFIRM = '/api/auth/password-reset/confirm/'

@pytest.fixture(autouse=True)
def email_backend(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

def request_link(user):
    client = APIClient()
    response = client.post(REQUEST, {'email': user.email}, format='json')
    assert response.status_code == 200
    url = re.search(r'http[^\s]+', mail.outbox[-1].body).group()
    return {k: v[0] for k, v in parse_qs(urlsplit(url).fragment).items()}

def test_unknown_email_does_not_reveal_account(user_marketero):
    client = APIClient()
    known = client.post(REQUEST, {'email': user_marketero.email}, format='json')
    unknown = client.post(REQUEST, {'email': 'unknown@example.com'}, format='json')
    assert known.data == unknown.data
    assert len(mail.outbox) == 1

def test_reset_is_single_use_and_revokes_access_and_refresh(user_marketero):
    refresh = RefreshToken.for_user(user_marketero)
    refresh['token_version'] = user_marketero.token_version
    old_access = str(refresh.access_token)
    data = request_link(user_marketero)
    data['new_password'] = 'NuevaClave2026!'
    client = APIClient()
    assert client.post(CONFIRM, data, format='json').status_code == 200
    assert client.post(CONFIRM, data, format='json').status_code == 400
    user_marketero.refresh_from_db()
    assert user_marketero.check_password(data['new_password'])
    assert client.post('/api/auth/token/refresh/', {'refresh': str(refresh)}, format='json').status_code == 401
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {old_access}')
    assert client.get('/api/auth/me/').status_code == 401

def test_expired_and_tampered_links_are_rejected(user_marketero):
    data = request_link(user_marketero)
    data['new_password'] = 'NuevaClave2026!'
    now = default_token_generator._now()
    with patch.object(default_token_generator, '_now', return_value=now + timedelta(minutes=31)):
        assert APIClient().post(CONFIRM, data, format='json').status_code == 400
    data['token'] += 'tampered'
    assert APIClient().post(CONFIRM, data, format='json').status_code == 400

def test_weak_password_and_invalid_uid(user_marketero):
    data = request_link(user_marketero)
    data['new_password'] = '123'
    assert APIClient().post(CONFIRM, data, format='json').status_code == 400
    data['uid'] = 'bad'
    assert APIClient().post(CONFIRM, data, format='json').status_code == 400

def test_inactive_account_does_not_receive_mail(user_marketero):
    user_marketero.is_active = False
    user_marketero.save()
    assert APIClient().post(REQUEST, {'email': user_marketero.email}, format='json').status_code == 200
    assert len(mail.outbox) == 0

def test_recovery_is_rate_limited():
    client = APIClient()
    for _ in range(5):
        assert client.post(REQUEST, {'email': 'unknown@example.com'}, format='json').status_code == 200
    assert client.post(REQUEST, {'email': 'unknown@example.com'}, format='json').status_code == 429
