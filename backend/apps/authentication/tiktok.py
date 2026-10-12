"""TikTok Web OAuth. The relay never exchanges a code without local authentication."""
import hashlib
import logging
import secrets
from datetime import timedelta
from urllib.parse import urlencode, urlsplit

import requests
from cryptography.fernet import InvalidToken
from django.conf import settings
from django.db import transaction
from django.db.utils import DatabaseError
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import api_response
from .instagram import cipher
from .models import TikTokAccount, TikTokAuthorization, User
from .permissions import IsMarketero

logger = logging.getLogger(__name__)
CALLBACK_PATH = '/api/auth/tiktok/callback/'
SCOPES = {'user.info.basic', 'video.upload'}
TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/'


def allowed_origins():
    origins = set()
    try:
        callback = urlsplit(settings.TIKTOK_REDIRECT_URI)
        public_origin = f'{callback.scheme}://{callback.netloc}' if callback.netloc else ''
        for value in (settings.FRONTEND_BASE_URL, public_origin):
            parsed = urlsplit(value)
            if (parsed.netloc and not parsed.username and not parsed.password and
                    parsed.path in ('', '/') and not parsed.query and not parsed.fragment and
                    (parsed.scheme == 'https' or parsed.scheme == 'http' and
                     parsed.hostname in ('localhost', '127.0.0.1'))):
                origin = f'{parsed.scheme}://{parsed.netloc}'
                if len(origin) <= 255:
                    origins.add(origin)
    except ValueError:
        pass
    return origins


def configured():
    try:
        redirect = urlsplit(settings.TIKTOK_REDIRECT_URI)
        cipher()
        return bool(settings.TIKTOK_CLIENT_KEY and settings.TIKTOK_CLIENT_SECRET and
                    len(settings.TIKTOK_REDIRECT_URI) < 512 and redirect.scheme == 'https' and
                    redirect.netloc and not redirect.username and not redirect.password and
                    redirect.path == CALLBACK_PATH and not redirect.query and not redirect.fragment)
    except (ValueError, TypeError):
        return False


def token_request(data):
    response = requests.post(TOKEN_URL, data={
        'client_key': settings.TIKTOK_CLIENT_KEY, 'client_secret': settings.TIKTOK_CLIENT_SECRET,
        **data}, timeout=20, allow_redirects=False)
    if response.status_code != 200:
        raise ValueError('TikTok rechazó la autorización.')
    values = response.json()
    if not isinstance(values, dict) or values.get('error'):
        raise ValueError('TikTok rechazó la autorización.')
    for field in ('access_token', 'refresh_token', 'open_id'):
        if not isinstance(values.get(field), str) or not 0 < len(values[field]) <= 4096:
            raise ValueError('Respuesta de autorización inválida.')
    if len(values['open_id']) > 128:
        raise ValueError('Identidad de TikTok inválida.')
    for field, maximum in (('expires_in', 86400), ('refresh_expires_in', 31536000)):
        if type(values.get(field)) is not int or not 0 < values[field] <= maximum:
            raise ValueError('Vigencia de autorización inválida.')
    if (str(values.get('token_type', '')).lower() != 'bearer' or
            not isinstance(values.get('scope'), str) or
            not SCOPES.issubset({scope.strip() for scope in values['scope'].split(',')})):
        raise ValueError('Faltan permisos de TikTok.')
    return values


def exchange(code):
    values = token_request({'grant_type': 'authorization_code', 'code': code,
                            'redirect_uri': settings.TIKTOK_REDIRECT_URI})
    response = requests.get('https://open.tiktokapis.com/v2/user/info/',
        params={'fields': 'open_id,display_name'},
        headers={'Authorization': f'Bearer {values["access_token"]}'},
        timeout=20, allow_redirects=False)
    profile = response.json()
    if response.status_code != 200 or not isinstance(profile, dict) or profile.get('error', {}).get('code') != 'ok':
        raise ValueError('No se pudo verificar la cuenta de TikTok.')
    user = profile.get('data', {}).get('user', {})
    name = user.get('display_name')
    if user.get('open_id') != values['open_id'] or not isinstance(name, str) or not 0 < len(name.strip()) <= 255:
        raise ValueError('Identidad de TikTok inválida.')
    return values, name.strip()


def token_fields(values):
    return {
        'encrypted_access_token': cipher().encrypt(values['access_token'].encode()).decode(),
        'encrypted_refresh_token': cipher().encrypt(values['refresh_token'].encode()).decode(),
        'expires_at': timezone.now() + timedelta(seconds=values['expires_in']),
        'refresh_expires_at': timezone.now() + timedelta(seconds=values['refresh_expires_in']),
        'scopes': sorted({scope.strip() for scope in values['scope'].split(',')}),
    }


def access_token_for(account):
    with transaction.atomic():
        current = TikTokAccount.objects.select_for_update().get(pk=account.pk, owner_id=account.owner_id)
        if current.expires_at > timezone.now() + timedelta(seconds=30):
            return cipher().decrypt(current.encrypted_access_token.encode()).decode()
        if current.refresh_expires_at <= timezone.now():
            raise ValueError('Reconecta TikTok para renovar la autorización.')
        refresh = cipher().decrypt(current.encrypted_refresh_token.encode()).decode()
        values = token_request({'grant_type': 'refresh_token', 'refresh_token': refresh})
        if values['open_id'] != current.open_id:
            raise ValueError('La renovación no corresponde a esta cuenta.')
        for key, value in token_fields(values).items():
            setattr(current, key, value)
        current.save(update_fields=['encrypted_access_token', 'encrypted_refresh_token',
                                    'expires_at', 'refresh_expires_at', 'scopes'])
        return values['access_token']


