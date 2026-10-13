import base64
from datetime import timedelta
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
import requests
from cryptography.fernet import Fernet
from django.test import override_settings
from django.utils import timezone
from PIL import Image

from apps.authentication.models import TikTokAccount
from apps.campaigns.models import TikTokUpload
from apps.campaigns.tiktok_publication import media_ready, send_upload, utf16_length, tiktok_jpeg

pytestmark = pytest.mark.django_db


@pytest.fixture
def tt_setup(settings, campaign, user_marketero):
    key = Fernet.generate_key()
    settings.SOCIAL_TOKEN_ENCRYPTION_KEY = key.decode()
    settings.TIKTOK_CLIENT_KEY = 'test-key'
    settings.TIKTOK_CLIENT_SECRET = 'test-secret'
    settings.TIKTOK_REDIRECT_URI = 'https://test.example/api/auth/tiktok/callback/'
    settings.TIKTOK_MEDIA_BASE_URL = 'https://test.example/api/tiktok/media/'
    settings.TIKTOK_MEDIA_VERIFIED = True
    image = BytesIO()
    Image.new('RGB', (400, 400), 'blue').save(image, 'PNG')
    campaign.imagen_b64 = base64.b64encode(image.getvalue()).decode()
    campaign.estado = 'aprobado'
    campaign.plataformas = ['tiktok']
    campaign.textos_por_plataforma = {'tiktok': 'Texto aprobado de café'}
    campaign.save()
    account = TikTokAccount.objects.create(owner=user_marketero, open_id='test-open-id', display_name='Test',
        encrypted_access_token=Fernet(key).encrypt(b'test-token').decode(),
        encrypted_refresh_token=Fernet(key).encrypt(b'test-refresh').decode(),
        expires_at=timezone.now() + timedelta(days=1), refresh_expires_at=timezone.now() + timedelta(days=30),
        scopes=['user.info.basic', 'video.upload'])
    return campaign, account


def send(client, setup, **extra):
    campaign, account = setup
    return client.post(f'/api/campaigns/{campaign.pk}/send-tiktok/',
        {'account_id': account.pk, 'version': campaign.version, 'confirm': True, **extra}, format='json')


def test_status_backfills_confirmed_numeric_public_ids_without_resending(api_client, tt_setup):
    campaign, account = tt_setup
    upload = TikTokUpload.objects.create(campaign=campaign, account=account, open_id=account.open_id,
        display_name='Test', campaign_version=campaign.version, caption='test', image_jpeg='',
        image_expires_at=timezone.now(), status='published', publish_id='p')
    with patch('apps.campaigns.tiktok_publication.provider_request', return_value={
            'status': 'PUBLISH_COMPLETE', 'publicaly_available_post_id': [123, '456']}) as query:
        response = api_client.post(f'/api/campaigns/{campaign.pk}/tiktok-status/', {'account_id': account.pk}, format='json')
    assert response.status_code == 200
    upload.refresh_from_db()
    assert upload.public_post_ids == ['123', '456'] and upload.status == 'published'
    assert query.call_args.args[0] == 'status/fetch/'


@patch('apps.campaigns.tiktok_publication.send_upload', return_value='publish-1')
def test_confirmed_approved_snapshot_and_duplicate_protection(mock_send, api_client, tt_setup):
    response = send(api_client, tt_setup, caption='not approved')
    assert response.status_code == 202 and response.data['data']['status'] == 'processing'
    upload = TikTokUpload.objects.get()
    assert upload.caption == 'Texto aprobado de café'
    assert send(api_client, tt_setup).data['data']['status'] == 'processing'
    assert mock_send.call_count == 1
    assert 'test-token' not in str(response.data)


@pytest.mark.parametrize('extra,status', [({'confirm': False}, 400), ({'version': False}, 409),
                                        ({'version': 999}, 409), ({'account_id': True}, 400)])
@patch('apps.campaigns.tiktok_publication.send_upload')
def test_invalid_confirmation_and_version(mock_send, api_client, tt_setup, extra, status):
    assert send(api_client, tt_setup, **extra).status_code == status
    mock_send.assert_not_called()


@patch('apps.campaigns.tiktok_publication.send_upload')
def test_unverified_media_blocked(mock_send, api_client, tt_setup, settings):
    settings.TIKTOK_MEDIA_VERIFIED = False
    assert send(api_client, tt_setup).status_code == 503
    assert not TikTokUpload.objects.exists()
    mock_send.assert_not_called()


@pytest.mark.parametrize('field,value', [('estado', 'generado'), ('plataformas', ['facebook']),
    ('imagen_b64', 'bad'), ('textos_por_plataforma', {'tiktok': '😀' * 2001})])
@patch('apps.campaigns.tiktok_publication.send_upload')
def test_invalid_content_blocked(mock_send, api_client, tt_setup, field, value):
    campaign, _ = tt_setup
    setattr(campaign, field, value)
    campaign.save()
    assert send(api_client, tt_setup).status_code == 400
    mock_send.assert_not_called()


