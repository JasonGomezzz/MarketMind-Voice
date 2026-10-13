from datetime import timedelta
from unittest.mock import patch

import pytest
import requests
from django.utils import timezone

from apps.authentication.models import TikTokAccount
from apps.campaigns.models import TikTokUpload, TikTokPublicationLink, PublicationMetricSnapshot, Campaign
from apps.campaigns.serializers import CampaignSerializer
from apps.campaigns.tiktok_post_ids import parse_publication

pytestmark = pytest.mark.django_db


@pytest.fixture
def upload(campaign, user_marketero):
    account = TikTokAccount.objects.create(owner=user_marketero, open_id='open', display_name='Test',
        encrypted_access_token='unused', encrypted_refresh_token='unused', scopes=['video.list', 'video.upload'],
        expires_at=timezone.now() + timedelta(days=1), refresh_expires_at=timezone.now() + timedelta(days=30))
    return TikTokUpload.objects.create(campaign=campaign, account=account, open_id='open', display_name='Test',
        campaign_version=campaign.version, status='inbox', publish_id='original',
        caption='Approved original', image_jpeg='', image_expires_at=timezone.now())


def payload(upload, **changes):
    result = {'upload_id': upload.pk, 'version': upload.campaign.version, 'publication': '123', 'confirm': True}
    result.update(changes)
    return result


def endpoint(upload):
    return f'/api/campaigns/{upload.campaign_id}/link-tiktok-publication/'


def videos():
    return [{'id': '123', 'like_count': 2, 'comment_count': 0, 'share_count': 0, 'view_count': 304,
             'share_url': 'https://www.tiktok.com/@test/photo/123?lang=en', 'video_description': 'Cafe',
             'create_time': int(timezone.now().timestamp()) - 3600}]


def test_preview_then_confirmation_no_resend_and_upload_status_preserved(api_client, upload):
    with patch('apps.campaigns.tiktok_publication_link.query_tiktok_publications', return_value=videos()) as read, patch(
            'apps.campaigns.tiktok_publication.send_upload') as send:
        preview = api_client.post(endpoint(upload), payload(upload, confirm=False), format='json')
        assert preview.status_code == 200 and preview.data['data']['metrics']['likes'] == 2
        assert preview.data['data']['linked'] is False
        assert not TikTokPublicationLink.objects.exists() and not PublicationMetricSnapshot.objects.exists()
        linked = api_client.post(endpoint(upload), payload(upload), format='json')
        assert linked.status_code == 200 and linked.data['data']['linked'] is True
        assert linked.data['data']['source'] == 'user_confirmed_display_api'
        assert read.call_count == 2
        assert api_client.post(endpoint(upload), payload(upload), format='json').status_code == 200
        assert read.call_count == 2
        send.assert_not_called()
    upload.refresh_from_db()
    assert upload.status == 'inbox' and upload.public_post_ids == [] and not upload.confirmation_source
    link = TikTokPublicationLink.objects.get()
    assert link.confirmed_by_id == upload.campaign.marketero_id
    assert link.post_url == 'https://www.tiktok.com/@test/photo/123'
    assert PublicationMetricSnapshot.objects.get().metrics['views'] == 304
    assert CampaignSerializer(upload.campaign).data['publication_status']['tiktok'] == 'linked'
    data = api_client.get('/api/campaigns/publication-statistics/').data['data']
    assert data['platforms']['tiktok']['publications'] == 1
    assert data['platforms']['tiktok']['pending'] == 0
    assert data['platforms']['tiktok']['metrics']['likes'] == {'value': 2, 'covered': 1}
    assert data['publications'][0]['confirmation_source'] == 'user_confirmed_display_api'
    assert data['publications'][0]['delivery_status'] == 'inbox'
    # A later authentic upload receipt of the same ID cannot count it twice.
    upload.status = 'published'
    upload.public_post_ids = ['123']
    upload.save()
    assert api_client.get('/api/campaigns/publication-statistics/').data['data']['platforms']['tiktok']['publications'] == 1


