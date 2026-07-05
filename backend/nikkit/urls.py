"""Root URL config. Per-module routes get mounted under /api/v1/ as we build them."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.menu.urls")),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.orders.urls")),
]

# Serve uploaded recipe images from the media volume during dev.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

