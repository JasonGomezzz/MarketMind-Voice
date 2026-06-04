from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.campaigns.views import AdminAnalyticsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/campaigns/', include('apps.campaigns.urls')),
    path('api/admin/analytics/', AdminAnalyticsView.as_view(), name='admin-analytics'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
