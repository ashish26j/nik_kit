# M04 — Customization (Contract)

> **Status:** DRAFT v1 · Traces to raw_input "customization option for each item —
> ingredients & preparation method" · Shared conventions in [README](README.md).
> **Depends on:** M01 (IsAdmin to author), M03 (attach groups to recipes).
> **Depended on by:** M02 (render options), M05 (selected options on cart/order lines).

---

## 1. Purpose

Let each item be **made to taste**: per-recipe **ingredient** and **preparation
method** choices the customer selects before adding to cart. Admin authors the option
catalog; customers pick from it.

## 2. Scope

**In v1:** admin-authored **customization groups** (e.g. "Spice level", "Add-ons")
each with **options**; attach groups to recipes; single- or multi-select; optional
per-option **price delta**; customer selections captured on cart/order lines.
Example paid add-ons in the "Add-ons" group: Extra butter (+₹10), Cheese (+₹20),
**Raita (+₹40)**. *(Free, included sides — pickle, chutney — are the recipe's
`default_accompaniment` field in M03, not a customization option.)*

**Out (later):** conditional/nested options, per-option stock, free-text special
requests, and any **healthiness weighting** of ingredients (that feeds M11 later).

## 3. Actors & authorization

| Action | Guest | Client | Admin |
|---|---|---|---|
| View a recipe's customization (read) | ✅ | ✅ | ✅ |
| Select options when ordering | ✅* | ✅ | ✅ |
| Create/edit/delete groups & options | 🚫 | 🚫 | ✅ |
| Attach groups to a recipe | 🚫 | 🚫 | ✅ (via M03) |

\* Guests can *choose* options while building a cart; identity is still only required
at checkout (M05).

## 4. Data model

**`CustomizationGroup`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `name` | varchar(60) | e.g. "Spice level", "Preparation" |
| `kind` | enum `INGREDIENT` \| `PREPARATION` | classifies for later M11 |
| `select_type` | enum `SINGLE` \| `MULTI` | radio vs. checkbox |
| `is_required` | bool | must pick ≥1 when SINGLE+required |
| `sort_order` | int | |

**`CustomizationOption`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `group_id` | FK → CustomizationGroup | |
| `label` | varchar(60) | e.g. "Extra spicy", "No onion" |
| `price_delta` | DECIMAL(8,2) | default `0.00`, may be negative |
| `is_default` | bool | pre-selected |
| `sort_order` | int | |

**`RecipeCustomization`** (join, owned here; set via M03)
`recipe_id` FK · `group_id` FK · `sort_order`.

> **Selections** made by a customer are **not** stored here — they live on
> `CartItem`/`OrderItem` (M05) as a snapshot (see R4).

## 5. API surface

### Public (read)
- Customization is embedded in `GET /recipes/{id}` (M02). No separate public call
  needed. Shape:
```json
"customization": [
  { "group_id": 5, "name": "Spice level", "kind": "PREPARATION",
    "select_type": "SINGLE", "is_required": true,
    "options": [ { "id": 51, "label": "Mild", "price_delta": "0.00", "is_default": true },
                 { "id": 52, "label": "Extra spicy", "price_delta": "0.00" } ] } ]
```

### Admin (`IsAdmin`)
- `GET/POST /api/v1/admin/customization/groups`
- `PATCH/DELETE /api/v1/admin/customization/groups/{id}`
- `POST /api/v1/admin/customization/groups/{id}/options`
- `PATCH/DELETE /api/v1/admin/customization/options/{id}`
- (attach to recipe) `PUT /api/v1/admin/recipes/{id}/customization` — body: ordered
  `group_id[]` (defined in M03).

## 6. Rules & invariants

- **R1** A `SINGLE + is_required` group must resolve to exactly one option at
  add-to-cart; `MULTI` allows 0..n unless required (≥1).
- **R2** Line price = recipe `price` + Σ selected `price_delta` (validated server-side
  in M05, never trusted from client).
- **R3** Deleting a group/option that is referenced by past orders **soft-deletes**
  (order snapshots preserve history — R4).
- **R4** The customer's chosen options are **snapshotted** onto the order line (label +
  price_delta at that moment); later catalog edits never alter past orders.
- **R5** `kind` (`INGREDIENT`/`PREPARATION`) is recorded now so **M11** can weight
  healthiness later without a migration.

## 7. States

Catalog entities are static config (no lifecycle). Selection state lives on the
cart/order line (M05).

## 8. Dependencies & seams

- **M03** attaches groups → recipes; **M05** stores selections + validates price.
- **Seam for M11:** add `health_weight` to `CustomizationOption`; `kind` already
  distinguishes ingredient vs. preparation.

## 9. Acceptance criteria

- [ ] Admin creates a "Spice level" SINGLE required group with 2 options; it embeds in
      `GET /recipes/{id}`.
- [ ] Adding to cart without choosing a required SINGLE option is rejected
      (`400 VALIDATION_ERROR`).
- [ ] An option with `price_delta="10.00"` raises the computed line price by 10.
- [ ] Editing an option label later does **not** change an already-placed order's line.
- [ ] Non-admin cannot create/edit groups or options (`403`).
