from django.urls import path

from . import views

urlpatterns = [
    path("sections", views.sections),
    path("sections/<slug:slug>/recipes", views.section_recipes),
    path("recipes/<int:pk>", views.recipe_detail),
    path("store/status", views.store_status),
]
