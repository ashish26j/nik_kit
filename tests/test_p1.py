"""P1 — Menu & recipes gate tests (M02/M03/M04).

Assumes `python manage.py seed_menu` has been run (3 sections, 7 recipes,
2 customization groups; Gobi Paratha seeded as UNAVAILABLE).
"""
from lib import BASE_URL, get_json, status_no_redirect, test


@test("TEST_P1_T01", "Sections: the 3 seeded sections appear in order")
def sections_in_order():
    names = [s["name"] for s in get_json("/api/v1/sections")]
    assert names == ["Parathas", "Snacks", "Sweets"], names


@test("TEST_P1_T02", "Browse: UNAVAILABLE shown (greyed), HIDDEN excluded")
def browse_display_status():
    recs = get_json("/api/v1/sections/parathas/recipes")
    statuses = {r["display_status"] for r in recs}
    assert "AVAILABLE" in statuses, statuses
    assert "UNAVAILABLE" in statuses, statuses  # Gobi Paratha
    assert "HIDDEN" not in statuses, statuses


@test("TEST_P1_T03", "Recipe detail embeds customization for a savoury item")
def savoury_customization():
    recs = get_json("/api/v1/sections/parathas/recipes")
    rid = next(r["id"] for r in recs if r["name"] == "Aloo Paratha")
    d = get_json(f"/api/v1/recipes/{rid}")
    assert d["is_sweet"] is False, d
    assert len(d["customization"]) >= 1, d
    grp = d["customization"][0]
    assert grp.get("options"), grp
    # price_delta must be a decimal string per contract (server-authoritative)
    assert all("price_delta" in o for o in grp["options"]), grp


@test("TEST_P1_T04", "Sweets carry no customization")
def sweets_no_customization():
    recs = get_json("/api/v1/sections/sweets/recipes")
    d = get_json(f"/api/v1/recipes/{recs[0]['id']}")
    assert d["is_sweet"] is True, d
    assert d["customization"] == [], d


@test("TEST_P1_T05", "Store status stub reports open")
def store_status_open():
    d = get_json("/api/v1/store/status")
    assert d["is_open"] is True, d


@test("TEST_P1_T06", "Unknown recipe returns 404")
def unknown_recipe_404():
    code = status_no_redirect(BASE_URL + "/api/v1/recipes/999999")
    assert code == 404, code


@test("TEST_P1_T07", "Django admin (owner authoring surface) is reachable")
def admin_reachable():
    code = status_no_redirect(BASE_URL + "/admin/")
    assert code in (301, 302), f"expected redirect to login, got {code}"


@test("TEST_P1_T08", "Included default accompaniments (pickle / chutney) on recipe detail")
def default_accompaniment():
    recs = get_json("/api/v1/sections/parathas/recipes")
    aloo = get_json(f"/api/v1/recipes/{next(r['id'] for r in recs if r['name'] == 'Aloo Paratha')}")
    assert aloo["default_accompaniment"] == "Pickle", aloo
    snacks = get_json("/api/v1/sections/snacks/recipes")
    samosa = get_json(f"/api/v1/recipes/{next(r['id'] for r in snacks if r['name'] == 'Samosa')}")
    assert "chutney" in samosa["default_accompaniment"].lower(), samosa


@test("TEST_P1_T09", "Raita (+40) is offered as an Add-ons customization option")
def raita_addon():
    recs = get_json("/api/v1/sections/parathas/recipes")
    d = get_json(f"/api/v1/recipes/{next(r['id'] for r in recs if r['name'] == 'Aloo Paratha')}")
    addons = next(g for g in d["customization"] if g["name"] == "Add-ons")
    raita = next((o for o in addons["options"] if o["label"] == "Raita"), None)
    assert raita and raita["price_delta"] == "40.00", addons


@test("TEST_P1_T10", "Recipe media gallery returns ordered items (images + video link)")
def media_gallery():
    recs = get_json("/api/v1/sections/parathas/recipes")
    d = get_json(f"/api/v1/recipes/{next(r['id'] for r in recs if r['name'] == 'Aloo Paratha')}")
    media = d["media"]
    assert len(media) >= 2, media
    kinds = {m["kind"] for m in media}
    assert "IMAGE" in kinds and "VIDEO" in kinds, kinds
    assert all(m["url"] for m in media), media


@test("TEST_P1_T11", "Thumbnail = first image; a recipe without media has none")
def thumbnail_from_media():
    recs = get_json("/api/v1/sections/parathas/recipes")
    aloo = next(r for r in recs if r["name"] == "Aloo Paratha")
    gobi = next(r for r in recs if r["name"] == "Gobi Paratha")
    assert aloo["thumbnail"], aloo
    assert gobi["thumbnail"] is None, gobi
    d = get_json(f"/api/v1/recipes/{gobi['id']}")
    assert d["media"] == [], d
