# Nik_kiT — Blueprint (the one-page north star)

> **Audience:** the team — the *why* and *what*, not the *how*.
> **Purpose:** the single vision everything else must serve. When a decision is
> unclear, we come back to this page. Pairs with
> [`02-architecture.md`](02-architecture.md) (the *how it runs*) and the per-module
> contracts under [`contracts/`](contracts/) (the *exact behavior*).
>
> **Status:** DRAFT for review.

---

## 1. The one sentence

> **Nik_kiT** is a warm, modern little food-ordering app for home-style
> **Parathas, Snacks & Sweets** — where anyone can browse freely, customize a dish
> to taste, and check out in seconds with no account friction; and where the owner
> runs the whole kitchen — menu, recipes, orders and payments — from one simple
> console.

---

## 2. Who it's for

| Persona | What they want | What Nik_kiT gives them |
|---|---|---|
| **The hungry guest** (not logged in) | See the food, drool, order fast | Browse everything with zero sign-up; register *only* at checkout (name, email, phone) |
| **The returning customer** | Reorder favourites, track their order | Light identity by phone/email; order history & status |
| **The owner / admin** (Nik) | Sell food without a tech headache | One console to add recipes, set prices/images, take orders, confirm UPI payments |

> **Guiding tension we always resolve toward the guest:** never make someone sign up
> to *look*. Friction is only allowed at the moment money changes hands.

---

## 3. Roles & authorization (who can do what)

Nik_kiT has exactly **two roles** in v1: **Admin** and **Client**. The Client role
has two *states* — **Guest** (anonymous) and **Registered** (after light checkout
registration). Admin is the owner (Nik) and their staff.

### The two roles in one line

| Role | Who | In one line |
|---|---|---|
| **Admin** | Nik / kitchen staff | Runs the kitchen: authors the menu and controls every order & payment. |
| **Client** | Customers | Enjoys the food: browses freely, customizes, orders, pays, tracks. |

### Capability matrix

Legend: ✅ allowed · 🚫 denied · 🔒 own-records-only (a Client can only touch their
own cart/orders/data).

| Capability | Guest (anon Client) | Registered Client | Admin |
|---|---|---|---|
| Browse sections & items (Parathas/Snacks/Sweets) | ✅ | ✅ | ✅ |
| View recipe detail (description, image, price) | ✅ | ✅ | ✅ |
| Customize a dish (ingredients + prep) | ✅ | ✅ | ✅ |
| Build a cart | ✅ | ✅ | ✅ |
| **Checkout / place an order** | 🚫 → prompted to register | ✅ | ✅ (on behalf, optional) |
| Provide light identity (name, email, phone) | ✅ (this *is* registering) | already done | — |
| Upload UPI payment proof | 🚫 | 🔒 own order | ✅ |
| View order status & history | 🚫 | 🔒 own orders only | ✅ all orders |
| Rate a completed order (≤5★ + optional ≤100-char note) | 🚫 | 🔒 own completed order | ✅ view all ratings |
| **Confirm / reject a payment** (Yes/No gate) | 🚫 | 🚫 | ✅ |
| Advance order state (preparing → ready → done) | 🚫 | 🚫 | ✅ |
| **Create / edit / delete recipes** (price, images, desc, options) | 🚫 | 🚫 | ✅ |
| Set a recipe's **display** (available / not-available-greyed / hidden) | 🚫 | 🚫 | ✅ |
| Mark the business **closed** (today / a date / a date range) | 🚫 | 🚫 | ✅ |
| Manage sections & the customization catalog | 🚫 | 🚫 | ✅ |
| View customer list & their order history | 🚫 | 🚫 | ✅ |
| Access the **Admin console** | 🚫 | 🚫 | ✅ |
| Receive "payment pending" notification | 🚫 | 🚫 | ✅ |

### Authorization rules (the seam the code enforces)

- **Deny by default.** Every write is denied unless the role explicitly allows it;
  Admin is the allow-listed role for menu/payment/order-state actions.
- **Explore is public.** All *reads* of the menu need no identity — that protects
  the explore-first promise.
- **Clients act only on their own resources** (🔒): their cart, their orders, their
  proof uploads, their history. Never another customer's.
- **Money & kitchen are Admin-only.** Confirming payment and advancing order state
  are the two levers that must never leak to a Client.