class TikTokAccountsView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def get(self, request):
        accounts = [{'id': account.pk, 'display_name': account.display_name,
                     'expired': account.expires_at <= timezone.now(),
                     'can_refresh': account.refresh_expires_at > timezone.now()}
                    for account in TikTokAccount.objects.filter(owner=request.user).order_by('display_name')]
        return Response(api_response(True, 'Cuentas de TikTok.', {'accounts': accounts, 'configured': configured()}))


class TikTokDisconnectView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def delete(self, request, pk):
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            deleted, _ = TikTokAccount.objects.filter(owner=request.user, pk=pk).delete()
            if not deleted:
                return Response(api_response(False, 'Cuenta no encontrada.'), status=404)
            # Cancel in-flight authorization too, so it cannot recreate the connection.
            TikTokAuthorization.objects.filter(owner=request.user).delete()
        return Response(api_response(True, 'Conexión local eliminada. Puedes revocar el acceso también desde TikTok.'))


class TikTokConnectView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def post(self, request):
        if not configured():
            return Response(api_response(False, 'Falta configurar TikTok en el servidor.'), status=503)
        origin = request.headers.get('Origin') or settings.FRONTEND_BASE_URL.rstrip('/')
        if origin not in allowed_origins():
            return Response(api_response(False, 'Inicia la conexión desde NexoMark.'), status=403)
        state = secrets.token_urlsafe(32)
        TikTokAuthorization.objects.filter(owner=request.user, expires_at__lt=timezone.now()).delete()
        TikTokAuthorization.objects.create(owner=request.user, token_version=request.user.token_version,
            state_hash=hashlib.sha256(state.encode()).hexdigest(), return_origin=origin,
            expires_at=timezone.now() + timedelta(minutes=10))
        query = urlencode({'client_key': settings.TIKTOK_CLIENT_KEY, 'response_type': 'code',
            'redirect_uri': settings.TIKTOK_REDIRECT_URI, 'scope': ','.join(sorted(SCOPES)),
            'state': state, 'disable_auto_auth': 1})
        return Response(api_response(True, 'Autoriza TikTok.',
            {'authorization_url': 'https://www.tiktok.com/v2/auth/authorize/?' + query}))


class TikTokCallbackView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        state, code = request.query_params.get('state', ''), request.query_params.get('code', '')
        denied = 'error' in request.query_params
        ticket = None
        if 0 < len(state) <= 128 and (denied or 0 < len(code) <= 4096):
            ticket = TikTokAuthorization.objects.select_related('owner').filter(
                state_hash=hashlib.sha256(state.encode()).hexdigest(), used=False,
                expires_at__gt=timezone.now()).first()
        if (not ticket or ticket.return_origin not in allowed_origins() or not ticket.owner.is_active or
                ticket.owner.rol != 'marketero' or ticket.owner.token_version != ticket.token_version):
            response = HttpResponse('Autorización inválida o vencida. Vuelve a Configuración.', status=400)
        else:
            values = {'provider': 'tiktok', 'state': state}
            values.update({'error': 'denied'} if denied else {'code': code})
            response = HttpResponseRedirect(ticket.return_origin + '/settings#' + urlencode(values))
        response['Cache-Control'] = 'no-store'
        response['Referrer-Policy'] = 'no-referrer'
        return response


class TikTokCompleteView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def post(self, request):
        state, code = request.data.get('state'), request.data.get('code')
        if (not isinstance(state, str) or not 0 < len(state) <= 128 or
                not isinstance(code, str) or not 0 < len(code) <= 4096):
            return Response(api_response(False, 'Autorización inválida.'), status=400)
        origin = request.headers.get('Origin') or settings.FRONTEND_BASE_URL.rstrip('/')
        ticket = TikTokAuthorization.objects.filter(owner=request.user,
            state_hash=hashlib.sha256(state.encode()).hexdigest(), used=False,
            token_version=request.user.token_version, return_origin=origin,
            expires_at__gt=timezone.now()).first()
        if not ticket or origin not in allowed_origins() or not configured():
            return Response(api_response(False, 'La autorización venció o pertenece a otra sesión.'), status=400)
        if not TikTokAuthorization.objects.filter(pk=ticket.pk, used=False).update(used=True):
            return Response(api_response(False, 'Autorización ya utilizada.'), status=400)
        try:
            values, name = exchange(code)
            with transaction.atomic():
                owner = User.objects.select_for_update().get(pk=request.user.pk)
                if (not owner.is_active or owner.rol != 'marketero' or owner.token_version != ticket.token_version or
                        not TikTokAuthorization.objects.filter(pk=ticket.pk).exists()):
                    raise ValueError('Sesión cambiada durante la autorización.')
                TikTokAccount.objects.update_or_create(owner=owner, open_id=values['open_id'],
                    defaults={'display_name': name, **token_fields(values)})
        except (requests.RequestException, ValueError, TypeError, AttributeError, KeyError, InvalidToken, DatabaseError):
            logger.warning('TikTok authorization failed; provider details omitted')
            return Response(api_response(False, 'No se pudo conectar TikTok. Revisa los permisos y vuelve a intentarlo.'), status=400)
        return Response(api_response(True, 'TikTok conectado. Conectar no envía ni publica contenido.'))
