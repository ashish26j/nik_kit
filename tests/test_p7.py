"""P7 — Client account area + Email-OTP (M13 + M01).

OTP codes are returned in the response as `dev_code` only because DEBUG=True (dev);
in production they go to email only.
"""
import time

from lib import bearer, get_json, patch, post, request, test


def _client():
    ph = "+9143" + str(int(time.time() * 1000))[-8:]
    em = f"p7_{ph[-6:]}@ex.com"
    _s, reg = post("/api/v1/auth/register", {"first_name": "Seven", "email": em, "phone": ph})
    return reg["token"], ph, em


@test("TEST_P7_T01", "PATCH /auth/me updates name/email; phone stays the identity")
def patch_me():
    tok, ph, em = _client()
    st, b = patch("/api/v1/auth/me", {"first_name": "Newname", "email": "new_" + em}, headers=bearer(tok))
    assert st == 200 and b["first_name"] == "Newname" and b["phone"] == ph, (st, b)


@test("TEST_P7_T02", "PATCH /auth/me rejects an invalid email (400)")
def patch_me_bad():
    tok, _ph, _em = _client()
    st, _b = patch("/api/v1/auth/me", {"email": "notanemail"}, headers=bearer(tok))
    assert st == 400, st


@test("TEST_P7_T03", "OTP request: existing email → 200 (+dev code); unknown → 404")
def otp_request():
    _tok, _ph, em = _client()
    st, b = post("/api/v1/auth/otp/request", {"email": em})
    assert st == 200 and "dev_code" in b, (st, b)
    st2, _b2 = post("/api/v1/auth/otp/request", {"email": "nobody-" + em})
    assert st2 == 404, st2


@test("TEST_P7_T04", "OTP verify restores the same account; wrong code → 400")
def otp_verify():
    _tok, ph, em = _client()
    _s, r = post("/api/v1/auth/otp/request", {"email": em})
    st, v = post("/api/v1/auth/otp/verify", {"email": em, "code": r["dev_code"]})
    assert st == 200 and v["user"]["phone"] == ph and v["token"], (st, v)
    st2, _b = post("/api/v1/auth/otp/verify", {"email": em, "code": "000000"})
    assert st2 == 400, st2


@test("TEST_P7_T05", "A restored (OTP) token sees the same client's order history")
def restored_orders():
    tok, _ph, em = _client()
    recs = get_json("/api/v1/sections/parathas/recipes")
    rid = next(r["id"] for r in recs if r["name"] == "Aloo Paratha")
    d = get_json(f"/api/v1/recipes/{rid}")
    sp = next(g for g in d["customization"] if g["select_type"] == "SINGLE")["options"][0]["id"]
    _s, cart = post("/api/v1/cart/items", {"recipe_id": rid, "selected_options": [sp]})
    _s, order = post("/api/v1/orders", {"cart_key": cart["cart_key"]}, headers=bearer(tok))
    _s, r = post("/api/v1/auth/otp/request", {"email": em})
    _s, v = post("/api/v1/auth/otp/verify", {"email": em, "code": r["dev_code"]})
    st, rows = request("GET", "/api/v1/orders", headers=bearer(v["token"]))
    assert st == 200 and any(o["id"] == order["id"] for o in rows), (st, rows)


@test("TEST_P7_T06", "/auth/me requires a token")
def me_needs_token():
    st, _b = request("GET", "/api/v1/auth/me")
    assert st in (401, 403), st
