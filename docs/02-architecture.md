# Nik_kiT — Development Architecture & Infrastructure Model

> **Audience:** the team, for shared reference during development.
> **Purpose:** the single agreed picture of *what we build, with what, and how it
> runs* — locally now and in production later. Pairs with
> [`01-toolchain-explained.md`](01-toolchain-explained.md) (the "why it works" doc).
>
> **Status:** architecture LOCKED. Module contracts & phased roadmap come next.

---

## 1. Locked decisions (the agreements)

| Area | Decision | Notes |
|---|---|---|
| **Product** | Nik_kiT — lightweight food-ordering app | Menu: Parathas, Snacks, Sweets |
| **Frontend / mobile** | **Expo (React Native + Web)** — one codebase | Android + iOS + Browser from one source |
| **Phase 1 targets** | **Android + Browser** | iOS deferred (same code, no rewrite) |
| **App-store presence** | Yes, eventually | Develop → test → then publish |
| **Backend** | **Django REST API** (Python) | The "brain"; serves data over REST |
| **Database** | **MySQL** | Users, menu, recipes, orders, payment proofs |
| **Containers** | **3** — `ui`, `app`, `db` | via Docker Compose (local dev) |
| **Payments** | **Manual UPI + reconciliation** | No gateway yet — QR → upload proof → WhatsApp/Email confirm |
| **Healthiness stars** | **ON HOLD** | Clean seam left; designed later |
| **Dev machine** | macOS (M4 Pro, 48 GB) | Emulator not needed — use real phone via Expo Go |
| **Editor** | Cursor | React Native + Expo on frontend; Django on backend |

---

## 2. Tech stack

```
Frontend (one codebase)   React Native + Expo  ·  React Native Web (browser)
Backend                   Python · Django · Django REST Framework
Database                  MySQL
Container/runtime         Docker + Docker Compose
Dev tooling               Cursor (editor) · Metro (dev server) · Expo Go (phone)
Cloud build (later)       EAS Build / EAS Submit (Play Store, then App Store)
Notifications             Email (now) · WhatsApp Business API / bridge (pluggable)
```

---

## 3. Repository structure (proposed)

Everything lives under `git_repos/zz-misc/wiz4/nik_kit/`. Two codebases, one repo.

```
nik_kit/
├── raw_input                     # original requirement (kept for provenance)
├── README.md                     # project overview + how to run
├── docs/
│   ├── 01-toolchain-explained.md # Expo/Metro/Expo Go/backend — team learning
│   ├── 02-architecture.md        # THIS FILE — infra & architecture model
│   ├── blueprint.md              # (next) the product vision / north star
│   └── contracts/                # (next) one contract per module
│       ├── M01-auth.md
│       ├── M02-menu.md
│       ├── M03-recipes-admin.md
│       ├── M04-customization.md
│       ├── M05-cart-order.md
│       ├── M06-payment-upi-cycle.md
│       ├── M07-order-tracking.md
│       ├── M08-notifications.md
│       ├── M09-admin-console.md
│       └── M10-rating-feedback.md
├── frontend/                     # React Native + Expo app (Android + iOS + Web)
│   ├── app/                      # screens / navigation
│   ├── components/               # reusable UI (foody vibe)
│   ├── services/                 # API client → talks to backend
│   ├── config/                   # API base URL (LAN IP), env
│   └── app.json / package.json
├── backend/                      # Django project
│   ├── nikkit/                   # Django settings/urls/wsgi
│   ├── apps/                     # Django apps per domain (users, menu, orders, payments)
│   ├── requirements.txt
│   └── manage.py
├── infra/
│   ├── docker-compose.yml        # ui + app + db
│   ├── app.Dockerfile            # Django image
│   ├── ui.Dockerfile             # web build image
│   └── env/                      # .env templates (never commit secrets)
└── progress/
    └── tracker.json              # single source of truth for phases/steps (WCAS-style)
```

> Note: the **mobile app is not a container** — it runs on the phone (Expo Go in dev,
> installed app in prod). The `ui` container serves the **web** build only.

---

## 4. The 3 containers (what each runs)

| Container | Runs | Serves | Always on in dev? |
|---|---|---|---|
| **`db`** | MySQL | The database (users, menu, recipes, orders, payment proofs) | ✅ Yes |
| **`app`** | Django + DRF | The REST API — data to phone **and** browser | ✅ Yes |
| **`ui`** | Web build of the frontend | The **browser** experience only | ⏳ When testing web |

**Not containers** (by design):
- **Metro** (Expo dev server) → runs on the **host** (Mac) for a fast phone loop.
- **The Nik_kiT mobile app** → runs on the **phone** (Expo Go / installed app).

---

## 5. Local development topology

