# M09 — Admin Console (Contract)

> **Status:** DRAFT v1 · Traces to blueprint §2 owner persona ("one console") ·
> Shared conventions in [README](README.md).
> **Depends on:** M01 (IsAdmin), M03, M04, M05, M06, M07, M08, M10 (it surfaces them).

---

## 1. Purpose

The owner's **single control surface**. It doesn't own new business rules — it's the
authenticated UI + thin endpoints that let Nik run the kitchen: author the menu,
watch the order queue, confirm payments, advance orders, and read ratings.

## 2. Scope

**In v1:** admin login (M01); dashboards for **Menu/Recipes** (M03/M04) incl. setting
a recipe's **display status** (available / not-available-greyed / hidden), **Orders
queue** with state controls (M07), **Payments queue** confirm/reject (M06),
**Ratings** view (M10), **Notifications** log (M08), and **Business Closures**
(mark closed today / a date / a date range).

**Out (later):** analytics/reporting, multi-staff roles & permissions, exports,
settings UI for UPI id/business profile beyond a basic config screen, audit search.

## 3. Actors & authorization

| Action | Client | Admin |
|---|---|---|
| Access **any** admin screen/endpoint | 🚫 | ✅ |
| Author menu/recipes/customization | 🚫 | ✅ (M03/M04) |
| Confirm/reject payment | 🚫 | ✅ (M06) |
| Advance/cancel order state | 🚫 | ✅ (M07) |
| Set recipe **display status** (available / not-available / hidden) | 🚫 | ✅ (M03) |
| Mark business **closed** (today / date / range) | 🚫 | ✅ |
| View all orders / ratings / notifications | 🚫 | ✅ |

**Everything under `/api/v1/admin/**` requires `IsAdmin`.** This is the enforcement
choke point for the "money & kitchen = admin only" rule (blueprint §3).

## 4. Data model

Mostly a composition/read-through layer, plus two small business-config entities it
owns:

**`AdminSettings`** (singleton): `business_upi_id`, `business_name`, `contact_email`
— used by M06 intents and M08 emails.

**`BusinessClosure`** (the "we're closed" control)
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `start_date` | date | required |
| `end_date` | date | required; = `start_date` for a single day ("closed today") |
| `message` | varchar(140) | optional; shown on the storefront banner |
| `created_by` | FK → User (ADMIN) | |
| `created_at` | datetime | |

> "Closed today" = a closure with `start_date = end_date = today`. A range is any
> `start_date … end_date`. **Store is closed** if today falls within any closure.

## 4a. Store-open logic (owned here, read publicly via M02)

`is_open(now)` = **false** if today ∈ any `BusinessClosure` range, else **true**.
(v1 has no recurring weekly hours — that's a later seam.) The public
`GET /api/v1/store/status` (documented in M02) reads this; **M05 checkout** calls it
to enforce `STORE_CLOSED`.

## 5. API surface (all `IsAdmin`; most defined in their owning module)

M09 groups them into the console; it adds only dashboard/aggregate reads:

- **Menu:** M03/M04 admin endpoints (`/admin/sections`, `/admin/recipes`,
  `/admin/customization/*`).
- **Orders queue:** `GET /api/v1/admin/orders?status=…` (M05 read) +
  `POST /admin/orders/{id}/advance|cancel` (M07).
- **Payments queue:** `GET /api/v1/admin/payments?status=PENDING` +
  confirm/reject (M06).
- **Ratings:** `GET /api/v1/admin/ratings` (M10).
- **Notifications:** `GET /api/v1/admin/notifications` (M08).
- **Dashboard (new here):** `GET /api/v1/admin/dashboard` — counts by status,
  today's orders, pending payments, latest ratings.
- **Settings (new here):** `GET/PATCH /api/v1/admin/settings` — UPI id, business name,
  contact email.
- **Closures (new here):** `GET /api/v1/admin/closures` · `POST /api/v1/admin/closures`
  `{ start_date, end_date, message }` (single day → equal dates) ·
  `DELETE /api/v1/admin/closures/{id}` (reopen). Public read is `GET /store/status`
  (M02).

```json
// GET /admin/dashboard
{ "orders_today": 12, "pending_payments": 3,
  "by_status": { "PLACED": 1, "PREPARING": 2, "READY_FOR_PICKUP": 1 },
  "avg_rating": 4.6 }
```

## 6. Rules & invariants

- **R1** M09 **adds no business logic** it doesn't already delegate; state changes go
  through the owning module (M07 for status, M06 for payment) so invariants hold once.
- **R2** All admin endpoints deny non-admins (`403`) — single enforcement layer.
- **R3** `AdminSettings.business_upi_id` is the source for M06 payment intents; changing
  it affects only **future** orders (existing intents froze their `upi_id`).
- **R4** Destructive actions (delete recipe/section) obey M03 rules (soft-delete /
  `409`).
- **R6** A `BusinessClosure` covering today makes `store/status.is_open=false`; this
  **blocks M05 checkout** (`STORE_CLOSED`) but never blocks browsing/cart-building.
- **R7** Deleting a closure (or its range passing) reopens the store automatically;
  closures are additive (overlaps are fine — closed if any matches).
- **R8** Recipe display status is set here but the field & visibility rules are owned by
  **M03** (M09 is just the UI/endpoint) — no duplicated logic.
- **R5** The console is a **client of the same REST API** (no privileged back-door);
  it works on web now and could be a screen-set in the Expo app.

## 7. States

None of its own; reflects M05/M06/M07 order states and M10 ratings.

## 8. Dependencies & seams

- Surfaces M03–M08 + M10.
- **Seam:** role/permission table for multi-staff; analytics endpoints; export jobs —
  all additive.

## 9. Acceptance criteria

- [ ] Admin logs in and reaches the dashboard; a client token gets `403` on any
      `/admin/**` route.
- [ ] Admin authors a recipe and it appears in public browse (M02).
- [ ] Payments queue lists PENDING proofs; confirming one moves the order to `ACCEPTED`
      (via M06→M07) and notifies the client (M08).
- [ ] Orders queue advances an order through kitchen states; each emits its stage.
- [ ] Ratings view shows submitted ratings; dashboard shows `avg_rating`.
- [ ] Changing `business_upi_id` in settings affects only new orders' QR.
- [ ] Marking "closed today" flips `GET /store/status` to `is_open=false` and makes
      M05 checkout return `409 STORE_CLOSED`; browsing still works; deleting the closure
      reopens.
- [ ] Setting a recipe's `display_status` from the console reflects in public browse
      (greyed for `UNAVAILABLE`, gone for `HIDDEN`).
