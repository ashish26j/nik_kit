"""M05 cart & order endpoints.

Cart is identified by an opaque `cart_key` the client holds (header `X-Cart-Key`
or body/query `cart_key`) — works for web/mobile without cookies. Anon can build a
cart; checkout requires a client token (M01).
"""
import os
import secrets
from datetime import timedelta

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.auth import AdminTokenAuthentication, ClientTokenAuthentication
from apps.accounts.permissions import IsAdmin, IsClient
from apps.business.services import is_open as store_is_open
from apps.menu.models import Recipe
from apps.notifications.services import notify

from . import transitions
from .models import Cart, CartItem, Order, OrderItem, PaymentIntent, PaymentProof
from .services import option_labels, validate_and_price


# --- helpers -----------------------------------------------------------------
def err(code, message, status, **extra):
    body = {"code": code, "message": message}
    body.update(extra)
    return Response({"error": body}, status=status)


def _msg(exc):
    d = exc.detail
    return str(d[0]) if isinstance(d, list) else str(d)


def _cart_key(request):
    return (
        request.headers.get("X-Cart-Key")
        or request.data.get("cart_key")
        or request.query_params.get("cart_key")
    )


def _resolve_cart(request):
    key = _cart_key(request)
    return Cart.objects.filter(cart_key=key, is_open=True).first() if key else None


def serialize_cart(cart):
    items = []
    for it in cart.items.select_related("recipe").all():
        items.append({
            "id": it.id,
            "recipe_id": it.recipe_id,
            "recipe_name": it.recipe.name,
            "qty": it.qty,
            "unit_price": str(it.unit_price),
            "line_total": str(it.line_total),
            "options": option_labels(it.recipe, it.selected_options),
        })
    sub = cart.subtotal
    return {"cart_key": cart.cart_key, "items": items,
            "subtotal": str(sub), "total": str(sub)}


def serialize_order(order):
    return {
        "id": order.id,
        "code": order.code,
        "status": order.status,
        "subtotal": str(order.subtotal),
        "total": str(order.total),
        "fulfilment": order.fulfilment,
        "fulfil_mode": order.fulfil_mode,
        "ready_by": order.ready_by.isoformat() if order.ready_by else None,
        "scheduled_for": order.scheduled_for.isoformat() if order.scheduled_for else None,
        "note": order.note,
        "items": [{
            "recipe_name": i.recipe_name, "qty": i.qty,
            "unit_price": str(i.unit_price), "line_total": str(i.line_total),
            "options": i.options_snapshot,
        } for i in order.items.all()],
        "created_at": order.created_at.isoformat(),
    }


