import base64
from datetime import timedelta
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
import requests
from cryptography.fernet import Fernet
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.authentication.models import XAccount, User
from apps.authentication.x_oauth import access_token_for
from apps.campaigns.models import XPublication, XSummary
from apps.campaigns.x_publication import XRejected, text_validation

pytestmark = pytest.mark.django_db


@pytest.fixture
def x_publication(settings, campaign, user_marketero):
    key = Fernet.generate_key()
    settings.SOCIAL_TOKEN_ENCRYPTION_KEY = key.decode()
    settings.X_CLIENT_ID = 'client-id'
    settings.X_CLIENT_SECRET = 'private-secret'
    settings.X_REDIRECT_URI = 'https://demo.example/api/auth/x/callback/'
    output = BytesIO()
    Image.new('RGB', (400, 400), 'blue').save(output, 'PNG')
    campaign.imagen_b64 = base64.b64encode(output.getvalue()).decode()
    campaign.texto_generado = 'Copy aprobado con café ☕'
    campaign.estado = 'aprobado'
    campaign.plataformas = ['twitter', 'instagram']
    campaign.save()
    account = XAccount.objects.create(owner=user_marketero, x_user_id='123456', username='ToyLokazo',
        encrypted_access_token=Fernet(key).encrypt(b'private-token').decode(),
        encrypted_refresh_token=Fernet(key).encrypt(b'private-refresh').decode(),
        expires_at=timezone.now() + timedelta(hours=2))
    return campaign, account


def publish(client, setup, **extra):
    campaign, account = setup
    return client.post(f'/api/campaigns/{campaign.pk}/publish-x/',
        {'account_id': account.pk, 'version': campaign.version, 'confirm': True, **extra}, format='json')


@patch('apps.campaigns.x_publication.send_post', return_value='987654')
@patch('apps.campaigns.x_publication.upload_image', return_value='12345')
def test_x_uses_its_own_approved_copy(upload, send, api_client, x_publication):
    campaign, account = x_publication
    campaign.texto_generado = 'Texto base largo ' * 100
    campaign.textos_por_plataforma = {'twitter': 'Texto breve aprobado para X', 'instagram': 'Versión para Instagram'}
    campaign.save()
    assert publish(api_client, x_publication, caption='Texto no aprobado').status_code == 200
    assert XPublication.objects.get().caption == 'Texto breve aprobado para X'
    assert send.call_args.args[0].caption == 'Texto breve aprobado para X'


def summarize(client, campaign):
    return client.post(f'/api/campaigns/{campaign.pk}/summarize-x/', {'version': campaign.version}, format='json')


@patch('apps.campaigns.x_publication.adapt_platform_copies', return_value={'twitter': 'Café artesanal con Aroma Andino ☕ #Café'})
@patch('apps.campaigns.x_publication.send_post', return_value='987654')
@patch('apps.campaigns.x_publication.upload_image', return_value='12345')
def test_summary_confirmation_does_not_change_approval_or_other_platforms(upload, send, adapt, api_client, x_publication):
    campaign, account = x_publication
    campaign.textos_por_plataforma = {'twitter': 'Contenido largo ' * 100, 'instagram': 'Copy Instagram aprobado', 'facebook': 'Copy Facebook aprobado'}
    campaign.save()
    approved_copies = dict(campaign.textos_por_plataforma)
    original_version = campaign.version
    response = summarize(api_client, campaign)
    assert response.status_code == 200
    summary_id = response.data['data']['summary_id']
    upload.assert_not_called()
    send.assert_not_called()
    assert publish(api_client, x_publication, summary_id=summary_id).status_code == 400
    send.assert_not_called()
    response = publish(api_client, x_publication, summary_id=summary_id, confirm_summary=True, caption='Injected text')
    assert response.status_code == 200 and response.data['data']['status'] == 'published'
    publication = XPublication.objects.get()
    assert publication.caption == 'Café artesanal con Aroma Andino ☕ #Café'
    assert publication.summary_id == XSummary.objects.get().pk
    assert publication.confirmed_by_id == campaign.marketero_id and publication.confirmed_at
    campaign.refresh_from_db()
    assert campaign.estado == 'aprobado' and campaign.version == original_version
    assert campaign.textos_por_plataforma == approved_copies
    assert publish(api_client, x_publication, summary_id=summary_id, confirm_summary=True).status_code == 200
    send.assert_called_once()
    status = api_client.get(f'/api/campaigns/{campaign.pk}/publish-x/', {'account_id': account.pk})
    assert status.data['data']['caption'] == publication.caption
    assert status.data['data']['summary_id'] == summary_id
    assert status.data['data']['caption_source'] == 'marketer_summary'


