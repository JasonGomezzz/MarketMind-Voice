import pytest
from rest_framework.test import APIClient
from django.utils import timezone
from apps.campaigns.models import CampaignVersion, TikTokUpload, XPublication

pytestmark = pytest.mark.django_db


def approved(campaign):
    campaign.estado = 'aprobado'
    campaign.plataformas = ['facebook', 'twitter']
    campaign.texto_generado = 'Café artesanal: contenido original.'
    campaign.textos_por_plataforma = {'facebook': 'Copy aprobado FB', 'twitter': 'Copy aprobado X'}
    campaign.imagen_b64 = 'original-image'
    campaign.email_enviado = True
    campaign.save()
    return f'/api/campaigns/{campaign.pk}/reopen-review/'


def test_add_tiktok_retains_content_history_and_published_records(api_client, campaign):
    url = approved(campaign)
    for number in range(1, 6):
        CampaignVersion.objects.create(campaign=campaign, version_number=number, texto_generado=f'Anterior {number}')
    publication = XPublication.objects.create(campaign=campaign, x_user_id='123', username='demo',
        campaign_version=1, caption='Copy aprobado X', image_jpeg='jpeg', status='published')
    response = api_client.post(url, {'version': 1, 'confirm': True, 'add_platform': 'tiktok'}, format='json')
    assert response.status_code == 200
    campaign.refresh_from_db()
    publication.refresh_from_db()
    assert campaign.estado == 'generado' and campaign.version == 2
    assert campaign.plataformas == ['facebook', 'twitter', 'tiktok']
    assert campaign.texto_generado == 'Café artesanal: contenido original.'
    assert campaign.imagen_b64 == 'original-image'
    assert campaign.textos_por_plataforma == {'facebook': 'Copy aprobado FB', 'twitter': 'Copy aprobado X', 'tiktok': campaign.texto_generado}
    assert campaign.versions.count() == 6
    assert campaign.versions.first().textos_por_plataforma == {'facebook': 'Copy aprobado FB', 'twitter': 'Copy aprobado X'}
    assert not campaign.email_enviado
    assert publication.status == 'published' and publication.campaign_version == 1
    assert api_client.post(url, {'version': 1, 'confirm': True, 'add_platform': 'tiktok'}, format='json').status_code == 409


@pytest.mark.parametrize('payload,status', [
    ({'version': 1, 'add_platform': 'tiktok'}, 400),
    ({'version': 0, 'confirm': True, 'add_platform': 'tiktok'}, 409),
    ({'version': True, 'confirm': True, 'add_platform': 'tiktok'}, 409),
    ({'version': 1, 'confirm': True, 'add_platform': 'linkedin'}, 400),
    ({'version': 1, 'confirm': True, 'add_platform': None}, 400),
])
def test_invalid_request_leaves_approval_untouched(api_client, campaign, payload, status):
    url = approved(campaign)
    assert api_client.post(url, payload, format='json').status_code == status
    campaign.refresh_from_db()
    assert campaign.estado == 'aprobado' and campaign.version == 1
    assert 'tiktok' not in campaign.plataformas


def test_duplicate_and_foreign_owner_rejected(api_client, campaign, cliente):
    url = approved(campaign)
    foreign = APIClient()
    foreign.force_authenticate(cliente)
    assert foreign.post(url, {'version': 1, 'confirm': True, 'add_platform': 'tiktok'}, format='json').status_code == 404
    campaign.plataformas.append('tiktok')
    campaign.save()
    assert api_client.post(url, {'version': 1, 'confirm': True, 'add_platform': 'tiktok'}, format='json').status_code == 400


@pytest.mark.parametrize('state', ['sending', 'processing', 'inbox', 'uncertain'])
def test_pending_tiktok_upload_blocks_revision(api_client, campaign, state):
    url = approved(campaign)
    TikTokUpload.objects.create(campaign=campaign, open_id='demo', display_name='demo', campaign_version=1,
        caption='Copy', image_jpeg='jpeg', image_expires_at=timezone.now(), status=state)
    assert api_client.post(url, {'version': 1, 'confirm': True, 'add_platform': 'tiktok'}, format='json').status_code == 409
    campaign.refresh_from_db()
    assert campaign.estado == 'aprobado' and campaign.version == 1
