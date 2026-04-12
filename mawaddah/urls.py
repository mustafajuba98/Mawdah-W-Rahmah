from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("console/", include("apps.console.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("profiles/", include("apps.profiles.urls")),
    path("browse/", include("apps.matching.urls")),
    path("messages/", include("apps.messaging.urls")),
    path("moderation/", include("apps.moderation.urls")),
    path("", include("apps.accounts.urls_home")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
