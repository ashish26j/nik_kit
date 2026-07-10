"""P4 — M09 Business closures (open/closed + checkout STORE_CLOSED enforcement).

Timezone note: the API container runs Asia/Kolkata while the test host may be in a
different zone, so "today" can differ by up to a day. To stay deterministic we use
ranges that unambiguously cover / exclude *now* for any zone within ±1 day.

Every test that creates a closure clears it in a finally block — a lingering closure
would wrongly block the P2/P3 checkout tests on the next run.
"""
import datetime
import time

from lib import PNG_1x1, bearer, get_json, patch, post, post_file, request, test

ADMIN_USER, ADMIN_PASS = "nik", "nikadmin123"


def _admin():
    st, b = post("/api/v1/auth/admin/login", {"username": ADMIN_USER, "password": ADMIN_PASS})
    assert st == 200, (st, b)
    return b["token"]


def _clear(admin):
    _s, rows = request("GET", "/api/v1/admin/closures", headers=bearer(admin))
    for c in rows or []:
        request("DELETE", f"/api/v1/admin/closures/{c['id']}", headers=bearer(admin))


def _day(offset):
    return (datetime.date.today() + datetime.timedelta(days=offset)).isoformat()


def _client_cart():
    """Register a client, put an item in a cart. Returns (token, cart_key)."""
    ph = "+9166" + str(int(time.time() * 1000))[-8:]
    _s, reg = post("/api/v1/auth/register", {"first_name": "Clo", "email": "clo@ex.com", "phone": ph})
    recs = get_json("/api/v1/sections/parathas/recipes")
    rid = next(r["id"] for r in recs if r["name"] == "Aloo Paratha")
    d = get_json(f"/api/v1/recipes/{rid}")
    sp = next(g for g in d["customization"] if g["select_type"] == "SINGLE")["options"][0]["id"]
    st, cart = post("/api/v1/cart/items", {"recipe_id": rid, "selected_options": [sp]})
    assert st == 201, (st, cart)
    return reg["token"], cart["cart_key"]


@test("TEST_P4_T01", "Store is open by default (no closures)")
def default_open():
    _clear(_admin())
    assert get_json("/api/v1/store/status")["is_open"] is True


@test("TEST_P4_T02", "A closure covering now → closed, with message + reopens_on")
def closed_now():
    admin = _admin()
    _clear(admin)
    st, c = post(
        "/api/v1/admin/closures",
        {"start_date": _day(-1), "end_date": _day(1), "message": "Festival break"},
        headers=bearer(admin),
    )
    assert st == 201, (st, c)
    try:
        d = get_json("/api/v1/store/status")
        assert d["is_open"] is False, d
        assert d["message"] == "Festival break", d
        assert d["reopens_on"] == _day(2), d  # end_date + 1
    finally:
        _clear(admin)


@test("TEST_P4_T03", "While closed: checkout 409 STORE_CLOSED; browsing & cart still work")
def closed_blocks_checkout():
    admin = _admin()
    _clear(admin)
    post("/api/v1/admin/closures", {"start_date": _day(-1), "end_date": _day(1)}, headers=bearer(admin))
    try:
        assert get_json("/api/v1/sections")            # browsing works
        token, cart_key = _client_cart()               # add-to-cart works
        st, b = post("/api/v1/orders", {"cart_key": cart_key}, headers=bearer(token))
        assert st == 409 and b["error"]["code"] == "STORE_CLOSED", (st, b)
    finally:
        _clear(admin)


@test("TEST_P4_T04", "Deleting the closure reopens the store; checkout then succeeds")
def reopen():
    admin = _admin()
    _clear(admin)
    st, c = post("/api/v1/admin/closures", {"start_date": _day(-1), "end_date": _day(1)}, headers=bearer(admin))
    dstat, _b = request("DELETE", f"/api/v1/admin/closures/{c['id']}", headers=bearer(admin))
    assert dstat == 204, dstat
    assert get_json("/api/v1/store/status")["is_open"] is True
    token, cart_key = _client_cart()
    st2, b2 = post("/api/v1/orders", {"cart_key": cart_key}, headers=bearer(token))
    assert st2 == 201 and b2["status"] == "PLACED", (st2, b2)


@test("TEST_P4_T05", "Closure management is admin-only")
def admin_only():
    st, _b = request("GET", "/api/v1/admin/closures")          # no token
    assert st in (401, 403), st
    st2, _b2 = post("/api/v1/admin/closures", {"start_date": _day(0)})  # no token
    assert st2 in (401, 403), st2


@test("TEST_P4_T06", "A future-only closure doesn't affect today")
def future_open():
    admin = _admin()
    _clear(admin)
    st, c = post("/api/v1/admin/closures", {"start_date": _day(3), "end_date": _day(5)}, headers=bearer(admin))
    assert st == 201, (st, c)
    try:
        assert get_json("/api/v1/store/status")["is_open"] is True
    finally:
        _clear(admin)


