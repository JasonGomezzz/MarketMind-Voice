from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    CampaignExportPDFView,
    CampaignVersionListView,
    CampaignVersionRestoreView,
    CampaignViewSet,
    EmailSentCallbackView,
    IaResultCallbackView,
    GeminiVoiceView,
)

router = SimpleRouter()
router.register(r"", CampaignViewSet, basename="campaign")

urlpatterns = [
    path("voice/synthesize/", GeminiVoiceView.as_view(), name="gemini-voice"),
    # Rutas de callback n8n → Django (sin JWT, antes del router para evitar colisiones)
    path("webhook/ia-result/", IaResultCallbackView.as_view(), name="ia-result-callback"),
    path("webhook/email-sent/", EmailSentCallbackView.as_view(), name="email-sent-callback"),
    # Historial de versiones (HU23)
    path("<int:campaign_id>/versions/", CampaignVersionListView.as_view(), name="campaign-versions"),
    path(
        "<int:campaign_id>/versions/<int:version_id>/restore/",
        CampaignVersionRestoreView.as_view(),
        name="campaign-version-restore",
    ),
    # Exportar PDF (HU25)
    path("<int:campaign_id>/export-pdf/", CampaignExportPDFView.as_view(), name="campaign-export-pdf"),
] + router.urls
