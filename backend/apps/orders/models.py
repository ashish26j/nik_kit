"""M05 — Cart & Order.

Prices are ALWAYS computed server-side (M05 R1). Order lines are immutable
snapshots (M05 R3) so later menu edits never rewrite history.
`Order.status` starts at PLACED; the full lifecycle machine is owned by M07 (P3) —
we size the field to hold those future states.
"""
import secrets
from decimal import Decimal

from django.db import models

from apps.accounts.models import Client
from apps.menu.models import Recipe


class Cart(models.Model):
    cart_key = models.CharField(max_length=40, unique=True, db_index=True)
    client = models.ForeignKey(
        Client, null=True, blank=True, on_delete=models.SET_NULL, related_name="carts"
    )
    is_open = models.BooleanField(default=True)  # closed once checked out
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def new(cls, client=None):
        return cls.objects.create(cart_key=secrets.token_hex(20), client=client)

    @property
    def subtotal(self):
        return sum((i.line_total for i in self.items.all()), Decimal("0.00"))

    def __str__(self):
        return f"cart {self.cart_key[:8]}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    recipe = models.ForeignKey(Recipe, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField(default=1)
    selected_options = models.JSONField(default=list)  # list[int] option ids
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def line_total(self):
        return self.unit_price * self.qty


class Order(models.Model):
    class Status(models.TextChoices):
        PLACED = "PLACED", "Placed"
        PAYMENT_SUBMITTED = "PAYMENT_SUBMITTED", "Payment submitted"
        PAYMENT_REJECTED = "PAYMENT_REJECTED", "Payment rejected"
        PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Payment confirmed"
        ACCEPTED = "ACCEPTED", "Accepted"
        PREPARING = "PREPARING", "Preparing"
        READY_FOR_PICKUP = "READY_FOR_PICKUP", "Ready for pickup"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class FulfilMode(models.TextChoices):
        ORDER_NOW = "ORDER_NOW", "Order now"
        ORDER_FOR_LATER = "ORDER_FOR_LATER", "Order for later"

    code = models.CharField(max_length=12, unique=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLACED)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fulfilment = models.CharField(max_length=12, default="PICKUP")
    # P6 order modes — chosen once per order (whole cart).
    fulfil_mode = models.CharField(
        max_length=16, choices=FulfilMode.choices, default=FulfilMode.ORDER_NOW
    )
    ready_by = models.DateTimeField(null=True, blank=True)       # NOW = created+1h
    scheduled_for = models.DateTimeField(null=True, blank=True)  # LATER = customer time
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def assign_code(self):
        self.code = f"NK-{self.id:04d}"
        self.save(update_fields=["code"])

    def __str__(self):
        return self.code or f"order#{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    recipe_name = models.CharField(max_length=120)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    qty = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    options_snapshot = models.JSONField(default=list)  # [{label, price_delta}]


class OrderEvent(models.Model):
    """Append-only lifecycle log (M07). One row per accepted transition."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    actor_label = models.CharField(max_length=60)  # "client:42" | "admin:nik" | "system"
    reason = models.CharField(max_length=140, blank=True)
    customer_stage = models.CharField(max_length=40, blank=True)  # headline stage or ""
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class PaymentIntent(models.Model):
    """UPI invoice for an order (M06). Amount frozen from order.total."""

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment_intent")
    upi_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    qr_payload = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class PaymentProof(models.Model):
    """Uploaded payment screenshot + the owner's decision (M06)."""

    class Decision(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REJECTED = "REJECTED", "Rejected"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="proofs")
    image = models.ImageField(upload_to="proofs/")
    is_current = models.BooleanField(default=True)
    decision = models.CharField(max_length=10, choices=Decision.choices, default=Decision.PENDING)
    decided_by = models.CharField(max_length=60, blank=True)
    reject_reason = models.CharField(max_length=140, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
