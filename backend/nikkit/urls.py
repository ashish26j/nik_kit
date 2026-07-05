"""Root URL config. Per-module routes get mounted under /api/v1/ as we build them."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
]
