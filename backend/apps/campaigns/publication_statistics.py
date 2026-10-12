"""Read-only social counters. No publishing or fabricated zeroes for missing data."""
import re
from datetime import timedelta

import requests
from cryptography.fernet import InvalidToken
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.instagram import cipher
from apps.authentication.models import InstagramAccount, FacebookPage
from apps.authentication.permissions import IsMarketeroOrSuperAdmin
from core.exceptions import api_response
from .models import (Campaign, InstagramPublication, FacebookPublication,
                     PublicationMetricSnapshot, XPublication, TikTokUpload)

MODELS = {'facebook': FacebookPublication, 'instagram': InstagramPublication,
          'twitter': XPublication, 'tiktok': TikTokUpload}
PLATFORMS = (*MODELS, 'google_ads')
METRICS = ('likes', 'comments', 'shares', 'views')


def campaigns_for(user):
    qs = Campaign.objects.all()
    return qs if user.rol == 'superadmin' else qs.filter(marketero=user)


def count(value):
    return value if type(value) is int and 0 <= value <= 2**63 - 1 else None


def read_counters(platform, publication):
    account = publication.page if platform == 'facebook' else publication.account
    if account is None:
        # Reconnection creates a new credential row; match immutable destination
        # and owner, never borrow another marketer's account or change history.
        account = (FacebookPage.objects.filter(owner_id=publication.campaign.marketero_id,
                   facebook_page_id=publication.facebook_page_id).first() if platform == 'facebook' else
                   InstagramAccount.objects.filter(owner_id=publication.campaign.marketero_id,
                   instagram_user_id=publication.instagram_user_id).first())
    if not account or account.owner_id != publication.campaign.marketero_id:
        raise ValueError('Cuenta desconectada.')
    if account.expires_at <= timezone.now():
        raise ValueError('Autorización vencida.')
    token = cipher().decrypt(account.encrypted_token.encode()).decode()
    identifier = publication.post_id if platform == 'facebook' else publication.media_id
    if not re.fullmatch(r'[0-9_]{1,140}', identifier):
        raise ValueError('No hay identificador confirmado.')
    host = 'graph.facebook.com' if platform == 'facebook' else 'graph.instagram.com'
    version = settings.FACEBOOK_GRAPH_VERSION if platform == 'facebook' else ''
    path = f'{version}/{identifier}' if version else identifier
    fields = ('reactions.type(LIKE).limit(0).summary(true),comments.limit(0).summary(true),shares'
              if platform == 'facebook' else 'like_count,comments_count')
    response = requests.get(f'https://{host}/{path}', params={'fields': fields},
                            headers={'Authorization': f'Bearer {token}'},
                            timeout=20, allow_redirects=False)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or 'error' in data:
        raise ValueError('No se obtuvieron métricas.')
    values = dict.fromkeys(METRICS)
    if platform == 'instagram':
        values.update(likes=count(data.get('like_count')), comments=count(data.get('comments_count')))
    else:
        for metric, field in [('likes', 'reactions'), ('comments', 'comments')]:
            edge = data.get(field)
            if isinstance(edge, dict) and isinstance(edge.get('summary'), dict):
                values[metric] = count(edge['summary'].get('total_count'))
        if isinstance(data.get('shares'), dict):
            values['shares'] = count(data['shares'].get('count'))
    if all(v is None for v in values.values()):
        raise ValueError('Meta no devolvió contadores disponibles.')
    return values


def publication_rows(campaigns):
    snapshots = {}
    for s in PublicationMetricSnapshot.objects.filter(campaign__in=campaigns).order_by('measured_at', 'id'):
        snapshots[(s.platform, s.publication_id)] = s
    rows = []
    for platform, model in MODELS.items():
        for p in model.objects.filter(campaign__in=campaigns, status='published').select_related('campaign'):
            s = snapshots.get((platform, p.pk))
            rows.append({'platform': platform, 'publication_id': p.pk, 'campaign_id': p.campaign_id,
                         'title': p.campaign.titulo, 'version': p.campaign_version,
                         'destination': p.page_name if platform == 'facebook' else
                                        p.display_name if platform == 'tiktok' else p.username,
                         'registered_at': (p.published_at or p.created_at).isoformat() if platform == 'tiktok' else p.created_at.isoformat(),
                         'can_refresh': platform in ('facebook', 'instagram'),
                         'metrics': {k: s.metrics.get(k) if s else None for k in METRICS},
                         'measured_at': s.measured_at.isoformat() if s else None})
    return sorted(rows, key=lambda r: r['registered_at'], reverse=True)


def summary(rows):
    return {platform: {'publications': len(group), 'metrics': {
        k: {'value': sum(r['metrics'][k] for r in group if r['metrics'][k] is not None)
                     if any(r['metrics'][k] is not None for r in group) else None,
            'covered': sum(r['metrics'][k] is not None for r in group)} for k in METRICS}}
        for platform in PLATFORMS for group in [[r for r in rows if r['platform'] == platform]]}


