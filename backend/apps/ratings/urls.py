from django.urls import path

from . import views

urlpatterns = [
    path("orders/<int:pk>/rating", views.order_rating),
    path("admin/ratings", views.admin_ratings),
    path("admin/ratings/summary", views.admin_ratings_summary),
]