```
   YOUR LAPTOP (M4 Pro, 48 GB)                        YOUR ANDROID PHONE
   ┌────────────────────────────────────┐            ┌──────────────────┐
   │  Cursor  — write code               │            │                  │
   │    frontend/ (React Native + Expo)  │            │     Expo Go       │
   │    backend/  (Django)               │            │  runs Nik_kiT app │
   │                                     │            │                  │
   │  Metro (host)  ── serves CODE ──────┼──── WiFi ──┤ ◄─ pulls code     │
   │                                     │            │                  │
   │  Docker:                            │            │                  │
   │    app (Django)  ── serves DATA ────┼──── WiFi ──┤ ◄─ REST calls     │
   │    db  (MySQL)                       │            │                  │
   │    ui  (web build) ── browser ──────┼─► localhost (web testing)      │
   └────────────────────────────────────┘            └──────────────────┘
```

**Two things run on the laptop during dev:** Metro (code) + Docker `app`/`db` (data).
Both reachable from the phone over the **same Wi-Fi**.

---

## 6. Networking rules (bake these into setup)

There are **two outbound connections from the app**, both phone → laptop:

| From the app | To (example) | Purpose |
|---|---|---|
| `→ Metro` | `http://<laptop-LAN-IP>:6060` | download the **code** bundle (dev only) |
| `→ Django` | `http://<laptop-LAN-IP>:6061` | fetch/send **data** (menu, orders, proof) |

Rules:
- **Real phone:** must share **Wi-Fi** with the laptop; use the laptop's **LAN IP**
  (never `localhost` — on a phone that means the phone).
- **Android emulator (if ever used):** reaches the host via the special IP `10.0.2.2`.
- **Docker port publishing:** `app` maps `6061→6061`, `db` maps `3306→3306` (internal),
  `ui` maps its web port. Only publish what's needed.

---

## 7. Dev → Production pipeline

```
                DEVELOPMENT (now)                 PRODUCTION (later)
Build           React Native + Expo               same code
Compile         Metro (local, live)               EAS (cloud build)
Deploy & Run    Expo Go on phone                  Play Store app  (Android)
                Browser (localhost)               Website (ui container / hosting)
Backend         Docker app + db (laptop)          hosted Django + MySQL
```

- **Android release path:** `EAS Build` → `.aab` → `EAS Submit` → Play Store
  (Google Play developer account, one-time \$25).
- **iOS release path (later):** same code, flip on iOS target → `EAS Build` → App Store
  (Apple Developer account, \$99/yr; Mac already available).
- **Web release path:** build the frontend for web → serve via `ui` container / host.

---

## 8. Order lifecycle & payment cycle (architectural — full contract comes later)

One canonical order lifecycle, owned by the **Order Tracking Engine (M07)**, which
fires a **customer notification on every transition**. The manual UPI **payment cycle**
is the sub-flow between `PLACED` and `ACCEPTED` (mirrors the WCAS "approval gate"
pattern — no gateway in v1).

```
 CART → PLACED → PAYMENT_SUBMITTED ─┬─ (owner: Yes) → PAYMENT_CONFIRMED ─┐
                                    └─ (owner: No)  → PAYMENT_REJECTED    │ (re-upload → back to submit)
                                                                         ▼
                    ACCEPTED → PREPARING → READY_FOR_PICKUP → COMPLETED
```

1. Order placed → `PLACED`; invoice with **UPI QR** (business UPI ID) shown **in-app**.
2. Customer pays in their own UPI app → returns to Nik_kiT, which has **auto-advanced
   to an in-app "Upload payment screenshot" screen** → they attach the proof against
   that invoice (from photo library / camera). Proof capture never leaves the app.
3. On submit, order → `PAYMENT_SUBMITTED`.
4. System notifies **business** on **WhatsApp + Email**: "Payment received? (Yes/No)"
   with invoice + proof.
5. Owner **Yes** → `PAYMENT_CONFIRMED` → order **ACCEPTED** (kitchen proceeds).
   Owner **No** → `PAYMENT_REJECTED` (customer re-uploads → back to step 2).
6. Kitchen advances the order: `ACCEPTED → PREPARING → READY_FOR_PICKUP → COMPLETED`
   — each an **Admin-only** action, each notifying the customer.

### Customer-facing stages (what M07 notifies)

| # | Customer sees | Internal state | Triggered by |
|---|---|---|---|
| 1 | **Order placed** | `PLACED` | customer checkout |
| 2 | **Order accepted** | `PAYMENT_CONFIRMED` → `ACCEPTED` | owner confirms payment (Yes) |
| 3 | **In preparation** | `PREPARING` | owner / kitchen |
| 4 | **Ready to pick up** | `READY_FOR_PICKUP` | owner / kitchen |
| 5 | **Order completed** | `COMPLETED` | owner / kitchen |

