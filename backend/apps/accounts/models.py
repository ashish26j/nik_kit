"""M01 — lightweight client identity.

Design note (deviation from M01's single-table `User`): we keep Django's built-in
User for ADMIN/staff (it powers Django admin), and model the CUSTOMER as a separate
lightweight `Client` with **no password** — phone is the identity. This kick-starts
customers with zero auth overhead and needs no AUTH_USER_MODEL change.
"""
import secrets

from django.db import models


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
