"""Link an existing public post after ownership verification and explicit consent."""
from datetime import datetime, timezone as utc_timezone

import requests
from cryptography.fernet import InvalidToken
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import TikTokAccount
from apps.authentication.permissions import IsMarketero
from core.exceptions import api_response
from .models import Campaign, TikTokUpload, TikTokPublicationLink, PublicationMetricSnapshot
from .publication_statistics import count
from .social_metric_readers import owned_account, query_tiktok_publications, tiktok_values, MetricReadUnavailable
from .tiktok_post_ids import parse_publication, effective_public_post_ids


def link_result(link):
    return {'linked': True, 'post_id': link.post_id, 'post_url': link.post_url,
            'verified_at': link.verified_at.isoformat(), 'source': 'user_confirmed_display_api'}


class TikTokPublicationLinkView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, pk=campaign_id, marketero=request.user)
        upload_id = request.data.get('upload_id')
        version = request.data.get('version')
        confirm = request.data.get('confirm')
        post_id, _ = parse_publication(request.data.get('publication'))
        if type(upload_id) is not int or upload_id <= 0 or not post_id or type(confirm) is not bool:
            return Response(api_response(False, 'Introduce una URL pública de TikTok o su ID y confirma la acción.'), status=400)
        if type(version) is not int or version != campaign.version:
            return Response(api_response(False, 'La campaña cambió. Recarga antes de vincular.'), status=409)
        upload = get_object_or_404(TikTokUpload, pk=upload_id, campaign=campaign)
        # Only a durable upload belonging to this campaign/account may be linked.
        # An arbitrary external post must never be imported as a new campaign.
        if not upload.publish_id:
            return Response(api_response(False, 'Se necesita un envío previo registrado para vincular esta publicación.'), status=400)
        existing = TikTokPublicationLink.objects.filter(upload=upload).first()
        if existing:
            if existing.post_id == post_id:
                return Response(api_response(True, 'La publicación ya está vinculada; no se volvió a enviar.', link_result(existing)))
            return Response(api_response(False, 'Este envío ya tiene otra publicación vinculada. No se reemplazará.'), status=409)
        other_ids = TikTokUpload.objects.exclude(pk=upload.pk).exclude(public_post_ids=[]).values_list('public_post_ids', flat=True)
        if TikTokPublicationLink.objects.filter(post_id=post_id).exists() or any(post_id in ids for ids in other_ids):
            return Response(api_response(False, 'Esta publicación ya está asociada a otro envío.'), status=409)
        try:
            account = owned_account(upload, TikTokAccount, 'open_id')
            videos = query_tiktok_publications(account, [post_id], details=True)
            values = tiktok_values(videos, count)
        except MetricReadUnavailable as error:
            return Response(api_response(False, str(error)), status=503)
        except (requests.RequestException, InvalidToken, ValueError, TypeError, UnicodeError, KeyError, ObjectDoesNotExist):
            return Response(api_response(False, 'TikTok no pudo verificar esa publicación en la cuenta del envío. No se vinculó ni se publicó contenido.'), status=503)
        video = videos[0]
        now = timezone.now()
        created = video.get('create_time')
        created_at = datetime.fromtimestamp(created, utc_timezone.utc) if type(created) is int and 946684800 <= created <= int(now.timestamp()) else None
        returned_id, url = parse_publication(video.get('share_url'))
        if returned_id != post_id:
            url = ''
        description = video.get('video_description')
        preview = {'linked': False, 'post_id': post_id, 'post_url': url,
                   'description': description[:4000] if isinstance(description, str) else '',
                   'created_at': created_at.isoformat() if created_at else None,
                   'metrics': {key: values[key] for key in ('likes', 'shares', 'views')},
                   'upload_id': upload.pk, 'upload_version': upload.campaign_version,
                   'campaign_version': campaign.version,
                   'account_name': account.display_name}
        if not confirm:
            return Response(api_response(True, 'TikTok verificó la propiedad. Confirma que este post corresponde a la campaña.', preview))
        try:
            with transaction.atomic():
                locked_campaign = Campaign.objects.select_for_update().get(pk=campaign.pk, marketero=request.user)
                if locked_campaign.version != version:
                    return Response(api_response(False, 'La campaña cambió durante la comprobación. Recarga.'), status=409)
                upload = TikTokUpload.objects.select_for_update().get(pk=upload.pk, campaign=locked_campaign)
                # Recheck destination after the provider read, before persisting.
                owned_account(upload, TikTokAccount, 'open_id')
                existing = TikTokPublicationLink.objects.filter(upload=upload).first()
                if existing:
                    if existing.post_id != post_id:
                        return Response(api_response(False, 'Este envío ya tiene otra publicación vinculada.'), status=409)
                    return Response(api_response(True, 'La publicación ya está vinculada.', link_result(existing)))
                link = TikTokPublicationLink.objects.create(upload=upload, post_id=post_id, post_url=url,
                    provider_created_at=created_at, verified_at=now, confirmed_by=request.user)
                # Do not pretend the original Content Posting delivery is complete.
                # Snapshot is complete only when it covers the whole confirmed set.
                if effective_public_post_ids(upload) == [post_id]:
                    PublicationMetricSnapshot.objects.update_or_create(platform='tiktok', publication_id=upload.pk,
                        day=timezone.localdate(), defaults={'campaign': campaign, 'metrics': values, 'measured_at': now})
        except IntegrityError:
            return Response(api_response(False, 'El post ya fue vinculado por otra solicitud. Recarga para comprobarlo.'), status=409)
        except (MetricReadUnavailable, ObjectDoesNotExist):
            return Response(api_response(False, 'La cuenta cambió durante la verificación. Reconecta y vuelve a comprobar.'), status=409)
        return Response(api_response(True, 'Publicación existente vinculada y verificada. No se envió contenido nuevo.', link_result(link)))
