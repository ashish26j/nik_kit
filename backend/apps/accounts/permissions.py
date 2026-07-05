from rest_framework.permissions import BasePermission

from .models import Client


class IsClient(BasePermission):
    message = "A registered client token is required."

    def has_permission(self, request, view):
        return isinstance(getattr(request, "user", None), Client)


class IsAdmin(BasePermission):
    message = "Admin (staff) token required."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user is not None and getattr(user, "is_staff", False))
