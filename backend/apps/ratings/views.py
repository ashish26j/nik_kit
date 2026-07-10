"""M10 endpoints — client rates own completed order; admin reads all + summary."""
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response

from apps.accounts.auth import AdminTokenAuthentication, ClientTokenAuthentication
from apps.accounts.permissions import IsAdmin, IsClient
from apps.orders.models import Order

from .models import Rating


def _err(code, msg, status):
    return Response({"error": {"code": code, "message": msg}}, status=status)


def _serialize(r):
    return {
        "order_id": r.order_id,
        "stars": r.stars,
        "note": r.note,
        "created_at": r.created_at.isoformat(),
    }


def _validate(data):
    """Return (stars, note, error_message)."""
    try:
        stars = int(data.get("stars"))
    except (TypeError, ValueError):
        return None, None, "stars must be an integer 1-5"
    if not 1 <= stars <= 5:
        return None, None, "stars must be 1-5"
    note = data.get("note") or ""
    if len(note) > 100:
        return None, None, "note must be <= 100 characters"
    return stars, note, None


@api_view(["GET", "POST", "PATCH"])
@authentication_classes([ClientTokenAuthentication])
@permission_classes([IsClient])
def order_rating(request, pk):
    order = get_object_or_404(Order, pk=pk, client=request.user)
    existing = getattr(order, "rating", None)

    if request.method == "GET":
        if not existing:
            return _err("NOT_FOUND", "no rating yet", 404)
        return Response(_serialize(existing))

    # POST / PATCH — write
    if order.status != Order.Status.COMPLETED:
        return _err("STATE_CONFLICT", "order must be completed to rate", 409)
    if request.method == "POST" and existing:
        return _err("STATE_CONFLICT", "already rated; use PATCH to change", 409)
    if request.method == "PATCH" and not existing:
        return _err("NOT_FOUND", "no rating to edit", 404)

    stars, note, error = _validate(request.data)
    if error:
        return _err("VALIDATION_ERROR", error, 400)

    if existing:
        existing.stars, existing.note = stars, note
        existing.save()
        return Response(_serialize(existing))

    rating = Rating.objects.create(order=order, client=request.user, stars=stars, note=note)
    return Response(_serialize(rating), status=201)


@api_view(["GET"])
@authentication_classes([AdminTokenAuthentication])
@permission_classes([IsAdmin])
def admin_ratings(request):
    qs = Rating.objects.select_related("order")
    return Response([{**_serialize(r), "code": r.order.code} for r in qs])


@api_view(["GET"])
@authentication_classes([AdminTokenAuthentication])
@permission_classes([IsAdmin])
def admin_ratings_summary(request):
    agg = Rating.objects.aggregate(count=Count("id"), avg=Avg("stars"))
    distribution = {str(i): Rating.objects.filter(stars=i).count() for i in range(1, 6)}
    return Response({
        "count": agg["count"] or 0,
        "avg": round(agg["avg"], 2) if agg["avg"] is not None else None,
        "distribution": distribution,
    })