@test("TEST_P4_T07", "Closure rejects end_date before start_date (400)")
def bad_range():
    admin = _admin()
    st, b = post("/api/v1/admin/closures", {"start_date": _day(5), "end_date": _day(2)}, headers=bearer(admin))
    assert st == 400, (st, b)


# --- M10 ratings -------------------------------------------------------------
def _place_order():
    """Register a client + place an order. Returns (token, order_id)."""
    ph = "+9155" + str(int(time.time() * 1000))[-8:]
    _s, reg = post("/api/v1/auth/register", {"first_name": "Rate", "email": "rate@ex.com", "phone": ph})
    tok = reg["token"]
    recs = get_json("/api/v1/sections/parathas/recipes")
    rid = next(r["id"] for r in recs if r["name"] == "Aloo Paratha")
    d = get_json(f"/api/v1/recipes/{rid}")
    sp = next(g for g in d["customization"] if g["select_type"] == "SINGLE")["options"][0]["id"]
    _s, cart = post("/api/v1/cart/items", {"recipe_id": rid, "selected_options": [sp]})
    _s, order = post("/api/v1/orders", {"cart_key": cart["cart_key"]}, headers=bearer(tok))
    return tok, order["id"]


def _completed_order():
    """A client with a fully COMPLETED order, ready to rate."""
    tok, oid = _place_order()
    post_file(f"/api/v1/orders/{oid}/payment/proof", "image", "p.png", PNG_1x1, headers=bearer(tok))
    admin = bearer(_admin())
    post(f"/api/v1/admin/orders/{oid}/payment/confirm", {}, headers=admin)  # → ACCEPTED
    for nxt in ("PREPARING", "READY_FOR_PICKUP", "COMPLETED"):
        post(f"/api/v1/admin/orders/{oid}/advance", {"to": nxt}, headers=admin)
    return tok, oid


@test("TEST_P4_T08", "Cannot rate an order that isn't completed (409)")
def rate_requires_completed():
    tok, oid = _place_order()  # still PLACED
    st, b = post(f"/api/v1/orders/{oid}/rating", {"stars": 5}, headers=bearer(tok))
    assert st == 409 and b["error"]["code"] == "STATE_CONFLICT", (st, b)


@test("TEST_P4_T09", "Rate a completed order (201) and read it back")
def rate_completed():
    tok, oid = _completed_order()
    st, b = post(f"/api/v1/orders/{oid}/rating", {"stars": 5, "note": "Loved it"}, headers=bearer(tok))
    assert st == 201 and b["stars"] == 5 and b["note"] == "Loved it", (st, b)
    st2, g = request("GET", f"/api/v1/orders/{oid}/rating", headers=bearer(tok))
    assert st2 == 200 and g["stars"] == 5, (st2, g)


@test("TEST_P4_T10", "Reject stars out of 1–5 and note over 100 chars (400)")
def rate_validation():
    tok, oid = _completed_order()
    for bad in ({"stars": 0}, {"stars": 6}, {"stars": 3, "note": "x" * 101}):
        st, b = post(f"/api/v1/orders/{oid}/rating", bad, headers=bearer(tok))
        assert st == 400, (bad, st, b)


@test("TEST_P4_T11", "One rating per order: second POST 409; PATCH updates")
def rate_one_then_patch():
    tok, oid = _completed_order()
    post(f"/api/v1/orders/{oid}/rating", {"stars": 4}, headers=bearer(tok))
    st, _b = post(f"/api/v1/orders/{oid}/rating", {"stars": 5}, headers=bearer(tok))
    assert st == 409, st
    st2, b2 = patch(f"/api/v1/orders/{oid}/rating", {"stars": 2, "note": "changed"}, headers=bearer(tok))
    assert st2 == 200 and b2["stars"] == 2, (st2, b2)


@test("TEST_P4_T12", "Admin summary + list reflect submitted ratings")
def admin_summary():
    tok, oid = _completed_order()
    post(f"/api/v1/orders/{oid}/rating", {"stars": 5}, headers=bearer(tok))
    admin = bearer(_admin())
    st, s = request("GET", "/api/v1/admin/ratings/summary", headers=admin)
    assert st == 200 and s["count"] >= 1 and s["avg"] is not None, (st, s)
    st2, rows = request("GET", "/api/v1/admin/ratings", headers=admin)
    assert st2 == 200 and any(r["order_id"] == oid for r in rows), (st2, rows)


@test("TEST_P4_T13", "Rating is own-only; admin endpoints need an admin token")
def rate_auth():
    tok, oid = _completed_order()
    ph = "+9153" + str(int(time.time() * 1000))[-8:]
    _s, other = post("/api/v1/auth/register", {"first_name": "O", "email": "o@ex.com", "phone": ph})
    st, _b = post(f"/api/v1/orders/{oid}/rating", {"stars": 5}, headers=bearer(other["token"]))
    assert st in (403, 404), st  # not the owner
    st2, _b2 = request("GET", "/api/v1/admin/ratings")  # no token
    assert st2 in (401, 403), st2
