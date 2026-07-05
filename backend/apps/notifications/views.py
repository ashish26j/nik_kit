"""M08 — admin read of the delivery log."""
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response

from apps.accounts.auth import AdminTokenAuthentication
from apps.accounts.permissions import IsAdmin

from .models import Notification


@api_view(["GET"])
@authentication_classes([AdminTokenAuthentication])
@permission_classes([IsAdmin])
def notifications_list(request):
    qs = Notification.objects.all()
    order_id = request.query_params.get("order")
    if order_id:
        qs = qs.filter(order_id=order_id)
    return Response([
        {
            "event_type": n.event_type,
            "channel": n.channel,
            "recipient_role": n.recipient_role,
            "recipient_ref": n.recipient_ref,
            "status": n.status,
            "order": n.order_id,
        }
        for n in qs
    ])
