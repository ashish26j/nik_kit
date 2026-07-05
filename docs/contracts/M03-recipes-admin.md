# M03 — Recipes & Admin Authoring (Contract)

> **Status:** DRAFT v1 · Traces to blueprint §4 principle "owner-authored menu" ·
> Shared conventions in [README](README.md).
> **Depends on:** M01 (IsAdmin), M04 (attach customization to a recipe).
> **Depended on by:** M02 (browse), M05 (order line snapshots), M09 (admin console UI).

---

## 1. Purpose

Let the **owner** author the menu without a developer: create/edit/delete
**sections** and **recipes** — name, **price**, **images**, **description**, extra
info, availability, and which section they belong to.

## 2. Scope

**In v1:** CRUD sections; CRUD recipes; multi-image upload per recipe; toggle
availability; mark `is_sweet`; attach M04 customization groups.

**Out (later):** categories/tags beyond the 3 sections, variants/SKUs, inventory
counts, scheduling (time-limited items), bulk import, healthiness authoring (M11).

## 3. Actors & authorization

| Action | Guest | Client | Admin |
|---|---|---|---|
| Any read | ✅ (via M02) | ✅ | ✅ |
| Create/edit/delete section | 🚫 | 🚫 | ✅ |
| Create/edit/delete recipe | 🚫 | 🚫 | ✅ |
| Upload/remove recipe images | 🚫 | 🚫 | ✅ |
| Toggle availability | 🚫 | 🚫 | ✅ |

All writes require **`IsAdmin`** (M01). Deny by default.

## 4. Data model

**`Section`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `name` | varchar(40) | `Parathas`/`Snacks`/`Sweets` (extensible) |
| `slug` | slug | unique |
| `sort_order` | int | |
| `is_active` | bool | default true |

**`Recipe`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `section_id` | FK → Section | required |
| `name` | varchar(120) | required |
| `price` | DECIMAL(8,2) | required, ≥ 0 |
| `description` | text | long "few more info about recipe" |
| `is_sweet` | bool | default false; Sweets excluded from healthiness later |
| `display_status` | enum `AVAILABLE`\|`UNAVAILABLE`\|`HIDDEN` | default `AVAILABLE`. **UNAVAILABLE** = shown in menu but **greyed / B&W image** + "Not available" badge, **not orderable**. **HIDDEN** = blocked from the public menu entirely. Derived `is_available` bool = (`display_status == AVAILABLE`) |
| `created_at`/`updated_at` | datetime | |

**`RecipeImage`**
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `recipe_id` | FK → Recipe | |
| `file` | image | ≤5 MB, jpeg/png/webp |
| `sort_order` | int | first = thumbnail |

## 5. API surface (all `IsAdmin` unless noted)

### Sections
- `GET /api/v1/admin/sections` — list (incl. inactive).
- `POST /api/v1/admin/sections` — `{ name, sort_order }`.
- `PATCH /api/v1/admin/sections/{id}` — edit / `is_active`.
  (Section `is_active=false` blocks the whole section from public browse.)
- `DELETE /api/v1/admin/sections/{id}` — allowed only if no recipes (else `409`).

### Recipes
- `GET /api/v1/admin/recipes?section={slug}` — list (incl. unavailable).
- `POST /api/v1/admin/recipes` — `{ section_id, name, price, description, is_sweet }`.
- `PATCH /api/v1/admin/recipes/{id}` — any field incl. `display_status`
  (`AVAILABLE` / `UNAVAILABLE` / `HIDDEN`).
- `DELETE /api/v1/admin/recipes/{id}` — soft-delete if referenced by past orders.
- `POST /api/v1/admin/recipes/{id}/images` — `multipart` image upload.
- `DELETE /api/v1/admin/recipes/{id}/images/{imageId}`.
- `PUT /api/v1/admin/recipes/{id}/customization` — set attached M04 groups.

```json
// POST recipe
{ "section_id": 1, "name": "Aloo Paratha", "price": "60.00",
  "description": "Stuffed potato flatbread, served with butter.", "is_sweet": false }
```

## 6. Rules & invariants

- **R1** `price ≥ 0`; name & section required.
- **R2** A recipe belongs to exactly **one** section.
- **R3** Deleting a section with recipes → `409 STATE_CONFLICT`.
- **R4** A recipe referenced by any past order is **soft-deleted** (`is_available=false`
  + hidden), never hard-deleted — protects order history (M05 snapshots price anyway).
- **R5** First image (`sort_order=0`) is the thumbnail used by M02.
- **R6** `is_sweet=true` marks the item out-of-scope for future healthiness (M11).
- **R7** `display_status` drives visibility: `AVAILABLE` (normal, orderable),
  `UNAVAILABLE` (visible but greyed/B&W + "Not available", **M05 refuses to add it to
  cart**), `HIDDEN` (absent from public browse). Admin always sees all three.

## 7. States

`Recipe.is_available` toggles visibility; no richer lifecycle in v1.

## 8. Dependencies & seams

- **M04**: recipes attach customization groups (via `PUT …/customization`).
- **M05**: order lines **snapshot** name+price at order time, so later edits/deletes
  don't rewrite history.
- **Seam:** `health_inputs` (ingredients/prep metadata) can be added for **M11**.

## 9. Acceptance criteria

- [ ] Admin creates a recipe under "Parathas" with price + description; it appears in
      M02 browse.
- [ ] Admin uploads 3 images; first is the M02 thumbnail.
- [ ] Setting `display_status=UNAVAILABLE` keeps it in the menu but greyed/B&W and
      non-orderable; `HIDDEN` removes it from public browse; both stay visible in admin.
- [ ] Deleting a section that still has recipes returns `409`.
- [ ] A recipe used in a completed order cannot be hard-deleted; it soft-deletes.
- [ ] Every write rejects non-admin callers with `403`.
