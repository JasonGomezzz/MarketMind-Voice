from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import CampaignViewSet, EmailSentCallbackView, IaResultCallbackView

router = SimpleRouter()
router.register(r"", CampaignViewSet, basename="campaign")

urlpatterns = [
    # Rutas de callback n8n → Django (sin JWT, antes del router para evitar colisiones)
    path("webhook/ia-result/", IaResultCallbackView.as_view(), name="ia-result-callback"),
    path("webhook/email-sent/", EmailSentCallbackView.as_view(), name="email-sent-callback"),
] + router.urls
