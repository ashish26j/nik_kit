"""P6 — Order modes (Order now / Order for later) + per-recipe ordering toggle.

Timezone note: the API runs Asia/Kolkata; the host may differ. For the closed-date
test we close a 3-day range around the scheduled date so it's covered regardless.
"""
import datetime
import time

from lib import bearer, get_json, post, request, test

ADMIN_USER, ADMIN_PASS = "nik", "nikadmin123"


def _admin():
    _s, b = post("/api/v1/auth/admin/login", {"username": ADMIN_USER, "password": ADMIN_PASS})
    return b["token"]


def _client():
    ph = "+9141" + str(int(time.time() * 1000))[-8:]
    _s, reg = post("/api/v1/auth/register", {"first_name": "Mode", "email": f"m{ph[-5:]}@ex.com", "phone": ph})
    return reg["token"]


def _cart_with_aloo():
    recs = get_json("/api/v1/sections/parathas/recipes")
    rid = next(r["id"] for r in recs if r["name"] == "Aloo Paratha")
    d = get_json(f"/api/v1/recipes/{rid}")
    sp = next(g for g in d["customization"] if g["select_type"] == "SINGLE")["options"][0]["id"]
    _s, cart = post("/api/v1/cart/items", {"recipe_id": rid, "selected_options": [sp]})
    return cart["cart_key"]


def _future(days, hour=18):
    return (datetime.datetime.now() + datetime.timedelta(days=days)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    ).isoformat()


@test("TEST_P6_T01", "Order now → PLACED, ready_by set (~1h), scheduled_for null")
def order_now():
    tok, ck = _client(), _cart_with_aloo()
    st, o = post("/api/v1/orders", {"cart_key": ck, "fulfil_mode": "ORDER_NOW"}, headers=bearer(tok))
    assert st == 201 and o["fulfil_mode"] == "ORDER_NOW", (st, o)
    assert o["ready_by"] and o["scheduled_for"] is None, o


@test("TEST_P6_T02", "Order for later with a valid future time → scheduled_for set")
def order_later():
    tok, ck = _client(), _cart_with_aloo()
    st, o = post("/api/v1/orders", {"cart_key": ck, "fulfil_mode": "ORDER_FOR_LATER", "scheduled_for": _future(2)}, headers=bearer(tok))
    assert st == 201 and o["fulfil_mode"] == "ORDER_FOR_LATER" and o["scheduled_for"], (st, o)


@test("TEST_P6_T03", "Order for later without a time → 400")
def later_needs_time():
    tok, ck = _client(), _cart_with_aloo()
    st, _b = post("/api/v1/orders", {"cart_key": ck, "fulfil_mode": "ORDER_FOR_LATER"}, headers=bearer(tok))
    assert st == 400, st


@test("TEST_P6_T04", "Order for later too soon (< lead time) → 400")
def later_too_soon():
    tok, ck = _client(), _cart_with_aloo()
    soon = (datetime.datetime.now() + datetime.timedelta(minutes=10)).isoformat()
    st, _b = post("/api/v1/orders", {"cart_key": ck, "fulfil_mode": "ORDER_FOR_LATER", "scheduled_for": soon}, headers=bearer(tok))
    assert st == 400, st


@test("TEST_P6_T05", "Order for later on a closed date → 409 STORE_CLOSED")
def later_closed_date():
    admin = _admin()
    # close a 3-day window around day+3 (tz-robust)
    st, c = post("/api/v1/admin/closures", {"start_date": (datetime.date.today() + datetime.timedelta(days=2)).isoformat(),
                                            "end_date": (datetime.date.today() + datetime.timedelta(days=4)).isoformat()},
                 headers=bearer(admin))
    assert st == 201, (st, c)
    try:
        tok, ck = _client(), _cart_with_aloo()
        st2, b2 = post("/api/v1/orders", {"cart_key": ck, "fulfil_mode": "ORDER_FOR_LATER", "scheduled_for": _future(3)}, headers=bearer(tok))
        assert st2 == 409 and b2["error"]["code"] == "STORE_CLOSED", (st2, b2)
    finally:
        request("DELETE", f"/api/v1/admin/closures/{c['id']}", headers=bearer(admin))


@test("TEST_P6_T06", "A recipe with ordering disabled is not orderable (add → 409)")
def ordering_disabled():
    recs = get_json("/api/v1/sections/snacks/recipes")
    kach = next(r for r in recs if r["name"] == "Kachori")
    assert kach["is_orderable"] is False, kach
    st, b = post("/api/v1/cart/items", {"recipe_id": kach["id"], "selected_options": []})
    assert st == 409 and b["error"]["code"] == "RECIPE_UNAVAILABLE", (st, b)


@test("TEST_P6_T07", "Default (no fulfil_mode) is ORDER_NOW")
def default_mode():
    tok, ck = _client(), _cart_with_aloo()
    st, o = post("/api/v1/orders", {"cart_key": ck}, headers=bearer(tok))
    assert st == 201 and o["fulfil_mode"] == "ORDER_NOW", (st, o)