@pytest.mark.parametrize('change', ['version', 'copy', 'image'])
@patch('apps.campaigns.x_publication.adapt_platform_copies', return_value={'twitter': 'Resumen válido'})
def test_summary_stale_version_or_changed_source_cannot_be_used(adapt, api_client, x_publication, change):
    campaign, account = x_publication
    summary_id = summarize(api_client, campaign).data['data']['summary_id']
    if change == 'version':
        campaign.version += 1
    elif change == 'copy':
        campaign.texto_generado = 'Otro texto aprobado'
    else:
        campaign.imagen_b64 = 'Another image'
    campaign.save()
    assert publish(api_client, x_publication, summary_id=summary_id, confirm_summary=True).status_code == 400
    assert not XPublication.objects.exists()


@patch('apps.campaigns.x_publication.adapt_platform_copies', return_value={'twitter': 'Resumen válido'})
def test_foreign_summary_rejected_and_arbitrary_text_cannot_bypass_limit(adapt, api_client, x_publication, user_marketero):
    from apps.campaigns.models import Campaign
    campaign, account = x_publication
    other = Campaign.objects.create(titulo='Otra campaña', cliente_nombre='Cliente', industria='retail',
        prompt='Otro prompt', marketero=user_marketero, estado='aprobado', plataforma='twitter', texto_generado='Otro texto')
    summary_id = summarize(api_client, other).data['data']['summary_id']
    assert publish(api_client, x_publication, summary_id=summary_id, confirm_summary=True).status_code == 404
    campaign.texto_generado = 'a' * 281
    campaign.save()
    assert publish(api_client, x_publication, caption='Texto inyectado corto', confirm_summary=True).status_code == 400
    assert publish(api_client, x_publication, summary_id='invalid', confirm_summary=True).status_code == 400
    assert not XPublication.objects.exists()


@patch('apps.campaigns.x_publication.adapt_platform_copies', return_value={'twitter': 'a' * 281})
def test_invalid_generated_summary_is_not_truncated_or_saved(adapt, api_client, x_publication):
    campaign, account = x_publication
    assert summarize(api_client, campaign).status_code == 503
    assert not XSummary.objects.exists() and not XPublication.objects.exists()
    campaign.refresh_from_db()
    assert campaign.estado == 'aprobado'


@pytest.mark.parametrize('state', ['generado', 'pendiente_aprobacion', 'rechazado'])
def test_summary_requires_approved_campaign(api_client, x_publication, state):
    campaign, account = x_publication
    campaign.estado = state
    campaign.save()
    assert summarize(api_client, campaign).status_code == 409
    assert not XSummary.objects.exists()


@patch('apps.campaigns.x_publication.adapt_platform_copies')
def test_campaign_change_during_summary_generation_is_rejected(adapt, api_client, x_publication):
    campaign, account = x_publication
    def changed(_campaign):
        type(campaign).objects.filter(pk=campaign.pk).update(version=campaign.version + 1)
        return {'twitter': 'Resumen válido'}
    adapt.side_effect = changed
    assert summarize(api_client, campaign).status_code == 409
    assert not XSummary.objects.exists()


