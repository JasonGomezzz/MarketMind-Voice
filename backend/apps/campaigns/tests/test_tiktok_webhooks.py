import hashlib
import hmac
import json
import time
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.campaigns.models import TikTokUpload, TikTokWebhookReceipt
from apps.campaigns.serializers import CampaignSerializer

pytestmark = pytest.mark.django_db
URL = '/api/tiktok/webhook/'


@pytest.fixture
def upload(settings, campaign):
    settings.TIKTOK_CLIENT_KEY = 'test-key'
    settings.TIKTOK_CLIENT_SECRET = 'test-secret'
    return TikTokUpload.objects.create(campaign=campaign, open_id='open-1', display_name='Test',
        campaign_version=1, caption='Café', image_jpeg='jpeg', image_expires_at=timezone.now(),
        publish_id='publish-1', status='inbox')


def notify(client, event='post.publish.complete', *, stamp=None, key='test-key', owner='open-1',
           publish_id='publish-1', secret='test-secret', content=None):
    body = json.dumps({'client_key': key, 'event': event, 'create_time': 1600000000,
        'user_openid': owner, 'content': json.dumps(content or {'publish_id': publish_id, 'publish_type': 'INBOX_SHARE'})}).encode()
    stamp = str(stamp if stamp is not None else int(time.time()))
    signature = hmac.new(secret.encode(), stamp.encode() + b'.' + body, hashlib.sha256).hexdigest()
    return client.post(URL, body, content_type='application/json', HTTP_TIKTOK_SIGNATURE=f't={stamp},s={signature}')


def test_signed_completion_confirms_without_resending(api_client, upload):
    with patch('apps.campaigns.tiktok_publication.send_upload') as send:
        assert notify(api_client).status_code == 200
        assert notify(api_client).status_code == 200
        send.assert_not_called()
    upload.refresh_from_db()
    assert upload.status == 'published' and upload.confirmation_source == 'webhook'
    assert upload.public_post_ids == []
    assert upload.published_at
    assert TikTokWebhookReceipt.objects.count() == 1
    assert CampaignSerializer(upload.campaign).data['publication_status']['tiktok'] == 'published'


@pytest.mark.parametrize('event', ['post.publish.inbox_delivered', 'post.publish.failed'])
def test_delayed_events_cannot_downgrade_published(api_client, upload, event):
    notify(api_client)
    notify(api_client, event)
    upload.refresh_from_db()
    assert upload.status == 'published'


@pytest.mark.parametrize('options,status', [
    ({'secret': 'wrong-secret'}, 403), ({'key': 'wrong-key'}, 403),
    ({'stamp': 1}, 403), ({'stamp': int(time.time()) + 9999}, 403),
    ({'owner': 'other-owner'}, 200), ({'publish_id': 'other-post'}, 200),
    ({'content': {'publish_id': 'publish-1', 'publish_type': 'DIRECT_POST'}}, 400),
])
def test_untrusted_or_unmatched_events_never_publish(api_client, upload, options, status):
    assert notify(api_client, **options).status_code == status
    upload.refresh_from_db()
    assert upload.status == 'inbox' and not upload.published_at
    assert not TikTokWebhookReceipt.objects.exists()


def test_unsigned_oversize_and_malformed_payloads_rejected(api_client, upload):
    assert api_client.post(URL, {}, format='json').status_code == 403
    assert api_client.post(URL, b'a' * 65537, content_type='application/json').status_code == 413
    assert notify(api_client, content={'publish_id': 1, 'publish_type': 'INBOX_SHARE'}).status_code == 400
    assert notify(api_client, event='video.publish.completed').status_code == 200
    assert not TikTokWebhookReceipt.objects.exists()


def test_failure_then_late_inbox_does_not_restore_success(api_client, upload):
    notify(api_client, 'post.publish.failed')
    notify(api_client, 'post.publish.inbox_delivered')
    upload.refresh_from_db()
    assert upload.status == 'failed'


def test_bridge_exposes_only_signed_callback(api_client, upload):
    with override_settings(ROOT_URLCONF='core.instagram_preview_urls'):
        assert api_client.get(URL).status_code == 200
        assert notify(api_client, 'post.publish.publicly_available').status_code == 200
        assert api_client.post('/api/campaigns/7/send-tiktok/', {}).status_code == 404
    upload.refresh_from_db()
    assert upload.status == 'published'


def test_publicly_available_event_without_optional_publish_type(api_client, upload):
    assert notify(api_client, 'post.publish.publicly_available', content={'publish_id': 'publish-1', 'post_id': '123'}).status_code == 200
    upload.refresh_from_db()
    assert upload.status == 'published' and upload.confirmation_source == 'webhook'
    assert upload.public_post_ids == ['123']


def test_multiple_public_events_keep_identifiers_and_ignore_invalid_ids(api_client, upload):
    for identifier in ['123', 456, True, 'https://invalid.example']:
        assert notify(api_client, 'post.publish.publicly_available', content={
            'publish_id': 'publish-1', 'post_id': identifier}).status_code == 200
    upload.refresh_from_db()
    assert upload.public_post_ids == ['123', '456']


def test_polling_retains_webhook_confirmation(api_client, upload, user_marketero):
    from apps.authentication.models import TikTokAccount
    account = TikTokAccount.objects.create(owner=user_marketero, open_id=upload.open_id, display_name='Test',
        encrypted_access_token='unused', encrypted_refresh_token='unused', expires_at=timezone.now(),
        refresh_expires_at=timezone.now(), scopes=['video.upload'])
    notify(api_client)
    upload.public_post_ids = ['123']
    upload.save(update_fields=['public_post_ids'])
    with patch('apps.campaigns.tiktok_publication.provider_request') as query:
        response = api_client.post(f'/api/campaigns/{upload.campaign_id}/tiktok-status/', {'account_id': account.pk}, format='json')
    assert response.status_code == 200 and response.data['data']['status'] == 'published'
    assert response.data['data']['confirmation_source'] == 'webhook'
    query.assert_not_called()
