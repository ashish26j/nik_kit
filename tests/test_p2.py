"""P2 — Cart & ordering gate tests (M01 auth + M04 selection + M05).

Assumes the P1 seed (Aloo Paratha with a required 'Spice level' SINGLE group and an
'Add-ons' MULTI group incl. 'Cheese' +20; Gobi Paratha = UNAVAILABLE).
"""
import time

from lib import bearer, get_json, post, patch, test


def _uniq_phone():
    return "+9199" + str(int(time.time() * 1000))[-8:]


def _register(name="Asha"):
    ph = _uniq_phone()
    st, body = post("/api/v1/auth/register",
                    {"first_name": name, "email": f"{name}@ex.com", "phone": ph})
    assert st == 200, (st, body)
    return body["token"], body["user"], ph


def _aloo():
    recs = get_json("/api/v1/sections/parathas/recipes")
    rid = next(r["id"] for r in recs if r["name"] == "Aloo Paratha")
    d = get_json(f"/api/v1/recipes/{rid}")
    spice = next(g for g in d["customization"] if g["select_type"] == "SINGLE")
    addons = next(g for g in d["customization"] if g["select_type"] == "MULTI")
    cheese = next(o for o in addons["options"] if "Cheese" in o["label"])
    return rid, spice["options"][0]["id"], cheese["id"]


@test("TEST_P2_T01", "Register issues a token; same phone re-registers to same client")
def register_idempotent():
    token, user, phone = _register()
    assert token and user["id"], (token, user)
    st, body = post("/api/v1/auth/register",
                    {"first_name": "Asha2", "email": "a2@ex.com", "phone": phone})
    assert st == 200 and body["user"]["id"] == user["id"], body


@test("TEST_P2_T02", "Add to cart computes server-side price (recipe + option deltas)")
def cart_price():
    rid, spice_opt, cheese_opt = _aloo()
    st, cart = post("/api/v1/cart/items",
                    {"recipe_id": rid, "qty": 1, "selected_options": [spice_opt, cheese_opt]})
    assert st == 201, (st, cart)
    # Aloo 60.00 + Cheese 20.00 = 80.00, regardless of any client-sent price
    assert cart["items"][0]["unit_price"] == "80.00", cart
    assert cart["total"] == "80.00", cart


@test("TEST_P2_T03", "Missing a required SINGLE option is rejected (400)")
def required_option():
    rid, _spice, _cheese = _aloo()
    st, body = post("/api/v1/cart/items", {"recipe_id": rid, "selected_options": []})
    assert st == 400 and body["error"]["code"] == "VALIDATION_ERROR", (st, body)


@test("TEST_P2_T04", "Adding an UNAVAILABLE recipe is rejected (409)")
def unavailable():
    recs = get_json("/api/v1/sections/parathas/recipes")
    gid = next(r["id"] for r in recs if r["display_status"] == "UNAVAILABLE")
    st, body = post("/api/v1/cart/items", {"recipe_id": gid, "selected_options": []})
    assert st == 409 and body["error"]["code"] == "RECIPE_UNAVAILABLE", (st, body)


@test("TEST_P2_T05", "Checkout without a client token is rejected (401/403)")
def checkout_needs_token():
    rid, spice_opt, _ = _aloo()
    _st, cart = post("/api/v1/cart/items",
                     {"recipe_id": rid, "selected_options": [spice_opt]})
    st, _ = post("/api/v1/orders", {"cart_key": cart["cart_key"]})
    assert st in (401, 403), st


@test("TEST_P2_T06", "Checkout places an order (PLACED) with snapshot + closed cart")
def checkout_places_order():
    token, _user, _ph = _register()
    rid, spice_opt, cheese_opt = _aloo()
    _st, cart = post("/api/v1/cart/items",
                     {"recipe_id": rid, "qty": 2, "selected_options": [spice_opt, cheese_opt]})
    key = cart["cart_key"]
    st, order = post("/api/v1/orders", {"cart_key": key}, headers=bearer(token))
    assert st == 201, (st, order)
    assert order["status"] == "PLACED", order
    assert order["code"].startswith("NK-"), order
    assert order["total"] == "160.00", order  # 80.00 x 2
    assert order["items"][0]["recipe_name"] == "Aloo Paratha", order
    # cart is now closed
    st2, _ = post("/api/v1/cart/items", {"recipe_id": rid, "selected_options": [spice_opt]},
                  headers={"X-Cart-Key": key})
    # adding with a closed key just starts a fresh cart (201) — the old one is gone:
    from lib import request
    st3, _b = request("GET", f"/api/v1/cart?cart_key={key}")
    assert st3 == 404, ("closed cart should be gone", st3)


@test("TEST_P2_T07", "A client sees only their own orders")
def own_orders_only():
    token_a, _u, _p = _register("Amit")
    rid, spice_opt, _ = _aloo()
    _st, cart = post("/api/v1/cart/items",
                     {"recipe_id": rid, "selected_options": [spice_opt]})
    _st, order = post("/api/v1/orders", {"cart_key": cart["cart_key"]}, headers=bearer(token_a))
    oid = order["id"]
    # a different client must not read it
    token_b, _u2, _p2 = _register("Bina")
    from lib import request
    st, _ = request("GET", f"/api/v1/orders/{oid}", headers=bearer(token_b))
    assert st == 404, ("other client should not see order", st)
    # owner can
    st2, _ = request("GET", f"/api/v1/orders/{oid}", headers=bearer(token_a))
    assert st2 == 200, st2
