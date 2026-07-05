"""P3 — UPI payment cycle (M06) + order tracking (M07) + notifications (M08).

Admin actions use the seeded superuser 'nik' / 'nikadmin123'.
"""
import time

from lib import PNG_1x1, bearer, get_json, post, post_file, request, test

ADMIN_USER, ADMIN_PASS = "nik", "nikadmin123"


def _client():
    ph = "+9188" + str(int(time.time() * 1000))[-8:]
    _s, b = post("/api/v1/auth/register", {"first_name": "Pay", "email": f"pay{ph[-5:]}@ex.com", "phone": ph})
    return b["token"]


def _place_order(token):
    recs = get_json("/api/v1/sections/parathas/recipes")
    rid = next(r["id"] for r in recs if r["name"] == "Aloo Paratha")
    d = get_json(f"/api/v1/recipes/{rid}")
    spice = next(g for g in d["customization"] if g["select_type"] == "SINGLE")["options"][0]["id"]
    _s, cart = post("/api/v1/cart/items", {"recipe_id": rid, "selected_options": [spice]})
    _s, order = post("/api/v1/orders", {"cart_key": cart["cart_key"]}, headers=bearer(token))
    return order


def _admin_token():
    st, b = post("/api/v1/auth/admin/login", {"username": ADMIN_USER, "password": ADMIN_PASS})
    assert st == 200, (st, b)
    return b["token"]


def _upload_proof(oid, token):
    return post_file(f"/api/v1/orders/{oid}/payment/proof", "image", "proof.png", PNG_1x1,
                     headers=bearer(token))


@test("TEST_P3_T01", "Payment info exposes UPI id + frozen amount + QR payload")
def payment_info():
    t = _client()
    o = _place_order(t)
    st, p = request("GET", f"/api/v1/orders/{o['id']}/payment", headers=bearer(t))
    assert st == 200, (st, p)
    assert p["upi_id"] and p["amount"] == o["total"], p
    assert p["qr_payload"].startswith("upi://pay?"), p


@test("TEST_P3_T02", "New order logs the 'Order placed' stage (M07 tracking)")
def placed_stage():
    t = _client()
    o = _place_order(t)
    st, tr = request("GET", f"/api/v1/orders/{o['id']}/tracking", headers=bearer(t))
    assert st == 200 and tr["customer_stage"] == "Order placed", tr
    assert any(e["to"] == "PLACED" for e in tr["history"]), tr


@test("TEST_P3_T03", "Uploading a proof moves the order to PAYMENT_SUBMITTED")
def upload_moves_state():
    t = _client()
    o = _place_order(t)
    st, b = _upload_proof(o["id"], t)
    assert st == 200 and b["order_status"] == "PAYMENT_SUBMITTED", (st, b)


@test("TEST_P3_T04", "Proof upload without an image is rejected (400)")
def upload_needs_image():
    t = _client()
    o = _place_order(t)
    st, b = post(f"/api/v1/orders/{o['id']}/payment/proof", {}, headers=bearer(t))
    assert st == 400, (st, b)


@test("TEST_P3_T05", "Admin login issues a token; bad creds rejected (401)")
def admin_login():
    tok = _admin_token()
    assert tok
    st, _ = post("/api/v1/auth/admin/login", {"username": ADMIN_USER, "password": "wrong"})
    assert st == 401, st


@test("TEST_P3_T06", "Owner confirm moves order to ACCEPTED with one 'Order accepted' notice")
def confirm_gate():
    t = _client()
    o = _place_order(t)
    _upload_proof(o["id"], t)
    admin = _admin_token()
    st, b = post(f"/api/v1/admin/orders/{o['id']}/payment/confirm", {}, headers=bearer(admin))
    assert st == 200 and b["order_status"] == "ACCEPTED", (st, b)
    _s, tr = request("GET", f"/api/v1/orders/{o['id']}/tracking", headers=bearer(t))
    assert tr["customer_stage"] == "Order accepted", tr
    accepted = [e for e in tr["history"] if e["stage"] == "Order accepted"]
    assert len(accepted) == 1, ("exactly one accepted notice", tr)


@test("TEST_P3_T07", "Kitchen advances ACCEPTED→PREPARING→READY→COMPLETED; illegal jump 409")
def advance_lifecycle():
    t = _client()
    o = _place_order(t)
    _upload_proof(o["id"], t)
    admin = _admin_token()
    ah = bearer(admin)
    post(f"/api/v1/admin/orders/{o['id']}/payment/confirm", {}, headers=ah)  # → ACCEPTED
    # illegal jump ACCEPTED → COMPLETED
    st_bad, _ = post(f"/api/v1/admin/orders/{o['id']}/advance", {"to": "COMPLETED"}, headers=ah)
    assert st_bad == 409, st_bad
    for nxt in ("PREPARING", "READY_FOR_PICKUP", "COMPLETED"):
        st, b = post(f"/api/v1/admin/orders/{o['id']}/advance", {"to": nxt}, headers=ah)
        assert st == 200 and b["order_status"] == nxt, (nxt, st, b)


@test("TEST_P3_T08", "Confirm is admin-only (client token forbidden)")
def confirm_admin_only():
    t = _client()
    o = _place_order(t)
    _upload_proof(o["id"], t)
    st, _ = post(f"/api/v1/admin/orders/{o['id']}/payment/confirm", {}, headers=bearer(t))
    assert st in (401, 403), st


@test("TEST_P3_T09", "Reject → PAYMENT_REJECTED; re-upload → PAYMENT_SUBMITTED")
def reject_then_reupload():
    t = _client()
    o = _place_order(t)
    _upload_proof(o["id"], t)
    admin = bearer(_admin_token())
    st, b = post(f"/api/v1/admin/orders/{o['id']}/payment/reject", {"reason": "blurred"}, headers=admin)
    assert st == 200 and b["order_status"] == "PAYMENT_REJECTED", (st, b)
    st2, b2 = _upload_proof(o["id"], t)
    assert st2 == 200 and b2["order_status"] == "PAYMENT_SUBMITTED", (st2, b2)


@test("TEST_P3_T10", "Notifications are logged (placed + owner ping + accepted)")
def notifications_logged():
    t = _client()
    o = _place_order(t)
    _upload_proof(o["id"], t)
    admin = bearer(_admin_token())
    post(f"/api/v1/admin/orders/{o['id']}/payment/confirm", {}, headers=admin)
    st, rows = request("GET", f"/api/v1/admin/notifications?order={o['id']}", headers=admin)
    assert st == 200, (st, rows)
    events = {r["event_type"] for r in rows}
    assert "ORDER_PLACED" in events, events
    assert "PAYMENT_SUBMITTED_OWNER" in events, events
    assert "ORDER_ACCEPTED" in events, events
    # idempotency: only one ORDER_ACCEPTED email
    accepted_emails = [r for r in rows if r["event_type"] == "ORDER_ACCEPTED" and r["channel"] == "EMAIL"]
    assert len(accepted_emails) == 1, accepted_emails
