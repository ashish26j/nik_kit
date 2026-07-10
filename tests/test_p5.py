"""P5 — M12 Chef profile & social (About-Chef + per-recipe "Check Chef style").

Assumes `manage.py seed_chef` has run (Niketa + Instagram bstvaranasi; example links on
Aloo/Paneer Paratha).
"""
from lib import BASE_URL, get_json, status_no_redirect, test


@test("TEST_P5_T01", "About-Chef returns the profile + Instagram handle bstvaranasi")
def chef_profile():
    d = get_json("/api/v1/chef")
    assert d["name"], d
    ig = [s for s in d["socials"] if s["platform"] == "INSTAGRAM"]
    assert ig and ig[0]["handle"] == "bstvaranasi", d
    assert "instagram.com/bstvaranasi" in ig[0]["url"], d


@test("TEST_P5_T02", "A recipe with a chef-style link exposes it in detail")
def recipe_has_chef_link():
    recs = get_json("/api/v1/sections/parathas/recipes")
    rid = next(r["id"] for r in recs if r["name"] == "Aloo Paratha")
    d = get_json(f"/api/v1/recipes/{rid}")
    assert d["chef_style"] and d["chef_style"]["platform"] == "INSTAGRAM", d
    assert d["chef_style"]["url"], d


@test("TEST_P5_T03", "A recipe without a chef-style link returns chef_style: null")
def recipe_no_chef_link():
    recs = get_json("/api/v1/sections/sweets/recipes")
    d = get_json(f"/api/v1/recipes/{recs[0]['id']}")
    assert d["chef_style"] is None, d


@test("TEST_P5_T04", "Editing the chef profile is gated (Django admin requires login)")
def chef_edit_gated():
    code = status_no_redirect(BASE_URL + "/admin/chef/chefprofile/")
    assert code in (301, 302), code