@patch('apps.campaigns.tiktok_publication.send_upload', side_effect=requests.Timeout('secret'))
def test_ambiguous_send_never_retried(mock_send, api_client, tt_setup):
    assert send(api_client, tt_setup).data['data']['status'] == 'uncertain'
    assert send(api_client, tt_setup).data['data']['status'] == 'uncertain'
    assert mock_send.call_count == 1


@patch('apps.campaigns.tiktok_publication.send_upload', return_value='publish-1')
def test_cross_owner_blocked(mock_send, api_client, tt_setup, cliente):
    campaign, account = tt_setup
    account.owner = cliente
    account.save()
    assert send(api_client, tt_setup).status_code == 404
    mock_send.assert_not_called()


@patch('apps.campaigns.tiktok_publication.send_upload', return_value='publish-1')
def test_inbox_not_published_and_status_throttled(mock_send, api_client, tt_setup):
    send(api_client, tt_setup)
    campaign, account = tt_setup
    url = f'/api/campaigns/{campaign.pk}/tiktok-status/'
    with patch('apps.campaigns.tiktok_publication.provider_request', return_value={'status': 'SEND_TO_USER_INBOX'}) as fetch:
        assert api_client.post(url, {'account_id': account.pk}, format='json').data['data']['status'] == 'inbox'
        api_client.post(url, {'account_id': account.pk}, format='json')
        assert fetch.call_count == 1
    TikTokUpload.objects.update(checked_at=timezone.now() - timedelta(minutes=1))
    with patch('apps.campaigns.tiktok_publication.provider_request', return_value={'status': 'PUBLISH_COMPLETE'}):
        assert api_client.post(url, {'account_id': account.pk}, format='json').data['data']['status'] == 'published'
    assert mock_send.call_count == 1


@patch('apps.campaigns.tiktok_publication.send_upload', return_value='publish-1')
def test_failed_query_keeps_last_state(mock_send, api_client, tt_setup):
    send(api_client, tt_setup)
    campaign, account = tt_setup
    with patch('apps.campaigns.tiktok_publication.provider_request', side_effect=ValueError('secret')):
        response = api_client.post(f'/api/campaigns/{campaign.pk}/tiktok-status/', {'account_id': account.pk}, format='json')
        assert response.status_code == 503 and 'secret' not in str(response.data)
    assert TikTokUpload.objects.get().status == 'processing'


@patch('apps.campaigns.tiktok_publication.send_upload', return_value='publish-1')
def test_bridge_image_ticket_expires(mock_send, api_client, tt_setup):
    send(api_client, tt_setup)
    upload = TikTokUpload.objects.get()
    with override_settings(ROOT_URLCONF='core.instagram_preview_urls'):
        path = f'/api/tiktok/media/{upload.image_ticket}/'
        response = api_client.get(path)
        assert response.status_code == 200 and response['Content-Type'] == 'image/jpeg'
        assert response['Cache-Control'] == 'no-store'
        TikTokUpload.objects.update(image_expires_at=timezone.now() - timedelta(seconds=1))
        assert api_client.get(path).status_code == 404
        assert api_client.post(f'/api/campaigns/{upload.campaign_id}/send-tiktok/').status_code == 404


@patch('apps.campaigns.tiktok_publication.requests.post')
def test_payload_uses_media_upload_and_ai_label(post, api_client, tt_setup):
    post.return_value = Mock(status_code=200, json=lambda: {'error': {'code': 'ok'}, 'data': {'publish_id': 'id'}})
    assert send(api_client, tt_setup).status_code == 202
    payload = post.call_args.kwargs['json']
    assert payload['post_mode'] == 'MEDIA_UPLOAD' and payload['media_type'] == 'PHOTO' and payload['is_aigc'] is True
    assert payload['post_info']['description'] == 'Texto aprobado de café'
    assert post.call_args.kwargs['allow_redirects'] is False
    assert payload['source_info']['photo_images'][0].startswith('https://test.example/api/tiktok/media/')


def test_media_config_and_utf16(settings):
    assert utf16_length('😀') == 2
    settings.TIKTOK_MEDIA_VERIFIED = True
    for url in ['http://test.example/api/tiktok/media/', 'https://test.example/other/',
                'https://user:pass@test.example/api/tiktok/media/']:
        settings.TIKTOK_MEDIA_BASE_URL = url
        assert media_ready() is False


def test_tiktok_image_dimensions():
    source = BytesIO()
    Image.new('RGB', (2000, 1400), 'blue').save(source, 'PNG')
    converted = tiktok_jpeg(base64.b64encode(source.getvalue()).decode())
    with Image.open(BytesIO(base64.b64decode(converted))) as image:
        assert image.width <= 1080 and image.height <= 1080 and image.format == 'JPEG'
