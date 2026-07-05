# M07 — Order Tracking Engine (Contract)

> **Status:** DRAFT v1 · Traces to architecture §8 · Shared conventions in
> [README](README.md).
> **Depends on:** M05 (order), M06 (payment transitions). **Feeds:** M08 (notify),
> M09 (admin controls), M10 (rate on `COMPLETED`).

---

## 1. Purpose

Own the **single canonical order lifecycle** and be the **only** component that
changes `Order.status`. Validate every transition, log it, and emit a **stage event**
so the customer is notified at each step: **placed → accepted → preparing → ready to
pick up → completed**.

## 2. Scope

**In v1:** the state machine + guards; append-only `OrderEvent` log; emit events to
M08; admin actions to advance/rewind within legal bounds; expose current status +
history to M05/M09.

**Out (later):** ETAs/time estimates, live courier tracking, SLA timers, auto-advance
rules, per-item station tracking.

## 3. Actors & authorization

| Action | Guest | Client | Admin |
|---|---|---|---|
| View own order status + history | 🚫 | 🔒 own | ✅ all |
| Trigger payment transitions | 🚫 | via M06 (own) | ✅ (confirm/reject) |
| Advance kitchen states (`ACCEPTED→…→COMPLETED`) | 🚫 | 🚫 | ✅ |
| Cancel | 🔒 pre-accept (via M05) | 🔒 pre-accept | ✅ any |

> Advancing kitchen states is **Admin-only** (money & kitchen lever, blueprint §3).

## 4. Data model

**`Order.status`** — enum owned here:
```
PLACED · PAYMENT_SUBMITTED · PAYMENT_REJECTED · PAYMENT_CONFIRMED ·
ACCEPTED · PREPARING · READY_FOR_PICKUP · COMPLETED · CANCELLED
```

**`OrderEvent`** (append-only audit + notification source)
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `order_id` | FK → Order | |
| `from_status` | enum | null for the first event |
| `to_status` | enum | |
| `actor_id` | FK → User | who triggered (client/admin/system) |
| `reason` | varchar(140) | e.g. reject reason |
| `created_at` | datetime | |
| `customer_stage` | enum \| null | the headline stage to notify (below), else null |

## 5. Transition table (the machine)

| From | Event / trigger | To | By | Customer stage notified |
|---|---|---|---|---|
| — | order created (M05) | `PLACED` | client | **Order placed** |
| `PLACED` | proof upload (M06) | `PAYMENT_SUBMITTED` | client | *(interstitial: under review)* |
| `PAYMENT_SUBMITTED` | admin reject (M06) | `PAYMENT_REJECTED` | admin | *(interstitial: re-upload)* |
| `PAYMENT_REJECTED` | re-upload (M06) | `PAYMENT_SUBMITTED` | client | *(interstitial)* |
| `PAYMENT_SUBMITTED` | admin confirm (M06) | `PAYMENT_CONFIRMED` → `ACCEPTED` | admin | **Order accepted** |
| `ACCEPTED` | admin start | `PREPARING` | admin | **In preparation** |
| `PREPARING` | admin ready | `READY_FOR_PICKUP` | admin | **Ready to pick up** |
| `READY_FOR_PICKUP` | admin complete | `COMPLETED` | admin | **Order completed** |
| `PLACED`/`PAYMENT_SUBMITTED`/`PAYMENT_REJECTED` | cancel | `CANCELLED` | client/admin | *(cancelled)* |
| `ACCEPTED`+ | admin cancel | `CANCELLED` | admin only | *(cancelled)* |

`PAYMENT_CONFIRMED` is transient — the engine moves straight to `ACCEPTED` in the same
step (customer sees one "accepted").

## 6. API surface

### Client
- `GET /api/v1/orders/{id}/tracking` — `{ status, customer_stage, history[] }` (🔒 own).

### Admin
- `POST /api/v1/admin/orders/{id}/advance` — `{ "to": "PREPARING" }` — validates the
  transition is legal from current status; else `409 STATE_CONFLICT`.
- `POST /api/v1/admin/orders/{id}/cancel` — `{ "reason": "…" }`.
- Payment confirm/reject live in **M06** but call this engine to perform the transition.

## 7. Rules & invariants

- **R1** `Order.status` is written **only** by M07. M05 sets the initial `PLACED` via
  M07's create hook; M06 requests payment transitions through M07.
- **R2** Every transition **must** be in the table above, else rejected `409`.
- **R3** Every accepted transition appends one **immutable `OrderEvent`**.
- **R4** When an event carries a `customer_stage`, M07 emits a notification request to
  **M08** (idempotent per stage — no duplicate stage notices).
- **R5** Terminal states (`COMPLETED`, `CANCELLED`) accept no further transitions.
- **R6** Kitchen advances require `IsAdmin`; only pre-accept cancels are client-allowed.
- **R7** `COMPLETED` unlocks rating (M10).

## 8. Dependencies & seams

- **M06** drives the payment sub-flow; **M08** delivers stage notifications; **M09**
  provides the admin advance/cancel buttons; **M10** gates on `COMPLETED`.
- **Seam:** add `estimated_ready_at` + timer-driven auto-advance without changing
  states; add a `DELIVERY` branch after `READY_FOR_PICKUP`.

## 9. Acceptance criteria

- [ ] A new order logs a `PLACED` event and notifies "Order placed".
- [ ] Illegal jump (e.g. `PLACED → COMPLETED`) is rejected `409`.
- [ ] Admin confirm (M06) yields a single **ACCEPTED** and one "Order accepted" notice.
- [ ] Advancing `ACCEPTED → PREPARING → READY_FOR_PICKUP → COMPLETED` emits exactly
      those three customer stages, each once.
- [ ] `GET …/tracking` returns current stage + ordered history for the owner only.
- [ ] `COMPLETED`/`CANCELLED` reject further transitions; `COMPLETED` enables M10.
