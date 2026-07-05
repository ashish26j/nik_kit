"""M08 — the notify() interface. Callers (M06/M07) say what/whom; we decide how.

Channels are pluggable: EMAIL (live, console backend in dev) + INAPP (client polls
tracking) now; WHATSAPP/PUSH are stub adapters that plug in with no caller changes.
"""
from django.core.mail import send_mail
from django.utils import timezone

from .models import Notification


def notify(event_type, order=None, recipients=None, channels=("EMAIL", "INAPP"), payload=None):
    """recipients: list of (role, ref). Idempotent per (order, event, channel, ref)."""
    payload = payload or {}
    created = []
    for role, ref in recipients or []:
        for ch in channels:
            if order and Notification.objects.filter(
                order=order, event_type=event_type, channel=ch, recipient_ref=ref
            ).exists():
                continue  # M08 R2: no duplicate stage notice on a retried transition
            n = Notification.objects.create(
                event_type=event_type, channel=ch, recipient_role=role,
                recipient_ref=ref, order=order, payload=payload,
            )
            _deliver(n)
            created.append(n)
    return created


def _deliver(n):
    """Best-effort send. A failure is logged and NEVER blocks the caller (M08 R3)."""
    try:
        if n.channel == Notification.Channel.EMAIL:
            send_mail(
                subject=f"[Nik_kiT] {n.payload.get('subject') or n.event_type}",
                message=n.payload.get("message") or n.event_type,
                from_email="noreply@nikkit.local",
                recipient_list=[n.recipient_ref],
                fail_silently=False,
            )
        # INAPP: nothing to push — the client polls /orders/{id}/tracking.
        # WHATSAPP / PUSH: stub adapters (no-op) until their channels go live.
        n.status = Notification.Status.SENT
        n.sent_at = timezone.now()
    except Exception as e:  # noqa: BLE001
        n.status = Notification.Status.FAILED
        n.error = str(e)[:200]
    n.save(update_fields=["status", "sent_at", "error"])
