"""M05 cart & order endpoints.

Cart is identified by an opaque `cart_key` the client holds (header `X-Cart-Key`
or body/query `cart_key`) — works for web/mobile without cookies. Anon can build a
cart; checkout requires a client token (M01).
"""
import secrets

from django.shortcuts import get_object_or_404
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.auth import ClientTokenAuthentication
from apps.accounts.permissions import IsClient
from apps.menu.models import Recipe

from .models import Cart, CartItem, Order, OrderItem
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
    if recipe.display_status != Recipe.Display.AVAILABLE:
        return err("RECIPE_UNAVAILABLE", f"{recipe.name} is not available", 409)
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
    # store open check is a P1 stub (always open); real closures = M09/P4.
    for it in items:
        if it.recipe.display_status != Recipe.Display.AVAILABLE:
            return err("RECIPE_UNAVAILABLE",
                       f"{it.recipe.name} is no longer available", 409)

    sub = cart.subtotal
    order = Order.objects.create(
        code=f"T{secrets.token_hex(4)}", client=request.user,  # temp (<=12), replaced below
        subtotal=sub, total=sub,
        fulfilment=(request.data.get("fulfilment") or "PICKUP"),
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
    return Response(serialize_order(order), status=201)


@api_view(["GET"])
@authentication_classes([ClientTokenAuthentication])
@permission_classes([IsClient])
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, client=request.user)
    return Response(serialize_order(order))
