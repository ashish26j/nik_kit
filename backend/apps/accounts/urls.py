from django.urls import path

from . import views

urlpatterns = [
    path("auth/register", views.register),
    path("auth/me", views.me),
    path("auth/admin/login", views.admin_login),
]
