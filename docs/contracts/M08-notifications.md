# M08 — Notifications (Contract)

> **Status:** DRAFT v1 · Traces to architecture §8 note (M07 decides *what/when*, M08
> decides *how*) · Shared conventions in [README](README.md).
> **Depends on:** M07 (stage events), M06 (payment ping). **Used by:** M06, M07, M09.

---

## 1. Purpose

Be the **delivery transport** for every outbound message. Other modules say *what* to
send and *to whom*; M08 decides *how* it's delivered and records the attempt. Channels
plug in behind one interface so **email works now** and **WhatsApp/push** slot in later
with no caller changes.

## 2. Scope

**In v1:** an internal `notify()` interface; an **Email** channel (live); an
**in-app/status** channel (client polls order tracking); a persisted `Notification`
log; templates for each event type. **WhatsApp** and **push** are stubbed adapters
behind the same interface.

**Out (later):** live WhatsApp Business Cloud API, Expo push notifications, SMS,
delivery-receipt tracking, user notification preferences/opt-out.

## 3. Actors & authorization

| Action | Guest | Client | Admin |
|---|---|---|---|
| Receive notifications | 🚫 | ✅ (own order events) | ✅ (owner alerts) |
| Trigger a send | — | via M06/M07 (system) | via M09/system |
| View notification log | 🚫 | 🚫 | ✅ |

M08 is **system-invoked**; there is no public "send" endpoint.

## 4. Data model

**`Notification`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `event_type` | enum | `ORDER_PLACED`, `ORDER_ACCEPTED`, `ORDER_PREPARING`, `ORDER_READY`, `ORDER_COMPLETED`, `PAYMENT_SUBMITTED_OWNER`, `PAYMENT_REJECTED`, `ORDER_CANCELLED` |
| `channel` | enum `EMAIL`\|`INAPP`\|`WHATSAPP`\|`PUSH` | WHATSAPP/PUSH stubbed |
| `recipient_role` | enum `CLIENT`\|`ADMIN` | |
| `recipient_ref` | varchar | email/phone/user_id |
| `order_id` | FK → Order | nullable |
| `payload` | json | rendered template vars |
| `status` | enum `QUEUED`\|`SENT`\|`FAILED` | |
| `error` | varchar(200) | on failure |
| `created_at`/`sent_at` | datetime | |

## 5. Interface (internal, not a public HTTP API)

```python
notify(event_type, order, recipients=[…], channels=[EMAIL, INAPP]) -> [Notification]
```
- Called by **M07** on every `customer_stage` event and by **M06** for the owner
  "payment received?" ping.
- Channel adapters implement `send(notification) -> status`. Adding WhatsApp = one new
  adapter; callers unchanged.

**Admin (HTTP):**
- `GET /api/v1/admin/notifications?order={id}` — the delivery log (`IsAdmin`).

## 6. Rules & invariants

- **R1** M08 never decides *whether* an event happened — it only delivers what M06/M07
  hand it (single source of truth stays with the engine).
- **R2** One `Notification` row per (event, channel, recipient); sends are **idempotent**
  per stage so a retried transition never double-notifies.
- **R3** A failed channel (`FAILED`) never blocks the order state machine — delivery is
  best-effort and logged.
- **R4** The **owner payment ping** goes to Email now (and WhatsApp when the adapter is
  live), carrying invoice + proof link.
- **R5** Client stage notices go to **Email + in-app status**; the in-app channel is
  always available (client polls M07 `/tracking`).
- **R6** Channel set is config-driven; enabling WhatsApp/push requires **no caller code
  change** (R1 of the "pluggable notifier" seam).

## 7. States

Per-notification: `QUEUED → SENT | FAILED`. No cross-entity lifecycle.

## 8. Dependencies & seams

- **M07/M06** are the only callers; **M09** reads the log.
- **Seam:** `WhatsAppAdapter` (Cloud API / Twilio bridge) and `ExpoPushAdapter` drop in
  behind `send()`; `NotificationPreference` per user can gate channels later.

## 9. Acceptance criteria

- [ ] Each M07 stage event creates a `Notification` and sends the **email** (in dev, a
      console/SMTP catcher) + exposes the in-app status.
- [ ] Payment upload triggers the **owner** ping with invoice + proof reference.
- [ ] A duplicated/retried transition does **not** produce a second stage notice (R2).
- [ ] An email send failure marks `FAILED` but the order still advances (R3).
- [ ] Enabling the WhatsApp stub adds rows with `channel=WHATSAPP` without changing
      M06/M07 code.
- [ ] Admin can list the delivery log for an order; clients cannot.
