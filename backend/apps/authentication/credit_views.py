"""Persist credit requests and require an explicit, audited admin decision."""
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CreditRequest, User
from .permissions import IsMarketeroOrSuperAdmin, IsSuperAdmin


class CreditRequestSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='requester.email', read_only=True)
    nombre = serializers.CharField(source='requester.nombre', read_only=True)

    class Meta:
        model = CreditRequest
        fields = ['id', 'requester', 'email', 'nombre', 'status', 'created_at', 'resolved_at', 'resolved_by', 'credits_granted']
        read_only_fields = fields


class CreditRequestListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsMarketeroOrSuperAdmin]
    serializer_class = CreditRequestSerializer

    def get_queryset(self):
        return CreditRequest.objects.filter(requester=self.request.user).select_related('requester')

    def create(self, request, *args, **kwargs):
        # Lock the user to serialize duplicate requests even across processes.
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            item, created = CreditRequest.objects.get_or_create(requester=request.user, status='pending')
        return Response({'message': 'Solicitud enviada al superadmin.' if created else 'Ya tienes una solicitud pendiente.', 'data': self.get_serializer(item).data}, status=201 if created else 200)


class AdminCreditRequestListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = CreditRequestSerializer
    queryset = CreditRequest.objects.select_related('requester').all()


class CreditDecisionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    credits = serializers.IntegerField(min_value=1, max_value=10000, required=False)

    def validate(self, attrs):
        if attrs['status'] == 'approved' and 'credits' not in attrs:
            raise serializers.ValidationError({'credits': 'Indica cuántos créditos deseas añadir.'})
        if attrs['status'] == 'rejected' and 'credits' in attrs:
            raise serializers.ValidationError({'credits': 'No se pueden añadir créditos al rechazar.'})
        return attrs


class AdminCreditRequestDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request, pk):
        payload = CreditDecisionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        with transaction.atomic():
            item = get_object_or_404(CreditRequest.objects.select_for_update(), pk=pk)
            if item.status != 'pending':
                return Response({'message': 'Esta solicitud ya fue resuelta.'}, status=409)
            user = User.objects.select_for_update().get(pk=item.requester_id)
            if not user.is_active:
                return Response({'message': 'La cuenta está suspendida. Reactívala antes de resolver la solicitud.'}, status=400)
            item.status = payload.validated_data['status']
            item.credits_granted = payload.validated_data.get('credits', 0)
            if item.status == 'approved':
                User.objects.filter(pk=user.pk).update(tokens_disponibles=F('tokens_disponibles') + item.credits_granted)
            item.resolved_by = request.user
            item.resolved_at = timezone.now()
            item.save(update_fields=['status', 'credits_granted', 'resolved_by', 'resolved_at'])
        return Response({'message': 'Solicitud resuelta.', 'data': CreditRequestSerializer(item).data})
