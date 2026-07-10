"""P4 — M09 Business closures (open/closed + checkout STORE_CLOSED enforcement).

Timezone note: the API container runs Asia/Kolkata while the test host may be in a
different zone, so "today" can differ by up to a day. To stay deterministic we use
ranges that unambiguously cover / exclude *now* for any zone within ±1 day.

Every test that creates a closure clears it in a finally block — a lingering closure
would wrongly block the P2/P3 checkout tests on the next run.
"""
import datetime
import time

from lib import bearer, get_json, post, request, test

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
