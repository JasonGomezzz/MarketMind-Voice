"""Instagram Login: per-user authorization; never return or log credentials."""
import hashlib
import logging
import secrets
from datetime import timedelta
from urllib.parse import urlencode, urlsplit

import requests
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import api_response
from .models import InstagramAccount, InstagramAuthorization
from .permissions import IsMarketero

SCOPES = {'instagram_business_basic', 'instagram_business_content_publish'}
logger = logging.getLogger(__name__)
FAILURE_MESSAGES = {
    'code_exchange': 'Instagram no aceptó el código de autorización. Comprueba la clave de la app y la URL de retorno en Meta, y vuelve a conectar.',
    'permissions': 'Instagram no concedió los permisos de acceso básico y publicación. Vuelve a conectar y autoriza ambos.',
    'extend_token': 'No se pudo ampliar la autorización de Instagram. Comprueba la clave secreta de la app de Instagram.',
    'profile': 'No se pudo verificar el perfil de Instagram con la autorización recibida.',
    'identity': 'El perfil recibido no coincide con la cuenta que autorizó Instagram.',
    'expiry': 'Instagram devolvió una autorización con vencimiento inválido.',
}


class InstagramError(Exception):
    """Safe boundary: upstream exceptions must never expose token-bearing URLs."""

    def __init__(self, stage='unknown'):
        self.stage = stage if stage in FAILURE_MESSAGES else 'unknown'
        super().__init__('Instagram authorization failed')


def cipher():
    return Fernet(settings.SOCIAL_TOKEN_ENCRYPTION_KEY.encode())


def configured():
    redirect = urlsplit(settings.INSTAGRAM_REDIRECT_URI)
    frontend = urlsplit(settings.INSTAGRAM_FRONTEND_ORIGIN or settings.FRONTEND_BASE_URL)
    try:
        cipher()
    except (ValueError, TypeError):
        return False
    return bool(settings.INSTAGRAM_APP_ID and settings.INSTAGRAM_APP_SECRET
                and redirect.scheme == 'https' and redirect.netloc
                and (redirect.scheme, redirect.netloc) == (frontend.scheme, frontend.netloc)
                and redirect.path == '/settings' and not redirect.query and not redirect.fragment)


def allowed_return_origins():
    """Only configured origins, never arbitrary browser-supplied return URLs."""
    origins = set()
    for value in (settings.INSTAGRAM_FRONTEND_ORIGIN, settings.FRONTEND_BASE_URL):
        parsed = urlsplit(value)
        if (parsed.netloc and not parsed.username and not parsed.password
                and not parsed.query and not parsed.fragment and parsed.path in ('', '/')
                and (parsed.scheme == 'https' or
                     parsed.scheme == 'http' and parsed.hostname in ('localhost', '127.0.0.1'))):
            origins.add(f'{parsed.scheme}://{parsed.netloc}')
    redirect = urlsplit(settings.INSTAGRAM_REDIRECT_URI)
    if redirect.scheme == 'https' and redirect.netloc:
        origins.add(f'{redirect.scheme}://{redirect.netloc}')
    return origins


