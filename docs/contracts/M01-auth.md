# M01 — Auth / Lightweight Registration (Contract)

> **Status:** DRAFT v1 · Traces to blueprint §3 (Roles & authorization) · Shared
> conventions in [README](README.md).
> **Depends on:** nothing. **Depended on by:** every other module (roles/permissions).

---

## 1. Purpose

Provide the two roles (**Admin**, **Client**) and the identity seam every other
module reads. Keep the customer **explore-first**: no identity to browse; capture
**First Name, Email, Phone** only at checkout. No client passwords in v1.

## 2. Scope

**In v1:**
- Client light registration (first name, email, phone) → issue a long-lived
  **client token**.
- Re-identify a returning client (same phone) — merge to the existing record.
- Admin login (seeded staff account, username + password) → admin token/session.
- DRF permission classes: `IsPublicRead`, `IsClient`, `IsAdmin`, `IsOwnerOrAdmin`.

**Planned (P7, see [M13](M13-client-account.md)):** `PATCH /auth/me` (profile update)
and **Email-OTP** verification — the passwordless way to restore an account on a new
device.

**Out (later):** client passwords, social login, multi-staff roles & granular admin
permissions, account deletion self-service, SMS/phone verification.

## 3. Actors & authorization

| Action | Guest | Client | Admin |
|---|---|---|---|
| Browse menu (read) | ✅ | ✅ | ✅ |
| Register (first name/email/phone) | ✅ (this creates the Client) | n/a | ✅ (create on behalf) |
| Obtain/refresh client token | ✅ at register | ✅ | — |
| Admin login | 🚫 | 🚫 | ✅ |
| View **any** user record | 🚫 | 🔒 self only | ✅ all |
| Become Admin | 🚫 (no public path) | 🚫 | seeded only |

> **How one becomes Admin:** a **seeded owner account** via Django management command
> / `createsuperuser` at deploy. No public "sign up as admin" endpoint exists in v1.

## 4. Data model

**`User`** (single table, role-discriminated)
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `role` | enum `CLIENT` \| `ADMIN` | default `CLIENT` |
| `first_name` | varchar(60) | required |
| `email` | varchar(254) | required; unique per role |
| `phone` | varchar(20) | required for CLIENT; **natural identity key** (normalized E.164-ish) |
| `password` | hash | **ADMIN only**; null for clients |
| `is_active` | bool | default true |
| `created_at` / `updated_at` | datetime | |

**`ClientToken`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `user_id` | FK → User | must be CLIENT |
| `token` | char(40) | opaque, random; sent as Bearer |
| `created_at` | datetime | |
| `last_used_at` | datetime | |

- **Uniqueness:** client identity = **normalized `phone`**. Registering an existing
  phone returns the existing client (optionally updates first_name/email), not a dup.

## 5. API surface

### `POST /api/v1/auth/register` — public
Creates or re-identifies a Client, returns a token.
```json
// request
{ "first_name": "Asha", "email": "asha@example.com", "phone": "+91 98765 43210" }
// 200
{ "user": { "id": 42, "first_name": "Asha", "email": "asha@…", "phone": "+919876543210" },
  "token": "b1e5…40chars" }
```
Errors: `VALIDATION_ERROR` (missing/invalid field).

### `GET /api/v1/auth/me` — client or admin
Returns the caller's own profile (from token). `401 AUTH_REQUIRED` if no token.

### `PATCH /api/v1/auth/me` — client *(planned P7)*
Update own `first_name` / `email`. **Phone is the identity key** and isn't changed here.

### `POST /api/v1/auth/otp/request` — public *(planned P7)*
`{ "email": "…" }` → emails a short code. Used to **restore** an account on a new device
(no password). Rate-limited.

### `POST /api/v1/auth/otp/verify` — public *(planned P7)*
`{ "email": "…", "code": "123456" }` → on a valid, unexpired code, issues a client token
for that account (same client → same order history).

### `POST /api/v1/auth/admin/login` — public → admin
```json
{ "username": "nik", "password": "••••" }  →  { "token": "…", "role": "ADMIN" }
```
Errors: `401 AUTH_REQUIRED` on bad creds.

### `POST /api/v1/auth/logout` — authenticated
Invalidates the presented token.

## 6. Rules & invariants

- **R1** Browsing/menu reads never require a token (guards explore-first).
- **R2** Checkout (M05) requires a valid **client token**; if absent, the client
  registers first (this endpoint) — registration is the only gate.
- **R3** Phone is normalized before storage & comparison; it is the client's identity.
- **R4** A client token grants access **only to that client's own** carts/orders/
  ratings (`IsOwnerOrAdmin`).
- **R5** Admin actions (menu writes, payment confirm, order-state advance, view-all)
  require `IsAdmin`. Deny by default otherwise.
- **R6** No password is ever stored or required for a Client in v1.
- **R7 (planned P7)** **Email OTP** is the only cross-device recovery: request → emailed
  code → verify → token for that account. Codes are short-lived + rate-limited. An
  **unverified** identity must never expose another client's orders (closes the
  "type any phone/email to see their orders" hole).

## 7. States

Identity is stateless beyond token validity. Client "state" is Guest (no token) →
Registered (holds valid token). No lifecycle machine here.

## 8. Dependencies & seams

- **Seam for later:** `password`/OTP verification for clients slots onto `User` +
  a `verify` endpoint without schema breakage.
- **Seam for multi-staff:** `role` enum can extend (`STAFF`) + a permission table.

## 9. Acceptance criteria

- [ ] Guest can `GET /menu` with **no** token (200).
- [ ] `POST /auth/register` with the 3 fields returns a user + token; re-registering
      the **same phone** returns the **same** user id (no duplicate).
- [ ] `GET /auth/me` returns the caller; fails 401 without a token.
- [ ] A client token cannot read another client's order (403 `FORBIDDEN`).
- [ ] Seeded admin can log in; no endpoint can mint an admin from the client side.
