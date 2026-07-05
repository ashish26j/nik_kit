from django.contrib import admin, messages

from . import transitions
from .models import Order, OrderEvent, OrderItem, PaymentProof


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("recipe_name", "unit_price", "qty", "line_total", "options_snapshot")
    can_delete = False


class PaymentProofInline(admin.TabularInline):
    model = PaymentProof
    extra = 0
    readonly_fields = ("image", "is_current", "decision", "decided_by", "reject_reason", "uploaded_at", "decided_at")
    can_delete = False


class OrderEventInline(admin.TabularInline):
    model = OrderEvent
    extra = 0
    readonly_fields = ("from_status", "to_status", "actor_label", "customer_stage", "reason", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("code", "client", "status", "total", "created_at")
    list_filter = ("status", "fulfilment")
    search_fields = ("code", "client__phone", "client__first_name")
    readonly_fields = ("code", "client", "subtotal", "total", "status", "created_at", "updated_at")
    inlines = [OrderItemInline, PaymentProofInline, OrderEventInline]
    actions = ["confirm_payment", "start_preparing", "mark_ready", "mark_completed"]

    # Owner controls — drive the M07 lifecycle from Django admin (custom console = P4).
    def _apply(self, request, queryset, fn, label):
        ok = 0
        for order in queryset:
            try:
                fn(order, f"admin:{request.user.username}")
                ok += 1
            except Exception as e:  # noqa: BLE001
                self.message_user(request, f"{order.code}: {e}", level=messages.ERROR)
        if ok:
            self.message_user(request, f"{label}: {ok} order(s).", level=messages.SUCCESS)

    @admin.action(description="Confirm payment (→ ACCEPTED)")
    def confirm_payment(self, request, queryset):
        self._apply(request, queryset, transitions.confirm_payment, "Confirmed")

    @admin.action(description="Start preparing")
    def start_preparing(self, request, queryset):
        self._apply(request, queryset,
                    lambda o, a: transitions.transition(o, Order.Status.PREPARING, a), "Preparing")

    @admin.action(description="Mark ready for pickup")
    def mark_ready(self, request, queryset):
        self._apply(request, queryset,
                    lambda o, a: transitions.transition(o, Order.Status.READY_FOR_PICKUP, a), "Ready")

    @admin.action(description="Mark completed")
    def mark_completed(self, request, queryset):
        self._apply(request, queryset,
                    lambda o, a: transitions.transition(o, Order.Status.COMPLETED, a), "Completed")
