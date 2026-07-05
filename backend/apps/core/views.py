"""Core, cross-cutting endpoints. P0: a health check that proves app → db works."""
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Report service liveness and whether the DB is reachable (the P0 gate slice)."""
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:  # noqa: BLE001 — any DB error means "not connected" here
        db_ok = False

    return Response(
        {
            "status": "ok" if db_ok else "degraded",
            "service": "nikkit-app",
            "db": "connected" if db_ok else "unreachable",
        }
    )
