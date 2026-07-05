"""M07 — Order Tracking Engine. The ONLY writer of Order.status.

Validates every transition against the table, appends an immutable OrderEvent, and
emits a customer stage notification (via M08) on headline transitions.
"""
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.notifications.services import notify

from .models import Order, OrderEvent

S = Order.Status

# Legal transitions (M07 §5). Anything not listed is rejected.
ALLOWED = {
    S.PLACED: {S.PAYMENT_SUBMITTED, S.CANCELLED},
    S.PAYMENT_SUBMITTED: {S.PAYMENT_CONFIRMED, S.PAYMENT_REJECTED, S.CANCELLED},
    S.PAYMENT_REJECTED: {S.PAYMENT_SUBMITTED, S.CANCELLED},
    S.PAYMENT_CONFIRMED: {S.ACCEPTED},  # transient — engine moves straight on
    S.ACCEPTED: {S.PREPARING, S.CANCELLED},
    S.PREPARING: {S.READY_FOR_PICKUP, S.CANCELLED},
    S.READY_FOR_PICKUP: {S.COMPLETED, S.CANCELLED},
    S.COMPLETED: set(),
    S.CANCELLED: set(),
}

# The five headline stages the customer is notified about.
STAGE = {
    S.PLACED: "Order placed",
    S.ACCEPTED: "Order accepted",
    S.PREPARING: "In preparation",
    S.READY_FOR_PICKUP: "Ready to pick up",
    S.COMPLETED: "Order completed",
}


def _client_recipients(order):
    if order.client and order.client.email:
        return [("CLIENT", order.client.email)]
    return []


@transaction.atomic
def transition(order, to_status, actor_label, reason="", notify_client=True):
    frm = order.status
    if to_status not in ALLOWED.get(frm, set()):
        raise ValidationError(f"illegal transition {frm} → {to_status}")
    order.status = to_status
    order.save(update_fields=["status", "updated_at"])

    stage = STAGE.get(to_status, "")
    OrderEvent.objects.create(
        order=order, from_status=frm, to_status=to_status,
        actor_label=actor_label, reason=reason, customer_stage=stage,
    )
    if stage and notify_client:
        notify(
            f"ORDER_{to_status}", order=order, recipients=_client_recipients(order),
            channels=("EMAIL", "INAPP"),
            payload={"subject": stage, "message": f"{stage} — order {order.code}", "stage": stage},
        )
    return order


def record_placed(order, actor_label):
    """Log the initial PLACED event + notify (order is created at PLACED in checkout)."""
    OrderEvent.objects.create(
        order=order, from_status="", to_status=S.PLACED,
        actor_label=actor_label, customer_stage=STAGE[S.PLACED],
    )
    notify(
        "ORDER_PLACED", order=order, recipients=_client_recipients(order),
        channels=("EMAIL", "INAPP"),
        payload={"subject": "Order placed", "message": f"Order placed — {order.code}",
                 "stage": STAGE[S.PLACED]},
    )


def confirm_payment(order, admin_label):
    """Owner 'Yes': PAYMENT_SUBMITTED → PAYMENT_CONFIRMED → ACCEPTED (one customer notice)."""
    transition(order, S.PAYMENT_CONFIRMED, admin_label, notify_client=False)
    transition(order, S.ACCEPTED, admin_label)
    return order
