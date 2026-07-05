"""DRF authentication for the client Bearer token (M01)."""
from django.utils import timezone
from rest_framework import authentication, exceptions

from .models import ClientToken


class ClientTokenAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        parts = request.headers.get("Authorization", "").split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None  # no/!Bearer → let permission layer decide
        try:
            ct = ClientToken.objects.select_related("client").get(token=parts[1])
        except ClientToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token")
        ct.last_used_at = timezone.now()
        ct.save(update_fields=["last_used_at"])
        return (ct.client, ct)  # request.user = Client, request.auth = ClientToken
