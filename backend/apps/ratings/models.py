"""M10 — customer satisfaction rating: 1–5 stars + optional <=100-char note.

One per completed order, by its owner. NOT the healthiness engine (M11) — no shared
schema, no coupling. Purely informational; never affects order state or price.
"""
from django.db import models

from apps.accounts.models import Client
from apps.orders.models import Order


class Rating(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="rating")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="ratings")
    stars = models.PositiveSmallIntegerField()  # 1..5 (validated in the view)
    note = models.CharField(max_length=100, blank=True)  # optional, <=100 chars
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.code}: {self.stars}★"
