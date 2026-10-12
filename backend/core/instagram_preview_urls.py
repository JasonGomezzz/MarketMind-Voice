from django.urls import path
from apps.campaigns.tiktok_webhooks import TikTokWebhookView
from core.tiktok_verification import TikTokVerificationView
from apps.campaigns.instagram_publication import InstagramMediaView
from apps.campaigns.tiktok_publication import TikTokMediaView
from apps.authentication.views import AuthBrandContentView, MeView
from apps.authentication.token_views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from apps.authentication.instagram import (
    InstagramAccountsView, InstagramConnectView, InstagramCompleteView, InstagramDisconnectView, InstagramCallbackRelayView,
)
from apps.authentication.facebook import (
    FacebookPagesView, FacebookConnectView, FacebookCompleteView, FacebookDisconnectView, FacebookCallbackRelayView,
)
from apps.authentication.x_oauth import XAccountsView, XConnectView, XDisconnectView, XCallbackView
from apps.authentication.tiktok import TikTokAccountsView, TikTokConnectView, TikTokCompleteView, TikTokDisconnectView, TikTokCallbackView

# Only sign-in, social authorization and short-lived Instagram images are exposed.
urlpatterns = [
    path('api/tiktok/webhook/', TikTokWebhookView.as_view()),
    path('api/tiktok/media/<uuid:ticket>/', TikTokMediaView.as_view()),
    path('api/tiktok/media/<str:filename>', TikTokVerificationView.as_view()),
    path('api/auth/tiktok/accounts/', TikTokAccountsView.as_view()),
    path('api/auth/tiktok/accounts/<int:pk>/', TikTokDisconnectView.as_view()),
    path('api/auth/tiktok/connect/', TikTokConnectView.as_view()),
    path('api/auth/tiktok/complete/', TikTokCompleteView.as_view()),
    path('api/auth/tiktok/callback/', TikTokCallbackView.as_view()),
    path('api/auth/x/accounts/', XAccountsView.as_view()),
    path('api/auth/x/accounts/<int:pk>/', XDisconnectView.as_view()),
    path('api/auth/x/connect/', XConnectView.as_view()),
    path('api/auth/x/callback/', XCallbackView.as_view()),
    path('api/auth/facebook/pages/', FacebookPagesView.as_view()),
    path('api/auth/facebook/pages/<int:pk>/', FacebookDisconnectView.as_view()),
    path('api/auth/facebook/connect/', FacebookConnectView.as_view()),
    path('api/auth/facebook/complete/', FacebookCompleteView.as_view()),
    path('api/auth/facebook/callback/', FacebookCallbackRelayView.as_view()),
    path('settings', InstagramCallbackRelayView.as_view()),
    path('api/instagram/media/<uuid:ticket>/', InstagramMediaView.as_view()),
    path('api/auth/token/', CustomTokenObtainPairView.as_view()),
    path('api/auth/token/refresh/', TokenRefreshView.as_view()),
    path('api/auth/brand-content/', AuthBrandContentView.as_view()),
    path('api/auth/me/', MeView.as_view()),
    path('api/auth/instagram/accounts/', InstagramAccountsView.as_view()),
    path('api/auth/instagram/accounts/<int:pk>/', InstagramDisconnectView.as_view()),
    path('api/auth/instagram/connect/', InstagramConnectView.as_view()),
    path('api/auth/instagram/complete/', InstagramCompleteView.as_view()),
]