> The payment sub-states (`PAYMENT_SUBMITTED`, `PAYMENT_REJECTED`) surface to the
> customer as an interstitial "payment under review / please re-upload" status — not
> one of the five headline stages. M07 owns the states & *when* to notify; **M08
> Notifications** owns *how* it's delivered (email now, WhatsApp later).

Notes:
- Payment proof image → storage (local volume in dev), attached to invoice for audit.
- **WhatsApp** automation needs the **WhatsApp Business Cloud API** or a bridge
  (e.g. Twilio) — an external prerequisite. Email works immediately. We put both
  behind a `notifier` interface so WhatsApp plugs in without code changes.

---

## 9. Module map (preview — contracts to follow)

Decomposition of Nik_kiT into named, single-responsibility modules (WCAS Stage 2):

| ID | Module | Responsibility |
|---|---|---|
| **M01** | Auth / lightweight registration | Explore freely; capture First Name, Email, Phone at order time |
| **M02** | Menu & sections | Parathas / Snacks / Sweets browsing |
| **M03** | Recipes & admin authoring | Add recipe: price, images, description, per section; **display status** (available / not-available-greyed / hidden) |
| **M04** | Customization | Per-item ingredients + preparation method choices |
| **M05** | Cart & ordering | Cart → place order → order states |
| **M06** | UPI payment cycle | Invoice + QR → proof upload → confirm gate |
| **M07** | Order tracking engine | Owns the order lifecycle state machine; emits a customer notification at every stage (placed → accepted → preparing → ready for pickup → completed) |
| **M08** | Notifications | Delivery transport — Email now; WhatsApp pluggable (used by M06 + M07) |
| **M09** | Admin console | Manage menu/recipes/orders; confirm payments; advance order states; **business-closed dates**; set recipe display status |
| **M10** | Rating & feedback | Customer-submitted rating on a completed order: 1–5 **stars** + optional ≤100-char note. *Distinct from M11* — this is user satisfaction, not auto healthiness. |
| *(later)* | **M11** Healthiness engine | ON HOLD — **auto-computed** star rating from ingredients/prep (excl. Sweets); not customer-entered |
| **M12** | Chef profile & social | About-Chef page (bio + social icons) + per-recipe "Check Chef style of making" link. Instagram only in v1 (`bstvaranasi`), platform enum extensible |
| **M13** | Client account area | *(planned P7)* My Orders (history + status) + Profile (view/edit) + Email-OTP restore; token-gated, passwordless. Also: order **modes** (Order now / Order for later) live in M03 + M05 |

---

## 10. Build approach (WCAS-influenced)

Following the maturation pattern from
`../claude_memory/project_wcas_evolution.md`:

```
Blueprint (vision, one page)
  → Decompose (name every module — done above)
  → Contract each module (inputs/outputs/rules/states/success — BEFORE code)
  → Infrastructure first (Docker: db, app, ui skeleton; Expo app boots)
  → Build phase by phase, test at each gate with real data
  → Track progress in progress/tracker.json (single source of truth)
  → Fix real bugs from real runs
  → (later) Healthiness engine, hardening, monitoring
```

**Proposed phases:**

| Phase | Milestone (gate test) |
|---|---|
| **P0** | Infra up: 3 containers run; Expo app boots on phone; app reaches backend |
| **P1** | Menu + recipes visible (admin can author; user can browse Parathas/Snacks/Sweets) |
| **P2** | Customization + cart + place order (order reaches `PLACED`) |
| **P3** | UPI payment cycle end-to-end (proof upload → email confirm → `PAYMENT_CONFIRMED`) |
| **P4** | Admin console + customer ratings (M10) + WhatsApp notifications wired |
| **P5** | **Chef & Social (M12)** — About-Chef page + per-recipe "Check Chef style of making" (Instagram) |
| **P6** | **Order modes** — Order now (ready ~1h) / Order for later (scheduled); per-recipe admin toggle (M03 + M05) |
| **P7** | **Client account area + Email-OTP** — My Orders + Profile + passwordless account restore (M13 + M01) |
| **P8** | Web (browser) polish + PWA/parity; production hardening |
| **P9** | EAS build → Play Store; (iOS later) |
| *(later)* | Healthiness engine (M11); Learn-from-Chef bookings (feature C, unscoped) |

---

## 11. What's intentionally deferred

- **Healthiness star engine** — on hold; `M11` seam reserved. Note: the **M10 rating**
  (customer stars) is a *separate*, in-v1 module and must not be conflated with this
  auto-computed healthiness score.
- **iOS target** — deferred to a later phase (same codebase).
- **Payment gateway** — replaced by manual UPI cycle for now.
- **WhatsApp live channel** — stubbed behind `notifier`; email works first.

---

*Next step: write `docs/blueprint.md` (the one-page vision) and the per-module
contracts under `docs/contracts/`, then stand up P0 infrastructure.*
