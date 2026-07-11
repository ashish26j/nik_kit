from django.urls import path

from . import views

urlpatterns = [
    path("auth/register", views.register),
    path("auth/me", views.me),  # GET + PATCH
    path("auth/otp/request", views.otp_request),
    path("auth/otp/verify", views.otp_verify),
    path("auth/admin/login", views.admin_login),
]