@patch('apps.campaigns.x_publication.requests.post')
def test_exact_approved_image_and_text_once_with_durable_intent(post, api_client, x_publication):
    campaign, account = x_publication
    campaign.texto_generado += ' https://example.com/' + 'path' * 100
    campaign.save()
    assert len(campaign.texto_generado) > 280 and text_validation(campaign.texto_generado)['valid']

    def external(url, **kwargs):
        publication = XPublication.objects.get()
        assert kwargs['headers'] == {'Authorization': 'Bearer private-token'}
        assert kwargs['timeout'] == 30 and kwargs['allow_redirects'] is False
        if url == 'https://api.x.com/2/media/upload':
            assert publication.status == 'preparing'
            payload = kwargs['json']
            assert payload['media_category'] == 'tweet_image'
            assert base64.b64decode(payload['media']).startswith(b'\xff\xd8')
            return Mock(status_code=200, json=Mock(return_value={'data': {'id': '987654'}}))
        assert url == 'https://api.x.com/2/tweets'
        assert publication.status == 'publishing' and publication.media_id == '987654'
        assert kwargs['json'] == {'text': campaign.texto_generado, 'media': {'media_ids': ['987654']}}
        return Mock(status_code=201, json=Mock(return_value={'data': {'id': '999999'}}))

    post.side_effect = external
    response = publish(api_client, x_publication, caption='Unapproved draft', imagen_b64='bad')
    assert response.data['data']['status'] == 'published'
    assert response.data['data']['publication_url'] == 'https://x.com/i/status/999999'
    assert 'private-token' not in str(response.data)
    assert publish(api_client, x_publication).data['data']['status'] == 'published'
    account.delete()
    assert XPublication.objects.get().account is None
    replacement = XAccount.objects.create(owner=campaign.marketero, x_user_id='123456', username='ToyLokazo',
        encrypted_access_token='new', encrypted_refresh_token='new', expires_at=timezone.now())
    assert publish(api_client, (campaign, replacement)).data['data']['status'] == 'published'
    assert post.call_count == 2


@patch('apps.campaigns.x_publication.upload_image', return_value='987654')
@patch('apps.campaigns.x_publication.send_post', side_effect=requests.Timeout('token-bearing-error'))
def test_uncertain_post_never_resent(send, upload, api_client, x_publication):
    response = publish(api_client, x_publication)
    assert response.data['data']['status'] == 'uncertain'
    assert 'token-bearing-error' not in str(response.data)
    assert publish(api_client, x_publication).data['data']['status'] == 'uncertain'
    send.assert_called_once()
    upload.assert_called_once()


@pytest.mark.parametrize('status', ['preparing', 'publishing'])
@patch('apps.campaigns.x_publication.upload_image')
def test_inflight_attempt_blocks_duplicate(upload, api_client, x_publication, status):
    campaign, account = x_publication
    XPublication.objects.create(campaign=campaign, account=account, x_user_id=account.x_user_id,
        username=account.username, campaign_version=campaign.version, caption=campaign.texto_generado,
        image_jpeg='snapshot', status=status)
    assert publish(api_client, x_publication).status_code == 202
    upload.assert_not_called()


@patch('apps.campaigns.x_publication.upload_image', side_effect=XRejected(402, 'media'))
@patch('apps.campaigns.x_publication.send_post')
def test_upload_rejection_creates_no_public_post_and_explicit_retry_is_safe(send, upload, api_client, x_publication):
    response = publish(api_client, x_publication)
    assert response.data['data']['status'] == 'failed' and 'créditos' in response.data['message']
    send.assert_not_called()
    upload.side_effect = None
    upload.return_value = '987654'
    send.return_value = '999999'
    assert publish(api_client, x_publication).data['data']['status'] == 'published'
    assert XPublication.objects.count() == 1


@patch('apps.campaigns.x_publication.upload_image', return_value='987654')
@patch('apps.campaigns.x_publication.send_post', side_effect=XRejected(429, 'post'))
def test_definite_post_rejection_allows_manual_confirmation(send, upload, api_client, x_publication):
    assert publish(api_client, x_publication).data['data']['status'] == 'failed'
    send.side_effect = None
    send.return_value = '999999'
    assert publish(api_client, x_publication).data['data']['status'] == 'published'


@patch('apps.campaigns.x_publication.requests.post')
def test_preconditions_before_external_requests(post, api_client, x_publication, cliente, settings):
    campaign, account = x_publication
    assert publish(api_client, x_publication, confirm=False).status_code == 400
    assert publish(api_client, x_publication, version=True).status_code == 409
    assert publish(api_client, x_publication, version=999).status_code == 409
    assert publish(api_client, x_publication, account_id=True).status_code == 400
    assert APIClient().get(f'/api/campaigns/{campaign.pk}/publish-x/').status_code == 401
    client = APIClient()
    client.force_authenticate(cliente)
    assert publish(client, x_publication).status_code == 403
    campaign.estado = 'generado'
    campaign.save()
    assert publish(api_client, x_publication).status_code == 400
    campaign.estado = 'aprobado'
    campaign.plataformas = ['instagram']
    campaign.save()
    assert publish(api_client, x_publication).status_code == 400
    campaign.plataformas = ['twitter']
    campaign.imagen_b64 = 'invalid'
    campaign.save()
    assert publish(api_client, x_publication).status_code == 400
    settings.X_CLIENT_SECRET = ''
    assert publish(api_client, x_publication).status_code == 503
    post.assert_not_called()
    assert not XPublication.objects.exists()


