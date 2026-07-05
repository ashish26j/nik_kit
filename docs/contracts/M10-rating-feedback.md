# M10 — Rating & Feedback (Contract)

> **Status:** DRAFT v1 · Traces to blueprint §3 matrix + scope · Shared conventions in
> [README](README.md).
> **Depends on:** M01 (client identity), M05/M07 (a `COMPLETED` order). **Read by:** M09.

---

## 1. Purpose

Let a customer leave a **tiny satisfaction rating** on a **completed** order: **1–5
stars** plus an **optional ≤100-character** note. Deliberately minimal.

> **Not** the healthiness engine. M10 is **customer-entered satisfaction**; the
> deferred **M11** auto-computes a *healthiness* star from ingredients/prep. Same word
> ("stars"), different meaning — never conflate (architecture §11).

## 2. Scope

**In v1:** one rating per completed order by its owner; stars 1–5; optional note
(≤100 chars); edit own rating; admin reads all + aggregate average.

**Out (later):** per-item ratings, photos, long reviews, replies, moderation queue,
public display of reviews, incentives.

## 3. Actors & authorization

| Action | Guest | Client | Admin |
|---|---|---|---|
| Rate an order | 🚫 | 🔒 own **COMPLETED** order | 🚫 (owner doesn't rate) |
| Edit own rating | 🚫 | 🔒 own | 🚫 |
| View a rating | 🚫 | 🔒 own | ✅ all |
| View aggregate (avg) | 🚫 | 🚫 | ✅ |

## 4. Data model

**`Rating`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `order_id` | FK → Order, **unique** | one rating per order |
| `client_id` | FK → User (CLIENT) | must equal order owner |
| `stars` | int | **1–5** inclusive |
| `note` | varchar(100) | optional, **≤100 chars** |
| `created_at`/`updated_at` | datetime | |

## 5. API surface

### Client (`🔒` own)
- `POST /api/v1/orders/{id}/rating` — `{ "stars": 5, "note": "Loved the aloo paratha" }`
  - allowed only if order is `COMPLETED` and owned by caller; else `403`/`409`.
  - one per order; a second `POST` → `409 STATE_CONFLICT` (use PATCH to change).
- `PATCH /api/v1/orders/{id}/rating` — edit own `stars`/`note`.
- `GET /api/v1/orders/{id}/rating` — own rating (or 404 if none).

### Admin
- `GET /api/v1/admin/ratings?min_stars=&order=` — list all.
- `GET /api/v1/admin/ratings/summary` — `{ "count": 128, "avg": 4.6,
  "distribution": {"5":80,"4":30,"3":10,"2":5,"1":3} }` (feeds M09 dashboard).

## 6. Rules & invariants

- **R1** `stars` ∈ [1,5]; `note` length ≤ 100 (server-enforced, not just UI).
- **R2** A rating requires the order to be **`COMPLETED`** (M07) and **owned** by the
  caller — else `409`/`403`.
- **R3** **One rating per order** (`order_id` unique); changes go through `PATCH`.
- **R4** `note` is optional; stars are required.
- **R5** Admins **read** ratings but cannot create/edit them (integrity of customer
  voice).
- **R6** Ratings never affect order state or price — purely informational in v1.

## 7. States

None. A `Rating` simply exists (created after `COMPLETED`) and may be edited by its
owner.

## 8. Dependencies & seams

- Gated by **M07** `COMPLETED`; surfaced by **M09** (list + avg).
- **Seam:** `recipe_id` can be added for per-item ratings; a `moderation_status` and
  public-review display can layer on without touching the core fields.
- **Explicitly independent of M11** (healthiness): no shared fields, no coupling.

## 9. Acceptance criteria

- [ ] Client can rate only their own **COMPLETED** order; rating a non-completed or
      others' order returns `409`/`403`.
- [ ] `stars` outside 1–5 or `note` > 100 chars is rejected `400`.
- [ ] A second create on the same order returns `409`; `PATCH` updates it.
- [ ] Admin sees all ratings and a correct `avg` in the dashboard (M09).
- [ ] Ratings do not change any order status or total.
- [ ] M10 shares no schema with the (deferred) M11 healthiness score.
