"""Serve only the explicitly configured TikTok ownership file, never a directory."""
from pathlib import Path
import re

from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class TikTokVerificationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, filename):
        configured = settings.TIKTOK_VERIFICATION_FILE
        if not configured or not re.fullmatch(r'tiktok[A-Za-z0-9]{16,128}\.txt', filename):
            raise Http404
        source = Path(configured)
        if source.name != filename:
            raise Http404
        try:
            if source.is_symlink() or not source.is_file() or not 0 < source.stat().st_size <= 4096:
                raise Http404
            content = source.read_bytes()
            if len(content) > 4096:
                raise Http404
        except OSError:
            raise Http404 from None
        response = HttpResponse(content, content_type='text/plain; charset=utf-8')
        response['Cache-Control'] = 'no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
