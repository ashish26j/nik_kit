# M13 — Client Account Area (Contract)

> **Status:** DRAFT v1 · New feature module (planned **P7**). Shared conventions in
> [README](README.md).
> **Depends on:** M01 (identity, `PATCH /auth/me`, Email-OTP), M05 (order history),
> M07 (order tracking). **Mirror of** M09 (admin console) — but for the customer.

---

## 1. Purpose

Give the customer a **passwordless** account area: see **order history + status**, view
and **edit their profile**, all behind the token they already hold — plus **Email-OTP**
to restore that account on a new device. No login wall; the token *is* the session.

## 2. Scope

**In v1 (P7):**
- **My Orders** — list the client's own orders with current status; open any → the M07
  tracking timeline (+ "Rate" when completed, M10).
- **Profile** — view + edit `first_name`/`email` (`GET`/`PATCH /auth/me`); phone is the
  identity (shown, not editable here).
- **Account restore** on a new device via **Email-OTP** (M01 planned endpoints).
- A **👤 entry on Home**, shown once the client has a token (or leads to "restore by
  email").

**Out (later):** passwords, saved addresses, payment methods, notification preferences,
account deletion, multi-device session management.

## 3. Actors & authorization

| Action | Guest (no token) | Client (has token) | Admin |
|---|---|---|---|
| See My Orders / Profile | 🚫 → prompt to order or restore | 🔒 own | ✅ (via M09, all) |
| Edit own profile | 🚫 | 🔒 own | — |
| Restore account (Email-OTP) | ✅ (proves ownership of the email) | ✅ | — |

Everything is **own-records-only** (`🔒`), enforced by the client token (M01).

## 4. Data model

**None of its own** — a composition/read-through layer:
- `Order` history & status ← M05 / M07
- `Client` profile ← M01
- OTP + token issuance ← M01

## 5. API surface (all defined in their owning module)

- **My Orders:** `GET /api/v1/orders` (own list) + `GET /orders/{id}/tracking` (M05/M07).
- **Profile:** `GET /api/v1/auth/me` + `PATCH /auth/me` (M01, planned P7).
- **Restore:** `POST /auth/otp/request` → `POST /auth/otp/verify` (M01, planned P7).

M13 adds **no new endpoints** — it's the client-facing screens over these.

## 6. Rules & invariants

- **R1** Same device (token present) → account area is **immediately** available, no
  verification (the token was issued to this person).
- **R2** New device / cleared storage → account is restored **only** via Email-OTP
  (M01 R7); an unverified email/phone never reveals another client's orders.
- **R3** Profile edits change `first_name`/`email` only; **phone stays the identity**.
- **R4** M13 adds no business logic — order status/history come from M05/M07 unchanged.

## 7. Dependencies & seams

- Composes M01 + M05 + M07 (+ M10 rate button on completed orders).
- **Seam:** saved addresses, notification preferences, and a "reorder" action slot onto
  this area without new auth.

## 8. Acceptance criteria

- [ ] With a token, the 👤 area lists the client's own orders + current status.
- [ ] Tapping an order opens its tracking timeline; completed orders offer **Rate** (M10).
- [ ] Profile shows name/email/phone; editing name/email persists via `PATCH /auth/me`.
- [ ] On a fresh device, entering the account **email** + the **OTP** restores the same
      account (same history); a wrong/expired code does not.
- [ ] A client never sees another client's orders or profile.
