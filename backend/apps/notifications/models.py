"""M08 — Notification delivery log. M08 delivers what M06/M07 hand it; it never
decides whether an event happened (single source of truth stays with the engine).
"""
from django.db import models


class Notification(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        INAPP = "INAPP", "In-app"
        WHATSAPP = "WHATSAPP", "WhatsApp"  # stub adapter (no-op) — P4+
        PUSH = "PUSH", "Push"              # stub adapter (no-op) — later

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    event_type = models.CharField(max_length=40)
    channel = models.CharField(max_length=10, choices=Channel.choices)
    recipient_role = models.CharField(max_length=10)  # CLIENT | ADMIN
    recipient_ref = models.CharField(max_length=254, blank=True)  # email/phone
    order = models.ForeignKey(
        "orders.Order", null=True, blank=True,
        on_delete=models.CASCADE, related_name="notifications",
    )
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.QUEUED)
    error = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_type} → {self.channel}:{self.recipient_ref} [{self.status}]"
