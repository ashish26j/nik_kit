# M06 — UPI Payment Cycle (Contract)

> **Status:** DRAFT v1 · Traces to architecture §8 (order lifecycle & payment cycle) ·
> Shared conventions in [README](README.md).
> **Depends on:** M05 (order), M01 (roles). **Feeds:** M07 (state), M08 (notify), M09.

---

## 1. Purpose

Collect payment **without a gateway**: show a **UPI QR + amount** in-app, let the
customer pay in their own UPI app, then **upload a screenshot** on the next in-app
screen. The **owner confirms** (Yes/No) — the manual reconciliation gate.

## 2. Scope

**In v1:** generate the UPI QR/intent for an order; the **in-app upload screen** for
the payment screenshot; store proof; owner **confirm/reject**; re-upload on reject.

**Out (later):** real payment gateway, auto-reconciliation, refunds, partial payments,
multiple proofs per order beyond re-upload.

## 3. Actors & authorization

| Action | Guest | Client | Admin |
|---|---|---|---|
| See order's UPI QR + amount | 🚫 | 🔒 own order | ✅ |
| Upload payment proof | 🚫 | 🔒 own order | ✅ (on behalf) |
| **Confirm / reject payment** | 🚫 | 🚫 | ✅ |
| View proof image | 🚫 | 🔒 own | ✅ all |

> **Confirm/reject is Admin-only** — one of the two money/kitchen levers (blueprint §3).

## 4. Data model

**`PaymentIntent`** (one per order)
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `order_id` | FK → Order (M05), unique | |
| `upi_id` | varchar | business UPI (config) |
| `amount` | DECIMAL(8,2) | = order.total (frozen) |
| `qr_payload` | text | UPI deep-link string encoded to QR client-side |
| `created_at` | datetime | |

**`PaymentProof`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `order_id` | FK → Order | |
| `image` | image | ≤5 MB, jpeg/png/webp |
| `uploaded_at` | datetime | |
| `is_current` | bool | latest re-upload = true |
| `decided_at` | datetime | when admin acted |
| `decision` | enum `PENDING`\|`CONFIRMED`\|`REJECTED` | |
| `decided_by` | FK → User (ADMIN) | |
| `reject_reason` | varchar(140) | optional |

## 5. API surface

### Client (`🔒` own order)
- `GET /api/v1/orders/{id}/payment` — returns `upi_id`, `amount`, `qr_payload`, and
  current proof decision. Used to render QR then the upload screen.
- `POST /api/v1/orders/{id}/payment/proof` — `multipart` image. Sets order
  `PAYMENT_SUBMITTED`, proof `decision=PENDING`, `is_current=true` (supersedes prior).

### Admin
- `GET /api/v1/admin/payments?status=PENDING` — queue of submitted proofs.
- `POST /api/v1/admin/orders/{id}/payment/confirm` — `{}` → proof `CONFIRMED`, order
  `PAYMENT_CONFIRMED → ACCEPTED` (M07).
- `POST /api/v1/admin/orders/{id}/payment/reject` — `{ "reason": "blurred" }` → proof
  `REJECTED`, order `PAYMENT_REJECTED`; client may re-upload.

```
render QR (GET payment) → pay in UPI app → app auto-advances →
POST proof (multipart) → PAYMENT_SUBMITTED → admin confirm/reject
```

## 6. Rules & invariants

- **R1** `amount` is frozen from `order.total` at intent creation; never client-set.
- **R2** Proof upload is only valid while order ∈ {`PLACED`,`PAYMENT_REJECTED`}; else
  `409 STATE_CONFLICT`.
- **R3** Uploading proof sets order → `PAYMENT_SUBMITTED` and pings the **owner** via
  M08 ("Payment received? Yes/No" + invoice + proof).
- **R4** **Confirm** → `PAYMENT_CONFIRMED` then immediately `ACCEPTED` (single owner
  action accepts the order); **Reject** → `PAYMENT_REJECTED`.
- **R5** Only **Admin** may confirm/reject (never a client).
- **R6** Re-upload supersedes prior proof (`is_current`) but retains history for audit.
- **R7** Proof capture is **in-app** (camera/library); the image is stored on the media
  volume, attached to the order.
- **R8** State writes here are delegated to **M07** (M06 requests transitions; M07
  validates legality).

## 7. States (payment sub-flow of M07)

```
PLACED ──upload──► PAYMENT_SUBMITTED ──confirm──► PAYMENT_CONFIRMED ─► ACCEPTED
                              │
                              └──reject──► PAYMENT_REJECTED ──re-upload──► PAYMENT_SUBMITTED
```

## 8. Dependencies & seams

- **M07** owns/validates the transitions; **M08** delivers owner + client alerts;
  **M09** renders the admin payments queue.
- **Seam:** a `Gateway` adapter can replace manual proof by satisfying the same
  "confirm" transition — the state machine is unchanged.

## 9. Acceptance criteria

- [ ] `GET …/payment` returns UPI id + frozen amount + QR payload for the owner's order.
- [ ] Uploading a proof moves the order to `PAYMENT_SUBMITTED` and notifies the owner.
- [ ] Admin **confirm** → order `ACCEPTED`; client notified; kitchen can proceed.
- [ ] Admin **reject** → `PAYMENT_REJECTED`; client can re-upload; new proof becomes
      current, old retained.
- [ ] A client cannot confirm their own payment (`403`).
- [ ] Uploading a proof on an already-`ACCEPTED` order returns `409`.
