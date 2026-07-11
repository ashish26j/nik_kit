"""M01 — lightweight client identity.

Design note (deviation from M01's single-table `User`): we keep Django's built-in
User for ADMIN/staff (it powers Django admin), and model the CUSTOMER as a separate
lightweight `Client` with **no password** — phone is the identity. This kick-starts
customers with zero auth overhead and needs no AUTH_USER_MODEL change.
"""
import random
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Client(models.Model):
    first_name = models.CharField(max_length=60)
    email = models.EmailField()
    phone = models.CharField(max_length=20, unique=True)  # normalized; identity key
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    # DRF sets request.user = this instance; some internals probe is_authenticated.
    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f"{self.first_name} ({self.phone})"


class ClientToken(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="tokens")
    token = models.CharField(max_length=40, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def issue(cls, client):
        return cls.objects.create(client=client, token=secrets.token_hex(20))

    def __str__(self):
        return f"token:{self.client.phone}"


class EmailOtp(models.Model):
    """One-time code emailed to restore a client account on a new device (M01 R7)."""

    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def issue(cls, email, minutes=10):
        code = f"{random.randint(0, 999999):06d}"
        return cls.objects.create(
            email=email, code=code, expires_at=timezone.now() + timedelta(minutes=minutes)
        )

    @property
    def is_valid(self):
        return (not self.used) and timezone.now() < self.expires_at


class AdminToken(models.Model):
    """Bearer token for a Django staff user (M01 admin login)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_tokens"
    )
    token = models.CharField(max_length=40, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def issue(cls, user):
        return cls.objects.create(user=user, token=secrets.token_hex(20))

    def __str__(self):
        return f"admintoken:{self.user}"
