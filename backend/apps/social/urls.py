from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    MetaCallbackView,
    MetaCompleteView,
    MetaConnectView,
    PublicationViewSet,
    SocialConnectionViewSet,
)

router = SimpleRouter()
router.register(r"connections", SocialConnectionViewSet, basename="social-connection")
router.register(r"publications", PublicationViewSet, basename="publication")

urlpatterns = [
    path("meta/connect/", MetaConnectView.as_view(), name="meta-connect"),
    path("meta/callback/", MetaCallbackView.as_view(), name="meta-callback"),
    path("meta/complete/", MetaCompleteView.as_view(), name="meta-complete"),
] + router.urls