@patch('apps.campaigns.x_publication.requests.post')
def test_foreign_account_and_campaign_are_inaccessible(post, api_client, x_publication):
    campaign, account = x_publication
    marketero2 = User.objects.create_user(email='other-x-publication@test.com', password='Test1234!', nombre='Other', rol='marketero')
    account.owner = marketero2
    account.save()
    assert publish(api_client, x_publication).status_code == 404
    assert api_client.get(f'/api/campaigns/{campaign.pk}/publish-x/', {'account_id': account.pk}).status_code == 404
    campaign.marketero = marketero2
    campaign.save()
    assert api_client.get(f'/api/campaigns/{campaign.pk}/publish-x/').status_code == 404
    post.assert_not_called()


@patch('apps.campaigns.x_publication.requests.post')
def test_overlong_text_is_visible_but_rejected_before_upload(post, api_client, x_publication):
    campaign, account = x_publication
    campaign.texto_generado = 'a' * 281
    campaign.save()
    response = api_client.get(f'/api/campaigns/{campaign.pk}/publish-x/', {'account_id': account.pk})
    assert response.data['data']['text_validation'] == {'valid': False, 'weighted_length': 281, 'limit': 280}
    assert publish(api_client, x_publication).status_code == 400
    post.assert_not_called()
    assert not XPublication.objects.exists()


def test_weighted_url_emoji_and_unicode_count():
    assert text_validation('a' * 256 + ' https://example.com/' + 'path' * 100)['valid']
    assert text_validation('👨‍👩‍👧‍👦' * 140)['weighted_length'] == 280
    assert text_validation('👨‍👩‍👧‍👦' * 141)['valid'] is False
    assert text_validation('cafe\u0301')['weighted_length'] == 4


@patch('apps.authentication.x_oauth.requests.post')
def test_expired_token_is_refreshed_encrypted_once_without_posting(post, api_client, x_publication, settings):
    campaign, account = x_publication
    account.expires_at = timezone.now() - timedelta(seconds=1)
    account.save()
    post.return_value = Mock(status_code=200, json=Mock(return_value={
        'access_token': 'renewed-access', 'refresh_token': 'rotated-refresh', 'expires_in': 7200}))
    assert access_token_for(account) == 'renewed-access'
    args = post.call_args
    assert args.args == ('https://api.x.com/2/oauth2/token',)
    assert args.kwargs['data'] == {'grant_type': 'refresh_token', 'refresh_token': 'private-refresh'}
    assert args.kwargs['auth'] == ('client-id', 'private-secret')
    assert args.kwargs['allow_redirects'] is False
    account.refresh_from_db()
    decoder = Fernet(settings.SOCIAL_TOKEN_ENCRYPTION_KEY.encode())
    assert decoder.decrypt(account.encrypted_refresh_token.encode()) == b'rotated-refresh'
    assert access_token_for(account) == 'renewed-access'
    assert post.call_count == 1
    assert not XPublication.objects.exists()
    api_client.get(f'/api/campaigns/{campaign.pk}/publish-x/', {'account_id': account.pk})
    assert post.call_count == 1


@patch('apps.campaigns.x_publication.requests.post')
def test_invalid_media_response_never_posts(post, api_client, x_publication):
    post.return_value = Mock(status_code=200, json=Mock(return_value={'data': {'id': 'unsafe/id'}}))
    assert publish(api_client, x_publication).data['data']['status'] == 'failed'
    assert post.call_count == 1


@pytest.mark.parametrize('response', [Mock(status_code=500),
    Mock(status_code=201, json=Mock(return_value={'data': {'id': 'unsafe/id'}}))])
@patch('apps.campaigns.x_publication.upload_image', return_value='987654')
@patch('apps.campaigns.x_publication.requests.post')
def test_unconfirmed_post_response_is_uncertain(post, upload, response, api_client, x_publication):
    post.return_value = response
    assert publish(api_client, x_publication).data['data']['status'] == 'uncertain'
    assert publish(api_client, x_publication).data['data']['status'] == 'uncertain'
    assert post.call_count == 1
