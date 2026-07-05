from django.contrib import admin

from .models import Client, ClientToken


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("first_name", "phone", "email", "created_at")
    search_fields = ("first_name", "phone", "email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ClientToken)
class ClientTokenAdmin(admin.ModelAdmin):
    list_display = ("client", "created_at", "last_used_at")
    readonly_fields = ("token", "created_at", "last_used_at")
