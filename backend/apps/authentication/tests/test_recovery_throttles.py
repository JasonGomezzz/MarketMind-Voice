from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from types import SimpleNamespace

import pytest
from django.core import mail
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.authentication.recovery_throttles import RecoveryRequestThrottle, recovery_key

pytestmark = pytest.mark.django_db
REQUEST = '/api/auth/password-reset/'
CONFIRM = '/api/auth/password-reset/confirm/'
CLOCK = 'apps.authentication.recovery_throttles.time.time'


def send(email, ip='127.0.0.1', **headers):
    return APIClient().post(REQUEST, {'email': email}, format='json', REMOTE_ADDR=ip, **headers)


def test_email_quota_survives_ip_changes_and_resets_next_hour():
    for index in range(5):
        with patch(CLOCK, return_value=3600 + index * 61):
            assert send('unknown@example.com', f'10.0.0.{index}').status_code == 200
    with patch(CLOCK, return_value=4000):
        response = send('UNKNOWN@example.com', '10.0.0.99')
        assert response.status_code == 429
        assert response.data['data']['retry_after'] == 3200
        assert send('another@example.com', '10.0.0.99').status_code == 200
    with patch(CLOCK, return_value=7200):
        assert send('unknown@example.com').status_code == 200


def test_ip_quota_counts_different_emails_and_ignores_spoofed_headers():
    for index in range(20):
        assert send(f'unknown{index}@example.com').status_code == 200
    assert send('extra@example.com', HTTP_X_FORWARDED_FOR='8.8.8.8').status_code == 429
    assert send('extra@example.com', ip='10.0.0.2').status_code == 200


def test_cooldown_expires_without_resending_before_expiry():
    with patch(CLOCK, return_value=3600):
        assert send('unknown@example.com').status_code == 200
    with patch(CLOCK, return_value=3630):
        response = send('unknown@example.com')
        assert response.status_code == 429
        assert response.data['data']['retry_after'] == 30
    with patch(CLOCK, return_value=3661):
        assert send('unknown@example.com').status_code == 200


def test_known_and_unknown_accounts_have_identical_throttle_policy(user_marketero, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    assert send(user_marketero.email).data == send('unknown@example.com').data
    assert send(user_marketero.email).data == send('unknown@example.com').data
    assert len(mail.outbox) == 1


def test_request_quota_does_not_block_confirmation_and_confirm_is_limited():
    for index in range(20):
        assert send(f'unknown{index}@example.com').status_code == 200
    client = APIClient()
    for _ in range(20):
        response = client.post(CONFIRM, {'uid': 'bad', 'token': 'bad', 'new_password': 'NuevaClave2026!'}, format='json')
        assert response.status_code == 400
    assert client.post(CONFIRM, {}, format='json').status_code == 429


def test_cache_outage_fails_closed_without_sending(user_marketero):
    with patch('apps.authentication.recovery_throttles.cache.add', side_effect=ConnectionError), patch('apps.authentication.password_reset.send_mail') as send_mail:
        assert send(user_marketero.email).status_code == 503
        send_mail.assert_not_called()


def test_keys_do_not_contain_personal_identifiers():
    key = recovery_key('email', 'unknown@example.com')
    assert 'unknown' not in key
    assert '@' not in key
    assert key != recovery_key('email', 'another@example.com')


def test_atomic_hourly_counter_under_concurrent_attempts():
    def attempt(_):
        return RecoveryRequestThrottle().hourly_limit('test:ip', '127.0.0.1', 20, 3600)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(50)))
    assert sum(results) == 20


def test_cooldown_is_reserved_atomically():
    def attempt(_):
        return cache.add(recovery_key('email:cooldown', 'unknown@example.com'), 3660, timeout=60)
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(50))) == 1


def test_parallel_requests_only_reserve_one_send():
    request = SimpleNamespace(method='POST', data={'email': 'unknown@example.com'}, META={'REMOTE_ADDR': '127.0.0.1'})
    with patch(CLOCK, return_value=3600), ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: RecoveryRequestThrottle().allow_request(request, None), range(50)))
    assert sum(results) == 1
