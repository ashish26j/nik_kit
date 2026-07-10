from django.contrib import admin

from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("order", "stars", "note", "client", "created_at")
    list_filter = ("stars",)
    search_fields = ("order__code", "client__phone")
    readonly_fields = ("order", "client", "stars", "note", "created_at", "updated_at")
