from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.campaigns.models import CampaignVersion, XPublication
from apps.campaigns.platform_content import platform_copy, content_errors
from services.version_service import save_campaign_version, restore_campaign_version

pytestmark = pytest.mark.django_db


def setup(campaign):
    campaign.estado = 'generado'
    campaign.texto_generado = 'Contenido original sin recortar ' * 20
    campaign.plataformas = ['facebook', 'twitter', 'instagram']
    campaign.save()
    return campaign


def test_edit_versions_independent_and_stale_edit_rejected(api_client, campaign):
    setup(campaign)
    copies = {'facebook': 'Texto amplio para Facebook', 'twitter': 'Texto breve ☕', 'instagram': 'Otro texto #Café'}
    response = api_client.patch(f'/api/campaigns/{campaign.pk}/', {
        'version': campaign.version, 'textos_por_plataforma': copies}, format='json')
    assert response.status_code == 200
    campaign.refresh_from_db()
    assert campaign.textos_por_plataforma == copies
    assert campaign.version == 2
    assert platform_copy(campaign, 'twitter') == 'Texto breve ☕'
    assert campaign.texto_generado.startswith('Contenido original')
    stale = api_client.patch(f'/api/campaigns/{campaign.pk}/', {'version': 1, 'texto_generado': 'Stale'}, format='json')
    assert stale.status_code == 409


@pytest.mark.parametrize('state', ['aprobado', 'pendiente_aprobacion', 'pendiente_ia', 'fracaso'])
def test_content_locked_during_review_and_after_approval(api_client, campaign, state):
    setup(campaign)
    campaign.estado = state
    campaign.save()
    assert api_client.patch(f'/api/campaigns/{campaign.pk}/', {'texto_generado': 'Alterado'}, format='json').status_code == 409
    assert api_client.post(f'/api/campaigns/{campaign.pk}/improve-text/').status_code == 409
    assert api_client.post(f'/api/campaigns/{campaign.pk}/adapt-platforms/', {'version': campaign.version}, format='json').status_code == 409


def test_explicit_reopen_preserves_legacy_content_and_requires_new_approval(api_client, campaign):
    setup(campaign)
    campaign.estado = 'aprobado'
    campaign.save()
    url = f'/api/campaigns/{campaign.pk}/reopen-review/'
    assert api_client.post(url, {'version': 1}, format='json').status_code == 400
    assert api_client.post(url, {'version': 0, 'confirm': True}, format='json').status_code == 409
    result = api_client.post(url, {'version': 1, 'confirm': True}, format='json')
    assert result.status_code == 200
    campaign.refresh_from_db()
    assert campaign.estado == 'generado' and campaign.version == 2
    assert campaign.textos_por_plataforma == {}
    assert CampaignVersion.objects.get(campaign=campaign).texto_generado == campaign.texto_generado
    assert api_client.post(f'/api/campaigns/{campaign.pk}/adapt-platforms/', {'version': 2}, format='json').status_code == 200
    campaign.refresh_from_db()
    assert len(campaign.textos_por_plataforma['twitter']) < 280
    assert campaign.estado == 'generado' and campaign.version == 3
    with patch('apps.campaigns.views.notify_campaign_submitted'), patch('services.email_n8n_service.disparar_email_cliente'):
        assert api_client.post(f'/api/campaigns/{campaign.pk}/submit/').status_code == 200
    campaign.refresh_from_db()
    assert campaign.estado == 'pendiente_aprobacion'


@pytest.mark.parametrize('state', ['preparing', 'publishing', 'uncertain'])
def test_cannot_reopen_an_unresolved_publication(api_client, campaign, state):
    setup(campaign)
    campaign.estado = 'aprobado'
    campaign.save()
    XPublication.objects.create(campaign=campaign, x_user_id='123', username='demo', campaign_version=1,
                              caption='Copy', image_jpeg='jpeg', status=state)
    assert api_client.post(f'/api/campaigns/{campaign.pk}/reopen-review/', {
        'version': 1, 'confirm': True}, format='json').status_code == 409


def test_x_limit_blocks_submission_not_save_and_validates_weighted_urls(api_client, campaign):
    setup(campaign)
    copies = {p: 'a' * 281 if p == 'twitter' else 'Copy' for p in campaign.plataformas}
    url = f'/api/campaigns/{campaign.pk}/'
    assert api_client.patch(url, {'textos_por_plataforma': copies}, format='json').status_code == 200
    assert api_client.post(url + 'submit/').status_code == 400
    copies['twitter'] = 'Café ☕ https://example.com/' + 'long-path' * 100
    result = api_client.post(url + 'validate-platforms/', {'textos_por_plataforma': copies}, format='json')
    assert result.status_code == 200 and result.data['data']['errors'] == {}
    assert result.data['data']['twitter_length'] < 280
    campaign.refresh_from_db()
    assert campaign.textos_por_plataforma['twitter'] == 'a' * 281  # validation is read-only


@pytest.mark.parametrize('copies', [[], {'twitter': 'Copy'}, {'facebook': 123, 'twitter': 'Copy', 'instagram': 'Copy'},
                                    {'facebook': '', 'twitter': 'Copy', 'instagram': 'Copy'}])
def test_invalid_platform_maps_rejected(api_client, campaign, copies):
    setup(campaign)
    assert api_client.patch(f'/api/campaigns/{campaign.pk}/', {'textos_por_plataforma': copies}, format='json').status_code == 400


def test_snapshot_restores_all_platforms(campaign):
    setup(campaign)
    campaign.textos_por_plataforma = {'facebook': 'Antes', 'twitter': 'Breve', 'instagram': 'Hashtags'}
    campaign.save()
    save_campaign_version(campaign)
    snapshot = campaign.versions.get()
    campaign.textos_por_plataforma = {'facebook': 'Después'}
    campaign.save()
    restore_campaign_version(campaign, snapshot)
    assert campaign.textos_por_plataforma == snapshot.textos_por_plataforma
    assert campaign.version == 2


def test_foreign_owner_and_customer_cannot_change_platform_content(cliente, campaign):
    setup(campaign)
    client = APIClient()
    client.force_authenticate(cliente)
    assert client.post(f'/api/campaigns/{campaign.pk}/adapt-platforms/', {'version': 1}, format='json').status_code == 404


def test_generator_failure_preserves_saved_content(api_client, campaign):
    setup(campaign)
    with patch('apps.campaigns.views.adapt_platform_copies', side_effect=ValueError('Fallo seguro')):
        assert api_client.post(f'/api/campaigns/{campaign.pk}/adapt-platforms/', {'version': 1}, format='json').status_code == 503
    campaign.refresh_from_db()
    assert campaign.version == 1 and campaign.textos_por_plataforma == {}


def test_legacy_fallback_and_instagram_validation(campaign):
    setup(campaign)
    assert platform_copy(campaign, 'twitter') == campaign.texto_generado
    campaign.textos_por_plataforma = {'twitter': 'Breve', 'facebook': 'Copy', 'instagram': 'a' * 2201}
    assert set(content_errors(campaign)) == {'instagram'}
