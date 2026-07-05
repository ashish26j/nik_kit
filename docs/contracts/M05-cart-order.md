# M05 — Cart & Ordering (Contract)

> **Status:** DRAFT v1 · Traces to blueprint §4 experience steps 3–4 · Shared
> conventions in [README](README.md).
> **Depends on:** M01 (client token at checkout), M03/M04 (items + options + price).
> **Depended on by:** M06 (payment), M07 (lifecycle), M09 (admin), M10 (rate order).

---

## 1. Purpose

Turn browsing into an order: a **cart** (buildable while anonymous), a **light
checkout** that registers the client, and an **`Order`** created in state `PLACED` —
the entry point of the M07 lifecycle.

## 2. Scope

**In v1:** add/update/remove cart items with customization; cart totals; checkout
(register via M01 if needed) → create Order (pickup only); list own orders; order
detail. **Server computes all prices.**

**Out (later):** delivery/addresses, scheduling/slots, coupons/discounts, tips,
multi-outlet, saved carts across devices, partial cancellation.

## 3. Actors & authorization

| Action | Guest | Client | Admin |
|---|---|---|---|
| Build/modify a cart | ✅ (anon cart) | ✅ | ✅ |
| View cart totals | ✅ | ✅ | ✅ |
| **Checkout / place order** | 🚫 → must register | ✅ | ✅ (on behalf) |
| List / view orders | 🚫 | 🔒 own only | ✅ all |
| Cancel own order (pre-accept) | 🚫 | 🔒 own, only in `PLACED`/`PAYMENT_*` | ✅ any |

## 4. Data model

**`Cart`** — `id`, `client_id` (nullable while anon), `session_key` (anon cart),
`created_at`. One active cart per client/session.

**`CartItem`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `cart_id` | FK → Cart | |
| `recipe_id` | FK → Recipe (M03) | |
| `qty` | int ≥1 | |
| `selected_options` | json | list of `option_id` (validated vs M04) |
| `unit_price` | DECIMAL(8,2) | computed = recipe.price + Σ deltas |

**`Order`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `code` | varchar(12) | human ref, e.g. `NK-0007` |
| `client_id` | FK → User (CLIENT) | required |
| `status` | enum | M07 states; starts `PLACED` |
| `subtotal` / `total` | DECIMAL(8,2) | server-computed |
| `fulfilment` | enum `PICKUP` | v1 fixed |
| `created_at` / `updated_at` | datetime | |

**`OrderItem`** (immutable snapshot)
`id`, `order_id`, `recipe_name`, `unit_price`, `qty`, `line_total`,
`options_snapshot` (json: labels + deltas at order time).

## 5. API surface

### Cart (public/anon or client)
- `POST /api/v1/cart/items` — `{ recipe_id, qty, selected_options[] }` → validates
  required groups (M04 R1), computes `unit_price`. Rejects recipes whose
  `display_status` ≠ `AVAILABLE` (`409 STATE_CONFLICT`, `RECIPE_UNAVAILABLE`).
- `PATCH /api/v1/cart/items/{id}` — qty/options.
- `DELETE /api/v1/cart/items/{id}`.
- `GET /api/v1/cart` — items + computed `subtotal`/`total`.

### Checkout (client)
- `POST /api/v1/orders` — creates the order from the caller's cart.
  Requires a **client token**; if the caller is anon, they call M01
  `/auth/register` first (front-end merges the anon cart to the new client).
```json
// POST /orders  (Bearer client-token)
{ "cart_id": 88, "fulfilment": "PICKUP", "note": "less oil" }
// 201
{ "id": 7, "code": "NK-0007", "status": "PLACED", "total": "180.00",
  "items": [ … snapshots … ] }
```
Errors: `400` (empty cart / invalid options), `401` (no client token), `409`
(cart already ordered · `STORE_CLOSED` · a line's recipe no longer `AVAILABLE`).

### Orders (client `🔒` / admin all)
- `GET /api/v1/orders` — own list (admin: all, filterable).
- `GET /api/v1/orders/{id}` — detail incl. current status (M07) + payment (M06).
- `POST /api/v1/orders/{id}/cancel` — allowed only in `PLACED`/`PAYMENT_SUBMITTED`/
  `PAYMENT_REJECTED` (client) → `409` otherwise.

## 6. Rules & invariants

- **R1** **All prices computed server-side** from M03/M04; client-sent prices ignored.
- **R2** Checkout requires a valid client token (M01 R2) — the only friction gate.
- **R2a** A recipe can be **added/ordered only when `display_status == AVAILABLE`**;
  `UNAVAILABLE`/`HIDDEN` items are rejected at add-to-cart and re-checked at checkout.
- **R2b** Checkout is **rejected while the business is closed** (M09 store status) with
  `409 STORE_CLOSED`; browsing and cart-building stay allowed (explore-first preserved).
- **R3** Creating an order **snapshots** each line (name, unit_price, options) into
  `OrderItem`; the cart is then closed.
- **R4** New order `status = PLACED`; all further transitions are owned by **M07**
  (M05 never sets `PREPARING`, etc.).
- **R5** An anon cart merges into the client on registration (match by session_key).
- **R6** Cancellation is only legal before acceptance; post-`ACCEPTED` is admin-only.
- **R7** `code` is unique, human-friendly, generated at creation.

## 7. States

M05 sets only the **entry** state `PLACED`. The full machine
(`PLACED → … → COMPLETED`) is defined in **M07**. Cancellation adds a terminal
`CANCELLED` (from pre-accept states only).

## 8. Dependencies & seams

- **M06** reads the order to attach the payment cycle; **M07** drives status from
  `PLACED` onward; **M10** allows rating once `COMPLETED`.
- **Seam:** `fulfilment` enum extends to `DELIVERY`; `address`, `coupon_id`, `tip`
  fields add without breaking snapshots.

## 9. Acceptance criteria

- [ ] Anonymous user adds items to a cart and sees a correct server-computed total.
- [ ] Checkout without a client token returns `401`; after register, succeeds.
- [ ] Adding an `UNAVAILABLE`/`HIDDEN` recipe to cart is rejected (`RECIPE_UNAVAILABLE`).
- [ ] Checkout while the business is closed returns `409 STORE_CLOSED`; browsing/cart
      still work.
- [ ] Placing an order creates immutable `OrderItem` snapshots and closes the cart.
- [ ] New order is `PLACED`; M05 exposes it to M06/M07.
- [ ] A client sees only their own orders; admin sees all.
- [ ] Cancel works in `PLACED`, is rejected (`409`) once `ACCEPTED`.
