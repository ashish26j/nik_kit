from django.urls import path

from . import views

urlpatterns = [
    path("store/status", views.store_status),
    path("admin/closures", views.closures),
    path("admin/closures/<int:pk>", views.closure_detail),
]
