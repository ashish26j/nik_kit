# M12 — Chef Profile & Social Presence (Contract)

> **Status:** DRAFT v1 · New feature module. Traces to blueprint "connect people with
> the business". Shared conventions in [README](README.md).
> **Depends on:** M01 (IsAdmin to edit). **Reused by:** M03 (per-recipe "chef style" link).
>
> *(M11 Healthiness stays reserved/deferred; this is M12.)*

---

## 1. Purpose

Let the chef (**Niketa**) build a personal connection with customers: an **"About Chef"**
page (bio + social links) and, per recipe, a link to **her cooking post/reel** so guests
can *"Check Chef style of making"*. **v1: Instagram only** (handle **`bstvaranasi`**),
modeled so more platforms plug in later.

## 2. Scope

**In v1:**
- A **ChefProfile** (name, tagline, bio, avatar) with **social links** → the *About Chef*
  page.
- A reusable **`SocialLink`** shape (`platform` + `handle`/`url`) — also used by M03's
  per-recipe chef-style link (feature A).
- Public read of the chef profile; admin edits it.
- Instagram only; `bstvaranasi` seeded as the business handle.

**Out (later):**
- Other platforms (Facebook / YouTube / WhatsApp), embedded/auto-pulled feeds, follower
  counts, multiple links per recipe, native-app deep links, per-post captions.

## 3. Actors & authorization

| Action | Guest | Client | Admin |
|---|---|---|---|
| View **About Chef** + social links | ✅ | ✅ | ✅ |
| Open a recipe's "Check Chef style" link | ✅ | ✅ | ✅ |
| Edit chef profile / social links | 🚫 | 🚫 | ✅ |
| Set a recipe's chef-style link | 🚫 | 🚫 | ✅ (via **M03**) |

Reads are **public** (no token). All edits require **`IsAdmin`** (M01).

## 4. Data model

**`SocialLink`** (value object — embedded on ChefProfile; the same shape is what a
recipe's chef-style link conforms to)
| Field | Type | Notes |
|---|---|---|
| `platform` | enum `INSTAGRAM` | v1 only value; enum reserved for FB/YT/etc. later |
| `handle` | varchar(60) | e.g. `bstvaranasi` |
| `url` | URL | full link; if omitted, derived as `https://instagram.com/<handle>` |

**`ChefProfile`** (singleton — the *About Chef* content)
| Field | Type | Notes |
|---|---|---|
| `id` | int PK | one row (singleton) |
| `name` | varchar(80) | e.g. "Niketa" |
| `tagline` | varchar(140) | short line under the name |
| `bio` | text | the story / description |
| `avatar` | image | chef photo (≤5 MB, jpeg/png/webp) |
| `socials` | list of `SocialLink` | v1: one Instagram link (`bstvaranasi`) |
| `updated_at` | datetime | |

> **Feature A (per-recipe link)** lives on the **Recipe** model (owned by **M03**) as
> `chef_style_platform` (enum, default `INSTAGRAM`) + `chef_style_url` (the post/reel
> link). It conforms to `SocialLink` above. See [M03](M03-recipes-admin.md).

## 5. API surface

### Public
- `GET /api/v1/chef` — the About-Chef payload.
```json
{ "name": "Niketa", "tagline": "Home-style Banarasi cooking",
  "bio": "…", "avatar_url": "/media/chef/avatar.jpg",
  "socials": [ { "platform": "INSTAGRAM", "handle": "bstvaranasi",
                 "url": "https://instagram.com/bstvaranasi" } ] }
```
- A recipe's chef-style link is delivered inside `GET /recipes/{id}` (M02), not here.

### Admin (`IsAdmin`)
- Managed via **Django admin** (edit the ChefProfile singleton + its socials) in v1.
  A thin `GET/PATCH /api/v1/admin/chef` may be added when the custom console lands.

## 6. Rules & invariants

- **R1** `platform` is an enum; **only `INSTAGRAM` is enabled in v1** — other values are
  rejected until their channel is turned on.
- **R2** If a `SocialLink.url` is blank, it's derived from the handle
  (`https://instagram.com/<handle>`).
- **R3** Reads are public; every edit is **Admin-only**.
- **R4** ChefProfile is a **singleton** — exactly one row; the About page reads it.
- **R5** The page is **content only** — it never exposes customer data, and the chef
  chooses what to publish.
- **R6** A recipe shows "Check Chef style of making" **only if** its `chef_style_url` is
  set (M03); otherwise the link is hidden.

## 7. Dependencies & seams

- **M03** per-recipe chef-style link uses this `SocialLink` shape; **M02** delivers it in
  recipe detail; the **About Chef** screen (frontend) renders `GET /chef`.
- **Seam:** extend `platform` to add channels; promote `socials` to allow several links;
  a recipe could later carry multiple posts.

## 8. Acceptance criteria

- [ ] `GET /chef` returns Niketa's profile with the Instagram link (`bstvaranasi`).
- [ ] The About-Chef screen renders bio + a tappable Instagram icon opening the handle.
- [ ] A recipe with `chef_style_url` set shows **"Check Chef style of making"** that opens
      that Instagram post; a recipe without it shows no such link.
- [ ] Non-admins cannot edit the chef profile or a recipe's chef-style link (`403`).
- [ ] A non-Instagram `platform` value is rejected in v1.
