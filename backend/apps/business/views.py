"""M09 — public store status + admin closure management."""
import datetime

from django.shortcuts import get_object_or_404
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.auth import AdminTokenAuthentication
from apps.accounts.permissions import IsAdmin

from .models import BusinessClosure
from .services import store_status as compute_store_status


def _serialize(c):
    return {
        "id": c.id,
        "start_date": c.start_date.isoformat(),
        "end_date": c.end_date.isoformat(),
        "message": c.message,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def store_status(request):
    """Public storefront banner + checkout pre-check."""
    return Response(compute_store_status())


@api_view(["GET", "POST"])
@authentication_classes([AdminTokenAuthentication])
@permission_classes([IsAdmin])
def closures(request):
    if request.method == "GET":
        return Response([_serialize(c) for c in BusinessClosure.objects.all()])

    # POST — create a closure (single day if end omitted).
    start = request.data.get("start_date")
    end = request.data.get("end_date") or start
    if not start:
        return Response(
            {"error": {"code": "VALIDATION_ERROR", "message": "start_date is required"}},
            status=400,
        )
    try:
        sd = datetime.date.fromisoformat(str(start))
        ed = datetime.date.fromisoformat(str(end))
    except ValueError:
        return Response(
            {"error": {"code": "VALIDATION_ERROR", "message": "dates must be YYYY-MM-DD"}},
            status=400,
        )
    if ed < sd:
        return Response(
            {"error": {"code": "VALIDATION_ERROR", "message": "end_date is before start_date"}},
            status=400,
        )
    c = BusinessClosure.objects.create(
        start_date=sd,
        end_date=ed,
        message=(request.data.get("message") or "")[:140],
        created_by=f"admin:{request.user.username}",
    )
    return Response(_serialize(c), status=201)


@api_view(["DELETE"])
@authentication_classes([AdminTokenAuthentication])
@permission_classes([IsAdmin])
def closure_detail(request, pk):
    get_object_or_404(BusinessClosure, pk=pk).delete()
    return Response(status=204)
