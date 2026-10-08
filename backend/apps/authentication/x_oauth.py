"""Per-marketer X OAuth 2.0 authorization with a server-side PKCE verifier."""
import base64
import hashlib
import logging
import re
import secrets
from datetime import timedelta
from urllib.parse import urlencode, urlsplit

import requests
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import api_response
from .instagram import cipher
from .models import XAccount, XAuthorization
from .permissions import IsMarketero

logger = logging.getLogger(__name__)
CALLBACK_PATH = '/api/auth/x/callback/'
SCOPES = 'tweet.read users.read tweet.write media.write offline.access'


def allowed_origins():
    redirect = urlsplit(settings.X_REDIRECT_URI)
    public_origin = f'{redirect.scheme}://{redirect.netloc}' if redirect.netloc else ''
    origins = set()
    for value in (settings.FRONTEND_BASE_URL, public_origin):
        parsed = urlsplit(value)
        if (parsed.netloc and not parsed.username and not parsed.password and
                parsed.path in ('', '/') and not parsed.query and not parsed.fragment and
                (parsed.scheme == 'https' or parsed.scheme == 'http' and
                 parsed.hostname in ('localhost', '127.0.0.1'))):
            origins.add(f'{parsed.scheme}://{parsed.netloc}')
    return origins


def configured():
    redirect = urlsplit(settings.X_REDIRECT_URI)
    try:
        cipher()
    except (ValueError, TypeError):
        return False
    return bool(settings.X_CLIENT_ID and settings.X_CLIENT_SECRET and
                redirect.scheme == 'https' and redirect.netloc and
                not redirect.username and not redirect.password and
                redirect.path == CALLBACK_PATH and not redirect.query and not redirect.fragment)


def exchange(code, verifier):
    try:
        response = requests.post('https://api.x.com/2/oauth2/token',
            data={'grant_type': 'authorization_code', 'code': code,
                  'redirect_uri': settings.X_REDIRECT_URI, 'code_verifier': verifier},
            auth=(settings.X_CLIENT_ID, settings.X_CLIENT_SECRET), timeout=20,
            allow_redirects=False)
        if response.status_code != 200:
            raise ValueError('token')
        token_data = response.json()
        access = token_data.get('access_token')
        refresh = token_data.get('refresh_token')
        lifetime = token_data.get('expires_in')
        scopes = set(token_data.get('scope', '').split())
        if (not isinstance(access, str) or not access or
                not isinstance(refresh, str) or not refresh or
                type(lifetime) is not int or not 0 < lifetime <= 86400 or
                not set(SCOPES.split()).issubset(scopes)):
            raise ValueError('token')
        profile = requests.get('https://api.x.com/2/users/me',
            headers={'Authorization': f'Bearer {access}'}, timeout=20,
            allow_redirects=False)
        if profile.status_code != 200:
            raise ValueError('profile')
        user = profile.json().get('data', {})
        user_id, username = user.get('id'), user.get('username')
        if (not isinstance(user_id, str) or not re.fullmatch(r'\d{1,64}', user_id)
                or not isinstance(username, str) or not re.fullmatch(r'[A-Za-z0-9_]{1,15}', username)):
            raise ValueError('profile')
        return user_id, username, access, refresh, lifetime
    except (requests.RequestException, ValueError, TypeError, AttributeError, KeyError) as error:
        logger.warning('X authorization failed at stage=%s', 'profile' if str(error) == 'profile' else 'token')
        return None


def access_token_for(account):
    """Refresh under an account lock so rotating refresh tokens aren't reused."""
    with transaction.atomic():
        account = XAccount.objects.select_for_update().get(pk=account.pk, owner_id=account.owner_id)
        if account.expires_at > timezone.now() + timedelta(seconds=30):
            return cipher().decrypt(account.encrypted_access_token.encode()).decode()
        refresh = cipher().decrypt(account.encrypted_refresh_token.encode()).decode()
        response = requests.post('https://api.x.com/2/oauth2/token',
            data={'grant_type': 'refresh_token', 'refresh_token': refresh},
            auth=(settings.X_CLIENT_ID, settings.X_CLIENT_SECRET), timeout=20, allow_redirects=False)
        if response.status_code != 200:
            raise ValueError('Reconecta X para renovar la autorización.')
        values = response.json()
        access = values.get('access_token')
        renewed_refresh = values.get('refresh_token', refresh)
        lifetime = values.get('expires_in')
        if (not isinstance(access, str) or not access or not isinstance(renewed_refresh, str)
                or not renewed_refresh or type(lifetime) is not int or not 0 < lifetime <= 86400
                or 'scope' in values and not set(SCOPES.split()).issubset(values['scope'].split())):
            raise ValueError('Reconecta X para renovar la autorización.')
        account.encrypted_access_token = cipher().encrypt(access.encode()).decode()
        account.encrypted_refresh_token = cipher().encrypt(renewed_refresh.encode()).decode()
        account.expires_at = timezone.now() + timedelta(seconds=lifetime)
        account.save(update_fields=['encrypted_access_token', 'encrypted_refresh_token', 'expires_at'])
        return access


