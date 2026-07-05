from rest_framework.permissions import BasePermission

from .models import Client


class IsClient(BasePermission):
    message = "A registered client token is required."

    def has_permission(self, request, view):
        return isinstance(getattr(request, "user", None), Client)