def monthly_likes(campaigns, year):
    """Net counter change between last samples in adjacent months, not event counts."""
    samples = {}
    for s in PublicationMetricSnapshot.objects.filter(campaign__in=campaigns).order_by('measured_at', 'id'):
        samples[(s.platform, s.publication_id, s.day.strftime('%Y-%m'))] = count(s.metrics.get('likes'))
    result = []
    for month in range(1, 13):
        key = f'{year}-{month:02d}'
        previous = f'{int(year)-1}-12' if month == 1 else f'{year}-{month-1:02d}'
        item = {'month': key}
        for platform in PLATFORMS:
            deltas = [value - samples[(p, pk, previous)] for (p, pk, m), value in samples.items()
                      if p == platform and m == key and value is not None and samples.get((p, pk, previous)) is not None]
            item[platform] = sum(deltas) if deltas else None
            item[f'{platform}_covered'] = len(deltas)
        result.append(item)
    return result


class PublicationStatisticsView(APIView):
    permission_classes = [IsAuthenticated, IsMarketeroOrSuperAdmin]

    def get(self, request, campaign_id=None):
        campaigns = campaigns_for(request.user)
        if campaign_id is not None:
            get_object_or_404(campaigns, pk=campaign_id)
            campaigns = campaigns.filter(pk=campaign_id)
        year = request.query_params.get('year', str(timezone.localdate().year))
        if not re.fullmatch(r'20[0-9]{2}', year):
            raise ValidationError('El año debe estar entre 2000 y 2099.')
        rows = publication_rows(campaigns)
        platforms = summary(rows)
        for platform, model in MODELS.items():
            platforms[platform]['pending'] = model.objects.filter(campaign__in=campaigns,
                status__in=['publishing', 'preparing', 'processing', 'inbox', 'uncertain', 'sending']).count()
        if request.user.rol != 'marketero':
            for row in rows:
                row['can_refresh'] = False
        monthly = []
        for month in range(1, 13):
            key = f'{year}-{month:02d}'
            item = {'month': key}
            for platform in PLATFORMS:
                item[platform] = sum(r['platform'] == platform and
                                     timezone.localtime(timezone.datetime.fromisoformat(r['registered_at'])).strftime('%Y-%m') == key
                                     for r in rows)
            monthly.append(item)
        return Response(api_response(True, 'Publicaciones confirmadas registradas por NexoMark.',
            {'platforms': platforms, 'publications': rows, 'monthly': monthly,
             'monthly_likes': monthly_likes(campaigns, year), 'year': int(year),
             'note': 'Contadores acumulados en la última medición; no interacciones ocurridas por mes. '
                     'Los meses cuentan la fecha de registro del envío confirmado, incluyendo versiones anteriores. '
                     'Vistas y compartidos de Instagram requieren integración Insights adicional. '
                     'X y TikTok: consulta de interacciones pendiente. Google Ads: anuncios no integrados, no publicaciones orgánicas. '
                     'No incluye publicaciones externas a NexoMark ni envíos sin confirmación.'}))


class RefreshPublicationStatisticsView(APIView):
    permission_classes = [IsAuthenticated, IsMarketeroOrSuperAdmin]

    def post(self, request, campaign_id):
        # Admin can inspect snapshots, not borrow another owner's credentials.
        campaign = get_object_or_404(Campaign, pk=campaign_id, marketero=request.user)
        platform, identifier = request.data.get('platform'), request.data.get('publication_id')
        if platform not in ('facebook', 'instagram') or type(identifier) is not int or identifier <= 0:
            raise ValidationError('Selecciona una publicación confirmada de Facebook o Instagram.')
        with transaction.atomic():
            p = get_object_or_404(MODELS[platform].objects.select_for_update(),
                                 pk=identifier, campaign=campaign, status='published')
            latest = PublicationMetricSnapshot.objects.filter(platform=platform, publication_id=p.pk).order_by('-measured_at').first()
            if latest and timezone.now() - latest.measured_at < timedelta(minutes=5):
                return Response(api_response(True, 'Se conserva la medición reciente; espera cinco minutos.',
                                             {'measured_at': latest.measured_at.isoformat()}))
            try:
                values = read_counters(platform, p)
            except (requests.RequestException, InvalidToken, ValueError, UnicodeError, TypeError, KeyError):
                return Response(api_response(False, 'No se pudieron consultar las métricas. Revisa la cuenta y los permisos de lectura de Meta. '
                                             'Se conservan las mediciones anteriores; no se publicó contenido.'), status=503)
            now = timezone.now()
            PublicationMetricSnapshot.objects.update_or_create(platform=platform, publication_id=p.pk,
                day=timezone.localdate(), defaults={'campaign': campaign, 'metrics': values, 'measured_at': now})
        return Response(api_response(True, 'Métricas consultadas en Meta.', {'measured_at': now.isoformat()}))
