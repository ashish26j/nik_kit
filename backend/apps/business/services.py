"""Store-open logic (M09 §4a). Read publicly via /store/status; enforced at checkout."""
from datetime import timedelta

from django.utils import timezone

from .models import BusinessClosure


def current_closure(today=None):
    today = today or timezone.localdate()
    return (
        BusinessClosure.objects.filter(start_date__lte=today, end_date__gte=today)
        .order_by("end_date")
        .first()
    )


def is_open(today=None):
    return current_closure(today) is None


def store_status(today=None):
    today = today or timezone.localdate()
    closure = current_closure(today)
    if closure is None:
        return {"is_open": True, "message": None, "reopens_on": None}
    return {
        "is_open": False,
        "message": closure.message or "We're closed right now.",
        "reopens_on": (closure.end_date + timedelta(days=1)).isoformat(),
    }
