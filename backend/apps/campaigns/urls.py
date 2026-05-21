from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import CampaignViewSet, IaResultCallbackView

router = SimpleRouter()
router.register(r"", CampaignViewSet, basename="campaign")

urlpatterns = [
    # Ruta de callback n8n → Django (sin JWT, antes del router para evitar colisiones)
    path("webhook/ia-result/", IaResultCallbackView.as_view(), name="ia-result-callback"),
] + router.urls