class InstagramCallbackRelayView(APIView):
    """Bridge an HTTPS callback to the initiating origin without moving its JWT."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        state = request.query_params.get('state', '')
        code = request.query_params.get('code', '')
        denied = 'error' in request.query_params
        if not state or len(state) > 128 or (not denied and (not code or len(code) > 4096)):
            response = HttpResponse('Autorización inválida. Vuelve a Configuración y conecta Instagram.', status=400)
        else:
            ticket = InstagramAuthorization.objects.select_related('owner').filter(
                state_hash=hashlib.sha256(state.encode()).hexdigest(),
                expires_at__gt=timezone.now(), used=False).first()
            if (not ticket or ticket.return_origin not in allowed_return_origins()
                    or not ticket.owner.is_active or ticket.owner.rol != 'marketero'
                    or ticket.owner.token_version != ticket.token_version):
                response = HttpResponse('La autorización venció. Vuelve a Configuración y conecta Instagram.', status=400)
            else:
                # Fragment values are not sent to the local HTTP server or referrers.
                values = {'state': state, 'error': 'access_denied'} if denied else {'state': state, 'code': code}
                response = HttpResponseRedirect(ticket.return_origin + '/settings#' + urlencode(values))
        response['Cache-Control'] = 'no-store'
        response['Referrer-Policy'] = 'no-referrer'
        return response


def exchange_code(code):
    stage = 'code_exchange'
    try:
        response = requests.post('https://api.instagram.com/oauth/access_token', data={
            'client_id': settings.INSTAGRAM_APP_ID, 'client_secret': settings.INSTAGRAM_APP_SECRET,
            'grant_type': 'authorization_code', 'redirect_uri': settings.INSTAGRAM_REDIRECT_URI,
            'code': code,
        }, timeout=20)
        response.raise_for_status()
        short = response.json()
        if 'data' in short:
            short = short['data'][0]
        stage = 'permissions'
        permissions = short.get('permissions', [])
        if isinstance(permissions, str):
            permissions = permissions.split(',')
        if not SCOPES.issubset(set(permissions)):
            raise InstagramError(stage)
        # Verify the actual token owner through /me, not by comparing identifiers
        # from two different OAuth/Graph response schemas.
        stage = 'profile'
        authorized_profile = fetch_profile(short['access_token'])
        stage = 'extend_token'
        response = requests.get('https://graph.instagram.com/access_token', params={
            'grant_type': 'ig_exchange_token', 'client_secret': settings.INSTAGRAM_APP_SECRET,
            'access_token': short['access_token'],
        }, timeout=20)
        response.raise_for_status()
        token = response.json()
        stage = 'profile'
        profile = fetch_profile(token['access_token'])
        stage = 'identity'
        if profile['user_id'] != authorized_profile['user_id']:
            raise InstagramError(stage)
        stage = 'expiry'
        lifetime = int(token['expires_in'])
        if lifetime <= 0 or lifetime > 90 * 86400:
            raise InstagramError(stage)
        return profile, token['access_token'], lifetime
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        raise InstagramError(stage) from None


def fetch_profile(token):
    response = requests.get('https://graph.instagram.com/me', params={
        'fields': 'user_id,username',
    }, headers={'Authorization': f'Bearer {token}'}, timeout=20)
    response.raise_for_status()
    profile = response.json()
    if not isinstance(profile, dict):
        raise InstagramError('profile')
    account_id = profile.get('user_id') or profile.get('id')
    username = profile.get('username')
    if (not isinstance(account_id, (str, int)) or isinstance(account_id, bool)
            or not str(account_id).strip() or len(str(account_id)) > 64
            or not isinstance(username, str) or not username.strip() or len(username) > 150):
        raise InstagramError('profile')
    return {'user_id': str(account_id), 'username': username}


class InstagramAccountsView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def get(self, request):
        accounts = [{
            'id': account.pk, 'username': account.username,
            'expires_at': account.expires_at.isoformat(),
            'expired': account.expires_at <= timezone.now(),
        } for account in InstagramAccount.objects.filter(owner=request.user).order_by('username')]
        return Response(api_response(True, 'Cuentas de Instagram.', {
            'accounts': accounts, 'configured': configured(),
        }))


class InstagramDisconnectView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def delete(self, request, pk):
        deleted, _ = InstagramAccount.objects.filter(owner=request.user, pk=pk).delete()
        if not deleted:
            return Response(api_response(False, 'Cuenta no encontrada.'), status=404)
        return Response(api_response(True, 'Conexión eliminada de NexoMark.'))


class InstagramConnectView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def post(self, request):
        if not configured():
            return Response(api_response(False, 'Falta configurar la conexión segura de Instagram en el servidor.'), status=503)
        origin = request.headers.get('Origin')
        if origin and origin not in allowed_return_origins():
            return Response(api_response(False, 'Inicia la conexión desde la web configurada de NexoMark.'), status=403)
        # Remove stale tickets for this owner; never delete tickets of other users.
        InstagramAuthorization.objects.filter(owner=request.user, expires_at__lt=timezone.now()).delete()
        state = secrets.token_urlsafe(32)
        InstagramAuthorization.objects.create(owner=request.user,
            state_hash=hashlib.sha256(state.encode()).hexdigest(),
            token_version=request.user.token_version,
            return_origin=origin or (settings.INSTAGRAM_FRONTEND_ORIGIN or settings.FRONTEND_BASE_URL).rstrip('/'),
            expires_at=timezone.now() + timedelta(minutes=10))
        query = urlencode({'client_id': settings.INSTAGRAM_APP_ID,
            'redirect_uri': settings.INSTAGRAM_REDIRECT_URI, 'response_type': 'code',
            'scope': ','.join(sorted(SCOPES)), 'state': state,
            'enable_fb_login': '0', 'force_authentication': '1'})
        return Response(api_response(True, 'Autoriza tu cuenta en Instagram.', {
            'authorization_url': f'https://www.instagram.com/oauth/authorize?{query}'}))


class InstagramCompleteView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def post(self, request):
        if not configured():
            return Response(api_response(False, 'La conexión de Instagram no está configurada.'), status=503)
        state, code = request.data.get('state'), request.data.get('code')
        if not isinstance(state, str) or not isinstance(code, str) or not state or not code or len(state) > 128 or len(code) > 4096:
            return Response(api_response(False, 'Autorización inválida.'), status=400)
        # Atomically consume the ticket, scoped to this authenticated marketer.
        consumed = InstagramAuthorization.objects.filter(
            owner=request.user, state_hash=hashlib.sha256(state.encode()).hexdigest(),
            token_version=request.user.token_version, expires_at__gt=timezone.now(), used=False,
        ).update(used=True)
        if not consumed:
            return Response(api_response(False, 'Autorización vencida o inválida. Vuelve a conectar Instagram.'), status=400)
        try:
            profile, token, lifetime = exchange_code(code)
            encrypted = cipher().encrypt(token.encode()).decode()
        except InstagramError as error:
            # Only a static stage label is logged; never the exception/response/URL.
            logger.warning('Instagram authorization failed at stage=%s', error.stage)
            return Response(api_response(False, FAILURE_MESSAGES.get(error.stage,
                'No se pudo autorizar Instagram. Revisa los permisos y vuelve a conectar.')), status=502)
        # Serialize completion against account suspension/token revocation.
        with transaction.atomic():
            owner = type(request.user).objects.select_for_update().get(pk=request.user.pk)
            if not owner.is_active or owner.rol != 'marketero' or owner.token_version != request.user.token_version:
                return Response(api_response(False, 'La sesión ya no es válida.'), status=403)
            account, _ = InstagramAccount.objects.update_or_create(
                owner=owner, instagram_user_id=str(profile['user_id']), defaults={
                    'username': profile['username'], 'encrypted_token': encrypted,
                    'expires_at': timezone.now() + timedelta(seconds=lifetime),
                })
        return Response(api_response(True, 'Instagram conectado.', {
            'account': {'id': account.pk, 'username': account.username}}))
