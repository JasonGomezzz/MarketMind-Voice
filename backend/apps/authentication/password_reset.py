"""Recuperación por enlace de un solo uso sin revelar cuentas existentes."""
import logging
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

class RecoveryThrottle(AnonRateThrottle):
    scope = 'password_recovery'
    rate = '5/hour'

class RecoveryRequest(serializers.Serializer):
    email = serializers.EmailField()

class RecoveryConfirm(serializers.Serializer):
    uid = serializers.CharField(max_length=128)
    token = serializers.CharField(max_length=256)
    new_password = serializers.CharField(write_only=True, max_length=128)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [RecoveryThrottle]

    def post(self, request):
        serializer = RecoveryRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_user_model().objects.filter(email__iexact=serializer.validated_data['email'], is_active=True).first()
        if user and user.has_usable_password():
            params = urlencode({'uid': urlsafe_base64_encode(force_bytes(user.pk)), 'token': default_token_generator.make_token(user)})
            # Fragmento: no expone el token en logs HTTP ni Referer.
            url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/reset-password#{params}"
            try:
                send_mail('Restablece tu contraseña — NexoMark IA',
                          f'Abre este enlace para elegir una nueva contraseña:\n\n{url}\n\nVence en 30 minutos. Si no lo solicitaste, ignora este correo.',
                          settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
            except Exception:
                logger.error('No se pudo enviar el correo de recuperación; revisa la configuración SMTP.')
        return Response({'message': 'Si el correo corresponde a una cuenta activa, recibirás un enlace para restablecer tu contraseña.'})

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [RecoveryThrottle]

    @transaction.atomic
    def post(self, request):
        serializer = RecoveryConfirm(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            pk = urlsafe_base64_decode(data['uid']).decode()
            user = get_user_model().objects.select_for_update().get(pk=pk, is_active=True)
        except (ValueError, UnicodeDecodeError, OverflowError, get_user_model().DoesNotExist):
            return Response({'message': 'El enlace no es válido o ha vencido.'}, status=400)
        if not default_token_generator.check_token(user, data['token']):
            return Response({'message': 'El enlace no es válido o ha vencido.'}, status=400)
        try:
            validate_password(data['new_password'], user=user)
        except ValidationError as exc:
            return Response({'message': ' '.join(exc.messages)}, status=400)
        user.set_password(data['new_password'])
        user.token_version += 1
        user.save(update_fields=['password', 'token_version', 'fecha_actualizacion'])
        return Response({'message': 'Contraseña actualizada. Inicia sesión con tu nueva contraseña.'})
