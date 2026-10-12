import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.fixture
def verification(settings, tmp_path):
    name = 'tiktok' + 'A' * 32 + '.txt'
    source = tmp_path / name
    source.write_bytes(b'ownership-test-only')
    settings.TIKTOK_VERIFICATION_FILE = str(source)
    return name, source


def test_exact_verification_file_only(verification):
    name, _ = verification
    with override_settings(ROOT_URLCONF='core.instagram_preview_urls'):
        client = APIClient()
        response = client.get('/api/tiktok/media/' + name)
        assert response.status_code == 200 and response.content == b'ownership-test-only'
        assert response['Content-Type'].startswith('text/plain')
        assert response['Cache-Control'] == 'no-store'
        assert client.get('/api/tiktok/media/tiktok' + 'B' * 32 + '.txt').status_code == 404
        assert client.get('/api/tiktok/media/.env').status_code == 404
        assert client.post('/api/tiktok/media/' + name).status_code == 405


@pytest.mark.parametrize('mode', ['unset', 'missing', 'oversize'])
def test_invalid_file_returns_404(verification, settings, mode):
    name, source = verification
    if mode == 'unset':
        settings.TIKTOK_VERIFICATION_FILE = ''
    elif mode == 'missing':
        settings.TIKTOK_VERIFICATION_FILE = str(source.parent / 'absent.txt')
    else:
        source.write_bytes(b'x' * 4097)
    with override_settings(ROOT_URLCONF='core.instagram_preview_urls'):
        assert APIClient().get('/api/tiktok/media/' + name).status_code == 404


def test_verification_not_exposed_on_main_api(verification):
    name, _ = verification
    assert APIClient().get('/api/tiktok/media/' + name).status_code == 404
