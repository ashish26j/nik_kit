# Nik_kiT — Module Contracts

> **Purpose:** one contract per module — the **exact agreed behavior** (inputs,
> outputs, data, rules, states, acceptance) written **before code**, per the
> WCAS "contract each module" stage. Traces up to [`../blueprint.md`](../blueprint.md)
> (why/what) and [`../02-architecture.md`](../02-architecture.md) (how it runs).
>
> **Status:** DRAFT v1 — all ten contracts.

---

## Index

| ID | Contract | Owns |
|---|---|---|
| [M01](M01-auth.md) | Auth / lightweight registration | Roles, identity, tokens, permissions |
| [M02](M02-menu.md) | Menu & sections | Public browsing of Parathas/Snacks/Sweets |
| [M03](M03-recipes-admin.md) | Recipes & admin authoring | Owner-authored recipes (price/images/desc) |
| [M04](M04-customization.md) | Customization | Per-item ingredient & preparation choices |
| [M05](M05-cart-order.md) | Cart & ordering | Cart, checkout, order creation |
| [M06](M06-payment-upi-cycle.md) | UPI payment cycle | QR invoice → in-app proof → confirm gate |
| [M07](M07-order-tracking.md) | Order tracking engine | Lifecycle state machine + stage events |
| [M08](M08-notifications.md) | Notifications | Delivery transport (email now, WhatsApp/push later) |
| [M09](M09-admin-console.md) | Admin console | Owner's single control surface |
| [M10](M10-rating-feedback.md) | Rating & feedback | Customer 1–5★ + ≤100-char note |
| *(later)* M11 | Healthiness engine | ON HOLD — auto star score (not in these contracts) |
| [M12](M12-chef-social.md) | Chef profile & social | About-Chef page + per-recipe "Check Chef style" (Instagram) |

---

## Shared conventions (apply to every contract)

These are stated **once** here; individual contracts assume them.

### API
- **Base path:** `/api/v1/` on the Django `app` container (host port **6061**).
- **Format:** JSON request/response; `Content-Type: application/json`, except file
  uploads which are `multipart/form-data`.
- **Versioned:** breaking changes bump `/v1/ → /v2/`.

### Identifiers & types
- **IDs:** integer auto PKs, exposed as `id` (e.g. `42`).
- **Timestamps:** ISO-8601 UTC strings (`2026-07-04T10:30:00Z`), field suffix `_at`.
- **Money:** stored `DECIMAL(8,2)`, currency **INR**; JSON as string `"120.00"`.
- **Enums:** UPPER_SNAKE_CASE string constants (e.g. `PREPARING`).

### Roles & auth (defined fully in M01; summarized here)
- **Public** — no auth; menu **reads** only.
- **Client** — `Authorization: Bearer <client-token>`; issued at registration; no
  password in v1. Acts only on **own** resources (`🔒`).
- **Admin** — Django staff account (username + password) → admin token/session.
  Allow-listed for menu/payment/order-state/rating-view actions.
- **Deny by default**: any write is rejected unless the caller's role permits it.

### Errors (uniform envelope)
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "phone is required", "field": "phone" } }
```
| HTTP | `code` examples | Meaning |
|---|---|---|
| 400 | `VALIDATION_ERROR` | bad/missing input |
| 401 | `AUTH_REQUIRED` | no/expired token |
| 403 | `FORBIDDEN` | role not allowed / not owner |
| 404 | `NOT_FOUND` | resource missing |
| 409 | `STATE_CONFLICT` | illegal state transition |
| 409 | `STORE_CLOSED` | checkout while business is closed (M09) |
| 409 | `RECIPE_UNAVAILABLE` | recipe not `AVAILABLE` at add-to-cart/checkout (M03/M05) |
| 413 | `FILE_TOO_LARGE` | upload over limit |

### Images / uploads
- Stored on a **local media volume** in dev (`/media/...`), served by Django as URLs.
- Limits: images ≤ **5 MB**, types `jpeg/png/webp`. Payment proof same limits.

### Contract template (each file follows this)
`1. Purpose` · `2. Scope (in/out)` · `3. Actors & authorization` · `4. Data model`
· `5. API surface` · `6. Rules & invariants` · `7. States` (if any) ·
`8. Dependencies & seams` · `9. Acceptance criteria`.

### Cross-module data ownership (avoids overlap)
| Entity | Owned by | Read by |
|---|---|---|
| `User` (Client/Admin) | M01 | all |
| `Section`, `Recipe` | M03 | M02, M04, M05 |
| `CustomizationGroup/Option` | M04 | M03, M05 |
| `Cart`, `CartItem` | M05 | M06 |
| `Order`, `OrderItem` | M05 | M06, M07, M09, M10 |
| `PaymentProof` | M06 | M07, M09 |
| `OrderEvent` (state log) | M07 | M08, M09 |
| `Notification` | M08 | M09 |
| `Rating` | M10 | M09 |
| `AdminSettings`, `BusinessClosure` | M09 | M02 (store status), M05 (checkout), M06 |