class XAccountsView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def get(self, request):
        accounts = [{'id': account.pk, 'username': account.username,
                     'expired': account.expires_at <= timezone.now(),
                     'can_refresh': bool(account.encrypted_refresh_token)}
                    for account in XAccount.objects.filter(owner=request.user).order_by('username')]
        return Response(api_response(True, 'Cuentas de X.', {'accounts': accounts, 'configured': configured()}))


class XDisconnectView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def delete(self, request, pk):
        deleted, _ = XAccount.objects.filter(owner=request.user, pk=pk).delete()
        if not deleted:
            return Response(api_response(False, 'Cuenta no encontrada.'), status=404)
        return Response(api_response(True, 'Conexión eliminada de NexoMark.'))


class XConnectView(APIView):
    permission_classes = [IsAuthenticated, IsMarketero]

    def post(self, request):
        if not configured():
            return Response(api_response(False, 'Falta configurar la conexión de X en el servidor.'), status=503)
        origin = request.headers.get('Origin') or settings.FRONTEND_BASE_URL.rstrip('/')
        if origin not in allowed_origins():
            return Response(api_response(False, 'Inicia la conexión desde NexoMark.'), status=403)
        state = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        XAuthorization.objects.filter(owner=request.user, expires_at__lt=timezone.now()).delete()
        XAuthorization.objects.create(owner=request.user,
            state_hash=hashlib.sha256(state.encode()).hexdigest(),
            encrypted_verifier=cipher().encrypt(verifier.encode()).decode(),
            token_version=request.user.token_version, return_origin=origin,
            expires_at=timezone.now() + timedelta(minutes=10))
        query = urlencode({'response_type': 'code', 'client_id': settings.X_CLIENT_ID,
            'redirect_uri': settings.X_REDIRECT_URI, 'scope': SCOPES,
            'state': state, 'code_challenge': challenge, 'code_challenge_method': 'S256'})
        return Response(api_response(True, 'Autoriza tu cuenta de X.',
            {'authorization_url': f'https://x.com/i/oauth2/authorize?{query}'}))


class XCallbackView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        state = request.query_params.get('state', '')
        code = request.query_params.get('code', '')
        denied = 'error' in request.query_params
        ticket = None
        if (isinstance(state, str) and 0 < len(state) <= 128 and
                (denied or isinstance(code, str) and 0 < len(code) <= 4096)):
            ticket = XAuthorization.objects.select_related('owner').filter(
                state_hash=hashlib.sha256(state.encode()).hexdigest(),
                expires_at__gt=timezone.now(), used=False).first()
        if (not ticket or ticket.return_origin not in allowed_origins() or
                not ticket.owner.is_active or ticket.owner.rol != 'marketero' or
                ticket.owner.token_version != ticket.token_version):
            response = HttpResponse('Autorización inválida o vencida. Vuelve a Configuración.', status=400)
        else:
            consumed = XAuthorization.objects.filter(pk=ticket.pk, used=False).update(used=True, encrypted_verifier='')
            outcome = 'error'
            if consumed and not denied and configured():
                try:
                    verifier = cipher().decrypt(ticket.encrypted_verifier.encode()).decode()
                    result = exchange(code, verifier)
                    if result:
                        user_id, username, access, refresh, lifetime = result
                        with transaction.atomic():
                            owner = type(ticket.owner).objects.select_for_update().get(pk=ticket.owner.pk)
                            if (owner.is_active and owner.rol == 'marketero' and
                                    owner.token_version == ticket.token_version):
                                XAccount.objects.update_or_create(owner=owner, x_user_id=user_id,
                                    defaults={'username': username,
                                              'encrypted_access_token': cipher().encrypt(access.encode()).decode(),
                                              'encrypted_refresh_token': cipher().encrypt(refresh.encode()).decode(),
                                              'expires_at': timezone.now() + timedelta(seconds=lifetime)})
                                outcome = 'connected'
                except Exception:
                    logger.warning('X authorization storage failed')
            response = HttpResponseRedirect(ticket.return_origin + '/settings#' +
                urlencode({'provider': 'x', 'state': state, 'result': outcome}))
        response['Cache-Control'] = 'no-store'
        response['Referrer-Policy'] = 'no-referrer'
        return response