# --- cart --------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def cart_add(request):
    cart = _resolve_cart(request) or Cart.new()
    recipe = get_object_or_404(Recipe, pk=request.data.get("recipe_id"))
    if not recipe.is_orderable:  # not AVAILABLE, or ordering_enabled off (M03 R9)
        return err("RECIPE_UNAVAILABLE", f"{recipe.name} is not available for ordering", 409)
    try:
        unit, chosen = validate_and_price(recipe, request.data.get("selected_options"))
    except ValidationError as e:
        return err("VALIDATION_ERROR", _msg(e), 400)
    qty = max(1, int(request.data.get("qty") or 1))
    CartItem.objects.create(
        cart=cart, recipe=recipe, qty=qty,
        selected_options=[o.id for o in chosen], unit_price=unit,
    )
    return Response(serialize_cart(cart), status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def cart_view(request):
    cart = _resolve_cart(request)
    if not cart:
        return err("NOT_FOUND", "cart not found", 404)
    return Response(serialize_cart(cart))


@api_view(["PATCH", "DELETE"])
@permission_classes([AllowAny])
def cart_item(request, pk):
    cart = _resolve_cart(request)
    if not cart:
        return err("NOT_FOUND", "cart not found", 404)
    item = get_object_or_404(CartItem, pk=pk, cart=cart)
    if request.method == "DELETE":
        item.delete()
        return Response(serialize_cart(cart))
    if "qty" in request.data:
        q = int(request.data["qty"])
        if q < 1:
            return err("VALIDATION_ERROR", "qty must be >= 1", 400)
        item.qty = q
    if "selected_options" in request.data:
        try:
            unit, chosen = validate_and_price(item.recipe, request.data["selected_options"])
        except ValidationError as e:
            return err("VALIDATION_ERROR", _msg(e), 400)
        item.selected_options = [o.id for o in chosen]
        item.unit_price = unit
    item.save()
    return Response(serialize_cart(cart))


# --- orders ------------------------------------------------------------------
@api_view(["GET", "POST"])
@authentication_classes([ClientTokenAuthentication])
@permission_classes([IsClient])
def orders_root(request):
    if request.method == "GET":
        qs = Order.objects.filter(client=request.user)
        return Response([serialize_order(o) for o in qs])

    # POST — checkout
    cart = _resolve_cart(request)
    if not cart:
        return err("NOT_FOUND", "cart not found", 404)
    items = list(cart.items.select_related("recipe").all())
    if not items:
        return err("VALIDATION_ERROR", "cart is empty", 400)
    # Re-check every item is still orderable (M03 R9 + display_status).
    for it in items:
        if not it.recipe.is_orderable:
            return err("RECIPE_UNAVAILABLE",
                       f"{it.recipe.name} is no longer available", 409)

    # P6 — one fulfilment mode for the whole cart.
    mode = request.data.get("fulfil_mode") or Order.FulfilMode.ORDER_NOW
    now = timezone.now()
    if mode == Order.FulfilMode.ORDER_NOW:
        if not store_is_open():  # ordering now requires the shop open now
            return err("STORE_CLOSED", "the shop is currently closed", 409)
        ready_by, scheduled_for = now + timedelta(hours=1), None
    elif mode == Order.FulfilMode.ORDER_FOR_LATER:
        raw = request.data.get("scheduled_for")
        if not raw:
            return err("VALIDATION_ERROR", "scheduled_for is required for Order for later", 400)
        sf = parse_datetime(raw)
        if sf is None:
            return err("VALIDATION_ERROR", "scheduled_for must be an ISO datetime", 400)
        if timezone.is_naive(sf):
            sf = timezone.make_aware(sf, timezone.get_current_timezone())
        lead = settings.MIN_SCHEDULE_LEAD_MINUTES
        if sf < now + timedelta(minutes=lead):
            return err("VALIDATION_ERROR", f"schedule at least {lead} minutes ahead", 400)
        if not store_is_open(timezone.localtime(sf).date()):  # must be open that day (M09)
            return err("STORE_CLOSED", "the shop is closed on the selected date", 409)
        ready_by, scheduled_for = sf, sf
    else:
        return err("VALIDATION_ERROR", "invalid fulfil_mode", 400)

    sub = cart.subtotal
    order = Order.objects.create(
        code=f"T{secrets.token_hex(4)}", client=request.user,  # temp (<=12), replaced below
        subtotal=sub, total=sub,
        fulfilment=(request.data.get("fulfilment") or "PICKUP"),
        fulfil_mode=mode, ready_by=ready_by, scheduled_for=scheduled_for,
        note=(request.data.get("note") or "")[:200],
    )
    order.assign_code()
    for it in items:
        OrderItem.objects.create(
            order=order, recipe_name=it.recipe.name, unit_price=it.unit_price,
            qty=it.qty, line_total=it.line_total,
            options_snapshot=option_labels(it.recipe, it.selected_options),
        )
    cart.is_open = False
    cart.client = request.user
    cart.save(update_fields=["is_open", "client"])

    # M06: freeze a UPI invoice for this order. M07: log PLACED + notify.
    PaymentIntent.objects.create(
        order=order,
        upi_id=settings.BUSINESS_UPI_ID,
        amount=order.total,
        qr_payload=(
            f"upi://pay?pa={settings.BUSINESS_UPI_ID}&pn=Nik_kiT"
            f"&am={order.total}&cu=INR&tn={order.code}"
        ),
    )
    transitions.record_placed(order, f"client:{request.user.id}")
    return Response(serialize_order(order), status=201)


@api_view(["GET"])
@authentication_classes([ClientTokenAuthentication])
@permission_classes([IsClient])
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, client=request.user)
    return Response(serialize_order(order))


# --- M06 payment (client) ----------------------------------------------------
@api_view(["GET"])
@authentication_classes([ClientTokenAuthentication])
@permission_classes([IsClient])
def payment_info(request, pk):
    order = get_object_or_404(Order, pk=pk, client=request.user)
    intent = order.payment_intent
    proof = order.proofs.filter(is_current=True).first()

    # Prefer the real business UPI QR image if it's been placed in media.
    qr_image_url = None
    rel = settings.BUSINESS_UPI_QR_MEDIA
    if rel and os.path.exists(os.path.join(settings.MEDIA_ROOT, rel)):
        qr_image_url = request.build_absolute_uri(settings.MEDIA_URL + rel)

    return Response({
        "upi_id": intent.upi_id,
        "amount": str(intent.amount),
        "qr_payload": intent.qr_payload,
        "qr_image_url": qr_image_url,
        "order_status": order.status,
        "proof": {"decision": proof.decision} if proof else None,
    })


