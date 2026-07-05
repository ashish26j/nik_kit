from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("recipe_name", "unit_price", "qty", "line_total", "options_snapshot")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("code", "client", "status", "total", "created_at")
    list_filter = ("status", "fulfilment")
    search_fields = ("code", "client__phone", "client__first_name")
    readonly_fields = ("code", "client", "subtotal", "total", "created_at", "updated_at")
    inlines = [OrderItemInline]
