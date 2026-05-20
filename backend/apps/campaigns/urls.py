from rest_framework.routers import SimpleRouter

from .views import CampaignViewSet

router = SimpleRouter()
router.register(r"", CampaignViewSet, basename="campaign")

urlpatterns = router.urls
