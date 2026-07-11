"""M01 endpoints: register (create/re-identify client → Bearer token) and me."""
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail

from .auth import ClientTokenAuthentication
from .models import AdminToken, Client, ClientToken, EmailOtp
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


@api_view(["GET", "PATCH"])
@authentication_classes([ClientTokenAuthentication])
@permission_classes([IsClient])
def me(request):
    client = request.user
    if request.method == "PATCH":
        # Update first_name / email only; phone stays the identity (M01 R? / M13 R3).
        if "first_name" in request.data:
            client.first_name = (request.data.get("first_name") or "").strip()
        if "email" in request.data:
            email = (request.data.get("email") or "").strip()
            if "@" not in email:
                return Response(
                    {"error": {"code": "VALIDATION_ERROR", "message": "valid email required"}},
                    status=400,
                )
            client.email = email
        if not client.first_name:
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": "first_name required"}},
                status=400,
            )
        client.save()
    return Response(_client_payload(client))


@api_view(["POST"])
@permission_classes([AllowAny])
def otp_request(request):
    """Email a one-time code to restore an existing account on a new device."""
    email = (request.data.get("email") or "").strip()
    if "@" not in email:
        return Response(
            {"error": {"code": "VALIDATION_ERROR", "message": "valid email required"}}, status=400
        )
    client = Client.objects.filter(email=email).order_by("-created_at").first()
    if not client:
        return Response(
            {"error": {"code": "NOT_FOUND", "message": "no account for this email"}}, status=404
        )
    otp = EmailOtp.issue(email)
    send_mail(
        subject="[Nik_kiT] Your login code",
        message=f"Your Nik_kiT code is {otp.code} (valid 10 minutes).",
        from_email="noreply@nikkit.local",
        recipient_list=[email],
        fail_silently=True,
    )
    body = {"sent": True}
    if settings.DEBUG:  # dev convenience only — never returned when DEBUG=False
        body["dev_code"] = otp.code
    return Response(body)


@api_view(["POST"])
@permission_classes([AllowAny])
def otp_verify(request):
    """Verify the code → issue a client token for that account (restore)."""
    email = (request.data.get("email") or "").strip()
    code = (request.data.get("code") or "").strip()
    otp = (
        EmailOtp.objects.filter(email=email, code=code, used=False)
        .order_by("-created_at")
        .first()
    )
    if not otp or not otp.is_valid:
        return Response(
            {"error": {"code": "VALIDATION_ERROR", "message": "invalid or expired code"}},
            status=400,
        )
    otp.used = True
    otp.save(update_fields=["used"])
    client = Client.objects.filter(email=email).order_by("-created_at").first()
    if not client:
        return Response(
            {"error": {"code": "NOT_FOUND", "message": "no account"}}, status=404
        )
    token = ClientToken.issue(client)
    return Response({"user": _client_payload(client), "token": token.token})


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