@api_view(["POST"])
@authentication_classes([ClientTokenAuthentication])
@permission_classes([IsClient])
def upload_proof(request, pk):
    order = get_object_or_404(Order, pk=pk, client=request.user)
    if order.status not in (Order.Status.PLACED, Order.Status.PAYMENT_REJECTED):
        return err("STATE_CONFLICT", "payment cannot be submitted for this order now", 409)
    image = request.FILES.get("image")
    if not image:
        return err("VALIDATION_ERROR", "image is required", 400)

    order.proofs.update(is_current=False)  # supersede any prior proof (keep history)
    PaymentProof.objects.create(order=order, image=image, is_current=True)
    transitions.transition(order, Order.Status.PAYMENT_SUBMITTED,
                           f"client:{request.user.id}", notify_client=False)
    # M06 R3 — ping the owner "Payment received? (Yes/No)".
    notify(
        "PAYMENT_SUBMITTED_OWNER", order=order,
        recipients=[("ADMIN", settings.BUSINESS_CONTACT_EMAIL)], channels=("EMAIL",),
        payload={"subject": f"Payment submitted · {order.code}",
                 "message": f"Payment proof submitted for {order.code} (₹{order.total}). Confirm? Yes/No"},
    )
    return Response({"order_status": order.status})


# --- M07 tracking (client) ---------------------------------------------------
@api_view(["GET"])
@authentication_classes([ClientTokenAuthentication])
@permission_classes([IsClient])
def order_tracking(request, pk):
    order = get_object_or_404(Order, pk=pk, client=request.user)
    events = list(order.events.all())
    current_stage = ""
    for e in events:
        if e.customer_stage:
            current_stage = e.customer_stage
    history = [
        {"to": e.to_status, "stage": e.customer_stage, "at": e.created_at.isoformat()}
        for e in events
    ]
    return Response({"status": order.status, "customer_stage": current_stage, "history": history})


# --- Admin (M06 confirm gate + M07 advance) ----------------------------------
def _admin_label(request):
    return f"admin:{request.user.username}"


@api_view(["POST"])
@authentication_classes([AdminTokenAuthentication])
@permission_classes([IsAdmin])
def admin_confirm_payment(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status != Order.Status.PAYMENT_SUBMITTED:
        return err("STATE_CONFLICT", "no submitted payment to confirm", 409)
    proof = order.proofs.filter(is_current=True).first()
    if proof:
        proof.decision = PaymentProof.Decision.CONFIRMED
        proof.decided_by = _admin_label(request)
        proof.decided_at = timezone.now()
        proof.save()
    transitions.confirm_payment(order, _admin_label(request))
    return Response({"order_status": order.status})


@api_view(["POST"])
@authentication_classes([AdminTokenAuthentication])
@permission_classes([IsAdmin])
def admin_reject_payment(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status != Order.Status.PAYMENT_SUBMITTED:
        return err("STATE_CONFLICT", "no submitted payment to reject", 409)
    reason = (request.data.get("reason") or "")[:140]
    proof = order.proofs.filter(is_current=True).first()
    if proof:
        proof.decision = PaymentProof.Decision.REJECTED
        proof.decided_by = _admin_label(request)
        proof.decided_at = timezone.now()
        proof.reject_reason = reason
        proof.save()
    transitions.transition(order, Order.Status.PAYMENT_REJECTED, _admin_label(request), reason=reason)
    notify(
        "PAYMENT_REJECTED", order=order,
        recipients=([("CLIENT", order.client.email)] if order.client.email else []),
        channels=("EMAIL", "INAPP"),
        payload={"subject": "Payment needs re-upload",
                 "message": f"Payment for {order.code} couldn't be confirmed. Please re-upload. {reason}"},
    )
    return Response({"order_status": order.status})


@api_view(["POST"])
@authentication_classes([AdminTokenAuthentication])
@permission_classes([IsAdmin])
def admin_advance(request, pk):
    order = get_object_or_404(Order, pk=pk)
    to = request.data.get("to")
    try:
        transitions.transition(order, to, _admin_label(request))
    except ValidationError as e:
        return err("STATE_CONFLICT", _msg(e), 409)
    return Response({"order_status": order.status})


@api_view(["POST"])
@authentication_classes([AdminTokenAuthentication])
@permission_classes([IsAdmin])
def admin_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk)
    try:
        transitions.transition(order, Order.Status.CANCELLED, _admin_label(request),
                               reason=(request.data.get("reason") or "")[:140])
    except ValidationError as e:
        return err("STATE_CONFLICT", _msg(e), 409)
    return Response({"order_status": order.status})


@api_view(["GET"])
@authentication_classes([AdminTokenAuthentication])
@permission_classes([IsAdmin])
def admin_payments_queue(request):
    qs = Order.objects.filter(status=Order.Status.PAYMENT_SUBMITTED)
    return Response([serialize_order(o) for o in qs])
