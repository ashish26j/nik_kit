# M02 — Menu & Sections (Contract)

> **Status:** DRAFT v1 · Traces to blueprint §4 (experience) · Shared conventions in
> [README](README.md).
> **Depends on:** M03 (recipes are authored there), M04 (customization preview).
> **Depended on by:** the client browse experience, M05 (add to cart).

---

## 1. Purpose

The **public, read-only** storefront: present the three sections (**Parathas, Snacks,
Sweets**) and their available recipes so anyone can browse with zero sign-up.

## 2. Scope

**In v1:** list sections; list recipes within a section; recipe detail view; search/
filter within a section; "available" filtering. **Read-only & public.**

**Out (later):** recommendations, favourites, cross-section search ranking,
promotions/badges, healthiness-star display (M11 seam).

## 3. Actors & authorization

| Action | Guest | Client | Admin |
|---|---|---|---|
| List sections | ✅ | ✅ | ✅ |
| List recipes in a section | ✅ | ✅ | ✅ |
| View recipe detail | ✅ | ✅ | ✅ |
| Create/edit sections or recipes | 🚫 | 🚫 | ✅ (via **M03**) |

> M02 **only reads**. All authoring lives in M03. Menu reads require **no token** (R1).

## 4. Data model

Reads entities owned by **M03** (`Section`, `Recipe`) and **M04**
(`CustomizationGroup`). No tables of its own. Relevant read-shape:

**`Section`** (owned M03): `id`, `name` (`Parathas|Snacks|Sweets`), `slug`,
`sort_order`, `is_active`.
**`Recipe`** (owned M03): `id`, `section_id`, `name`, `price`, `description`,
`images[]`, `display_status` (`AVAILABLE`/`UNAVAILABLE`/`HIDDEN`), `is_sweet`.

**Store status** (owned by **M09** `BusinessClosure`): whether the business is open now
and, if closed, until when — surfaced publicly here for the storefront banner.

## 5. API surface

### `GET /api/v1/sections` — public
```json
[ { "id": 1, "name": "Parathas", "slug": "parathas", "sort_order": 1 },
  { "id": 2, "name": "Snacks",   "slug": "snacks",   "sort_order": 2 },
  { "id": 3, "name": "Sweets",   "slug": "sweets",   "sort_order": 3 } ]
```

### `GET /api/v1/sections/{slug}/recipes` — public
Query params: `?q=<text>` (name search). Returns `AVAILABLE` **and** `UNAVAILABLE`
items (so "Not available" dishes still show, greyed); **excludes `HIDDEN`**.
```json
[ { "id": 10, "name": "Aloo Paratha", "price": "60.00",
    "thumbnail": "/media/recipes/10/thumb.jpg",
    "display_status": "AVAILABLE", "is_available": true } ]
```
The client greys/desaturates the image and disables "Add" when
`display_status == "UNAVAILABLE"`.

### `GET /api/v1/store/status` — public
Storefront banner + a checkout pre-check (data owned by M09).
```json
{ "is_open": false, "message": "Closed until 10 Jul", "reopens_on": "2026-07-10" }
```

### `GET /api/v1/recipes/{id}` — public
Full detail incl. description, all images, and the **customization groups** (from M04)
needed to render the "make it yours" screen.
```json
{ "id": 10, "section": "Parathas", "name": "Aloo Paratha", "price": "60.00",
  "description": "Stuffed potato flatbread…", "images": ["/media/…1.jpg","…2.jpg"],
  "is_sweet": false,
  "chef_style": { "platform": "INSTAGRAM", "url": "https://instagram.com/p/…" } | null,
  "customization": [ /* M04 group shape */ ] }
```
Errors: `404 NOT_FOUND` (unknown or inactive recipe).

## 6. Rules & invariants

- **R1** Only `is_active` sections appear. Within them, `AVAILABLE` + `UNAVAILABLE`
  recipes appear (UNAVAILABLE greyed & non-orderable); `HIDDEN` recipes are excluded.
- **R2** Sections render in `sort_order`; the three v1 sections are seeded.
- **R3** Prices/images/description shown are exactly M03's stored values (no
  transformation).
- **R4** Recipe detail embeds M04 customization so the client screen is one call.
- **R4a** Recipe detail includes `chef_style` (platform + url) when the recipe has one
  set (M03 R8 / [M12](M12-chef-social.md)), else `null`; the app renders "Check Chef
  style of making" only when present.
- **R5** Endpoints are cache-friendly (GET, public) — safe to CDN later.

## 7. States

Stateless (read-only projection of M03/M04 data).

## 8. Dependencies & seams

- **M03** supplies sections/recipes; **M04** supplies customization groups.
- **Seam:** a `health_stars` field can appear in recipe detail when **M11** ships;
  clients ignore it until then.

## 9. Acceptance criteria

- [ ] `GET /sections` returns exactly the three seeded sections in order.
- [ ] `GET /sections/parathas/recipes` lists only available parathas.
- [ ] `GET /recipes/{id}` returns detail **with** customization groups embedded.
- [ ] `UNAVAILABLE` recipes still appear (with `display_status` set so the UI greys
      them); `HIDDEN` recipes and inactive sections are excluded; direct fetch of a
      `HIDDEN` recipe returns 404.
- [ ] `GET /store/status` returns open/closed + banner message from M09 closures.
- [ ] All three endpoints succeed with **no** auth token.