- **Registration is a state change, not a wall** — a Guest becomes a Registered
  Client at checkout by supplying three fields; nothing more is gated behind it.

> This section is the backbone of the **M01 (Auth/authorization)** and **M09 (Admin
> console)** contracts, and every other module inherits these rules.

---

## 4. The experience we're promising

1. **Open → appetite.** A lively, foody home screen — big photos, three clear
   sections (Parathas · Snacks · Sweets), prices right there.
2. **Tap a dish → make it yours.** Each item opens with a description, image, and
   **customization** (ingredients + preparation method). Sweets skip the health
   angle; savoury items leave room for the *(deferred)* healthiness stars.
3. **Add to cart → checkout in seconds.** First order asks only **First Name,
   Email, Phone** — nothing more.
4. **Pay by UPI, honestly.** Show a **QR + amount**; guest pays in their own UPI app,
   then the app **auto-advances to an in-app upload screen** where they attach the
   **payment screenshot** against that order. Owner gets pinged, taps **Yes**, order
   moves to the kitchen. Simple, human, no gateway.
5. **Know what's happening.** An **Order Tracking Engine** walks every order through
   five customer-visible stages — **placed → accepted → in preparation → ready to pick
   up → completed** — notifying the guest at each step while the owner stays in control.

---

## 5. What "good" looks like (product principles)

- **Explore-first, register-late** — browsing never asks who you are.
- **Light identity, not accounts** — three fields, no passwords-as-a-wall in v1.
- **The photo sells the food** — visual, appetizing, modern; catchy "foody vibe".
- **Owner-authored menu** — Nik adds/edits any recipe (price, images, description,
  customization) without a developer.
- **The chef is part of the brand** — an **About Chef** page and per-recipe **"Check
  Chef style of making"** links to her cooking posts (Instagram) turn a transaction into
  a relationship.
- **Honest manual payments** — a trust-based UPI cycle with an explicit owner
  confirmation gate, not a black-box gateway.
- **One codebase, everywhere** — the same app is a website *and* a phone app.
- **Contracts before code** — every module's behavior is agreed in writing first.

---

## 6. The whole thing on one screen (value loop)

```
   GUEST                                   OWNER (Nik)
   ─────                                   ───────────
   browse  Parathas · Snacks · Sweets  ◄── authors menu & recipes
     │                                        (price, images, desc, options)
     ▼
   customize a dish (ingredients + prep)
     │
     ▼
   cart ─► checkout (Name · Email · Phone)
     │
     ▼
   pay by UPI QR ─► upload proof ─────────► confirm payment?  ── Yes ──► kitchen
                                              │                          preparing
                                              └── No ──► guest re-uploads   ▼
                                                                          ready ─► done
```

---

## 7. Scope boundary (v1 north star vs. later)

**In v1 (the promise above):**
Explore-first browsing · light checkout registration · owner-authored menu &
recipes · per-item customization · cart & ordering · manual UPI cycle with owner
confirmation · **order-tracking engine (5-stage lifecycle + per-stage notifications)**
· email notifications · **post-order rating (≤5★ + ≤100-char feedback)** · admin
console (incl. **business-closed dates** & **recipe display states**) · **chef social
presence (About-Chef page + per-recipe "Check Chef style" → Instagram)** · web + Android.

**Deliberately later (seams reserved, not built):**
Healthiness star engine (savoury only) · WhatsApp live notifications · iOS ·
payment gateway · app-store publishing · accounts/passwords/loyalty.

> These are named here so we *design around them* without *building them now*.
> The detailed cut lives in [`02-architecture.md` §11](02-architecture.md).

---

## 8. How this page connects to the rest

```
   blueprint.md   ── the WHY / WHAT (this page, the north star)
        │
        ├── 02-architecture.md ── the HOW IT RUNS (stack, containers, topology)
        │
        └── contracts/M01…M10  ── the EXACT BEHAVIOR (inputs, outputs, rules, states)
                                   per module — written BEFORE code
```

Every contract, screen, and API must trace back to a promise on this page. If it
doesn't serve the guest's *explore-first* joy or the owner's *one-console* control,
we question whether it belongs in v1.

---

*Next step after this is approved: write the eight module contracts under
`docs/contracts/` (M01 Auth → M10 Rating & feedback), then stand up P0 infrastructure.*
