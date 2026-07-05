"""M01 endpoints: register (create/re-identify client → Bearer token) and me."""
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.contrib.auth import authenticate

from .auth import ClientTokenAuthentication
from .models import AdminToken, Client, ClientToken
from .permissions import IsClient
from .utils import normalize_phone


def _client_payload(client):
    return {
        "id": client.id,
        "first_name": client.first_name,
        "email": client.email,
        "phone": client.phone,
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Create or re-identify a client by phone; return the client + a token.

    No password (M01). Re-registering the same phone returns the same client.
    """
    first_name = (request.data.get("first_name") or "").strip()
    email = (request.data.get("email") or "").strip()
    phone = normalize_phone(request.data.get("phone"))

    fields = {}
    if not first_name:
        fields["first_name"] = "required"
    if "@" not in email:
        fields["email"] = "valid email required"
    if len(phone) < 8:
        fields["phone"] = "valid phone required"
    if fields:
        return Response(
            {"error": {"code": "VALIDATION_ERROR", "message": "invalid input", "fields": fields}},
            status=400,
        )

    client, created = Client.objects.get_or_create(
        phone=phone, defaults={"first_name": first_name, "email": email}
    )
    if not created:
        changed = False
        if first_name and client.first_name != first_name:
            client.first_name, changed = first_name, True
        if email and client.email != email:
            client.email, changed = email, True
        if changed:
            client.save()

    token = ClientToken.issue(client)
    return Response({"user": _client_payload(client), "token": token.token})


@api_view(["GET"])
@authentication_classes([ClientTokenAuthentication])
@permission_classes([IsClient])
def me(request):
    return Response(_client_payload(request.user))


@api_view(["POST"])
@permission_classes([AllowAny])
def admin_login(request):
    """Authenticate a Django staff user → issue an admin Bearer token (M01)."""
    user = authenticate(
        username=request.data.get("username"), password=request.data.get("password")
    )
    if not user or not user.is_staff:
        return Response(
            {"error": {"code": "AUTH_REQUIRED", "message": "invalid credentials"}},
            status=401,
        )
    token = AdminToken.issue(user)
    return Response({"token": token.token, "role": "ADMIN", "username": user.username})