@pytest.mark.parametrize('changes,status', [
    ({'confirm': 'true'}, 400), ({'confirm': None}, 400), ({'upload_id': True}, 400),
    ({'publication': 'https://evil.example/@test/photo/123'}, 400),
    ({'version': True}, 409), ({'version': 999}, 409),
])
def test_bad_link_requests_never_call_provider(api_client, upload, changes, status):
    with patch('apps.campaigns.tiktok_publication_link.query_tiktok_publications') as read:
        assert api_client.post(endpoint(upload), payload(upload, **changes), format='json').status_code == status
        read.assert_not_called()


def test_other_owner_and_admin_cannot_link(api_client, upload, superadmin_client, superadmin):
    other = Campaign.objects.create(marketero=superadmin, titulo='Other', industria='otro', prompt='test')
    with patch('apps.campaigns.tiktok_publication_link.query_tiktok_publications') as read:
        assert api_client.post(f'/api/campaigns/{other.pk}/link-tiktok-publication/', payload(upload), format='json').status_code == 404
        assert superadmin_client.post(endpoint(upload), payload(upload), format='json').status_code == 403
        read.assert_not_called()


def test_provider_failure_never_links_or_exposes_secret(api_client, upload):
    with patch('apps.campaigns.tiktok_publication_link.query_tiktok_publications', side_effect=requests.Timeout('private')):
        response = api_client.post(endpoint(upload), payload(upload), format='json')
    assert response.status_code == 503 and 'private' not in str(response.data)
    assert not TikTokPublicationLink.objects.exists() and not PublicationMetricSnapshot.objects.exists()


def test_missing_scope_is_not_bypassed(api_client, upload):
    upload.account.scopes = ['video.upload']
    upload.account.save()
    with patch('apps.campaigns.social_metric_readers.requests.post') as read:
        assert api_client.post(endpoint(upload), payload(upload), format='json').status_code == 503
        read.assert_not_called()


def test_cannot_replace_or_double_link_post(api_client, upload, user_marketero):
    TikTokPublicationLink.objects.create(upload=upload, post_id='123', confirmed_by=user_marketero)
    second = TikTokUpload.objects.create(campaign=upload.campaign, account=upload.account, open_id='open', display_name='Test',
        campaign_version=upload.campaign_version + 1, status='inbox', publish_id='another',
        caption='Approved', image_jpeg='', image_expires_at=timezone.now())
    with patch('apps.campaigns.tiktok_publication_link.query_tiktok_publications') as read:
        assert api_client.post(endpoint(upload), payload(upload, publication='456'), format='json').status_code == 409
        assert api_client.post(endpoint(second), payload(second), format='json').status_code == 409
        read.assert_not_called()


def test_linked_publication_can_refresh_without_changing_inbox(api_client, upload, user_marketero):
    TikTokPublicationLink.objects.create(upload=upload, post_id='123', confirmed_by=user_marketero)
    with patch('apps.campaigns.publication_statistics.read_counters', return_value={
            'likes': 3, 'shares': 0, 'views': 310, '_public_post_ids': ['123']}):
        response = api_client.post(f'/api/campaigns/{upload.campaign_id}/publication-statistics/refresh/',
            {'platform': 'tiktok', 'publication_id': upload.pk}, format='json')
    assert response.status_code == 200
    upload.refresh_from_db()
    assert upload.status == 'inbox'


@pytest.mark.parametrize('value', ['http://www.tiktok.com/@test/photo/123', 'https://www.tiktok.com.evil/@test/photo/123',
    'https://user:password@www.tiktok.com/@test/photo/123', 'https://www.tiktok.com:443/@test/photo/123',
    'https://vm.tiktok.com/redirect', True, '0', '-1'])
def test_url_parser_never_accepts_arbitrary_fetch_targets(value):
    assert parse_publication(value) == (None, '')


def test_link_route_not_exposed_on_public_bridge(api_client, upload, settings):
    settings.ROOT_URLCONF = 'core.instagram_preview_urls'
    assert api_client.post(endpoint(upload), payload(upload), format='json').status_code == 404
