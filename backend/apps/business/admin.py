from django.contrib import admin

from .models import BusinessClosure


@admin.register(BusinessClosure)
class BusinessClosureAdmin(admin.ModelAdmin):
    list_display = ("start_date", "end_date", "message", "created_by", "created_at")
    readonly_fields = ("created_by", "created_at")
