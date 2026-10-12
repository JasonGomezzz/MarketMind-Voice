"""Receive TikTok Content Posting events, authenticated against their raw body."""
import hashlib
import hmac
import json
import re
import time

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import TikTokUpload, TikTokWebhookReceipt

EVENTS = {
    'post.publish.complete': 'published',
    'post.publish.publicly_available': 'published',
    'post.publish.inbox_delivered': 'inbox',
    'post.publish.failed': 'failed',
}


def valid_signature(header, body):
    if not settings.TIKTOK_CLIENT_SECRET or not isinstance(header, str) or len(header) > 512:
        return False
    parts = header.split(',')
    timestamps = [p.strip()[2:] for p in parts if p.strip().startswith('t=')]
    signatures = [p.strip()[2:] for p in parts if p.strip().startswith('s=')]
    if len(timestamps) != 1 or not re.fullmatch(r'[0-9]{1,12}', timestamps[0]):
        return False
    stamp = timestamps[0]
    if abs(time.time() - int(stamp)) > 300:
        return False
    expected = hmac.new(settings.TIKTOK_CLIENT_SECRET.encode(), stamp.encode() + b'.' + body,
                        hashlib.sha256).hexdigest()
    return any(re.fullmatch(r'[0-9a-f]{64}', s) and hmac.compare_digest(expected, s) for s in signatures)


class TikTokWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return JsonResponse({'service': 'tiktok-webhook'})

    def post(self, request):
        if request.META.get('CONTENT_LENGTH', '').isdigit() and int(request.META['CONTENT_LENGTH']) > 65536:
            return JsonResponse({'error': 'payload_too_large'}, status=413)
        body = request.body
        if len(body) > 65536:
            return JsonResponse({'error': 'payload_too_large'}, status=413)
        if not valid_signature(request.headers.get('TikTok-Signature'), body):
            return JsonResponse({'error': 'invalid_signature'}, status=403)
        try:
            event = json.loads(body)
            if not isinstance(event, dict) or not isinstance(event.get('client_key'), str):
                raise ValueError()
            if not settings.TIKTOK_CLIENT_KEY or not hmac.compare_digest(event['client_key'], settings.TIKTOK_CLIENT_KEY):
                return JsonResponse({'error': 'invalid_client'}, status=403)
            event_name = event.get('event')
            if event_name not in EVENTS:
                return JsonResponse({'received': True})
            content = event.get('content')
            content = json.loads(content) if isinstance(content, str) else content
            if not isinstance(content, dict):
                raise ValueError()
            publish_id, open_id = content.get('publish_id'), event.get('user_openid')
            if (not isinstance(publish_id, str) or not 0 < len(publish_id) <= 64 or
                    not isinstance(open_id, str) or not 0 < len(open_id) <= 128 or
                    content.get('publish_type') not in (None, 'INBOX_SHARE')):
                raise ValueError()
        except (ValueError, UnicodeError, TypeError):
            return JsonResponse({'error': 'invalid_event'}, status=400)
        with transaction.atomic():
            upload = TikTokUpload.objects.select_for_update().filter(publish_id=publish_id, open_id=open_id).first()
            if upload is None:
                # No matching immutable intent: never infer by caption or similar images.
                return JsonResponse({'received': True})
            _, created = TikTokWebhookReceipt.objects.get_or_create(
                digest=hashlib.sha256(body).hexdigest(), defaults={'event': event_name, 'upload': upload})
            if not created:
                return JsonResponse({'received': True})
            target = EVENTS[event_name]
            if target == 'published':
                upload.status = 'published'
                upload.confirmation_source = 'webhook'
                upload.published_at = upload.published_at or timezone.now()
                upload.save(update_fields=['status', 'confirmation_source', 'published_at'])
            elif upload.status != 'published' and not (upload.status == 'failed' and target == 'inbox'):
                upload.status = target
                upload.save(update_fields=['status'])
        return JsonResponse({'received': True})
