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
