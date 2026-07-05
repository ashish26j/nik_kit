from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("event_type", "channel", "recipient_role", "recipient_ref", "status", "created_at")
    list_filter = ("channel", "status", "recipient_role")
    search_fields = ("event_type", "recipient_ref")
    readonly_fields = [f.name for f in Notification._meta.fields]
