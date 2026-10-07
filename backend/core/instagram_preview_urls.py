from django.urls import path
from apps.campaigns.instagram_publication import InstagramMediaView
from apps.authentication.views import AuthBrandContentView, MeView
from apps.authentication.token_views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from apps.authentication.instagram import (
    InstagramAccountsView, InstagramConnectView, InstagramCompleteView, InstagramDisconnectView, InstagramCallbackRelayView,
)
from apps.authentication.facebook import (
    FacebookPagesView, FacebookConnectView, FacebookCompleteView, FacebookDisconnectView, FacebookCallbackRelayView,
)

# Only sign-in, social authorization and short-lived Instagram images are exposed.
urlpatterns = [
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
