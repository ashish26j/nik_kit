"""P0 — Infrastructure gate tests. Requires: docker compose up (db, app, ui)."""
from lib import UI_URL, get_json, http_get, test


@test("TEST_P0_T01", "API health endpoint reports ok + db connected")
def health_ok():
    data = get_json("/api/v1/health")
    assert data["status"] == "ok", data
    assert data["db"] == "connected", data


@test("TEST_P0_T02", "Web (ui/nginx) serves the page and proxies the API")
def ui_serves_and_proxies():
    status, _ = http_get(UI_URL + "/")
    assert status == 200, f"ui root → HTTP {status}"
    status, body = http_get(UI_URL + "/api/v1/health")
    assert status == 200 and '"ok"' in body, f"ui proxy → {status} {body}"
